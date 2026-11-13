"""Local inference endpoint. Predictions are review candidates, not confirmed notation."""
import io,json,threading
from pathlib import Path
import joblib,librosa,numpy as np,soundfile as sf
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from core import Extractor,windows,SR,CONFIG
from guitar_separation import GuitarSeparator,CHECKPOINT

app=FastAPI(title='Guitar technique research prototype')
artifact=Path(__file__).parent/'artifacts/classifier.joblib'
lock=threading.Lock();bundle=None;extractor=None;loaded_key=None
backend_config=Path(__file__).parent/'active-backend.json'
separator=GuitarSeparator()
DISABLED_DETAIL='Automatic technique analysis is turned off.'

def backend_selection():
    if not backend_config.exists():return 'svm',artifact
    settings=json.loads(backend_config.read_text(encoding='utf-8'))
    kind=settings.get('backend')
    if kind=='disabled':return kind,None
    if kind not in {'svm','crnn','crnn_transfer','tab_pitch'}:raise ValueError('Unsupported technique backend')
    root=Path(__file__).resolve().parent
    path=(root/settings['artifact']).resolve()
    if not path.is_relative_to(root):raise ValueError('Technique artifact must stay inside the local model directory')
    return kind,path

@app.get('/health')
def health():
    try:kind,path=backend_selection()
    except (ValueError,KeyError):return {'available':False,'detail':'Invalid local technique backend configuration'}
    if kind=='disabled':return {'available':False,'backend':kind,'detail':DISABLED_DETAIL}
    if kind=='tab_pitch':
        return {'available':path.exists() and CHECKPOINT.exists(),'backend':kind,
                'model':'TAB pitch-span CNN-BiGRU CRNN','requires_muscriptor_notes':True,
                'separation':{'model':'htdemucs_6s','stem':'guitar','available':CHECKPOINT.exists()}}
    return {'available':path.exists() and CHECKPOINT.exists(),'classifier_available':path.exists(),'backend':kind,'model':'CNN-BiGRU CRNN' if kind!='svm' else 'SpectroFusionNet-inspired reproduction',
     'separation':{'model':'htdemucs_6s','stem':'guitar','available':CHECKPOINT.exists()},
     'context_seconds':2,'validated_scope':'dataset clips only','unsupported':['pick_scrape','up_down_pick_direction','bend_amount','simultaneous_techniques']}

@app.post('/analyze')
def analyze(file:UploadFile=File(...),notes:str|None=Form(None)):
    global bundle,extractor,loaded_key
    try:kind,path=backend_selection()
    except (ValueError,KeyError):raise HTTPException(503,'Invalid local technique backend configuration')
    if kind=='disabled':raise HTTPException(503,DISABLED_DETAIL)
    if not path.exists():raise HTTPException(503,'Technique classifier has not been trained.')
    if not lock.acquire(blocking=False):raise HTTPException(409,'Technique analysis is busy.')
    try:
        content=file.file.read(100*1024*1024+1)
        if len(content)>100*1024*1024:raise HTTPException(413,'Audio exceeds 100 MB')
        try:y,sr=sf.read(io.BytesIO(content),dtype='float32',always_2d=True)
        except Exception:raise HTTPException(400,'Could not decode audio')
        if len(y)/sr>300:raise HTTPException(413,'Audio exceeds 5 minutes')
        if not y.size or not np.isfinite(y).all():raise HTTPException(400,'Empty or invalid audio')
        if kind=='tab_pitch':
            from tab_pitch_inference import MODEL_ID,Predictor,spans_from_notes
            try:spans=spans_from_notes(notes,len(y)/sr)
            except (ValueError,OverflowError) as error:raise HTTPException(400,str(error))
        try:y,sr,separation=separator.separate(y,sr,content)
        except (ValueError,RuntimeError,ImportError) as error:raise HTTPException(503,f'Guitar separation failed; original mix was not analyzed. {error}')
        y=y.mean(axis=1)
        key=(kind,str(path.resolve()),path.stat().st_mtime_ns)
        if kind=='tab_pitch':
            if bundle is None or loaded_key!=key:
                bundle=Predictor(path);extractor=None;loaded_key=key
            return {'model':MODEL_ID,'architecture':'crnn','backend':kind,
                    'probability_method':'uncalibrated_sigmoid','candidates':bundle.predict(y,sr,spans),
                    'automatic_note_assignment':True,'input_source':'separated_guitar','separation':separation,
                    'warning':'Experimental pitch-span predictions. Mixed-song and ordinary playing accuracy is unverified.'}
        if sr!=SR:y=librosa.resample(y,orig_sr=sr,target_sr=SR)
        if bundle is None or loaded_key!=key:
            if kind!='svm':
                if kind=='crnn_transfer':
                    from crnn_transfer import Predictor
                else:
                    from crnn import Predictor
                candidate=Predictor(path);candidate_extractor=None
            else:
                candidate=joblib.load(path)
                if candidate['config']!=CONFIG:raise HTTPException(503,'Model configuration mismatch')
                candidate_extractor=Extractor()
            bundle=candidate;extractor=candidate_extractor;loaded_key=key
        candidates=[];chunks=list(windows(y))
        for i in range(0,len(chunks),8):
            batch=chunks[i:i+8]
            if kind!='svm':
                model=bundle;probabilities=model.predict_audio([a for _,a in batch])
            else:
                f=extractor.features([a for _,a in batch]);model=bundle['classifier'];probabilities=model.predict_proba(f)
            for (start,a),scores in zip(batch,probabilities):
                if np.sqrt(np.mean(a*a))<1e-4:continue
                ranked=sorted([{'label':str(label),'probability':float(score)} for label,score in zip(model.classes_,scores)],key=lambda c:-c['probability'])
                candidates.append({'start':start,'end':min(len(y)/SR,start+2),'label':ranked[0]['label'],'alternatives':ranked,
                  'status':'estimated','granularity':'audio_window','confidence':ranked[0]['probability']})
        return {'model':bundle.model_id if kind!='svm' else bundle.get('model_id','spectrofusion-inspired-v2'),
          'architecture':'crnn' if kind!='svm' else 'svm','backend':kind,'context_seconds':2,'probability_method':'uncalibrated_softmax' if kind!='svm' else 'group_calibrated_sigmoid',
          'candidates':candidates,'automatic_note_assignment':True,'input_source':'separated_guitar','separation':separation,
          'warning':('Experimental clip predictions; note-level and mixed audio are not validated.' if 'normal' in model.classes_ else 'Closed-set experimental clip predictions; ordinary playing and mixed audio may be misclassified.')}
    finally:lock.release()

if __name__=='__main__':
    import uvicorn
    import torch
    torch.set_num_threads(4)
    uvicorn.run(app,host='127.0.0.1',port=8224)

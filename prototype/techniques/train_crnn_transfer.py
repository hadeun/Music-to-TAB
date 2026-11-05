"""Train the recurrent head on cached ordered features from the existing CNN."""
import argparse,hashlib,json,os
from pathlib import Path
import numpy as np,torch
from crnn import recording_sequences
from crnn_transfer import Encoder,TransferCRNN,CONFIG
from train_crnn import fit,predict,inner_split
from train_combined import outer_splits,metrics
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts-crnn-transfer'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=24);args=parser.parse_args()
    torch.set_num_threads(min(4,os.cpu_count() or 1));OUT.mkdir(exist_ok=True);cache=OUT/'cache';cache.mkdir(exist_ok=True)
    rows=json.loads((ROOT/'artifacts-guitar-techs-no-normal/manifest-used.json').read_text());rows=[r for r in rows if r['label']!='normal']
    classes=sorted({r['label'] for r in rows});ids={label:i for i,label in enumerate(classes)};encoder=Encoder()
    arrays=[];owners=[]
    for i,row in enumerate(rows):
        spectra=recording_sequences(row,ROOT/'artifacts-crnn/cache')
        digest=hashlib.sha256(spectra.astype(np.float16).tobytes()+b'resnet-temporal-v1').hexdigest();path=cache/f'{digest}.npz'
        if path.exists():
            with np.load(path) as cached:sequence=cached['sequence']
        else:
            sequence=encoder.features(spectra).astype(np.float16)
            pending=path.with_suffix('.pending.npz');np.savez_compressed(pending,sequence=sequence);pending.replace(path)
        arrays.append(sequence);owners.extend([i]*len(sequence))
        if (i+1)%100==0:print(f'Pretrained temporal features {i+1}/{len(rows)}',flush=True)
    del encoder
    X=np.concatenate(arrays);del arrays;owners=np.array(owners);y=np.array([ids[r['label']] for r in rows]);targets=y[owners];groups=np.array([r['group'] for r in rows])
    (OUT/'manifest-used.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    guesses=np.empty(len(rows),dtype=int);folds=[];epochs=[]
    for number,(player,tr,te) in enumerate(outer_splits(rows)):
        a,b=inner_split(tr,y,groups);print('Transfer CRNN epoch selection:',player,flush=True)
        model,best,history=fit(X,targets,owners,y,a,args.epochs,len(classes),b,342+number,TransferCRNN);del model
        print('Refit transfer CRNN outer training:',player,best,flush=True)
        model,_,_=fit(X,targets,owners,y,tr,best,len(classes),run_seed=442+number,model_cls=TransferCRNN)
        guesses[te]=predict(model,X,targets,owners,te).argmax(axis=1);del model;epochs.append(best)
        folds.append({'held_out_player':player,'selected_epoch':best,'selection_history':history,
         'metrics':metrics(np.array(classes)[y[te]],np.array(classes)[guesses[te]],classes)})
    truth=np.array(classes)[y];prediction=np.array(classes)[guesses]
    report={'config':CONFIG,'classes':classes,'recordings':len(rows),'temporal_windows':len(X),'folds':folds,
     'combined':metrics(truth,prediction,classes),'datasets':{},'probability_method':'uncalibrated softmax',
     'scope':'Same grouped outer evaluation; frozen pretrained CNN with seven ordered steps per two-second context. Single-label clip supervision, no exact note-pair or compound-technique validation.',
     'selection':'Group-disjoint inner epoch selection, outer refit and held-out prediction; outer data already used in previous development.',
     'preprocessing':'Up to four legacy crops per recording; cached MFCC/gammatone 64x201 inputs resized to224; differs from original SVM preprocessing.'}
    for dataset in ['guitar_style','guitar_techs']:
        mask=np.array([r['dataset']==dataset for r in rows]);report['datasets'][dataset]=metrics(truth[mask],prediction[mask],sorted(set(truth[mask])))
    (OUT/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (OUT/'predictions.json').write_text(json.dumps([{'index':i,'truth':str(a),'prediction':str(b)} for i,(a,b) in enumerate(zip(truth,prediction))],indent=2),encoding='utf-8')
    final_epochs=max(1,int(np.median(epochs)));print('Fit final transfer CRNN:',final_epochs,flush=True)
    model,_,_=fit(X,targets,owners,y,np.arange(len(rows)),final_epochs,len(classes),run_seed=542,model_cls=TransferCRNN)
    torch.save({'config':CONFIG,'classes':classes,'model_id':'guitar-technique-crnn-transfer-v2','epochs':final_epochs,
      'state_dict':{k:v.detach().cpu() for k,v in model.state_dict().items()}},OUT/'classifier.pending')
    (OUT/'classifier.pending').replace(OUT/'classifier.pt')
    print(json.dumps({'combined_macro_f1':report['combined']['macro_f1'],'datasets':{k:v['macro_f1'] for k,v in report['datasets'].items()}},indent=2),flush=True)
if __name__=='__main__':main()

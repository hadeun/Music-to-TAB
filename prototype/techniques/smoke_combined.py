"""Run an actual local candidate through the endpoint without changing the live model."""
import io,json
from pathlib import Path
import librosa,soundfile as sf
from starlette.datastructures import UploadFile
import server
ROOT=Path(__file__).resolve().parent
out=ROOT/'artifacts-guitar-techs-no-normal'
rows=json.loads((out/'manifest-used.json').read_text())
row=next(r for r in rows if r['dataset']=='guitar_techs' and r['label']=='palm_mute')
y,_=librosa.load(row['path'],sr=22050,mono=True,offset=row['start'],duration=2)
buffer=io.BytesIO();sf.write(buffer,y,22050,format='WAV');buffer.seek(0)
server.artifact=out/'classifier.joblib'
server.backend_config=ROOT/'disabled-selector-for-isolated-svm-smoke.json'
result=server.analyze(UploadFile(file=buffer,filename='smoke.wav'))
assert result['model']=='spectrofusion-inspired-guitar-techs-v4-no-normal'
assert result['candidates']
for candidate in result['candidates']:
    assert len(candidate['alternatives'])==12
    assert all(c['label']!='normal' for c in candidate['alternatives'])
    assert abs(sum(c['probability'] for c in candidate['alternatives'])-1)<1e-6
report={'model':result['model'],'windows':len(result['candidates']),'classes':len(result['candidates'][0]['alternatives']),
 'top_label':result['candidates'][0]['label'],'note':'Smoke test uses a training clip and is not generalization evidence; live classifier unchanged.'}
(out/'smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)

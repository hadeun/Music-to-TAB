"""Actual trained CRNN endpoint smoke test; never edits the live backend selector."""
import argparse,io,json,tempfile
from pathlib import Path
import librosa,numpy as np,soundfile as sf
from starlette.datastructures import UploadFile
import server
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--transfer',action='store_true');args=parser.parse_args()
out=ROOT/('artifacts-crnn-transfer' if args.transfer else 'artifacts-crnn')
kind='crnn_transfer' if args.transfer else 'crnn'
model_id='guitar-technique-crnn-transfer-v2' if args.transfer else 'guitar-technique-crnn-v1'
rows=json.loads((out/'manifest-used.json').read_text())
row=next(r for r in rows if r['label']=='palm_mute')
y,_=librosa.load(row['path'],sr=22050,mono=True,offset=row.get('start',0),duration=2)
buffer=io.BytesIO();sf.write(buffer,y,22050,format='WAV');buffer.seek(0)
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
    settings=Path(folder)/'backend.json';settings.write_text(json.dumps({'backend':kind,'artifact':str(out.relative_to(ROOT)/'classifier.pt')}))
    server.backend_config=settings
    assert server.health()['backend']==kind and server.health()['available']
    result=server.analyze(UploadFile(file=buffer,filename='smoke.wav'))
assert result['model']==model_id and result['architecture']=='crnn'
assert result['probability_method']=='uncalibrated_softmax'
assert result['candidates']
for candidate in result['candidates']:
    alternatives=candidate['alternatives'];assert len(alternatives)==12
    assert all(c['label']!='normal' and np.isfinite(c['probability']) for c in alternatives)
    assert abs(sum(c['probability'] for c in alternatives)-1)<1e-5
summary={'model':result['model'],'windows':len(result['candidates']),'classes':12,'top_label':result['candidates'][0]['label'],
 'scope':'Training-clip endpoint smoke test only, not generalization evidence; live backend unchanged.'}
(out/'smoke.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)

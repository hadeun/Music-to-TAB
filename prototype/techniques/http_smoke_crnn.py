"""Verify the active CRNN through the actual local website proxy."""
import io,json,urllib.request
from pathlib import Path
import librosa,soundfile as sf
ROOT=Path(__file__).resolve().parent
with urllib.request.urlopen('http://127.0.0.1:4181/api/techniques/health',timeout=30) as response:health=json.load(response)
assert health['available'] and health['backend']=='crnn_transfer'
rows=json.loads((ROOT/'artifacts-crnn-transfer/manifest-used.json').read_text())
if health.get('separation'):
    assert health['separation']['model']=='htdemucs_6s' and health['separation']['stem']=='guitar'
    content=(ROOT/'separation-models/smoke-input.wav').read_bytes()
else:
    row=next(r for r in rows if r['label']=='palm_mute')
    y,_=librosa.load(row['path'],sr=22050,mono=True,offset=row.get('start',0),duration=2)
    audio=io.BytesIO();sf.write(audio,y,22050,format='WAV');content=audio.getvalue()
boundary='MusicToTabCRNNSmokeBoundary'
body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="smoke.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+content+f'\r\n--{boundary}--\r\n'.encode())
request=urllib.request.Request('http://127.0.0.1:4181/api/techniques/analyze',data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(request,timeout=180) as response:result=json.load(response)
assert result['model']=='guitar-technique-crnn-transfer-v2' and result['architecture']=='crnn'
assert len(result['candidates'][0]['alternatives'])==12
if health.get('separation'):
    assert result['input_source']=='separated_guitar' and result['separation']['config']['stem']=='guitar'
    assert abs(result['separation']['duration_seconds']-8)<.001
summary={'health':health,'model':result['model'],'classes':len(result['candidates'][0]['alternatives']),
 'top_label':result['candidates'][0]['label'],'input_source':result.get('input_source'),'separation':result.get('separation'),
 'scope':'Actual HTTP proxy routing smoke test; not generalization or separation-quality evidence.'}
(ROOT/'artifacts-crnn-transfer/http-smoke.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)

"""Compute completed downloads while the remaining dataset transfers."""
import time
from pathlib import Path
from core import Extractor,file_features
root=Path(__file__).resolve().parent
extractor=Extractor();done=set()
while True:
    files=sorted((root/'dataset').rglob('*.wav'))
    for path in files:
        if str(path) in done:continue
        file_features(path,extractor,root/'artifacts/cache');done.add(str(path))
        if len(done)%10==0:print('Cached recordings:',len(done),flush=True)
    if (root/'dataset-source.json').exists():break
    time.sleep(5)
print('Feature cache ready:',len(done),flush=True)

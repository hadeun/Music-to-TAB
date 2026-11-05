"""Fetch only WAVs from the public dataset at a pinned Git commit."""
import concurrent.futures,hashlib,json,subprocess,time
from pathlib import Path
from urllib.parse import quote
import requests
root=Path(__file__).resolve().parent.parent
repo=root/'technique-data'
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
names=subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD','data/wav'],cwd=repo,text=True).splitlines()
names=[n for n in names if n.endswith('.wav')]
def download(name):
    target=root/'techniques/dataset'/Path(name).relative_to('data/wav')
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.stat().st_size>44:return
    url=f'https://raw.githubusercontent.com/magcil/guitar_style_dataset/{commit}/{quote(name)}'
    for attempt in range(3):
        try:
            session=requests.Session();session.trust_env=False
            with session.get(url,timeout=(20,90),stream=True) as response:
                response.raise_for_status()
                temp=target.with_suffix('.partial')
                with temp.open('wb') as f:
                    for chunk in response.iter_content(1024*128):f.write(chunk)
                if temp.stat().st_size<=44:raise ValueError('Empty WAV')
                temp.replace(target)
            return
        except Exception:
            if attempt==2:raise
            time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    for i,result in enumerate(pool.map(download,names),1):
        if i%10==0:print(f'Downloaded {i}/{len(names)}',flush=True)
(root/'techniques/dataset-source.json').write_text(json.dumps({'commit':commit,'files':len(names),'url':'https://github.com/magcil/guitar_style_dataset'},indent=2))
print('Dataset download complete',flush=True)

"""Download a pinned Guitar-TECHS subset from the official CC BY 4.0 record."""
import concurrent.futures, hashlib, json, shutil, time, urllib.request, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent/'guitar-techs'
NAMES={'P1_techniques.zip','P2_techniques.zip'}

def fetch(entry):
    target=ROOT/'archives'/entry['key'];target.parent.mkdir(parents=True,exist_ok=True)
    expected=entry['checksum'].split(':',1)[1]
    def valid():
        if not target.exists() or target.stat().st_size!=entry['size']:return False
        h=hashlib.md5()
        with target.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        return h.hexdigest()==expected
    if not valid():
        pending=target.with_suffix('.partial')
        for attempt in range(5):
            try:
                offset=pending.stat().st_size if pending.exists() else 0
                req=urllib.request.Request(entry['links']['self'],headers={'Range':f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(req,timeout=90) as response:
                    resume=offset>0 and response.status==206
                    size=offset if resume else 0;last=time.monotonic()
                    with pending.open('ab' if resume else 'wb') as f:
                        while True:
                            block=response.read(1024*1024)
                            if not block:break
                            f.write(block);size+=len(block)
                            if time.monotonic()-last>15:
                                print(f"{entry['key']}: {size/entry['size']:.0%}",flush=True);last=time.monotonic()
                if pending.stat().st_size!=entry['size']:raise ValueError('Incomplete download')
                pending.replace(target)
                if not valid():raise ValueError('Checksum mismatch')
                break
            except Exception as error:
                print(f"Retry {entry['key']}: {error}",flush=True)
                if attempt==4:raise
                time.sleep(2)
    destination=ROOT/'data';destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        for member in archive.infolist():
            path=(destination/member.filename).resolve()
            if not path.is_relative_to(destination.resolve()):raise ValueError('Unsafe archive path')
            if member.is_dir():path.mkdir(parents=True,exist_ok=True);continue
            if path.exists() and path.stat().st_size==member.file_size:continue
            path.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(member) as source,path.open('wb') as out:shutil.copyfileobj(source,out)
    print(f"Verified and extracted {entry['key']}",flush=True)

def main():
    ROOT.mkdir(exist_ok=True)
    with urllib.request.urlopen('https://zenodo.org/api/records/14963133',timeout=60) as response:record=json.load(response)
    (ROOT/'record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    entries=[f for f in record['files'] if f['key'] in NAMES]
    if len(entries)!=len(NAMES):raise ValueError('Unexpected dataset record')
    (ROOT/'ATTRIBUTION.md').write_text('Guitar-TECHS — Pedroza et al., ICASSP 2025.\nSource: https://zenodo.org/records/14963133\nWebsite: https://guitar-techs.github.io/\nLicense: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/\nLocal changes: subset selection; derived features and labels are documented in the training manifest.\n',encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(fetch,entries))
    (ROOT/'download-complete.json').write_text(json.dumps({'record':14963133,'files':[{k:e[k] for k in ('key','size','checksum')} for e in entries]},indent=2),encoding='utf-8')
if __name__=='__main__':main()

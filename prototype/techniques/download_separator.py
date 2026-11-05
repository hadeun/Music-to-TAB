"""Download the official htdemucs_6s checkpoint, with filename SHA256 verification."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'separation-models'
NAME='5c90dfd2-34c22ccb.th'
URL='https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/'+NAME

def main():
    ROOT.mkdir(exist_ok=True);target=ROOT/NAME
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest().startswith('34c22ccb'):
        print('Verified existing htdemucs_6s checkpoint',flush=True);return
    pending=target.with_suffix('.partial');total=0
    with urllib.request.urlopen(URL,timeout=120) as response,pending.open('wb') as output:
        size=int(response.headers.get('content-length',0))
        while True:
            data=response.read(4*1024*1024)
            if not data:break
            output.write(data);total+=len(data)
            print(f'Downloaded {total//1048576} MiB'+(f' / {size//1048576} MiB' if size else ''),flush=True)
    sha=hashlib.sha256(pending.read_bytes()).hexdigest()
    if not sha.startswith('34c22ccb'):raise ValueError('Official checkpoint checksum mismatch')
    pending.replace(target)
    (ROOT/'source.json').write_text(json.dumps({'model':'htdemucs_6s','url':URL,'sha256':sha,'source':'https://github.com/facebookresearch/demucs','license':'MIT (Demucs repository)'},indent=2),encoding='utf-8')
    print('Verified htdemucs_6s:',sha,flush=True)
if __name__=='__main__':main()

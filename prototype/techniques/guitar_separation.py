"""Official htdemucs_6s guitar-only inference, local verified weights and cached stems."""
import hashlib,json,threading,time
from fractions import Fraction
from pathlib import Path
import numpy as np,soundfile as sf,torch

ROOT=Path(__file__).resolve().parent
CHECKPOINT=ROOT/'separation-models/5c90dfd2-34c22ccb.th'
EXPECTED_SHA='34c22ccb381c6f9fdbf324f04e1e2fe21aaaf293f5ded163a162697ff9a02ddd'
CONFIG={'model':'htdemucs_6s','stem':'guitar','checkpoint_sha256':EXPECTED_SHA,'shifts':0,'overlap':.25,'segment_seconds':4,'version':1}

class GuitarSeparator:
    def __init__(self,cache=None,device=None):
        self.cache=Path(cache or ROOT/'separated-guitar-cache');self.device=device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model=None;self.lock=threading.Lock()

    def _load(self):
        if self.model is not None:return
        if not CHECKPOINT.exists():raise RuntimeError('Guitar separation weights are missing. Run techniques/download_separator.py.')
        if hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()!=EXPECTED_SHA:raise RuntimeError('Guitar separator checkpoint verification failed.')
        from demucs.htdemucs import HTDemucs
        from demucs.states import load_model
        # Explicitly allow only the two types required by this verified official package.
        with torch.serialization.safe_globals([HTDemucs,Fraction]):package=torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
        model=load_model(package)
        if 'guitar' not in model.sources:raise RuntimeError('Selected separator does not provide a guitar stem.')
        self.model=model.eval()

    def _infer(self,audio,sr):
        from demucs.apply import apply_model
        from julius import resample_frac
        self._load();model=self.model
        mix=torch.from_numpy(np.ascontiguousarray(audio.T,dtype=np.float32))
        if mix.shape[0]==1:mix=mix.repeat(2,1)
        if mix.shape[0]!=2:raise ValueError('Guitar separation requires mono or stereo audio.')
        if sr!=model.samplerate:mix=resample_frac(mix,sr,model.samplerate)
        reference=mix.mean(dim=0);mean=reference.mean();std=reference.std()
        if not torch.isfinite(std) or std<1e-8:raise ValueError('No usable audio for guitar separation.')
        normalized=(mix-mean)/std;device=self.device
        def run(on_device):
            return apply_model(model,normalized[None],device=on_device,split=True,shifts=CONFIG['shifts'],
             overlap=CONFIG['overlap'],segment=CONFIG['segment_seconds'],progress=False,num_workers=0)
        try:
            with torch.inference_mode():
                try:estimates=run(device)
                except torch.cuda.OutOfMemoryError:
                    model.to('cpu');torch.cuda.empty_cache();device='cpu';estimates=run(device)
                guitar=(estimates[0,model.sources.index('guitar')]*std+mean).T.cpu().numpy().copy()
            if not np.isfinite(guitar).all():raise RuntimeError('Invalid guitar separator output.')
            return guitar,int(model.samplerate),device
        finally:
            model.to('cpu')
            if torch.cuda.is_available():torch.cuda.empty_cache()

    def separate(self,audio,sr,source_bytes):
        audio=np.asarray(audio,dtype=np.float32)
        if audio.ndim!=2 or audio.shape[1] not in (1,2) or not len(audio) or not np.isfinite(audio).all():raise ValueError('Invalid separation input')
        if sr<=0:raise ValueError('Invalid separation sample rate')
        key=hashlib.sha256(source_bytes+json.dumps(CONFIG,sort_keys=True).encode()).hexdigest()
        self.cache.mkdir(parents=True,exist_ok=True);wave=self.cache/f'{key}.wav';meta=self.cache/f'{key}.json'
        with self.lock:
            if wave.exists() and meta.exists():
                info=json.loads(meta.read_text(encoding='utf-8'));guitar,rate=sf.read(wave,dtype='float32',always_2d=True)
                if info.get('config')!=CONFIG or rate!=44100 or not len(guitar) or not np.isfinite(guitar).all():raise RuntimeError('Invalid cached guitar stem')
                return guitar,rate,{**info,'cache_hit':True}
            started=time.monotonic();guitar,rate,device=self._infer(audio,sr)
            expected=round(len(audio)*rate/sr)
            if abs(len(guitar)-expected)>2:raise RuntimeError('Guitar stem timing mismatch')
            info={'config':CONFIG,'cache_key':key,'cache_hit':False,'input_sample_rate':sr,'sample_rate':rate,
             'duration_seconds':len(guitar)/rate,'device':device,'separation_seconds':time.monotonic()-started,'source':'separated_guitar'}
            pending=wave.with_suffix('.pending.wav');sf.write(pending,guitar,rate,subtype='FLOAT');pending.replace(wave)
            pending_meta=meta.with_suffix('.pending.json');pending_meta.write_text(json.dumps(info,indent=2),encoding='utf-8');pending_meta.replace(meta)
            return guitar,rate,info

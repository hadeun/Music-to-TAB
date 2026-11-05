"""Independent SpectroFusionNet-inspired MFCC/gammatone late-fusion implementation.

Not the authors' implementation or weights. See REPRODUCTION.md for deviations.
"""
from pathlib import Path
import hashlib
import numpy as np
import torch
import torch.nn.functional as F
import librosa
from gammatone.gtgram import gtgram
from torchvision.models import resnet50, ResNet50_Weights

SR = 22050
WINDOW = 2.0
CONFIG = {'version': 1, 'sample_rate': SR, 'window_seconds': WINDOW,
          'mfcc': 40, 'gammatone_channels': 64, 'image_size': 224,
          'backbone': 'ResNet50_Weights.IMAGENET1K_V2', 'fusion': 'elementwise_max'}


def images(samples):
    y = np.asarray(samples, dtype=np.float32).reshape(-1)
    if not y.size or not np.isfinite(y).all():
        raise ValueError('Empty or non-finite audio')
    if len(y) < int(SR * WINDOW):
        y = np.pad(y, (0, int(SR * WINDOW) - len(y)))
    mfcc = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=40, n_fft=1024, hop_length=220)
    gamma = np.log1p(gtgram(y, SR, .025, .010, 64, 50))
    out = []
    for a in (mfcc, gamma):
        low, high = np.percentile(a, [1, 99])
        a = np.clip((a - low) / max(high-low, 1e-6), 0, 1)
        t = torch.from_numpy(a.astype(np.float32))[None, None]
        t = F.interpolate(t, (224, 224), mode='bilinear', align_corners=False)
        t = t.repeat(1, 3, 1, 1)
        t = (t - torch.tensor([.485,.456,.406])[None,:,None,None]) / torch.tensor([.229,.224,.225])[None,:,None,None]
        out.append(t[0])
    return torch.stack(out)


class Extractor:
    def __init__(self, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        local = Path(__file__).parent/'resnet50-11ad3fa6.pth'
        if local.exists() and hashlib.sha256(local.read_bytes()).hexdigest().startswith('11ad3fa6'):
            self.model = resnet50(weights=None)
            self.model.load_state_dict(torch.load(local,map_location='cpu',weights_only=True))
        else:
            self.model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        self.model.fc = torch.nn.Identity()
        self.model.to(self.device).eval()

    @torch.inference_mode()
    def features(self, windows):
        x = torch.cat([images(y) for y in windows]).to(self.device)
        f = self.model(x).reshape(len(windows), 2, -1)
        return f.max(dim=1).values.cpu().numpy()


def windows(y, hop=1.0):
    size = round(SR*WINDOW)
    for start in range(0, max(1,len(y)-size+1), round(SR*hop)):
        yield start/SR, y[start:start+size]
    if len(y)>size and (len(y)-size)%round(SR*hop):
        yield (len(y)-size)/SR, y[-size:]


def file_features(path, extractor, cache, start=None, duration=None):
    path = Path(path)
    stat=path.stat()
    # Memoize source hashes: a long recording supplies many non-overlapping clips.
    key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns)
    if not hasattr(file_features,'hashes'):file_features.hashes={}
    if key not in file_features.hashes:file_features.hashes[key]=hashlib.sha256(path.read_bytes()).hexdigest()
    digest=file_features.hashes[key]
    if start is not None:digest=hashlib.sha256(f'{digest}:{start:.6f}:{duration:.6f}'.encode()).hexdigest()
    cached = Path(cache)/f'{digest}-v1.npz'
    if cached.exists():
        return np.load(cached)['features'],digest
    y,_ = librosa.load(path,sr=SR,mono=True,offset=start or 0,duration=duration)
    if not y.size or np.max(np.abs(y)) < 1e-6:
        raise ValueError(f'Silent file: {path}')
    # Non-overlapping training windows; splits are by whole source file/group.
    chunks=list(windows(y, WINDOW))
    features=[]
    for i in range(0,len(chunks),8):
        features.extend(extractor.features([a for _,a in chunks[i:i+8]]))
    result=np.asarray(features).mean(axis=0)
    cached.parent.mkdir(parents=True,exist_ok=True)
    temp=cached.with_suffix('.pending.npz')
    np.savez_compressed(temp,features=result)
    temp.replace(cached)
    return result,digest

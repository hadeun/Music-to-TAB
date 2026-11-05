"""Trainable spectral CNN -> ordered BiGRU -> attention -> clip classifier.

This is an independent CRNN, not an official SpectroFusionNet checkpoint.
Two-second context is retained; clip labels cannot supervise articulation boundaries.
"""
import hashlib
from pathlib import Path
import librosa,numpy as np,torch
from torch import nn
from gammatone.gtgram import gtgram
from core import SR

CONFIG={'version':1,'architecture':'spectral-cnn-bigru-attention','sample_rate':SR,
 'window_seconds':2.,'frames':201,'bands':64,'inputs':['mfcc','gammatone'],
 'cnn_channels':[16,32,64],'gru_hidden':64,'gru_layers':1,'bidirectional':True,
 'output':'single-label clip logits','normal_excluded':True}

def spectral_sequence(samples):
    y=np.asarray(samples,dtype=np.float32).reshape(-1)
    if not y.size or not np.isfinite(y).all():raise ValueError('Invalid audio')
    y=np.pad(y[:SR*2],(0,max(0,SR*2-len(y))))
    mfcc=librosa.feature.mfcc(y=y,sr=SR,n_mfcc=40,n_fft=1024,hop_length=220)
    gamma=np.log1p(gtgram(y,SR,.025,.010,64,50))
    images=[]
    for array in (mfcc,gamma):
        lo,hi=np.percentile(array,[1,99]);array=np.clip((array-lo)/max(hi-lo,1e-6),0,1)
        t=torch.tensor(array,dtype=torch.float32)[None,None]
        images.append(torch.nn.functional.interpolate(t,(64,201),mode='bilinear',align_corners=False)[0,0])
    return torch.stack(images)

class CRNN(nn.Module):
    def __init__(self,classes):
        super().__init__()
        layers=[];before=2
        for channels,pool in [(16,(2,2)),(32,(2,2)),(64,(2,1))]:
            layers.extend([nn.Conv2d(before,channels,3,padding=1,bias=False),nn.BatchNorm2d(channels),nn.ReLU(),nn.MaxPool2d(pool)])
            before=channels
        self.cnn=nn.Sequential(*layers)
        self.rnn=nn.GRU(64,64,batch_first=True,bidirectional=True)
        self.attention=nn.Linear(128,1)
        self.classifier=nn.Sequential(nn.Dropout(.25),nn.Linear(128,classes))

    def forward(self,x):
        # Average frequency only: retain the ordered time axis for the recurrent layer.
        sequence=self.cnn(x).mean(dim=2).transpose(1,2)
        sequence,_=self.rnn(sequence)
        weights=self.attention(sequence).softmax(dim=1)
        return self.classifier((sequence*weights).sum(dim=1))

def recording_sequences(row,cache):
    path=Path(row['path']);stat=path.stat();key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns)
    if not hasattr(recording_sequences,'hashes'):recording_sequences.hashes={}
    if key not in recording_sequences.hashes:recording_sequences.hashes[key]=hashlib.sha256(path.read_bytes()).hexdigest()
    identity=f"{recording_sequences.hashes[key]}:{row.get('start')}:{row.get('duration')}:crnn-v1-four-crops"
    digest=hashlib.sha256(identity.encode()).hexdigest();target=Path(cache)/f'{digest}.npz'
    if target.exists():
        with np.load(target) as data:return data['sequences'].astype(np.float32)
    y,_=librosa.load(path,sr=SR,mono=True,offset=row.get('start',0),duration=row.get('duration'))
    if not len(y) or np.max(np.abs(y))<1e-6:raise ValueError(f'Silent recording: {path}')
    # Preserve source grouping. Legacy exercise labels cover the whole recording;
    # sample up to four non-overlapping windows rather than average away their time axes.
    starts=list(range(0,max(1,len(y)-2*SR+1),2*SR))
    starts=[starts[i] for i in np.unique(np.linspace(0,len(starts)-1,min(4,len(starts))).astype(int))]
    result=np.stack([spectral_sequence(y[start:start+2*SR]).numpy() for start in starts])
    target.parent.mkdir(parents=True,exist_ok=True)
    pending=target.with_suffix('.pending.npz');np.savez_compressed(pending,sequences=result.astype(np.float16));pending.replace(target)
    return result

class Predictor:
    def __init__(self,path,device=None):
        self.device=device or ('cuda' if torch.cuda.is_available() else 'cpu')
        bundle=torch.load(path,map_location='cpu',weights_only=True)
        if bundle['config']!=CONFIG:raise ValueError('CRNN configuration mismatch')
        self.classes_=np.array(bundle['classes']);self.model_id=bundle['model_id']
        self.model=CRNN(len(self.classes_));self.model.load_state_dict(bundle['state_dict']);self.model.to(self.device).eval()
        self.temperature=float(bundle.get('temperature',1.))

    @torch.inference_mode()
    def predict_audio(self,windows):
        x=torch.stack([spectral_sequence(y) for y in windows]).to(self.device)
        return (self.model(x)/self.temperature).softmax(dim=1).cpu().numpy()

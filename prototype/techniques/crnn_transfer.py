"""Reuse the existing frozen ResNet50, preserving its temporal feature map for a GRU."""
import numpy as np,torch
from torch import nn
from core import Extractor
from crnn import spectral_sequence

CONFIG={'version':2,'architecture':'pretrained-resnet50-bigru-attention','sample_rate':22050,
 'window_seconds':2.,'input':'mfcc-gammatone-64x201-resized224','cnn':'ImageNet ResNet50 IMAGENET1K_V2 frozen',
 'temporal_steps':7,'feature_dim':2048,'fusion':'elementwise_max','gru_hidden':64,
 'output':'single-label clip logits','normal_excluded':True}

class Encoder:
    def __init__(self,device=None):
        source=Extractor(device);self.device=source.device
        self.model=nn.Sequential(*list(source.model.children())[:-2]).eval()
        for parameter in self.model.parameters():parameter.requires_grad_(False)

    @torch.inference_mode()
    def features(self,windows):
        x=torch.as_tensor(windows,dtype=torch.float32,device=self.device);batch=len(x)
        x=x.reshape(batch*2,1,64,201)
        x=nn.functional.interpolate(x,(224,224),mode='bilinear',align_corners=False).repeat(1,3,1,1)
        mean=torch.tensor([.485,.456,.406],device=self.device)[None,:,None,None]
        std=torch.tensor([.229,.224,.225],device=self.device)[None,:,None,None]
        fmap=self.model((x-mean)/std)
        # Only frequency is pooled. Seven time-ordered vectors survive the CNN.
        sequence=fmap.mean(dim=2).reshape(batch,2,2048,7).max(dim=1).values.transpose(1,2)
        return sequence.cpu().numpy()

class TransferCRNN(nn.Module):
    def __init__(self,classes):
        super().__init__()
        self.projection=nn.Sequential(nn.LayerNorm(2048),nn.Linear(2048,128),nn.GELU(),nn.Dropout(.15))
        self.rnn=nn.GRU(128,64,batch_first=True,bidirectional=True)
        self.attention=nn.Linear(128,1)
        self.classifier=nn.Sequential(nn.Dropout(.25),nn.Linear(256,classes))
    def forward(self,x):
        projected=self.projection(x);sequence,_=self.rnn(projected)
        weights=self.attention(sequence).softmax(dim=1)
        return self.classifier(torch.cat([(sequence*weights).sum(dim=1),projected.mean(dim=1)],dim=1))

class Predictor:
    def __init__(self,path,device=None):
        self.encoder=Encoder(device);self.device=self.encoder.device
        bundle=torch.load(path,map_location='cpu',weights_only=True)
        if bundle['config']!=CONFIG:raise ValueError('Transfer CRNN configuration mismatch')
        self.classes_=np.array(bundle['classes']);self.model_id=bundle['model_id']
        self.model=TransferCRNN(len(self.classes_));self.model.load_state_dict(bundle['state_dict']);self.model.to(self.device).eval()
    @torch.inference_mode()
    def predict_audio(self,windows):
        x=self.encoder.features(torch.stack([spectral_sequence(y) for y in windows]).numpy())
        return self.model(torch.as_tensor(x,device=self.device)).softmax(dim=1).cpu().numpy()

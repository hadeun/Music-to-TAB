"""Variable-length CRNN and log-mel preprocessing."""
from math import gcd
from scipy.signal import resample_poly
import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence
from torchaudio.transforms import MelSpectrogram

CONFIG = {"sample_rate": 22050, "fft": 1024, "hop": 220, "mels": 80}


class SpanCRNN(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv1d(CONFIG["mels"], 48, 5, stride=2, padding=2), nn.GELU())
        self.gru = nn.GRU(48, 48, batch_first=True, bidirectional=True)
        self.technique = nn.Linear(96, len(classes))

    def forward(self, features, lengths):
        sequence = self.conv(features.transpose(1, 2)).transpose(1, 2)
        packed = pack_padded_sequence(sequence, (lengths + 1) // 2, batch_first=True, enforce_sorted=False)
        _, hidden = self.gru(packed)
        embedding = torch.cat((hidden[0], hidden[1]), dim=1)
        return self.technique(embedding)


def mel_transform():
    return MelSpectrogram(sample_rate=CONFIG["sample_rate"], n_fft=CONFIG["fft"],
                          hop_length=CONFIG["hop"], n_mels=CONFIG["mels"],
                          pad_mode="constant")


def log_mel(clip, rate, transform):
    factor = gcd(rate, CONFIG["sample_rate"])
    clip = resample_poly(clip, CONFIG["sample_rate"] // factor, rate // factor)
    spec = transform(torch.from_numpy(clip)).clamp_min(1e-10).log10()
    return ((spec - spec.max()).clamp_min(-8) / 8 + 1).T.contiguous()

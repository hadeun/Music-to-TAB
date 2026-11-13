"""Apply the expanded technique classifier to Muscriptor guitar pitch spans."""

from collections import defaultdict
import json
import math

import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence

from prepare_tab_pitch import build_examples, pitch_events
from tab_pitch_model import CONFIG, SpanCRNN, log_mel, mel_transform

MODEL_ID = "guitar-technique-tab-pitch-expanded"


def spans_from_notes(notes_json, duration):
    notes = json.loads(notes_json or "null")
    if not isinstance(notes, list) or not 0 < len(notes) <= 20000:
        raise ValueError("Muscriptor guitar notes are required for technique analysis.")
    onsets = defaultdict(list)
    for note in notes:
        if not isinstance(note, list) or len(note) != 3:
            raise ValueError("Invalid Muscriptor guitar note.")
        start, end, pitch = note
        if (type(pitch) is not int or not 0 <= pitch <= 127
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in (start, end))
                or not 0 <= start < end):
            raise ValueError("Invalid Muscriptor guitar note.")
        if start < duration:
            onsets[start].append((pitch, min(end, duration)))
    events, end = pitch_events(onsets)
    if not events:
        raise ValueError("No Muscriptor guitar notes overlap the audio.")
    recording = {"song_id": "inference", "recording_id": "inference",
                 "permission_ref": "inference", "events": events, "end": end}
    return list(build_examples(recording, duration, 0.15))


class Predictor:
    def __init__(self, path):
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        if checkpoint["config"] != CONFIG:
            raise ValueError("Model configuration mismatch.")
        self.classes_ = checkpoint["classes"]
        self.model = SpanCRNN(self.classes_).eval()
        self.model.load_state_dict(checkpoint["state_dict"])
        self.transform = mel_transform()

    @torch.inference_mode()
    def predict(self, audio, rate, spans):
        candidates = []
        for offset in range(0, len(spans), 16):
            batch = []
            for span in spans[offset:offset + 16]:
                start = span["start"]
                end = start + span["duration"]
                clip = audio[round(start * rate):round(end * rate)]
                if clip.size and np.sqrt(np.mean(clip * clip)) >= 1e-4:
                    batch.append((start, end, log_mel(clip, rate, self.transform)))
            if not batch:
                continue
            spectra = [spec for _, _, spec in batch]
            lengths = torch.tensor([len(spec) for spec in spectra])
            scores = self.model(pad_sequence(spectra, batch_first=True), lengths).sigmoid().tolist()
            for (start, end, _), row in zip(batch, scores):
                ranked = sorted(
                    ({"label": label, "probability": score} for label, score in zip(self.classes_, row)),
                    key=lambda candidate: -candidate["probability"],
                )
                candidates.append({"start": start, "end": end, "label": ranked[0]["label"],
                                   "alternatives": ranked, "confidence": ranked[0]["probability"],
                                   "status": "estimated", "granularity": "midi_pitch_span"})
        return candidates

# Guitar-only technique input

Approved model: `htdemucs_6s`, which provides `drums`, `bass`, `other`, `vocals`, `guitar`, and `piano`. `htdemucs_ft` is a four-source model and cannot produce a guitar-only stem. Official source: https://github.com/facebookresearch/demucs . Demucs 4.0.1 is installed without changing the existing PyTorch version.

## Analysis path

Browser-stored original recording → browser decode at 44.1kHz preserving mono/stereo → PCM16 WAV upload → htdemucs_6s → **guitar** source only → mono/22,050Hz conversion → existing CRNN → temporal-overlap assignment to TAB notes → automatic marks at scores ≥70%.

There is no original-mix fallback. Missing weights, invalid output or separation errors stop technique analysis. Muscriptor note transcription is separate and is not rerouted by this change. Original/synth playback remains independent of the cached guitar stem.

The official checkpoint is `5c90dfd2-34c22ccb.th`, SHA256 `34c22ccb381c6f9fdbf324f04e1e2fe21aaaf293f5ded163a162697ff9a02ddd`. It is downloaded from the fixed official Meta URL by `download_separator.py`, verified before loading, and deserialized with a narrow `weights_only=True` allowlist. Requests do not download arbitrary checkpoints or accept a model path from the browser.

Demucs uses four-second split segments, 25% overlap, and zero random shifts for reproducible lower-latency operation. GPU is used when available; GPU-memory failure retries genuine separation on CPU, never classification of the original mix. The separator is moved back to CPU after use to free GPU memory for other local models. Output sample count is checked against input duration; no onset trimming or timeline shift is introduced.

## Cache and traceability

`separated-guitar-cache/` stores a float WAV and JSON metadata keyed by uploaded audio bytes + separator configuration/checkpoint identity. Repeat uploads reuse the same guitar stem. API results include `input_source=separated_guitar`, model/stem/configuration, cache hit, duration, and runtime device. Cache/model directories are excluded from Git.

The original classifier training and validation recordings are unchanged. Previous classifier scores do not establish accuracy on separated full-mix inputs: separation leakage and artifacts require separate evaluation. Real model inference, duration/cache checks and HTTP routing smoke tests verify implementation, not musical accuracy.

Setup: `uv pip install --python .venv-muscriptor/Scripts/python.exe demucs==4.0.1`, then `.venv-muscriptor/Scripts/python.exe techniques/download_separator.py`. Restart the local technique server after updating its code. The static server uses no-store responses and picks up updated browser scripts on refresh.

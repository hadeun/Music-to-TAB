# Guitar technique recognition reproduction

Independent research implementation based on Chellamani et al., *SpectroFusionNet a CNN approach utilizing spectrogram fusion for electric guitar play recognition*, Scientific Reports (2025), https://doi.org/10.1038/s41598-025-00287-w.

This is not the authors' code, trained model or an exact numerical reproduction. No figures, text or weights from the article are redistributed. Dataset: https://github.com/magcil/guitar_style_dataset (retain its accompanying LICENSE).

## Implemented branch and explicit choices

MFCC and gammatone images → frozen ImageNet ResNet50 pooled features → elementwise maximum → standardized linear SVM. Elementwise maximum follows the paper's feature-level description of “max voting”, not a vote across class predictions. This implements one of the paper's fusion branches; CWT, early fusion and other backbones/classifiers are not included. Exact preprocessing and backbone checkpoint settings are not specified sufficiently for identical reproduction; our versioned choices are in `core.CONFIG`.

Audio is 22,050 Hz mono. Two-second windows, 40 MFCCs, 64 gammatone channels, percentile grayscale normalization, 224×224 images repeated into RGB with ImageNet normalization. Training averages window feature vectors into one recording vector. Inference runs sliding two-second windows with one-second hop; the train/inference duration mismatch is a limitation requiring separate evaluation.

Data split is by class + full numeric pattern suffix across guitars and amplifiers (61 groups), preventing matching named patterns from crossing folds. This is our explicit grouping convention; independence between different variations of a musical exercise is not guaranteed. Frozen CNN is never fitted on held-out clips; the scaler and SVM fit within each training fold. Report grouped five-fold accuracy, macro F1, per-class metrics and confusion matrix. The final deployment classifier is then fitted on all recordings; its training performance is not reported as test accuracy. Dataset has one performer, so these results cannot establish performer-independent generalization.

## Run

Use the existing `.venv-muscriptor` and install `requirements.txt` with the CUDA-compatible torchvision wheel. Download dataset WAVs into `techniques/dataset` using `download_data.py` and retain the pinned commit in `dataset-source.json`.

```
.venv-muscriptor/Scripts/python.exe techniques/prepare.py
.venv-muscriptor/Scripts/python.exe techniques/train.py techniques/manifest.json
.venv-muscriptor/Scripts/python.exe techniques/server.py
```

Start/restart `node muscriptor-server.cjs` to enable the proxy. The studio's **Analyze techniques · experimental** button sends the project's original audio to the local technique endpoint. The current classifier adds sigmoid probability calibration on group-disjoint out-of-fold predictions; the base SVM is refit on all training recordings. Five outer folds evaluate this calibrated pipeline. For each note, overlapping window probabilities are averaged with overlap-duration weights, and the highest-ranked technique is applied in a new revision. All alternatives are stored. User edits and revision 0 are preserved. Candidates can be changed or removed through the note inspector or paginated candidate editor.

Missing classifier produces HTTP 503, busy inference HTTP 409. No random-weight fallback is used. Silence is skipped. Probabilities come from the calibrated classifier, not normalized SVM margins, and remain clip-level estimates. Automatic note assignment is a temporal-overlap heuristic requiring review: the dataset is closed-set, with no ordinary-playing/unknown class. Mixed recordings, acoustic guitar, note-level location, bend amount, simultaneous techniques, pick scrape and up/down picking direction are not validated. MIDI export does not encode these articulations.

Artifacts: `artifacts/evaluation.json` (actual grouped evaluation), `artifacts/classifier.joblib` (locally trained model), `artifacts/cache` (recording features). Pickle/joblib loading is restricted to the locally produced artifact; do not load untrusted models.

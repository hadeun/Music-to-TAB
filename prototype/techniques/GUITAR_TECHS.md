# Guitar-TECHS integration

Source: Pedroza et al., *Guitar-TECHS: An Electric Guitar Dataset Covering Techniques, Musical Excerpts, Chords and Scales Using a Diverse Array of Hardware*, ICASSP 2025.
Official data: https://zenodo.org/records/14963133 ; https://guitar-techs.github.io/ . The project site specifies CC BY 4.0. Preserve attribution and document preprocessing changes.

## Scope

The CNN stays frozen (ImageNet ResNet50); MFCC/gammatone fusion, standardization, linear SVM and group-based sigmoid calibration are retained. This is classifier retraining with combined data, not fine-tuning CNN weights or Muscriptor.

Only P1/P2 technique archives are selected for new downloads and training. At the user's request, ordinary single notes are excluded before feature extraction or cache lookup. Previously downloaded single-note files and the historical 13-class experiment remain as reference and are not used by the current pipeline. DI and amp WAV views are used first. Camera MP3 views remain available but are excluded because the official record warns about temporal misalignment. Chords, scales and P3 music are not downloaded for this technique-only experiment.

New classes: `palm_mute`, `harmonics`, `pinch_harmonics`. Bend and vibrato augment existing classes; all nine legacy classes remain, for 12 classes total. There is no normal/unknown class in the current candidate; ordinary playing can consequently receive a technique prediction. The dataset exercise labels do not imply that every inferred note has a verified articulation, and techniques can physically co-occur despite this single-label classifier.

## Preparation and evaluation

Two-second excerpts start 100ms before positive-velocity MIDI note-on events, clipped to zero. MIDI retriggers within 2.25s of the retained onset are discarded. Pitch-pickup artifacts can remain, especially during bends; exact onset localization is not claimed. Audio is downmixed and resampled with the existing extractor. Silent excerpts are recorded in `excluded.json`. Excerpt identities include the source hash and interval. Features are cached without overwriting the deployed model.

Outer evaluation has two folds: hold out every Guitar-TECHS recording/view from P1, then P2. Legacy data uses disjoint exercise groups in the corresponding two folds. Calibration uses two inner folds grouped by the original legacy pattern or shared 16-second TECHS block. All microphone views of a block stay together. The inner calibration is not performer-disjoint; the outer evaluation is. Legacy splitting retains the original exercise grouping limitations.

Report combined metrics, per-dataset/per-class metrics and confusion matrices. Compare the original nine-class model on Guitar-TECHS (unseen classes cannot be recognized by it), and retrain a legacy-only baseline on the exact same legacy outer partitions. Do not compare a new two-fold metric to the old five-fold metric as evidence of improvement.

## Run

From `prototype`, using `.venv-muscriptor/Scripts/python.exe`:

1. `techniques/download_guitar_techs.py` — resumable official download, size and MD5 verification, checked archive extraction.
2. `techniques/prepare_guitar_techs.py` — create combined manifest only after all archives finish.
3. `techniques/train_combined.py` — extract, evaluate, and fit a separate candidate.

`techniques/run_guitar_techs.py` waits for the verified download and runs steps 2–3. Its status is stored in `guitar-techs/training-status.json`.

Current 12-class candidate files are under `artifacts-guitar-techs-no-normal/`; the historical 13-class run remains under `artifacts-guitar-techs/`. The original deployed `artifacts/classifier.joblib` remains untouched. A completed candidate is not automatically promoted: inspect performer-held-out and same-split legacy metrics before activation. Clip results do not establish note-level, mixed-track, simultaneous-technique or bend-amount accuracy.

The current run contains 2,225 clips and excludes all 550 normal clips before cache access. Its Guitar-TECHS macro F1 covers five classes rather than the six classes in the historical run, so those two aggregate scores are not a like-for-like improvement measurement. The legacy-only comparison uses the same nine labels and identical outer partitions.

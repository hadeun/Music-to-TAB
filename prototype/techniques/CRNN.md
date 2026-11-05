# CRNN temporal technique classifier

Current inference first separates the original recording with htdemucs_6s and passes only its guitar stem to this classifier. See GUITAR_SEPARATION.md. The training/evaluation numbers below precede this separation change and do not validate separated-mix accuracy.

This independent architecture replaces the frozen ImageNet embedding + SVM path with a trainable CNN, bidirectional GRU, temporal attention pooling, and a 12-class clip head. No ordinary-single-note examples or cached normal features are used.

## Temporal representation

The inputs remain MFCC and gammatone spectra: 22,050 Hz mono, two-second windows, per-window percentile normalization, two channels of 64 × 201 values. Unlike the old recording-level averaged ResNet features, time is retained through the CNN and reaches the GRU as 50 ordered feature steps. CNN convolutions and the GRU are trained together. Bidirectionality can use both sides of a point within the window; it is an offline classifier, not a causal real-time model.

This is not a whole-song recurrent model. Context stops at the two-second window boundary. The existing exercise/clip labels do not identify hammer-on/pull-off note pairs, exact articulation boundaries, or simultaneous bend/vibrato intervals. Those remain separate annotation/modeling requirements. The current output is single-label, not multilabel. CNN + GRU does not establish accuracy by itself.

## Training and evaluation

Source manifest: `artifacts-guitar-techs-no-normal/manifest-used.json`. The same 2,225 source entries and existing outer partitions are used. Guitar-TECHS holds out every recording/view of one player; legacy exercises remain group-disjoint. Each legacy recording supplies at most four evenly distributed non-overlapping two-second crops. Guitar-TECHS entries supply their existing two-second crop. Predictions are aggregated per source entry before metrics are computed. This cropping differs from the SVM's averaging of all windows, so architecture is not the only experimental difference.

Each outer training partition has a separate group-disjoint inner validation split. Select the number of epochs there, refit on the entire outer training partition, and only then predict the outer test partition. Final deployment weights use all training entries and the median selected epoch count. The reported metrics come from out-of-fold predictions, never the final model's training accuracy. These outer partitions have already been inspected during prior development and are validation evidence, not a new untouched final benchmark.

Softmax outputs are uncalibrated scores, even though they sum to one. Do not equate them with validated note-level confidence. Normal/unknown rejection, compound technique labels, bend amount, full-mix detection and exact event timing are not validated.

## Commands and local backend

From `prototype`:

```
.venv-muscriptor/Scripts/python.exe techniques/train_crnn.py --epochs 18
.venv-muscriptor/Scripts/python.exe -m unittest discover -s techniques -p test_crnn.py
```

Outputs: `artifacts-crnn/classifier.pt`, `evaluation.json`, `predictions.json`, and time-preserving feature caches. Existing SVM artifacts remain untouched.

The technique server supports a local `techniques/active-backend.json` containing `{"backend":"crnn","artifact":"artifacts-crnn/classifier.pt"}` or an SVM artifact under the same techniques directory. Without this file it continues using its existing default SVM. The selector is local configuration, never a client-supplied model path. A running updated server reloads the model when the selector or artifact changes; older running code must be restarted. Validate a trained candidate before selecting it.

## Transfer CRNN variant

The first compact CNN trained from scratch did not meet the existing SVM reference. A second CRNN retains the original verified ImageNet ResNet50 weights, freezes them, and removes only its final spatial average pooling. Frequency is pooled, but seven ordered vectors of 2,048 channels remain across each two-second window. MFCC/gammatone vectors are fused by elementwise maximum at the corresponding time steps. A trainable LayerNorm/projection, bidirectional GRU, temporal attention and clip classifier then learn temporal context. A mean-projection branch is concatenated with recurrent features to retain useful static cues. The CNN stays frozen in this variant; it is still a convolutional recurrent network.

Inputs reuse the normalized 64×201 spectral caches, resized to 224×224 and ImageNet-normalized. This is close to, but not identical to, the original SVM's direct 40-coefficient MFCC interpolation. The seven recurrent steps have coarse time resolution and do not justify frame-level articulation timing claims.

Run `techniques/train_crnn_transfer.py --epochs 24`. It uses the same inner selection / outer refit protocol, records a separate evaluation, and stores final weights in `artifacts-crnn-transfer/classifier.pt`. The checkpoint contains the recurrent head and depends on the existing verified ResNet weight file. `techniques/smoke_crnn.py --transfer` checks the actual endpoint with this trained model without changing live settings. `techniques/summarize_crnn.py --transfer` reports the comparison.

The selector for this variant is `{"backend":"crnn_transfer","artifact":"artifacts-crnn-transfer/classifier.pt"}`. Neither training command automatically overwrites the existing default model. The user's CRNN migration request is now implemented by this active selector. The existing SVM files and the compact from-scratch CRNN remain available separately. Overall validation was near parity, with better hammer-on F1 but worse bending, vibrato and pull-off F1; migration does not imply uniform improvement.

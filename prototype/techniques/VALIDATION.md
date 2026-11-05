# Validation — 2026-10-25

Current model: MFCC + gammatone → frozen ResNet50 → max feature fusion → linear SVM with sigmoid probability calibration. Calibration uses group-disjoint inner folds with out-of-fold predictions (ensemble=False); evaluation uses five outer pattern-disjoint folds.

Dataset: 549 recordings, 61 named-pattern groups, 9 classes. Current calibrated accuracy: 85.25%; macro F1: 84.21%. These are held-out recording metrics, not note-level or mixed-song accuracy.

| Class | F1 |
| --- | --- |
| alternate_picking | 0.994 |
| bend | 0.938 |
| hammer_on | 0.462 |
| legato | 0.927 |
| pull_off | 0.509 |
| slide | 0.897 |
| sweep_picking | 0.986 |
| tapping | 0.926 |
| vibrato | 0.941 |

Each note receives overlap-weighted window probabilities; the highest-ranked technique is applied automatically. All alternatives are retained. Users can change or remove techniques; re-analysis preserves deliberate user edits. Revision 0 stays unchanged.

Actual 12-second inference integration assigned 47 guitar notes, retained nine alternatives per note, preserved originalParts and retained a manual none override. Backend returned 11 windows with normalized probability vectors. Eight JavaScript checks passed. Browser checks confirmed Korean/English switching, saved preference across reload and Korean upload dialog.

The dataset has no ordinary/unknown class. Hammer-on/pull-off remain difficult. Probabilities reflect closed-set audio-window evidence and are not calibrated note-level confidence. No pick scrape, individual picking direction, bend amount or simultaneous techniques. MIDI/TuxGuitar articulation export remains unimplemented.

Region default is inferred locally from Korean browser locale/region or Asia/Seoul time zone; no IP lookup or location permission. Explicit language choice takes precedence.

Machine-readable report: artifacts/evaluation.json. Model: artifacts/classifier.joblib. Screenshot: ../test-output/korean-studio.png.

Playback mixer: added simultaneous original/synth playback with a live 0–100 crossfade, saved balance and shared original-audio clock. Gain changes affect sustained synth notes through a master GainNode. Tests cover live gain routing, shared-clock position, seek into sustained notes, speed scaling, pause cleanup and missing-audio handling. Browser playback, seeking and fader updates were also exercised. Screenshot: ../test-output/playback-mixer.png.

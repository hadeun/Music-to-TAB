# Missing introduction — Mr. Crowley

User-reported range: approximately 6–49 seconds.

Reproduced using the first 55 seconds of the supplied guitar-only recording and the actual local Muscriptor medium model. With automatic instrument detection, the first emitted note was at 50.00 seconds and no start events existed in [6,49). With the allowed-instrument list restricted to acoustic_guitar, clean_electric_guitar and distorted_electric_guitar, the first event appeared at 6.35 seconds and 150 start events were emitted in [6,49). 149 of those were assigned to standard-tuning TAB; one remains among unassigned events. This confirms model omission under the original decoding configuration, rather than a UI crop or a missing playback intro. It does not establish exact transcription accuracy of the recovered events.

Fix: solo/isolated-guitar uploads send the explicit instrument list before model decoding. Full mixes keep multi-instrument detection. The mode is stored as instrumentMode in the score. No estimated notes are fabricated and no substitute model is used.

Existing projects remain unchanged. The new “Re-transcribe with guitar focus” action uses their stored original audio, creates a new project with a [Guitar focus] suffix, and preserves previous scores/edits. Original MIDI and raw events are retained for comparison. This operation regenerates the transcription; previous manual edits and technique assignments are not copied into the new score.

Regression checks: actual before/after SSE recordings, recovery of more than 100 TAB notes in [6,49), first TAB onset before 7 seconds, string/fret pitch consistency and preservation of full-mix request behavior. Development artifacts are in test-output/crowley-intro-*.sse.

Full-song browser re-transcription also completed. A new [Guitar focus] project contains 1,415 assigned TAB notes and its first displayed note is at 6.350 seconds (measure 3 at the entered 108 BPM). The existing project remained in the library. Screenshot: test-output/crowley-intro-fixed.png. Recovered events have not been manually checked against a reference score; restored coverage is distinct from note accuracy.

# Muscriptor-only local integration

Run `node muscriptor-server.cjs`, then open http://127.0.0.1:4181/.
The frontend posts decoded PCM WAV to the same-origin proxy, which streams the official Muscriptor `/transcribe` response from localhost:8222. Instrument-labelled events are mapped to guitar TAB; the original multi-instrument MIDI is preserved in score JSON. Edited guitar MIDI still uses the current revision.

Model server (after installation and Hugging Face model access):

```
.venv-muscriptor\Scripts\muscriptor.exe serve --model medium --device cuda --port 8222
```

Accept the selected model's terms at https://huggingface.co/muscriptor, then authenticate locally using `hf auth login`. Never place tokens in source or frontend configuration. Weight download and real-audio inference must succeed before treating integration as verified.

No Basic Pitch model is invoked or used as fallback. Legacy assets are retained on disk but blocked by the new server. Previous Basic Pitch projects are preserved under their previous browser-storage key, separate from Muscriptor projects. Use the new server; older preview processes serve an obsolete version.

Muscriptor provides instrument-labelled notes/MIDI, not isolated audio stems. Lead/rhythm separation is not implemented. Fingering is heuristic. Bar lines use entered BPM; the original beat grid is retained. Google authentication, server project persistence and TuxGuitar export remain unimplemented. The model license requires separate review for a commercial service.

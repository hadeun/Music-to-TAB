"""Build variable-length technique examples from reviewed, audio-aligned TAB."""

import argparse
import json
import math
from pathlib import Path


def pitch_events(onsets):
    events = []
    active = []
    for start, notes in sorted(onsets.items()):
        if active and start - max(end for _, end in active) >= 0.12:
            events.append({"time": max(end for _, end in active), "pitches": [], "techniques": []})
        active = [(pitch, end) for pitch, end in active if end > start]
        active.extend(notes)
        events.append({"time": start, "pitches": [pitch for pitch, _ in active], "techniques": []})
    return events, max((end for _, end in active), default=0)



def labels(event, key):
    values = event.get(key)
    if values is None:
        return None
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ValueError(f"{key} must be a list of nonempty strings")
    return set(values)


def build_examples(recording, audio_duration, transition_context):
    source = {
        "group": recording["song_id"],
        "source_recording": recording["recording_id"],
        "permission_ref": recording["permission_ref"],
    }
    if any(not isinstance(value, str) or not value.strip() for value in source.values()):
        raise ValueError("song_id, recording_id and permission_ref must be nonempty strings")
    end = recording["end"]
    if not math.isfinite(end) or not 0 < end <= audio_duration:
        raise ValueError("end must be within the audio")

    runs = []
    previous_onset = -1
    for event in recording["events"]:
        onset = event["time"]
        if not math.isfinite(onset) or not 0 <= onset < end or onset <= previous_onset:
            raise ValueError("TAB onset times must be strictly increasing and before end")
        previous_onset = onset
        pitches = event["pitches"]
        if not isinstance(pitches, list) or any(
            type(pitch) is not int or not 0 <= pitch <= 127 for pitch in pitches
        ):
            raise ValueError("pitches must be a list of MIDI pitch numbers")
        pitch_set = sorted(set(pitches))
        note_labels = labels(event, "techniques")
        transition_labels = labels(event, "transition")

        if runs and runs[-1]["pitches"] == pitch_set:
            if transition_labels:
                raise ValueError("transition labels require a change of TAB pitch")
            run = runs[-1]
            run["onsets"].append(onset)
            if run["labels"] is None or note_labels is None:
                run["labels"] = None
            else:
                run["labels"].update(note_labels)
        else:
            runs.append({
                "pitches": pitch_set, "onsets": [onset],
                "labels": note_labels, "transition": transition_labels,
            })

    def example(kind, start, stop, techniques, **details):
        return {
            **source, "kind": kind, "start": start, "duration": round(stop - start, 9),
            "labels": sorted(techniques), **details,
        }

    for index, run in enumerate(runs):
        onset = run["onsets"][0]
        stop = runs[index + 1]["onsets"][0] if index + 1 < len(runs) else end
        pitches = run["pitches"]
        if pitches and run["labels"] is not None:
            yield example("pitch_span", onset, stop, run["labels"],
                          pitches=pitches, tab_onsets=run["onsets"])

        previous = runs[index - 1] if index else None
        if previous and previous["pitches"] and pitches and run["transition"] is not None:
            yield example(
                "pitch_transition", max(previous["onsets"][0], onset - transition_context),
                min(stop, onset + transition_context), run["transition"], boundary=onset,
                from_pitches=previous["pitches"], to_pitches=pitches,
            )
        elif run["transition"]:
            raise ValueError("a labeled transition must connect two pitched TAB events")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--transition-context", type=float, default=0.15,
                        help="seconds of audio to keep on each side of a pitch transition")
    args = parser.parse_args()
    if not math.isfinite(args.transition_context) or args.transition_context <= 0:
        parser.error("--transition-context must be positive and finite")

    import soundfile as sf

    recordings = json.loads(args.annotations.read_text(encoding="utf-8-sig"))
    rows = []
    recording_ids = set()
    for recording in recordings:
        audio = (args.annotations.parent / recording["path"]).resolve()
        if recording["recording_id"] in recording_ids:
            raise ValueError(f"Duplicate recording_id: {recording['recording_id']}")
        recording_ids.add(recording["recording_id"])
        for row in build_examples(recording, sf.info(audio).duration, args.transition_context):
            rows.append({**row, "path": str(audio)})
    if not rows:
        raise ValueError("No reviewed TAB examples found")
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(rows, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"Wrote {len(rows)} examples to {args.output}")


if __name__ == "__main__":
    main()

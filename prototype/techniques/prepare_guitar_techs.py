"""Merge nine legacy classes with note-centered Guitar-TECHS DI/amp clips.

Labels describe whole source exercises, not manually verified note articulations.
Camera MP3 views are retained on disk but excluded from this first alignment-sensitive run.
"""
import argparse,json,math
from collections import Counter
from pathlib import Path
import mido,soundfile as sf
ROOT=Path(__file__).resolve().parent
LABELS={'Bendings':'bend','PalmMute':'palm_mute','Vibrato':'vibrato','Harmonics':'harmonics','PinchHarmonics':'pinch_harmonics'}

def onsets(path):
    time=0;events=[]
    for message in mido.MidiFile(path):
        time+=message.time
        if message.type=='note_on' and message.velocity:
            # Discard pickup retriggers and pitch-tracker artifacts within one attack.
            if not events or time-events[-1][0]>=2.25:events.append((time,message.note))
    return events

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    if not args.partial and not (ROOT/'guitar-techs/download-complete.json').exists():raise ValueError('Dataset download is incomplete')
    legacy=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    rows=[{**r,'dataset':'guitar_style','group':'legacy:'+r['group']} for r in legacy]
    for player in ['P1','P2']:
        for category in ['techniques']:
            folder=ROOT/'guitar-techs/data'/f'{player}_{category}'
            for midi in sorted((folder/'midi').glob('*.mid')):
                token=midi.stem.removeprefix('midi_')
                if token not in LABELS:raise ValueError(f'Unrecognized label: {token}')
                events=onsets(midi)
                for view in ['directinput','micamp']:
                    audio=folder/'audio'/view/f'{view}_{token}.wav'
                    if not audio.exists() and args.partial:continue
                    length=sf.info(audio).duration
                    for index,(onset,pitch) in enumerate(events):
                        start=max(0,onset-.1)
                        if start+2>length:continue
                        rows.append({'path':str(audio),'label':LABELS[token],'group':f'techs:{token}:block{math.floor(onset/16)}',
                         'dataset':'guitar_techs','player':player,'view':view,'source_recording':f'{player}:{token}',
                         'start':round(start,6),'duration':2.,'midi_pitch':pitch,'onset_index':index})
    out=ROOT/'guitar-techs'/('manifest-partial.json' if args.partial else 'manifest-combined.json')
    out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps({'rows':len(rows),'labels':Counter(r['label'] for r in rows),'datasets':Counter(r['dataset'] for r in rows)},indent=2),flush=True)
if __name__=='__main__':main()

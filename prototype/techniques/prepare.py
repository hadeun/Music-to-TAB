"""Prepare recording manifest; related exercise variants share one group."""
from pathlib import Path
import json,re
root=Path(__file__).resolve().parent.parent
rows=[]
source=root/'techniques/dataset-source.json'
if not source.exists():raise ValueError('Dataset download has not completed; refusing a partial manifest')
for path in sorted((root/'techniques/dataset').rglob('*.wav')):
    # class_0_carvin_dc-modern_1_2.wav: class, guitar, amp, exercise, take.
    match=re.match(r'class_(\d+)_([^_]+)_([^_]+)_(\d+(?:_\d+)?)$',path.stem)
    if not match:raise ValueError(f'Unknown filename grouping: {path.name}')
    cls,guitar,amp,exercise=match.groups()
    rows.append({'path':str(path),'label':path.parent.name.replace(' ','_').replace('-','_'),
                 'group':f'class_{cls}_pattern_{exercise}','guitar':guitar,'amplifier':amp})
if not rows:raise ValueError('No audio downloaded')
expected=json.loads(source.read_text())['files']
if len(rows)!=expected or len({r['label'] for r in rows})!=9:raise ValueError('Incomplete nine-class dataset')
out=root/'techniques/manifest.json';out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Manifest:',len(rows),'recordings;',len({r['label'] for r in rows}),'classes;',len({r['group'] for r in rows}),'exercise groups')

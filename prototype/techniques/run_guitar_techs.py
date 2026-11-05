"""Wait for the verified download, then prepare and train a separate candidate."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
status=ROOT/'guitar-techs/training-status.json'
def phase(name):
    status.write_text(json.dumps({'phase':name,'updated':time.time()},indent=2),encoding='utf-8')
    print(name,flush=True)
try:
    phase('waiting_for_verified_download')
    while not (ROOT/'guitar-techs/download-complete.json').exists():time.sleep(2)
    phase('preparing_manifest')
    subprocess.run([sys.executable,str(ROOT/'prepare_guitar_techs.py')],check=True)
    phase('extracting_features_and_training')
    subprocess.run([sys.executable,'-u',str(ROOT/'train_combined.py')],check=True)
    phase('candidate_complete_not_activated')
except Exception:
    phase('failed');raise

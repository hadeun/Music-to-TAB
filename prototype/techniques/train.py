"""Train/evaluate by source recording, never split windows across partitions."""
import argparse,json,time
from pathlib import Path
import joblib,numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from sklearn.calibration import CalibratedClassifierCV
from core import Extractor,file_features,CONFIG

def calibrated(X,y,groups):
    classes=set(y)
    for seed in range(42,142):
        splits=list(StratifiedGroupKFold(2,shuffle=True,random_state=seed).split(X,y,groups))
        if all(set(y[a])==classes and set(y[b])==classes for a,b in splits):break
    else:raise ValueError('Not enough independent groups for probability calibration')
    base=make_pipeline(StandardScaler(),SVC(kernel='linear',C=1,class_weight='balanced'))
    model=CalibratedClassifierCV(base,method='sigmoid',cv=splits,ensemble=False)
    model.fit(X,y)
    return model

def main():
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--output',default='techniques/artifacts');a=p.parse_args()
    rows=json.loads(Path(a.manifest).read_text(encoding='utf-8'));out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    if not rows or not all({'path','label','group'}<=set(r) for r in rows):
        raise ValueError('Manifest needs path,label,group for each recording')
    extractor=Extractor();features=[];hashes=[]
    for i,r in enumerate(rows):
        f,h=file_features(r['path'],extractor,out/'cache');features.append(f);hashes.append(h)
        print(f'Features {i+1}/{len(rows)} {r["label"]}',flush=True)
    if len(set(hashes))!=len(hashes):raise ValueError('Duplicate recordings in manifest')
    X=np.asarray(features);y=np.asarray([r['label'] for r in rows]);groups=np.asarray([r['group'] for r in rows])
    splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    folds=[];truth=[];pred=[]
    for fold,(tr,te) in enumerate(splitter.split(X,y,groups)):
        if set(groups[tr]) & set(groups[te]):raise ValueError('Group leakage')
        if set(y[tr])!=set(y):raise ValueError('Training fold missing a class')
        clf=calibrated(X[tr],y[tr],groups[tr]);guess=clf.predict(X[te]);truth.extend(y[te]);pred.extend(guess)
        folds.append({'fold':fold,'train_groups':sorted(set(groups[tr])),'test_groups':sorted(set(groups[te])),
                      'accuracy':accuracy_score(y[te],guess),'macro_f1':f1_score(y[te],guess,average='macro',zero_division=0)})
    classes=sorted(set(y));report={'config':CONFIG,'recordings':len(rows),'classes':classes,'folds':folds,
      'accuracy':accuracy_score(truth,pred),'macro_f1':f1_score(truth,pred,average='macro',zero_division=0),
      'classification_report':classification_report(truth,pred,output_dict=True,zero_division=0),
      'confusion_matrix':confusion_matrix(truth,pred,labels=classes).tolist(),
      'probability_method':'sigmoid calibration using two group-disjoint inner folds',
      'scope':'Clip classification on dataset groups; not validated note-level or full-mix detection.'}
    (out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    clf=calibrated(X,y,groups)
    joblib.dump({'classifier':clf,'config':CONFIG,'report':report,'created':time.time()},out/'classifier.pending')
    (out/'classifier.pending').replace(out/'classifier.joblib')
    print(json.dumps({k:report[k] for k in ('accuracy','macro_f1','recordings')},indent=2),flush=True)
if __name__=='__main__':main()

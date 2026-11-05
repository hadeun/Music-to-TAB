"""Candidate-only training; two outer folds hold out each Guitar-TECHS player.

Existing exercises also remain disjoint. Calibration splits by legacy exercise
and shared 16-second TECHS blocks across all microphone views and players.
"""
import argparse,json,time
from collections import Counter
from pathlib import Path
import joblib,numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from core import Extractor,file_features,CONFIG
from train import calibrated
ROOT=Path(__file__).resolve().parent

def metrics(y,pred,classes):
    return {'accuracy':float(accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,labels=classes,average='macro',zero_division=0)),
     'classification_report':classification_report(y,pred,labels=classes,output_dict=True,zero_division=0),
     'confusion_matrix':confusion_matrix(y,pred,labels=classes).tolist()}

def outer_splits(rows):
    legacy=np.array([i for i,r in enumerate(rows) if r['dataset']=='guitar_style'])
    ly=np.array([rows[i]['label'] for i in legacy]);lg=np.array([rows[i]['group'] for i in legacy])
    for fold,(tr,te) in enumerate(StratifiedGroupKFold(2,shuffle=True,random_state=42).split(legacy,ly,lg)):
        player=['P1','P2'][fold]
        train=np.concatenate([legacy[tr],[i for i,r in enumerate(rows) if r['dataset']=='guitar_techs' and r['player']!=player]]).astype(int)
        test=np.concatenate([legacy[te],[i for i,r in enumerate(rows) if r['dataset']=='guitar_techs' and r['player']==player]]).astype(int)
        if set(rows[i]['group'] for i in legacy[tr])&set(rows[i]['group'] for i in legacy[te]):raise ValueError('Legacy exercise leakage')
        a={rows[i].get('source_recording') for i in train if rows[i]['dataset']=='guitar_techs'}
        b={rows[i].get('source_recording') for i in test if rows[i]['dataset']=='guitar_techs'}
        if a&b:raise ValueError('Guitar-TECHS recording leakage')
        yield player,train,test

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--features-only',action='store_true');parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    if args.partial and not args.features_only:raise ValueError('Partial data can only precompute features')
    rows=json.loads((ROOT/'guitar-techs'/('manifest-partial.json' if args.partial else 'manifest-combined.json')).read_text(encoding='utf-8'))
    # Exclude normal before even looking in the feature cache, including stale manifests.
    rows=[r for r in rows if r['label']!='normal']
    out=ROOT/'artifacts-guitar-techs-no-normal';out.mkdir(exist_ok=True)
    extractor=Extractor();features=[];hashes=[];kept=[];excluded=[]
    for i,r in enumerate(rows):
        try:f,h=file_features(r['path'],extractor,ROOT/'artifacts/cache',r.get('start'),r.get('duration'))
        except ValueError as error:
            if 'Silent file:' not in str(error):raise
            excluded.append({**r,'reason':str(error)});continue
        features.append(f);hashes.append(h);kept.append(r)
        if (i+1)%25==0:print(f'Features {i+1}/{len(rows)}',flush=True)
    if len(set(hashes))!=len(hashes):raise ValueError('Duplicate clip content in manifest')
    rows=kept
    (out/'excluded.json').write_text(json.dumps(excluded,indent=2),encoding='utf-8')
    (out/'manifest-used.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    X=np.asarray(features);y=np.array([r['label'] for r in rows]);groups=np.array([r['group'] for r in rows]);classes=sorted(set(y))
    np.savez_compressed(out/'features.npz',X=X,y=y,groups=groups)
    if args.features_only:return
    prediction=np.empty(len(rows),dtype=object);folds=[]
    old=joblib.load(ROOT/'artifacts/classifier.joblib')['classifier'];old_predictions=np.empty(len(rows),dtype=object)
    legacy_baseline=np.empty(len(rows),dtype=object)
    for player,tr,te in outer_splits(rows):
        if set(y[tr])!=set(y):raise ValueError('Training fold missing a class')
        print('Evaluating held-out player:',player,'train',len(tr),'test',len(te),flush=True)
        model=calibrated(X[tr],y[tr],groups[tr]);prediction[te]=model.predict(X[te]);old_predictions[te]=old.predict(X[te])
        legacy_tr=np.array([i for i in tr if rows[i]['dataset']=='guitar_style']);legacy_te=np.array([i for i in te if rows[i]['dataset']=='guitar_style'])
        base=calibrated(X[legacy_tr],y[legacy_tr],groups[legacy_tr]);legacy_baseline[legacy_te]=base.predict(X[legacy_te])
        folds.append({'held_out_player':player,'train':len(tr),'test':len(te),'metrics':metrics(y[te],prediction[te],classes)})
    report={'config':CONFIG,'classes':classes,'samples':len(rows),'class_counts':dict(Counter(y)),'excluded_labels':['normal'],
     'folds':folds,'combined':metrics(y,prediction,classes),'datasets':{},'baseline_on_guitar_techs':{},
     'scope':'Two-fold Guitar-TECHS performer-disjoint and legacy exercise-disjoint evaluation; not note-level or full-mix validation.',
     'calibration':'Two group-disjoint inner folds: legacy patterns and Guitar-TECHS 16-second blocks across views/players.',
     'preprocessing':'2-second clips starting 100ms before MIDI onsets; retriggers within 2.25s discarded; DI and amp WAV views only.'}
    for dataset in ['guitar_style','guitar_techs']:
        select=np.array([r['dataset']==dataset for r in rows]);labels=sorted(set(y[select]))
        report['datasets'][dataset]=metrics(y[select],prediction[select],labels)
        if dataset=='guitar_techs':
            report['baseline_on_guitar_techs']=metrics(y[select],old_predictions[select],labels)
            report['baseline_on_guitar_techs']['confusion_matrix_all_classes']=confusion_matrix(y[select],old_predictions[select],labels=classes).tolist()
        else:report['legacy_baseline_same_split']=metrics(y[select],legacy_baseline[select],labels)
    (out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Fitting deployment candidate on all clips',flush=True)
    model=calibrated(X,y,groups)
    joblib.dump({'classifier':model,'config':CONFIG,'report':report,'created':time.time(),'model_id':'spectrofusion-inspired-guitar-techs-v4-no-normal'},out/'classifier.pending')
    (out/'classifier.pending').replace(out/'classifier.joblib')
    print(json.dumps({'combined':report['combined']['macro_f1'],'by_dataset':{k:v['macro_f1'] for k,v in report['datasets'].items()}},indent=2),flush=True)
if __name__=='__main__':main()

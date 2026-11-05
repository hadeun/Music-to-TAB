"""Grouped CRNN selection/refit/evaluation with untouched outer test folds."""
import argparse,json,os,random,time
from pathlib import Path
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import numpy as np,torch
from torch.utils.data import DataLoader,TensorDataset
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score
from crnn import CRNN,CONFIG,recording_sequences
from train_combined import outer_splits,metrics

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts-crnn'
DEVICE='cuda' if torch.cuda.is_available() else 'cpu'

def seed(value):
    random.seed(value);np.random.seed(value);torch.manual_seed(value)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(value)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True

def loader(X,targets,owners,ids,shuffle=False):
    mask=np.isin(owners,ids);indices=np.flatnonzero(mask)
    return DataLoader(TensorDataset(torch.from_numpy(X[indices]),torch.tensor(targets[indices],dtype=torch.long),torch.tensor(owners[indices],dtype=torch.long)),batch_size=48,shuffle=shuffle,num_workers=0)

@torch.inference_mode()
def predict(model,X,targets,owners,ids):
    totals={};counts={};model.eval()
    for x,_,owner in loader(X,targets,owners,ids):
        logits=model(x.to(DEVICE,dtype=torch.float32)).cpu().numpy()
        for row,value in zip(owner.tolist(),logits):totals[row]=totals.get(row,0)+value;counts[row]=counts.get(row,0)+1
    return np.stack([totals[int(i)]/counts[int(i)] for i in ids])

def fit(X,targets,owners,y,train,epochs,classes,validation=None,run_seed=42,model_cls=CRNN):
    seed(run_seed);model=model_cls(classes).to(DEVICE)
    train_loader=loader(X,targets,owners,train,shuffle=True)
    counts=np.bincount(targets[np.isin(owners,train)],minlength=classes)
    weights=1/np.sqrt(np.maximum(1,counts));weights=weights/weights.mean()
    criterion=torch.nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32,device=DEVICE))
    optimizer=torch.optim.AdamW(model.parameters(),lr=8e-4,weight_decay=1e-3)
    best=-1;best_epoch=1;history=[];stale=0
    for epoch in range(1,epochs+1):
        model.train();total=0.;batches=0
        for x,target,_ in train_loader:
            optimizer.zero_grad(set_to_none=True);logits=model(x.to(DEVICE,dtype=torch.float32));loss=criterion(logits,target.to(DEVICE))
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step();total+=loss.item();batches+=1
        entry={'epoch':epoch,'loss':total/max(1,batches)}
        if validation is not None:
            guess=predict(model,X,targets,owners,validation).argmax(axis=1)
            score=float(f1_score(y[validation],guess,labels=np.arange(classes),average='macro',zero_division=0));entry['validation_macro_f1']=score
            if score>best+1e-5:best=score;best_epoch=epoch;stale=0
            else:stale+=1
        history.append(entry);print(json.dumps(entry),flush=True)
        if validation is not None and stale>=5:break
    return model,best_epoch,history

def inner_split(train,y,groups):
    for value in range(42,100):
        for a,b in StratifiedGroupKFold(3,shuffle=True,random_state=value).split(train,y[train],groups[train]):
            tr,va=train[a],train[b]
            if set(y[tr])==set(y) and set(y[va])==set(y):
                if set(groups[tr])&set(groups[va]):raise ValueError('Inner group leakage')
                return tr,va
    raise ValueError('Insufficient independent groups for validation')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=18);parser.add_argument('--features-only',action='store_true');args=parser.parse_args()
    if args.epochs<1:raise ValueError('epochs must be positive')
    torch.set_num_threads(min(4,os.cpu_count() or 1));OUT.mkdir(exist_ok=True)
    rows=json.loads((ROOT/'artifacts-guitar-techs-no-normal/manifest-used.json').read_text());rows=[r for r in rows if r['label']!='normal']
    classes=sorted({r['label'] for r in rows});label_to_id={label:i for i,label in enumerate(classes)}
    arrays=[];owner=[]
    for i,row in enumerate(rows):
        sequence=recording_sequences(row,OUT/'cache');arrays.append(sequence.astype(np.float16));owner.extend([i]*len(sequence))
        if (i+1)%50==0:print(f'Temporal features {i+1}/{len(rows)}',flush=True)
    X=np.concatenate(arrays);del arrays;owners=np.array(owner);y=np.array([label_to_id[r['label']] for r in rows]);targets=y[owners];groups=np.array([r['group'] for r in rows])
    (OUT/'manifest-used.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    if args.features_only:return
    print('Training device:',DEVICE,'sequences:',len(X),'recordings:',len(rows),flush=True)
    prediction=np.empty(len(rows),dtype=int);folds=[];epochs=[]
    for number,(player,tr,te) in enumerate(outer_splits(rows)):
        inner_tr,inner_va=inner_split(tr,y,groups)
        print('Epoch selection; held-out test player remains unseen:',player,flush=True)
        model,best,history=fit(X,targets,owners,y,inner_tr,args.epochs,len(classes),inner_va,42+number)
        del model
        print('Refit outer training fold:',player,'epochs',best,flush=True)
        model,_,_=fit(X,targets,owners,y,tr,best,len(classes),run_seed=142+number)
        prediction[te]=predict(model,X,targets,owners,te).argmax(axis=1)
        folds.append({'held_out_player':player,'selected_epoch':best,'selection_history':history,
         'train_recordings':len(tr),'test_recordings':len(te),'inner_train':len(inner_tr),'inner_validation':len(inner_va),
         'metrics':metrics(np.array(classes)[y[te]],np.array(classes)[prediction[te]],classes)})
        epochs.append(best);del model
    truth=np.array(classes)[y];guesses=np.array(classes)[prediction]
    report={'config':CONFIG,'classes':classes,'recordings':len(rows),'temporal_windows':len(X),'folds':folds,
     'combined':metrics(truth,guesses,classes),'datasets':{},'probability_method':'uncalibrated softmax',
     'scope':'Grouped clip classification; two-second temporal context, single-label supervision; not note-boundary or simultaneous-technique validation.',
     'selection':'Epochs selected on group-disjoint inner validation; refit on outer training only before outer test prediction.'}
    for dataset in ['guitar_style','guitar_techs']:
        mask=np.array([r['dataset']==dataset for r in rows]);labels=sorted(set(truth[mask]));report['datasets'][dataset]=metrics(truth[mask],guesses[mask],labels)
    reference=json.loads((ROOT/'artifacts-guitar-techs-no-normal/evaluation.json').read_text())
    report['svm_reference']={'combined_macro_f1':reference['combined']['macro_f1'],'datasets':{k:v['macro_f1'] for k,v in reference['datasets'].items()},
     'caution':'Same source recordings and outer partitions; CRNN uses up to four ordered two-second crops per legacy file while SVM averages all recording windows.'}
    (OUT/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (OUT/'predictions.json').write_text(json.dumps([{'index':i,'truth':str(a),'prediction':str(b)} for i,(a,b) in enumerate(zip(truth,guesses))],indent=2),encoding='utf-8')
    final_epochs=max(1,int(np.median(epochs)));print('Fitting final CRNN:',final_epochs,flush=True)
    model,_,_=fit(X,targets,owners,y,np.arange(len(rows)),final_epochs,len(classes),run_seed=242)
    state={k:v.detach().cpu() for k,v in model.state_dict().items()}
    torch.save({'config':CONFIG,'classes':classes,'state_dict':state,'temperature':1.,'model_id':'guitar-technique-crnn-v1','epochs':final_epochs},OUT/'classifier.pending')
    (OUT/'classifier.pending').replace(OUT/'classifier.pt')
    print(json.dumps({'combined_macro_f1':report['combined']['macro_f1'],'datasets':{k:v['macro_f1'] for k,v in report['datasets'].items()}},indent=2),flush=True)
if __name__=='__main__':main()

"""Paired out-of-fold comparison using the same test clips for both models.

The baseline is refitted on legacy training folds, not evaluated on its own
full-data deployment training set. The deployed and candidate models stay intact.
"""
import csv,json,os
from pathlib import Path
import numpy as np
from sklearn.metrics import confusion_matrix,accuracy_score,f1_score
from train import calibrated
from train_combined import outer_splits

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'artifacts-guitar-techs-no-normal'
OUT=ROOT/'comparison-no-normal'
NAMES={'alternate_picking':'얼터네이트 피킹','bend':'벤딩','hammer_on':'해머링온','legato':'레가토','pull_off':'풀링오프','slide':'슬라이드','sweep_picking':'스윕 피킹','tapping':'태핑','vibrato':'비브라토','palm_mute':'팜뮤트','harmonics':'자연 하모닉스','pinch_harmonics':'피치 하모닉스'}
ORDER=list(NAMES)

def per_class(truth,prediction,classes,supported):
    matrix=confusion_matrix(truth,prediction,labels=classes)
    if int(matrix.sum())!=len(truth):raise ValueError('Unaccounted prediction labels')
    result={}
    for i,label in enumerate(classes):
        tp=int(matrix[i,i]);fn=int(matrix[i].sum())-tp;fp=int(matrix[:,i].sum())-tp;tn=len(truth)-tp-fn-fp
        result[label]={'supported':label in supported,'support':tp+fn,'tp':tp,'fp':fp,'fn':fn,'tn':tn,
          'accuracy':(tp+tn)/len(truth),'precision':tp/(tp+fp) if tp+fp else 0.,'recall':tp/(tp+fn) if tp+fn else 0.}
    return {'n':len(truth),'multiclass_accuracy':float(accuracy_score(truth,prediction)),
     'macro_f1':float(f1_score(truth,prediction,labels=classes,average='macro',zero_division=0)),
     'labels':classes,'confusion_matrix':matrix.tolist(),'per_class':result}

def main():
    OUT.mkdir(exist_ok=True)
    rows=json.loads((SOURCE/'manifest-used.json').read_text())
    data=np.load(SOURCE/'features.npz');X=data['X'];y=data['y'];groups=data['groups'];classes=sorted(set(y))
    if 'normal' in classes:raise ValueError('Normal clips must remain excluded')
    baseline=np.empty(len(rows),dtype=object);combined=np.empty(len(rows),dtype=object);fold_ids={}
    legacy_labels=sorted({r['label'] for r in rows if r['dataset']=='guitar_style'})
    for player,tr,te in outer_splits(rows):
        print('Paired evaluation:',player,flush=True)
        legacy_tr=np.array([i for i in tr if rows[i]['dataset']=='guitar_style'])
        old=calibrated(X[legacy_tr],y[legacy_tr],groups[legacy_tr]);new=calibrated(X[tr],y[tr],groups[tr])
        baseline[te]=old.predict(X[te]);combined[te]=new.predict(X[te])
        for i in te:fold_ids[int(i)]=player
    reference=json.loads((SOURCE/'evaluation.json').read_text())
    if abs(f1_score(y,combined,average='macro')-reference['combined']['macro_f1'])>1e-9:raise ValueError('Candidate evaluation did not reproduce')
    result={'method':{'baseline':'Legacy-only 9-class pipeline refitted inside each outer training fold.',
      'combined':'12-class pipeline trained on legacy + Guitar-TECHS P1/P2 technique clips; normal excluded.',
      'split':'Identical held-out clips: two player-disjoint Guitar-TECHS folds and exercise-disjoint legacy folds.',
      'accuracy':'One-vs-rest (TP+TN)/N; includes true negatives and can look high for rare classes.',
      'precision':'TP/(TP+FP); a value of zero is used when no positive prediction exists.',
      'recall':'TP/(TP+FN), the fraction of true instances detected.',
      'unsupported':'Baseline palm_mute, harmonics and pinch_harmonics are not supported; chart displays N/A.',
      'scope':'Clip/exercise evaluation, not confirmed accuracy on individual TAB notes or full mixes.'},'evaluations':{}}
    for scope in ['all','guitar_style','guitar_techs']:
        mask=np.ones(len(rows),dtype=bool) if scope=='all' else np.array([r['dataset']==scope for r in rows])
        result['evaluations'][scope]={'baseline':per_class(y[mask],baseline[mask],classes,legacy_labels),
         'combined':per_class(y[mask],combined[mask],classes,classes)}
    (OUT/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with (OUT/'per-technique.csv').open('w',newline='',encoding='utf-8-sig') as file:
        writer=csv.writer(file);writer.writerow(['evaluation','model','technique','supported','support','accuracy','precision','recall','tp','fp','fn','tn'])
        for scope,models in result['evaluations'].items():
            for model,metrics in models.items():
                for label,c in metrics['per_class'].items():writer.writerow([scope,model,label,*[c[k] for k in ['supported','support','accuracy','precision','recall','tp','fp','fn','tn']]])
    with (OUT/'predictions.csv').open('w',newline='',encoding='utf-8-sig') as file:
        writer=csv.writer(file);writer.writerow(['index','dataset','held_out_player','group','truth','baseline','combined'])
        for i,r in enumerate(rows):writer.writerow([i,r['dataset'],fold_ids[i],r['group'],y[i],baseline[i],combined[i]])
    plot(result,'all','technique-comparison.png','동일한 전체 평가 자료 · 2,225개 구간')
    plot(result,'guitar_style','legacy-technique-comparison.png','기존 9개 주법 평가 자료 · 549개 녹음')
    print(json.dumps({k:{m:round(v['multiclass_accuracy']*100,2) for m,v in models.items()} for k,models in result['evaluations'].items()},indent=2),flush=True)

def plot(result,scope,filename,subtitle):
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'mpl-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Patch
    font=FontProperties(fname='C:/Windows/Fonts/malgun.ttf')
    plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
    models=result['evaluations'][scope]
    labels=ORDER if scope=='all' else [l for l in ORDER if models['baseline']['per_class'][l]['support']>0]
    fig,axes=plt.subplots(1,3,figsize=(15,9),sharey=True)
    fig.patch.set_facecolor('#ffffff');colors={'baseline':'#94a3b8','combined':'#0f766e'}
    y=np.arange(len(labels));height=.29
    for ax,metric,title in zip(axes,['accuracy','precision','recall'],['정확도 · 일대나머지','정밀도 · Precision','재현율 · Recall']):
        for model,offset in [('baseline',-height/2),('combined',height/2)]:
            for i,label in enumerate(labels):
                entry=models[model]['per_class'][label]
                if not entry['supported']:
                    ax.text(1,i+offset,'미지원',ha='left',va='center',fontsize=9,color='#64748b');continue
                value=entry[metric]*100
                ax.barh(i+offset,value,height=height-.025,color=colors[model],zorder=3)
                ax.text(min(value+1,102),i+offset,f'{value:.1f}',ha='left',va='center',fontsize=8.5,color='#1e293b')
        ax.set_title(title,loc='left',fontsize=13,fontweight='bold',pad=18,color='#0f172a')
        ax.set_xlim(0,114);ax.set_xticks([0,25,50,75,100],['0','25','50','75','100%'])
        ax.grid(axis='x',color='#e2e8f0',linewidth=.7,zorder=0);ax.tick_params(axis='both',length=0,labelcolor='#334155')
        for spine in ax.spines.values():spine.set_visible(False)
        ax.set_yticks(y,[NAMES[l]+f"  (n={models['combined']['per_class'][l]['support']})" for l in labels])
        if scope=='all':ax.axhline(8.5,color='#cbd5e1',linewidth=.8)
    axes[0].invert_yaxis()
    fig.suptitle('기타 주법별 모델 성능 비교',x=.025,y=.98,ha='left',fontsize=22,fontweight='bold',color='#0f172a')
    fig.text(.025,.925,subtitle+'  |  일반 단음 제외',fontsize=11,color='#475569')
    fig.legend(handles=[Patch(color=colors['baseline'],label='기존 9클래스 방식'),Patch(color=colors['combined'],label='통합 학습 12클래스')],loc='upper right',bbox_to_anchor=(.97,.95),frameon=False,ncol=2,fontsize=11)
    fig.text(.025,.045,'정확도는 해당 주법이 아닌 음을 맞힌 경우도 포함합니다. 주법 검출 성능은 정밀도와 재현율을 함께 확인하세요.',fontsize=10,color='#475569')
    fig.text(.025,.018,'두 방식 모두 같은 시험 자료로 평가 · 기존 방식도 학습/시험을 분리해 재학습 · 구간 분류 결과이며 TAB 개별 음표 정확도는 아님',fontsize=9,color='#64748b')
    fig.subplots_adjust(left=.19,right=.98,top=.86,bottom=.10,wspace=.13)
    fig.savefig(OUT/filename,dpi=160,facecolor=fig.get_facecolor())
    fig.savefig(OUT/filename.replace('.png','.svg'),facecolor=fig.get_facecolor())
    plt.close(fig)

if __name__=='__main__':main()

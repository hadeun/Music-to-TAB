"""Audit the locally produced candidate and write a concise validation summary."""
import hashlib,json
from pathlib import Path
import joblib,numpy as np
from sklearn.metrics import confusion_matrix
from train_combined import metrics
ROOT=Path(__file__).resolve().parent
out=ROOT/'artifacts-guitar-techs-no-normal'
report=json.loads((out/'evaluation.json').read_text())
rows=json.loads((out/'manifest-used.json').read_text())
features=np.load(out/'features.npz');X=features['X'];y=features['y']
select=np.array([r['dataset']=='guitar_techs' for r in rows])
old=joblib.load(ROOT/'artifacts/classifier.joblib')['classifier'];pred=old.predict(X[select])
report['baseline_on_guitar_techs']=metrics(y[select],pred,sorted(set(y[select])))
report['baseline_on_guitar_techs']['confusion_matrix_all_classes']=confusion_matrix(y[select],pred,labels=report['classes']).tolist()
candidate=joblib.load(out/'classifier.joblib')
if 'normal' in y or 'normal' in candidate['classifier'].classes_:raise ValueError('Ordinary single notes must not enter training')
probabilities=candidate['classifier'].predict_proba(X[::max(1,len(X)//30)])
if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=1),1):raise ValueError('Invalid candidate probabilities')
report['artifact_audit']={'probabilities_finite_normalized':True,'classes':len(candidate['classifier'].classes_),
 'source_manifest_sha256':hashlib.sha256((out/'manifest-used.json').read_bytes()).hexdigest(),
 'deployed_original_sha256':hashlib.sha256((ROOT/'artifacts/classifier.joblib').read_bytes()).hexdigest(),
 'activated':False}
candidate['report']=report
joblib.dump(candidate,out/'classifier.audited.pending');(out/'classifier.audited.pending').replace(out/'classifier.joblib')
(out/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
legacy=report['datasets']['guitar_style'];baseline=report['legacy_baseline_same_split'];techs=report['datasets']['guitar_techs']
lines=['# Guitar-TECHS candidate validation','',f"Samples: {report['samples']}; classes: {len(report['classes'])}.",'',
 '| Evaluation | Accuracy | Macro F1 |','|---|---:|---:|',
 f"| Combined held-out folds | {report['combined']['accuracy']:.2%} | {report['combined']['macro_f1']:.2%} |",
 f"| Guitar-TECHS held-out players | {techs['accuracy']:.2%} | {techs['macro_f1']:.2%} |",
 f"| Legacy data, combined model | {legacy['accuracy']:.2%} | {legacy['macro_f1']:.2%} |",
 f"| Legacy data, legacy-only baseline, identical split | {baseline['accuracy']:.2%} | {baseline['macro_f1']:.2%} |",'',
 'The original deployed classifier has not been replaced. This report evaluates clips/exercises, not note-level or mixed-track detection.',
 'Technique data has only two players. Calibration uses time blocks; outer evaluation holds out each player and every corresponding recording/view.',
 '', '## Guitar-TECHS per-class held-out F1','']
for label in sorted(set(y[select])):lines.append(f"- {label}: {techs['classification_report'][label]['f1-score']:.2%}")
(out/'VALIDATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines),flush=True)

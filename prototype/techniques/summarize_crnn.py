"""Compare the grouped CRNN run with the previous 12-class pipeline."""
import argparse,json,hashlib
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--transfer',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parent;OUT=ROOT/('artifacts-crnn-transfer' if args.transfer else 'artifacts-crnn')
new=json.loads((OUT/'evaluation.json').read_text())
old=json.loads((ROOT/'artifacts-guitar-techs-no-normal/evaluation.json').read_text())
names={'bend':'벤딩','vibrato':'비브라토','hammer_on':'해머링온','pull_off':'풀링오프'}
old_temporal=sum(old['combined']['classification_report'][label]['f1-score'] for label in names)/4
new_temporal=sum(new['combined']['classification_report'][label]['f1-score'] for label in names)/4
recommended=new['combined']['macro_f1']>=old['combined']['macro_f1'] and new_temporal>=old_temporal
settings=json.loads((ROOT/'active-backend.json').read_text()) if (ROOT/'active-backend.json').exists() else {}
activated=settings.get('artifact','').replace('\\','/')==str(OUT.relative_to(ROOT)/'classifier.pt').replace('\\','/')
decision={'recommend_activation':recommended,'activated':activated,'selection_reason':'User requested CRNN migration; transfer variant selected at near-parity overall validation with disclosed per-technique tradeoffs.' if activated else 'Candidate retained separately.',
 'old_combined_macro_f1':old['combined']['macro_f1'],
 'crnn_combined_macro_f1':new['combined']['macro_f1'],'old_temporal_four_macro_f1':old_temporal,'crnn_temporal_four_macro_f1':new_temporal,
 'checkpoint_sha256':hashlib.sha256((OUT/'classifier.pt').read_bytes()).hexdigest(),
 'note':'Activation recommendation requires no decline in overall macro F1 and the four requested temporal techniques; not a fresh final benchmark.'}
(OUT/'decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
lines=['# CRNN 시간 문맥 모델 검증','',f"평가 원본 {new['recordings']}개, 시간 구간 {new['temporal_windows']}개, 12개 주법. 일반 단음 제외.",'',
 '| 평가 | 기존 CNN 특징 + SVM macro F1 | CNN + BiGRU CRNN macro F1 |','|---|---:|---:|',
 f"| 전체 | {old['combined']['macro_f1']:.2%} | {new['combined']['macro_f1']:.2%} |"]
for dataset,name in [('guitar_style','기존 자료'),('guitar_techs','Guitar-TECHS 연주자 분리')]:
    lines.append(f"| {name} | {old['datasets'][dataset]['macro_f1']:.2%} | {new['datasets'][dataset]['macro_f1']:.2%} |")
lines.extend(['','| 주법 | 기존 F1 | CRNN 정밀도 | CRNN 재현율 | CRNN F1 |','|---|---:|---:|---:|---:|'])
for label,name in names.items():
    a=old['combined']['classification_report'][label];b=new['combined']['classification_report'][label]
    lines.append(f"| {name} | {a['f1-score']:.2%} | {b['precision']:.2%} | {b['recall']:.2%} | {b['f1-score']:.2%} |")
lines.extend(['','## 범위와 해석','',
 ('기존 ImageNet ResNet50을 고정하고 시간 순서를 유지한 특징으로 투영층/GRU/분류기를 학습했다. 구간당 시간 단계는 7개다.' if args.transfer else 'CNN의 시간축을 유지해 양방향 GRU로 전달하고, CNN/GRU를 함께 학습했다.')+' 시간 문맥은 각 2초 구간 안으로 제한된다.',
 '동일 원본과 외부 평가 분할을 사용하지만, CRNN은 기존 녹음에서 최대 네 개의 구간을 선택하므로 전처리도 달라졌다. 순환층 추가만의 효과로 해석할 수 없다.',
 '학습 횟수는 내부 그룹 분리 검증에서 선택하고, 외부 시험 자료는 학습/선택에 쓰지 않았다. 다만 기존 개발 중 이미 확인한 외부 분할이므로 완전히 새로운 최종 시험은 아니다.',
 '확률 출력은 보정하지 않은 softmax다. 정확한 주법 시작/끝, 두 음의 해머링·풀링 연결, 벤딩+비브라토 동시 주법은 현재 라벨로 검증하지 못한다.',
 '', '## 적용 판단','', '사용자의 CRNN 전환 요청에 따라 이 모델을 활성화했다. 전체 성능은 비슷하지만 주법별 개선·하락이 함께 있으므로 일괄적인 성능 향상으로 해석하면 안 된다.' if activated else ('성능 기준상 적용 권장.' if recommended else '이번 실행은 기존 모델 대비 성능 기준을 충족하지 못해 기본 모델을 자동 교체하지 않음.'),
 'checkpoint는 classifier.pt에 별도 저장했으며, 최종 가중치는 전체 자료를 학습한 것이다. 표의 수치는 이 최종 모델의 학습 정답률이 아니라 분리 평가 결과다.'])
(OUT/'VALIDATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines),flush=True)

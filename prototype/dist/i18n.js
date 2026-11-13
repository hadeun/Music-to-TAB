(function(root){
function detectLanguage(saved,languages,zone){
 if(saved==='ko'||saved==='en')return saved;
 return zone==='Asia/Seoul'||languages.some(l=>/^ko(?:-|$)/i.test(l)||/-KR(?:-|$)/i.test(l))?'ko':'en';
}
if(typeof document==='undefined'){module.exports={detectLanguage};return;}
const ko={
 'Re-transcribe with guitar focus':'기타 집중 모드로 다시 채보',
 'The original project and edits will be kept. A new project will use guitar-conditioned Muscriptor decoding from the beginning.':'기존 프로젝트와 수정본은 보존합니다. 처음부터 기타로 악기를 제한해 채보하고 새 프로젝트로 저장합니다.',
 'Original / synth balance':'원본 음원 / 악보 합성음 비율',
 'Original audio is available after uploading a file in this session.':'원본 음원을 다시 업로드하면 재생할 수 있습니다.',
 'Audio could not be played. Please upload it again.':'음원을 재생할 수 없습니다. 다시 업로드하세요.',
 'Original audio could not be saved.':'원본 음원을 저장하지 못했습니다.',
 'This project changed in another tab. Reopen it from My projects.':'다른 탭에서 프로젝트가 변경됐습니다. 내 프로젝트에서 다시 열어주세요.',
 'Local Muscriptor server → instrument-labelled notes and MIDI → guitar fingering → TAB. No audio stem separation or lead/rhythm separation is implemented. No alternative transcription model is used.':'로컬 Muscriptor 서버 → 악기별 음표 및 MIDI → 기타 운지 배치 → TAB 순서로 처리합니다. 오디오 STEM 분리와 리드·리듬 분리는 구현되지 않았으며 다른 채보 모델로 대체하지 않습니다.',
 'Technique research server is not running. No technique was inferred.':'주법 분석 서버가 실행 중이 아닙니다. 주법을 추정하지 않았습니다.',
 'Audio exceeds 100 MB':'음원이 100MB를 초과합니다.','Audio exceeds 5 minutes':'음원이 5분을 초과합니다.','Could not decode audio':'음원을 디코딩할 수 없습니다.','Empty or invalid audio':'음원이 비어 있거나 올바르지 않습니다.',
 'Model configuration mismatch':'모델 설정이 일치하지 않습니다.',
 'YOUR WORKSPACE':'내 작업 공간','Practice studio':'연습 작업실','My projects':'내 프로젝트','＋ New transcription':'＋ 새 채보',
 'Workspace':'작업 공간','Browser-local prototype':'브라우저 로컬 프로토타입','Private workspace':'개인 작업 공간','Prototype scope':'프로토타입 기능 안내',
 'YOUR SONG. YOUR SIX STRINGS.':'좋아하는 곡을, 나의 여섯 줄로.','Make it your next song.':'다음 연주곡을 준비하세요.',
 'From a recording to the way you play.':'녹음에서 나만의 연주까지.','＋ Upload a song':'＋ 음원 업로드','Real AI transcription.':'AI 자동 채보',
 'Muscriptor runs on your local server. Instrument-labelled MIDI → guitar TAB.':'로컬 Muscriptor 서버에서 악기별 MIDI를 추출하고 기타 TAB으로 변환합니다.',
 'How it works ↗':'작동 방식 ↗','YOUR':'나의','RECORDING':'녹음','AI TRANSCRIPTION':'AI 채보','No audio loaded':'음원 없음',
 'Your recording':'내 녹음','Upload your first recording':'첫 음원을 업로드하세요','Upload your recording to transcribe':'채보할 음원을 업로드하세요',
 'Single guitar recommended':'기타 단독 녹음 권장','Mixed audio · no source separation':'전체 믹스 · 오디오 분리 없음','AI transcription':'AI 채보',
 'E standard':'E 표준 튜닝','No capo':'카포 없음','↓ Export TAB':'↓ TAB 내보내기','✓ All changes saved':'✓ 모든 변경 저장됨','✓ Saved in this browser':'✓ 이 브라우저에 저장됨',
 'Not saved — export JSON':'저장되지 않음 — JSON으로 내려받으세요','⌁ Guitar transcription':'⌁ 기타 채보','Part separation unavailable':'파트 분리 미지원',
 'Source separation is not connected':'오디오 분리가 연결되지 않았습니다','Guitar · AI note estimates':'기타 · AI 추정 음표','Standard tuning':'표준 튜닝',
 'SCORE':'악보','Original audio timing':'원본 음원 시간 기준','Click any note to fine-tune your transcription.':'음표를 클릭해 채보를 수정하세요.',
 '6 strings. Endless possibilities.':'여섯 줄에 담는 무한한 가능성.','A starting point for your ears.':'직접 듣고 확인해보세요.',
 'Automatic transcription can miss a detail. Listen, adjust, and make it yours.':'자동 채보에는 오류가 있을 수 있습니다. 듣고 수정하며 나만의 악보를 만드세요.',
 'Give feedback ↗':'의견 보내기 ↗','Note inspector':'음표 편집','Every note matters.':'음표 하나까지 세밀하게.',
 'Select a note on the TAB to adjust its pitch, timing, or technique.':'TAB의 음표를 선택해 음높이, 길이, 주법을 수정하세요.',
 'String':'줄','Fret':'프렛','Start (ticks, 480 = quarter note)':'시작 위치 (틱, 480 = 4분음표)','Duration (ticks)':'음 길이 (틱)',
 'Technique':'주법','None':'없음','Bend':'벤딩','Slide':'슬라이드','Hammer-on':'해머링온','Pull-off':'풀링오프','Apply & save':'적용 및 저장',
 'Pitch follows your string and fret.':'줄과 프렛에 따라 음높이가 바뀝니다.','TUNING':'튜닝','Standard · 6-string guitar · No capo':'표준 튜닝 · 6현 기타 · 카포 없음',
 '♫ Synth TAB':'♫ 악보 합성음','Original audio':'원본 음원','Auto-scroll':'자동 스크롤','Restart playback':'처음부터 재생','Play':'재생','Pause':'일시 정지',
 'Playback position':'재생 위치','Playback speed':'재생 속도','Zoom out':'축소','Zoom in':'확대','Close dialog':'창 닫기',
 'A little practice, a little closer.':'연습할수록 가까워지는 연주.','Built for the songs you love.':'좋아하는 곡을 연주하세요.',
 'LOCAL MUSCRIPTOR SERVER':'로컬 MUSCRIPTOR 서버','Audio is sent to your local model server.':'음원을 이 PC의 모델 서버로 전송합니다.',
 'No conversion limit in this build.':'이 프로토타입에는 변환 횟수 제한이 없습니다.','Local workspace':'로컬 작업 공간','Local model server · no sign-in':'로컬 모델 서버 · 로그인 없음',
 'No sample notes. Upload a recording to start.':'샘플 음표를 사용하지 않습니다. 녹음을 업로드하세요.','Your TAB appears only after real model inference.':'실제 모델 분석이 완료되면 TAB이 표시됩니다.',
 'Let’s hear your guitar.':'기타 연주를 들려주세요.','Real audio in. AI-estimated notes out.':'실제 음원에서 AI가 음표를 추정합니다.',
 'Transcribe your recording.':'녹음 채보하기','Muscriptor analyses audio on your local model server and returns instrument-labelled notes and MIDI.':'로컬 Muscriptor 서버가 음원을 분석해 악기별 음표와 MIDI를 반환합니다.',
 'Drop your song here':'여기에 음원을 놓으세요','MP3, WAV or M4A · 100 MB maximum · 5 minutes maximum':'MP3, WAV, M4A · 최대 100MB · 최대 5분',
 'Choose audio file':'음원 파일 선택','Song title':'곡명','Give your song a name':'곡명을 입력하세요','Recording type':'녹음 종류',
 'Solo guitar / isolated stem (recommended)':'기타 단독 / 분리된 기타 음원 (권장)','Full mix (instrument-labelled transcription)':'전체 믹스 (악기별 음표 추정)',
 'Muscriptor identifies instrument groups. Lead/rhythm separation and audio STEM extraction are not available.':'Muscriptor는 악기 종류를 구분합니다. 리드·리듬 분리와 오디오 STEM 추출은 지원하지 않습니다.',
 'Tempo (BPM, for bar lines)':'템포 (BPM, 마디 구분 기준)','Time signature':'박자표',
 'Muscriptor detects instrument-labelled notes. Guitar notes are mapped to standard tuning; audio STEM separation is not included.':'Muscriptor가 악기별 음표를 추정합니다. 기타 음표는 표준 튜닝에 배치하며 오디오 STEM 분리는 포함하지 않습니다.',
 'Standard tuning · No capo · Original note timing retained':'표준 튜닝 · 카포 없음 · 원본 음표 시간 유지','Transcribe with AI →':'AI로 채보하기 →',
 'Decoding & resampling audio…':'음원을 디코딩하고 변환하는 중…','Choose an MP3, WAV or M4A file.':'MP3, WAV 또는 M4A 파일을 선택하세요.',
 'This file exceeds 100 MB.':'파일이 100MB를 초과합니다.','This recording exceeds 5 minutes. Audio will not be trimmed.':'음원이 5분을 초과합니다. 자동으로 자르지 않습니다.',
 'This recording contains no playable audio.':'재생 가능한 오디오가 없습니다.','This file could not be decoded.':'이 음원을 디코딩할 수 없습니다.',
 'Muscriptor transcription':'Muscriptor 채보','Connecting to local Muscriptor…':'로컬 Muscriptor에 연결하는 중…',
 'Audio is processed by the local Muscriptor server. Keep this tab open.':'로컬 Muscriptor 서버가 음원을 처리합니다. 이 탭을 열어두세요.',
 'Cancel transcription':'채보 취소','Transcription cancelled.':'채보를 취소했습니다.','Muscriptor transcription complete.':'Muscriptor 채보가 완료됐습니다.',
 'A transcription is already running.':'이미 채보가 진행 중입니다.','Cancel the active transcription first.':'진행 중인 채보를 먼저 취소하세요.',
 'Muscriptor must be running locally with authorized model weights. No alternative model is used.':'접근 승인된 모델로 로컬 Muscriptor 서버가 실행 중이어야 합니다. 다른 모델로 대체하지 않습니다.',
 'Muscriptor disconnected before completion.':'채보가 완료되기 전에 Muscriptor 연결이 끊어졌습니다.','Muscriptor returned no playable guitar notes.':'Muscriptor가 연주 가능한 기타 음표를 찾지 못했습니다.',
 'PICK UP WHERE YOU LEFT OFF':'이어서 연습하세요','Your private collection, ready for another session.':'다음 연습을 위한 나만의 악보 모음입니다.',
 'Browser-local storage · Projects expire 30 days after creation. Download before expiry.':'브라우저 로컬 저장 · 프로젝트는 생성 후 30일에 만료됩니다. 만료 전에 내려받으세요.',
 'Open studio →':'작업실 열기 →','Delete this project?':'프로젝트를 삭제할까요?','Delete project':'프로젝트 삭제','Project deleted.':'프로젝트를 삭제했습니다.',
 'No projects yet. Upload a recording to transcribe. Old prototype samples are not AI results and are not listed here.':'아직 프로젝트가 없습니다. 채보할 녹음을 업로드하세요. 이전 프로토타입의 샘플은 표시하지 않습니다.',
 'Take your practice with you.':'악보 내보내기','PDF sheet music':'PDF 악보','Print the current TAB or save as PDF':'현재 TAB을 인쇄하거나 PDF로 저장',
 'MIDI file':'MIDI 파일','Edited pitches and timing · techniques not encoded':'수정한 음높이와 시간 반영 · 주법 정보는 포함되지 않음',
 'Editable score JSON':'편집 가능한 악보 JSON','AI events, unassigned notes, original and edited score':'AI 이벤트, 미배치 음표, 원본 및 수정 악보',
 'Unavailable · exporter integration not yet validated':'미지원 · 내보내기 연동 검증 전','MIDI downloaded.':'MIDI를 내려받았습니다.',
 'Help us find the right notes.':'채보 개선 의견','How did this transcription feel? Feedback stays in this browser in this prototype.':'채보 결과는 어떠셨나요? 의견은 이 브라우저에 저장됩니다.',
 'What needs a closer listen?':'어떤 부분을 개선하면 좋을까요?','Notes':'음표','Rhythm':'리듬','Techniques':'주법','Part separation':'파트 분리',
 'Optional comment':'추가 의견 (선택)','Tell us what you heard…':'어떤 부분이 달랐는지 알려주세요…','Save feedback locally':'이 브라우저에 의견 저장',
 'Choose a rating from 1 to 5.':'1~5점 중 평점을 선택하세요.','Thanks — your feedback is saved locally.':'감사합니다. 의견을 이 브라우저에 저장했습니다.',
 'Analyze techniques · experimental':'주법 분석 및 자동 적용 · 실험 기능','Review technique candidates':'주법 후보 변경','Analyzing original audio…':'원본 음원의 주법을 분석하는 중…',
 'Separating guitar and analyzing techniques…':'기타 음원 분리 및 주법 분석 중…','Use mono or stereo audio for guitar separation.':'기타 분리에는 모노 또는 스테레오 음원을 사용해 주세요.',
 'Edit technique candidates':'주법 후보 변경','Apply change':'변경 적용','Confirmed':'적용됨','Techniques applied to TAB:':'TAB에 주법을 적용한 음표 수:',
 'Previous':'이전','Next':'다음','Estimated technique probabilities':'주법 후보별 추정 확률',
 'Only techniques scoring at least 70% are applied automatically. Lower-scoring candidates remain available for manual selection. Scores are estimates from audio windows, not guarantees about individual notes.':'점수가 70% 이상인 주법만 자동 표기합니다. 낮은 점수의 후보도 직접 선택할 수 있습니다. 점수는 음원 구간에서 추정한 값이며 개별 음표의 정확도를 보장하지 않습니다.',
 'Closed-set experimental clip predictions; ordinary playing and mixed audio may be misclassified.':'제한된 주법 종류를 구분하는 실험 모델입니다. 일반 연주와 전체 믹스에서는 오인식할 수 있습니다.',
 'Experimental clip predictions; note-level and mixed audio are not validated.':'실험 단계의 구간 분류 결과입니다. 개별 음표와 전체 믹스에 대한 정확도는 검증되지 않았습니다.',
 'Upload and transcribe a recording first.':'먼저 녹음을 업로드하고 채보하세요.','Analyze this recording first.':'먼저 이 녹음의 주법을 분석하세요.',
 'Transcribe with Muscriptor first.':'먼저 Muscriptor로 이 음원을 채보하세요.',
 'Choose instruments':'악기 직접 선택','Instruments in the recording':'음원에 포함된 악기',
 'Select at least one guitar type.':'기타 종류를 하나 이상 선택하세요.',
 'Acoustic guitar':'어쿠스틱 기타','Clean electric guitar':'클린 일렉트릭 기타','Distorted electric guitar':'디스토션 일렉트릭 기타',
 'Acoustic piano':'어쿠스틱 피아노','Electric piano':'일렉트릭 피아노','Acoustic bass':'어쿠스틱 베이스','Electric bass':'일렉트릭 베이스','Drums':'드럼','Voice':'보컬',
 'The technique classifier has not been trained yet.':'주법 모델이 아직 학습되지 않았습니다.','Original audio is missing. Re-upload the recording.':'원본 음원이 없습니다. 다시 업로드하세요.',
 'Technique analysis failed.':'주법 분석에 실패했습니다.','Technique analysis is busy.':'다른 주법 분석이 진행 중입니다.','Technique classifier has not been trained.':'주법 모델이 아직 학습되지 않았습니다.',
 'Reopen this project first.':'이 프로젝트를 다시 열어주세요.','This project changed in another tab. Reopen it first.':'다른 탭에서 프로젝트가 변경됐습니다. 다시 열어주세요.',
 'This project changed in another tab. Reopen it before saving technique candidates.':'다른 탭에서 프로젝트가 변경됐습니다. 다시 연 뒤 주법을 분석하세요.',
 'Technique confirmed and saved. MIDI does not encode this articulation.':'주법 변경을 저장했습니다. MIDI에는 이 주법 정보가 포함되지 않습니다.',
 'Choose a fret from 0 to 24.':'0~24 범위의 프렛과 올바른 음 길이를 입력하세요.','Another note overlaps on this string. Choose a different string or length.':'같은 줄에서 다른 음표와 겹칩니다. 줄이나 음 길이를 바꾸세요.',
 'Storage is full. Download your score to keep a copy.':'저장 공간이 부족합니다. 악보를 내려받아 보관하세요.',
 'Muscriptor instrument labels are not lead/rhythm separation. Fingering is suggested. Bar lines use a fixed 120 BPM display grid, not detected song tempo.':'Muscriptor의 악기 분류는 리드·리듬 분리가 아닙니다. 운지는 추정값이며 마디는 고정 120 BPM 표시 기준이며 곡의 실제 템포를 분석한 값이 아닙니다.',
 'bend':'벤딩','hammer_on':'해머링온','pull_off':'풀링오프','slide':'슬라이드','vibrato':'비브라토','tapping':'태핑','alternate_picking':'얼터네이트 피킹','sweep_picking':'스윕 피킹','legato':'레가토',
 'palm_mute':'팜뮤트','palm mute':'팜뮤트','harmonics':'자연 하모닉스','pinch_harmonics':'피치 하모닉스','pinch harmonics':'피치 하모닉스','normal':'일반 단음 (주법 기호 없음)',
 'hammer on':'해머링온','pull off':'풀링오프','alternate picking':'얼터네이트 피킹','sweep picking':'스윕 피킹',
 'What you can try today':'현재 사용할 수 있는 기능','Available':'지원 기능','Still to build and validate':'추가 구현·검증이 필요한 기능','Product decisions still open':'아직 결정되지 않은 정책',
 'Try uploading a recording →':'음원 업로드하기 →',
 'This working prototype explores the upload → transcription → practice → edit → export flow. It is not the public beta.':'업로드 → 채보 → 연습 → 편집 → 내보내기 흐름을 체험하는 프로토타입입니다. 공개 베타 서비스는 아닙니다.',
 'MP3, WAV and M4A decoding; up to 100 MB and 5 minutes; Muscriptor note estimation through a local server (requires authorized weights); standard six-string TAB; original and synthesized playback; playback speed; note editing; browser-local projects; MIDI, score JSON and browser PDF printing.':'MP3·WAV·M4A 디코딩, 최대 100MB·5분, 로컬 Muscriptor 채보, 6현 표준 튜닝 TAB, 원본·합성음 재생, 속도 조절, 음표 편집, 로컬 프로젝트 저장, MIDI·JSON·PDF 인쇄를 지원합니다.',
 'Google sign-in, private server storage, lead/rhythm separation, validated automatic note-level technique recognition, validated TuxGuitar .tg exports, weekly account quotas and server-side 30-day deletion.':'Google 로그인, 서버 개인 저장, 리드·리듬 분리, 신뢰할 수 있는 음표별 주법 자동 인식, TuxGuitar .tg 내보내기, 주간 사용 한도, 서버의 30일 자동 삭제는 추가 검증이 필요합니다.',
 'Local expiry is checked when the app opens; it is not a server retention guarantee. Conversion speed and transcription quality depend on the recording and device. Full mixes may include notes from other instruments.':'로컬 만료는 앱을 열 때 확인합니다. 서버의 보관 기간을 보장하는 기능은 아닙니다. 처리 속도와 채보 품질은 녹음과 기기에 따라 다르며 전체 믹스에 다른 악기의 음이 포함될 수 있습니다.',
 'Whether a result with a quality warning consumes a weekly conversion; supported commercial recordings and rights arrangements; launch dates and the final playback-speed range.':'품질 경고 결과의 사용 횟수 차감 여부, 상업 음원 지원 범위와 권리 확보, 출시 일정, 최종 재생 속도 범위는 아직 결정되지 않았습니다.'
};
let saved;try{saved=localStorage.getItem('music-to-tab-language')}catch{}
let language=detectLanguage(saved,navigator.languages||[navigator.language],Intl.DateTimeFormat().resolvedOptions().timeZone);
function t(s){
 if(language!=='ko')return s;
 if(ko[s])return ko[s];
 if(/^Revision (\d+) saved in this browser\.$/.test(s))return s.replace(/^Revision (\d+) saved in this browser\.$/,'수정본 $1을 이 브라우저에 저장했습니다.');
 let v=s;
 for(const [en,value] of Object.entries(ko))if(en.length>35&&v.includes(en))v=v.replaceAll(en,value);
 return v.replace(/^Revision (\d+)/,'수정본 $1').replace(/^Available until /,'보관 만료일: ').replace(/(\d+) notes from your audio ·/,'음원에서 추정한 음표 $1개 ·').replace(/Measure (\d+), string (\d+), fret (\d+),/,'$1마디, $2번 줄, $3프렛,').replace(/^Measure (\d+) · /,'$1마디 · ').replace(/^Muscriptor: (\d+) \/ (\d+) chunks/,'Muscriptor: $1 / $2 구간').replace(/^Revision (\d+) saved in this browser\./,'수정본 $1을 이 브라우저에 저장했습니다.').replace(/^Review (\d+) excluded notes/,'제외된 음표 $1개 검토').replace(/^AI transcription · Revision (\d+) · Expires /,'AI 채보 · 수정본 $1 · 만료일 ').replace(/^(\d+) · E4 \(high\)$/,'$1 · E4 (가장 높은 줄)').replace(/^(\d+) · E2 \(low\)$/,'$1 · E2 (가장 낮은 줄)');
}
root.t=t;root.appLocale=language==='ko'?'ko-KR':'en-US';
const originals=new WeakMap(),attrs=new WeakMap();
function translate(node){
 if(node.nodeType===3){
  if(!node.parentElement||node.parentElement.closest('script,style,[data-i18n-skip],#songTitle,#scoreTitle,.project-row h3'))return;
  const current=node.nodeValue;let state=originals.get(node);if(!state||current!==state.rendered)state={source:current};
  const trim=state.source.trim();state.rendered=state.source.replace(trim,t(trim));originals.set(node,state);if(current!==state.rendered)node.nodeValue=state.rendered;
 }else if(node.nodeType===1){
  if(node.matches('script,style,[data-i18n-skip]'))return;
  for(const name of ['placeholder','aria-label','title'])if(node.hasAttribute(name)){
   const current=node.getAttribute(name),all=attrs.get(node)||{};let state=all[name];if(!state||state.rendered!==current)state={source:current};state.rendered=t(state.source);all[name]=state;attrs.set(node,all);if(current!==state.rendered)node.setAttribute(name,state.rendered);
  }
  [...node.childNodes].forEach(translate);
 }
}
const picker=document.createElement('select');picker.dataset.i18nSkip='';picker.setAttribute('aria-label','언어 / Language');picker.innerHTML='<option value="ko">한국어</option><option value="en">English</option>';picker.value=language;picker.style.cssText='font-size:12px;margin-left:16px;min-width:90px';document.querySelector('header').append(picker);
document.documentElement.lang=language;
picker.onchange=()=>{language=picker.value;root.appLocale=language==='ko'?'ko-KR':'en-US';try{localStorage.setItem('music-to-tab-language',language)}catch{}document.documentElement.lang=language;if(typeof render==='function')render();if(typeof renderProjects==='function'&&!document.querySelector('#projects').hidden)renderProjects();translate(document.body);};
translate(document.body);
new MutationObserver(records=>{for(const r of records){if(r.type==='childList')r.addedNodes.forEach(translate);else translate(r.target);}}).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['placeholder','aria-label','title']});
})(globalThis);

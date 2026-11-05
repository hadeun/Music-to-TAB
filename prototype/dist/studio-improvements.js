// Display choices do not delete recognized events or user edits.
const optimizeFingeringButton=document.createElement('button');optimizeFingeringButton.className='button';optimizeFingeringButton.textContent='운지 정리 / Optimize fingering';document.querySelector('.score-tools').prepend(optimizeFingeringButton);
optimizeFingeringButton.onclick=()=>{
 if(!project.id)return;
 pause();const optimized=GuitarFingering.optimize(project.parts[part],{bpm:project.bpm,ppq:project.ppq||480});
 const changed=optimized.filter((n,i)=>n.string!==project.parts[part][i].string||n.fret!==project.parts[part][i].fret).length;
 if(!changed)return toast('변경할 운지가 없습니다. / No fingering changes.');
 const stored=JSON.parse(localStorage.getItem(KEY)||'null')?.projects.find(p=>p.id===project.id);
 if(stored&&stored.revision!==project.revision)return toast('프로젝트를 다시 열어주세요. / Reopen this project.');
 project.parts[part]=optimized;project.revision++;if(persist()){render();toast(changed+'개 음의 운지를 정리했습니다. / Notes repositioned.');}
};
const techniqueNames={b:'벤딩',h:'해머링온',p:'풀링오프','/':'슬라이드','~':'비브라토',T:'태핑',AP:'얼터네이트 피킹',SP:'스윕 피킹',L:'레가토',PM:'팜뮤트',NH:'자연 하모닉스',PH:'피치 하모닉스'};
let visibleTechniques;try{visibleTechniques=new Set(JSON.parse(localStorage.getItem('mtt-visible-techniques'))||Object.keys(techniqueNames));}catch{visibleTechniques=new Set(Object.keys(techniqueNames));}
try{if(!localStorage.getItem('mtt-visible-techniques-v3')){for(const symbol of ['PM','NH','PH'])visibleTechniques.add(symbol);localStorage.setItem('mtt-visible-techniques',JSON.stringify([...visibleTechniques]));localStorage.setItem('mtt-visible-techniques-v3','1');}}catch{}
const filters=document.createElement('details');filters.className='technique-filters';filters.innerHTML='<summary>표시할 주법 선택 / Visible techniques</summary>'+Object.entries(techniqueNames).map(([symbol,name])=>'<label><input type="checkbox" value="'+symbol+'" '+(visibleTechniques.has(symbol)?'checked':'')+'> '+name+' ('+symbol+')</label>').join('');document.querySelector('.score-toolbar').after(filters);
filters.onchange=()=>{visibleTechniques=new Set([...filters.querySelectorAll('input:checked')].map(e=>e.value));try{localStorage.setItem('mtt-visible-techniques',JSON.stringify([...visibleTechniques]));}catch{}renderScore();};
const scoreBeforeImprovements=renderScore;
renderScore=function(){
 scoreBeforeImprovements();
 for(const row of document.querySelectorAll('.staff-row')){
  let total=24;
  for(const bar of row.querySelectorAll('.measure')){
   const elements=[...bar.querySelectorAll('[data-note]')],notes=elements.map(el=>project.parts[part].find(n=>n.id===el.dataset.note));
   const times=[...new Set(notes.map(n=>n.start_tick))].sort((a,b)=>a-b),positions=new Map();let previous=-16;
   for(const tick of times){const x=Math.max(20+(tick%ticksPerBar())/ticksPerBar()*190,previous+56);positions.set(tick,x);previous=x;}
   const width=Math.max(220,previous+64);bar.style.flex='none';bar.style.width=width+'px';total+=width;
   elements.forEach((el,i)=>{const n=notes[i];el.style.left=positions.get(n.start_tick)+'px';const mark=el.querySelector('small');if(mark){mark.hidden=!visibleTechniques.has(n.technique)||!TechniqueAssignment.shouldDisplay(n);if(n.technique==='b')mark.textContent=Number.isFinite(n.bendSemitones)?'b→'+pitchName(n.pitch+n.bendSemitones):'b?';}});
  }
  row.style.width=total+'px';row.style.minWidth='100%';
 }
};
const bendField=document.createElement('label');bendField.innerHTML='벤딩 도착음 (시작음 대비 반음 수) / Bend semitones<input id="bendSemitones" type="number" min="0" max="24" step="1" placeholder="미확인 / Unknown">';document.querySelector('#noteForm .primary').before(bendField);
const inspectBeforeBend=inspect;inspect=function(){inspectBeforeBend();const n=project.parts[part].find(n=>n.id===selected);bendField.hidden=!n||n.technique!=='b';document.querySelector('#bendSemitones').value=n?.bendSemitones??'';};
document.querySelector('#noteTechnique').addEventListener('change',e=>{bendField.hidden=e.target.value!=='b';});
const submitBeforeBend=document.querySelector('#noteForm').onsubmit;document.querySelector('#noteForm').onsubmit=e=>{
 const n=project.parts[part].find(n=>n.id===selected),value=document.querySelector('#bendSemitones').value,revision=project.revision;
 if(value!==''&&(!Number.isInteger(+value)||+value<0||+value>24)){e.preventDefault();return toast('벤딩 폭은 0~24 반음으로 입력하세요.');}
 submitBeforeBend(e);if(project.revision!==revision&&n){if(value==='')delete n.bendSemitones;else n.bendSemitones=+value;persist();renderScore();}
};
const studioBeforeFocus=showStudio;showStudio=function(){studioBeforeFocus();document.querySelector('#scorePaper').scrollIntoView({block:'start',behavior:'smooth'});};
renderScore();inspect();
const highlightBeforeSpacing=highlight;highlight=function(){highlightBeforeSpacing();if(playing&&document.querySelector('#autoScroll').checked){const cursor=document.querySelector('.note.current')||document.querySelector('.measure.playing'),paper=document.querySelector('#scorePaper');if(cursor){const a=cursor.getBoundingClientRect(),b=paper.getBoundingClientRect();if(a.right>b.right-25)paper.scrollLeft+=a.right-b.right+40;else if(a.left<b.left+25)paper.scrollLeft+=a.left-b.left-40;}}};

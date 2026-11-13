// Automatic estimates are editable; source events and revision zero are preserved.
const techniqueButton=document.createElement('button');
techniqueButton.className='button';techniqueButton.textContent='Analyze techniques · experimental';
techniqueButton.hidden=true;
document.querySelector('.score-toolbar').before(techniqueButton);
fetch('/api/techniques/health').then(async response=>{
 if(response.ok){
  const status=await response.json();
  techniqueButton.hidden=!status.backend||status.backend==='disabled';
 }
}).catch(()=>{});
const techniqueSymbols=TechniqueAssignment.symbols;
function selectedTechniqueLabel(note){
 const alternatives=note.techniqueCandidates||[];
 return alternatives.find(c=>c.label===note.techniqueLabel&&techniqueSymbols[c.label]===note.technique)?.label||alternatives.find(c=>note.technique&&techniqueSymbols[c.label]===note.technique)?.label||'';
}
for(const [label,value] of Object.entries(techniqueSymbols)){
 if(![...document.querySelector('#noteTechnique').options].some(o=>o.value===value)){
  const option=document.createElement('option');option.value=value;option.textContent=label.replaceAll('_',' ');document.querySelector('#noteTechnique').append(option);
 }
}
const reviewTechniques=document.createElement('button');reviewTechniques.className='button';reviewTechniques.textContent='Review technique candidates';techniqueButton.after(reviewTechniques);
reviewTechniques.onclick=()=>showTechniqueCandidates(project);
function showTechniqueCandidates(target,page=0){
 const result=target.techniqueAnalysis;if(!result)return toast('Analyze this recording first.');
 const all=target.parts.guitar.filter(n=>n.techniqueCandidates?.length),notes=all.slice(page*30,(page+1)*30);
 modal('Edit technique candidates','<p>Only techniques scoring at least 70% are applied automatically. Lower-scoring candidates remain available for manual selection.</p><div style="max-height:420px;overflow:auto">'+notes.map((n,i)=>{
  const alternatives=n.techniqueCandidates,selectedLabel=selectedTechniqueLabel(n);
  return '<div class="technique-review-row"><p><b>'+time(n.start_tick/(target.bpm*8))+'</b> · '+(window.t?window.t('String'):'String')+' '+n.string+' · '+(window.t?window.t('Fret'):'Fret')+' '+n.fret+'</p><select data-tech-choice="'+i+'" aria-label="Technique"><option value="" '+(!selectedLabel?'selected':'')+'>'+(window.t?window.t('None'):'None')+'</option>'+alternatives.map(c=>'<option value="'+c.label+'" '+(c.label===selectedLabel?'selected':'')+'>'+(window.t?window.t(c.label):c.label)+' · '+(100*c.probability).toFixed(1)+'%</option>').join('')+'</select><button class="button" data-tech-confirm="'+i+'">Apply change</button></div>';
 }).join('')+'</div><div class="candidate-pages"><button class="button" id="techPrev" '+(!page?'disabled':'')+'>Previous</button><span>'+(page+1)+' / '+Math.max(1,Math.ceil(all.length/30))+'</span><button class="button" id="techNext" '+((page+1)*30>=all.length?'disabled':'')+'>Next</button></div>');
 document.querySelector('#techPrev').onclick=()=>showTechniqueCandidates(target,page-1);
 document.querySelector('#techNext').onclick=()=>showTechniqueCandidates(target,page+1);
 document.querySelectorAll('[data-tech-confirm]').forEach(button=>button.onclick=()=>{
  if(project!==target)return toast('Reopen this project first.');
  const i=+button.dataset.techConfirm,note=notes[i],label=document.querySelector('[data-tech-choice="'+i+'"]').value;
  const stored=JSON.parse(localStorage.getItem(KEY)||'null')?.projects.find(p=>p.id===target.id);
  if(stored&&stored.revision!==target.revision)return toast('This project changed in another tab. Reopen it first.');
  note.technique=techniqueSymbols[label]||'';note.techniqueLabel=label;note.techniqueSource='user-confirmed-spectrofusion-candidate';target.revision++;
  if(persist()){render();button.textContent='Confirmed';toast('Technique confirmed and saved. MIDI does not encode this articulation.');}
 });
}
techniqueButton.onclick=async()=>{
 if(!project.id)return toast('Upload and transcribe a recording first.');
 const target=project;techniqueButton.disabled=true;
 try{
  const health=await fetch('/api/techniques/health');const status=await health.json();
  if(!health.ok||!status.available)throw Error(status.detail||'The technique classifier has not been trained yet.');
  let notes;
  if(status.requires_muscriptor_notes){
   const delay=target.beatGrid?.onset_delay||0;
   notes=(target.rawEvents||[]).filter(n=>/guitar|distortion|overdriven/i.test(n.instrument))
    .map(n=>[Math.max(0,n.start_time-delay),n.end_time-delay,n.pitch])
    .filter(([start,end,pitch])=>Number.isFinite(start)&&Number.isFinite(end)&&end>start&&Number.isInteger(pitch));
   if(!notes.length)throw Error(window.t?window.t('Transcribe with Muscriptor first.'): 'Transcribe with Muscriptor first.');
  }
  const blob=await audioRecord(target.id,'get');
  if(!blob)throw Error('Original audio is missing. Re-upload the recording.');
  const ac=new AudioContext({sampleRate:44100});let audio;try{audio=await ac.decodeAudioData(await blob.arrayBuffer())}finally{await ac.close()}
  // Preserve stereo and full-band audio for Demucs; downmix only after guitar extraction.
  const buf=TechniqueAudio.wav(audio);
  techniqueButton.textContent='Separating guitar and analyzing techniques…';const form=new FormData();form.append('file',new Blob([buf],{type:'audio/wav'}),'audio.wav');
  if(notes)form.append('notes',JSON.stringify(notes));
  const response=await fetch('/api/techniques/analyze',{method:'POST',body:form}),result=await response.json();if(!response.ok)throw Error(result.detail||'Technique analysis failed.');
  if(project!==target)return;
  const stored=JSON.parse(localStorage.getItem(KEY)||'null')?.projects.find(p=>p.id===target.id);
  if(stored&&stored.revision!==target.revision)throw Error('This project changed in another tab. Reopen it before saving technique candidates.');
  pause();target.techniqueAnalysis=result;const count=TechniqueAssignment.assign(target,result);target.revision++;
  if(persist()){render();toast((window.t?window.t('Techniques applied to TAB:'):'Techniques applied to TAB:')+' '+count);}
 }catch(error){toast(error.message)}finally{techniqueButton.disabled=false;techniqueButton.textContent='Analyze techniques · experimental'}
};
const baseInspectTechniques=inspect;
inspect=function(){
 baseInspectTechniques();const n=project.parts[part].find(n=>n.id===selected);let field=document.querySelector('#rankedTechniqueField');
 if(!field){field=document.createElement('label');field.id='rankedTechniqueField';field.innerHTML='<span>Estimated technique probabilities</span><select id="rankedTechnique"></select>';document.querySelector('#noteForm .primary').before(field);}
 field.hidden=!n?.techniqueCandidates?.length;if(field.hidden)return;
 const select=field.querySelector('select');select.innerHTML='<option value="">'+(window.t?window.t('None'):'None')+'</option>'+n.techniqueCandidates.map(c=>'<option value="'+c.label+'">'+(window.t?window.t(c.label):c.label)+' · '+(100*c.probability).toFixed(1)+'%</option>').join('');select.value=selectedTechniqueLabel(n);
 select.onchange=()=>{document.querySelector('#noteTechnique').value=techniqueSymbols[select.value]||'';};
};

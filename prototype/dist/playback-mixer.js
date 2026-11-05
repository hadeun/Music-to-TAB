(function(root){
function gains(value){const synth=Math.max(0,Math.min(100,Number(value)||0))/100;return {original:1-synth,synth};}
if(typeof document==='undefined'){module.exports={gains};return;}
let balance=50;try{const saved=localStorage.getItem('music-to-tab-audio-balance');if(saved!==null&&Number.isFinite(+saved))balance=Math.max(0,Math.min(100,+saved));}catch{}
let synthMaster=null,mediaClock=false,starting=false,run=0;
const transport=document.querySelector('.transport'),switcher=document.querySelector('.source-switch');
switcher.classList.add('mixer');
switcher.innerHTML='<div class="mixer-labels"><button data-source="original">Original audio</button><button data-source="synth">♫ Synth TAB</button></div><input id="audioBalance" type="range" min="0" max="100" step="1" aria-label="Original / synth balance"><output id="balanceValue"></output>';
const slider=document.querySelector('#audioBalance');slider.value=balance;
function syncMix(){
 const levels=gains(balance);media.volume=levels.original;
 if(synthMaster&&ctx)synthMaster.gain.setTargetAtTime(levels.synth,ctx.currentTime,.015);
 document.querySelector('#balanceValue').textContent=Math.round(levels.original*100)+'% / '+Math.round(levels.synth*100)+'%';
 slider.setAttribute('aria-valuetext',(root.t?root.t('Original audio'):'Original audio')+' '+Math.round(levels.original*100)+'%, '+(root.t?root.t('♫ Synth TAB'):'Synth TAB')+' '+Math.round(levels.synth*100)+'%');
 document.querySelectorAll('[data-source]').forEach(b=>b.classList.toggle('selected',b.dataset.source==='original'?balance===0:balance===100));
}
function setBalance(value){balance=+value;slider.value=balance;syncMix();try{localStorage.setItem('music-to-tab-audio-balance',String(balance))}catch{}}
slider.oninput=()=>{
 // A muted original stays running as the shared clock, so moving the fader
 // during sustained notes changes both gains without restarting the song.
 if(playing&&!mediaClock&&!audioFiles.has(project.id)&&+slider.value<100){slider.value=100;return toast('Original audio is missing. Re-upload the recording.');}
 setBalance(slider.value);
};
document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>{slider.value=b.dataset.source==='original'?0:100;slider.oninput();});
function timelineDuration(){return Math.max(duration(),audioFiles.has(project.id)&&Number.isFinite(media.duration)?media.duration:0);}
tone=function(n,elapsedTicks=0){
 if(!ctx||!synthMaster)return;
 const speed=+document.querySelector('#speed').value,len=Math.max(0,n.duration_ticks-elapsedTicks)/480*60/project.bpm/speed;
 if(len<=0)return;
 const osc=ctx.createOscillator(),envelope=ctx.createGain();osc.type='triangle';osc.frequency.value=440*Math.pow(2,(n.pitch-69)/12);
 if(n.technique==='b'&&Number.isFinite(n.bendSemitones))osc.frequency.exponentialRampToValueAtTime(osc.frequency.value*Math.pow(2,n.bendSemitones/12),ctx.currentTime+len*.7);
 envelope.gain.setValueAtTime(0,ctx.currentTime);envelope.gain.linearRampToValueAtTime(.12,ctx.currentTime+Math.min(.008,len*.1));envelope.gain.exponentialRampToValueAtTime(.001,ctx.currentTime+Math.max(.01,len*.9));
 osc.connect(envelope).connect(synthMaster);osc.start();osc.stop(ctx.currentTime+len);osc.onended=()=>{osc.disconnect();envelope.disconnect();};
};
updateTimeline=function(){const d=timelineDuration();document.querySelector('#seek').max=d;document.querySelector('#seek').value=position;document.querySelector('#currentTime').textContent=time(position);document.querySelector('#totalTime').textContent=time(d);highlight();};
pause=function(){
 run++;starting=false;playing=false;clearInterval(timer);media.pause();
 if(ctx){ctx.close().catch(()=>{});ctx=null;}synthMaster=null;mediaClock=false;
 document.querySelector('#playBtn').textContent='▶';document.querySelector('#playBtn').setAttribute('aria-label','Play');
};
play=async function(){
 if(playing||starting)return pause();if(!project.id)return;
 const token=++run;starting=true;
 try{
  if(balance<100&&!audioFiles.has(project.id))await restoreAudio(project.id);
  if(token!==run)return;
  if(balance<100&&!audioFiles.has(project.id))throw Error('Original audio is missing. Re-upload the recording.');
  if(position>=timelineDuration())position=0;
  ctx=new AudioContext();await ctx.resume();if(token!==run)return;
  synthMaster=ctx.createGain();synthMaster.gain.value=gains(balance).synth;synthMaster.connect(ctx.destination);syncMix();
  mediaClock=audioFiles.has(project.id)&&(!Number.isFinite(media.duration)||position<media.duration);
  if(mediaClock){media.currentTime=position;media.playbackRate=+document.querySelector('#speed').value;media.preservesPitch=true;await media.play();}
  if(token!==run)return;
  starting=false;playing=true;document.querySelector('#playBtn').textContent='Ⅱ';document.querySelector('#playBtn').setAttribute('aria-label','Pause');
  last=performance.now();lastTick=position*project.bpm*8;
  for(const n of project.parts[part])if(n.start_tick<=lastTick&&n.start_tick+n.duration_ticks>lastTick)tone(n,lastTick-n.start_tick);
  timer=setInterval(()=>{
   if(!playing)return;const now=performance.now();
   position=mediaClock&&!media.ended?media.currentTime:position+(now-last)/1000*(+document.querySelector('#speed').value);last=now;
   const tick=position*project.bpm*8;
   project.parts[part].filter(n=>n.start_tick>lastTick&&n.start_tick<=tick).forEach(n=>tone(n));lastTick=tick;updateTimeline();
   if(position>=timelineDuration()){const end=timelineDuration();pause();position=end;updateTimeline();}
  },20);
 }catch(error){if(token===run){pause();toast(error.message||'Audio could not be played. Please upload it again.');}}
};
document.querySelector('#playBtn').onclick=()=>play();
document.querySelector('#restart').onclick=()=>{pause();position=0;updateTimeline();};
document.querySelector('#seek').oninput=e=>{pause();position=+e.target.value;if(audioFiles.has(project.id)&&Number.isFinite(media.duration))media.currentTime=Math.min(position,media.duration);updateTimeline();};
document.querySelector('#speed').onchange=()=>{const resume=playing;pause();if(resume)play();};
if(typeof render==='function'){const renderBeforeMixer=render;render=function(){renderBeforeMixer();syncMix();};}
syncMix();
})(globalThis);

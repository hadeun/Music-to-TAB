const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(withAudio=true){
 const element=()=>({value:0,textContent:'',classList:{add(){},toggle(){}},setAttribute(){}});
 const ids=Object.fromEntries(['.transport','.source-switch','#audioBalance','#balanceValue','#seek','#currentTime','#totalTime','#playBtn','#speed','#restart'].map(s=>[s,element()]));ids['#speed'].value=1;
 const buttons=[{...element(),dataset:{source:'original'}},{...element(),dataset:{source:'synth'}}];
 const contexts=[],oscillators=[];let callback,now=0;
 const param=()=>({value:0,setTargetAtTime(v){this.value=v},setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}});
 class AudioContext{
  constructor(){this.currentTime=0;this.destination={};this.gains=[];contexts.push(this)}
  resume(){return Promise.resolve()}close(){this.closed=true;return Promise.resolve()}
  createGain(){const g={gain:param(),connect(to){this.destination=to;return to},disconnect(){}};this.gains.push(g);return g}
  createOscillator(){const o={frequency:param(),connect(to){this.destination=to;return to},start(){},stop(at){this.stopAt=at},disconnect(){}};oscillators.push(o);return o}
 }
 const media={duration:10,currentTime:0,volume:1,ended:false,paused:true,async play(){this.paused=false},pause(){this.paused=true}};
 const c={document:{querySelector:s=>ids[s],querySelectorAll:()=>buttons},localStorage:{getItem:()=>null,setItem(){}},AudioContext,media,
  audioFiles:new Map(withAudio?[['p','blob:audio']]:[]),project:{id:'p',bpm:120,parts:{guitar:[{pitch:64,start_tick:0,duration_ticks:1920}]}},part:'guitar',ctx:null,playing:false,position:0,timer:null,last:0,lastTick:0,
  performance:{now:()=>now},setInterval(fn){callback=fn;return 1},clearInterval(){callback=null},duration:()=>10,time:s=>String(s),highlight(){},restoreAudio:async()=>{},toast(message){c.error=message}};
 vm.createContext(c);vm.runInContext(fs.readFileSync('dist/playback-mixer.js','utf8'),c);
 return {c,ids,contexts,oscillators,tick(ms){now=ms;callback?.()}};
}
test('crossfade changes a sustained synth master without restarting either timeline',async()=>{
 const {c,ids,contexts,oscillators,tick}=setup();await c.play();assert(c.playing);assert.equal(c.media.volume,.5);assert.equal(oscillators.length,1);
 const master=contexts[0].gains[0];assert.equal(master.gain.value,.5);assert.equal(oscillators[0].destination.destination,master);
 c.media.currentTime=1.25;tick(500);assert.equal(c.position,1.25);
 ids['#audioBalance'].value=100;ids['#audioBalance'].oninput();assert.equal(c.media.volume,0);assert.equal(master.gain.value,1);assert.equal(c.position,1.25);assert(!c.media.paused);assert.equal(contexts.length,1);
 ids['#audioBalance'].value=0;ids['#audioBalance'].oninput();assert.equal(c.media.volume,1);assert.equal(master.gain.value,0);c.pause();assert(c.media.paused);assert(contexts[0].closed);
});
test('seek into a held note resumes only its remaining duration at selected speed',async()=>{
 const {c,ids,oscillators}=setup();ids['#seek'].oninput({target:{value:1.25}});ids['#speed'].value=.5;await c.play();assert.equal(c.media.currentTime,1.25);assert.equal(c.media.playbackRate,.5);assert.equal(oscillators.length,1);assert.equal(oscillators[0].stopAt,1.5);assert.equal(oscillators[0].frequency.value,440*Math.pow(2,(64-69)/12));c.pause();
});
test('missing original is explicit; synth-only playback still advances',async()=>{
 const {c,ids,tick}=setup(false);await c.play();assert.match(c.error,/Original audio is missing/);assert(!c.playing);
 ids['#audioBalance'].value=100;ids['#audioBalance'].oninput();await c.play();tick(1000);assert.equal(c.position,1);assert(c.playing);c.pause();
});

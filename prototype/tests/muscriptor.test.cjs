const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const text=fs.readFileSync('dist/app.js','utf8');
const fn=text.slice(text.indexOf('function muscriptorScore('),text.indexOf('function showStudio()'));
const context={OPEN:[64,59,55,50,45,40],clone:structuredClone,crypto:require('node:crypto'),GuitarFingering:require('../dist/fingering.js')};vm.createContext(context);vm.runInContext(fn,context);
test('Muscriptor maps guitar only, corrects delay and preserves source MIDI',()=>{const p=context.muscriptorScore([{instrument:'electric_guitar',pitch:64,start_time:1,end_time:2},{instrument:'piano',pitch:70,start_time:1,end_time:2}],{duration:4,bpm:120},{data:'TUlESQ==',beat_grid:{onset_delay:.1}});assert.equal(p.parts.guitar.length,1);assert.equal(p.parts.guitar[0].pitch,64);assert.equal(p.parts.guitar[0].start_tick,864);assert.equal(p.originalMidiBase64,'TUlESQ==');assert.equal(p.engine,'Muscriptor 0.4.0');});
test('No fabricated guitar result when no playable guitar notes exist',()=>{assert.throws(()=>context.muscriptorScore([{instrument:'piano',pitch:60,start_time:0,end_time:1}],{duration:2,bpm:120},{}),/no playable guitar/)});
test('Browser has no Basic Pitch worker or fallback invocation',()=>{assert.doesNotMatch(text,/new Worker|BasicPitch|basic-pitch/i);assert.match(text,/api\/muscriptor\/transcribe/);});
test('Upload starts decoding without the removed BPM input and recovers on decoding failure',async()=>{
 const button={},error={},elements={
  '#recording':{value:'solo'},'#audioFile':{files:[{name:'song.mp3',size:1,arrayBuffer:async()=>new ArrayBuffer(1)}]},
  '#dropzone':{},'#uploadForm':{},'#uploadTitle':{value:'Song'},'#uploadMeter':{value:'4'},'#uploadError':error,'#newProject':{},'#uploadTop':{}
 };
 let decoded=false;
 const uploadContext={pause(){},modal(){},crypto:require('node:crypto'),$:selector=>elements[selector],
  AudioContext:class{async decodeAudioData(){decoded=true;throw Error('Invalid audio fixture');}async close(){}},toast(){}};
 vm.createContext(uploadContext);
 vm.runInContext(text.slice(text.indexOf('function showUpload()'),text.indexOf('async function startConversion(')),uploadContext);
 uploadContext.showUpload();
 await elements['#uploadForm'].onsubmit({preventDefault(){},target:{querySelector:()=>button}});
 assert.equal(decoded,true);assert.equal(error.textContent,'Invalid audio fixture');assert.equal(button.disabled,false);
});

const test=require('node:test'),assert=require('node:assert/strict');
const {wav}=require('../dist/technique-audio.js');
test('Separation upload keeps stereo channels and sample rate',()=>{
 const buffer=wav({numberOfChannels:2,sampleRate:44100,length:2,getChannelData:c=>c?[-1,-.25]:[1,.5]});
 const view=new DataView(buffer);
 assert.equal(view.getUint16(22,true),2);assert.equal(view.getUint32(24,true),44100);assert.equal(view.getUint32(28,true),176400);
 assert.equal(view.getInt16(44,true),32767);assert.equal(view.getInt16(46,true),-32767);
 assert.equal(view.getInt16(48,true),16384);assert.equal(view.getInt16(50,true),-8192);
 assert.equal(view.getUint32(40,true),8);
});
test('Mono audio stays mono and unsupported layouts are explicit',()=>{
 assert.equal(new DataView(wav({numberOfChannels:1,sampleRate:48000,length:1,getChannelData:()=>[0]})).getUint16(22,true),1);
 assert.throws(()=>wav({numberOfChannels:6}),/mono or stereo/);
});

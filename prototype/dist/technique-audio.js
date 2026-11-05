(function(root){
function wav(audio){
 const channels=audio.numberOfChannels,rate=audio.sampleRate,length=audio.length;
 if(![1,2].includes(channels))throw Error('Use mono or stereo audio for guitar separation.');
 const buffer=new ArrayBuffer(44+length*channels*2),view=new DataView(buffer);
 const str=(offset,text)=>[...text].forEach((c,i)=>view.setUint8(offset+i,c.charCodeAt(0)));
 str(0,'RIFF');view.setUint32(4,buffer.byteLength-8,true);str(8,'WAVE');str(12,'fmt ');
 view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,channels,true);view.setUint32(24,rate,true);
 view.setUint32(28,rate*channels*2,true);view.setUint16(32,channels*2,true);view.setUint16(34,16,true);
 str(36,'data');view.setUint32(40,length*channels*2,true);
 const data=Array.from({length:channels},(_,i)=>audio.getChannelData(i));
 for(let i=0;i<length;i++)for(let c=0;c<channels;c++)view.setInt16(44+(i*channels+c)*2,Math.round(Math.max(-1,Math.min(1,data[c][i]))*32767),true);
 return buffer;
}
const api={wav};if(typeof module!=='undefined')module.exports=api;else root.TechniqueAudio=api;
})(globalThis);

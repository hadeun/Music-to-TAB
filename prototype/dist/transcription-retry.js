// Re-run the real model into a new project; retain the user's existing score.
const retryGuitarButton=document.createElement('button');retryGuitarButton.className='button';retryGuitarButton.textContent='Re-transcribe with guitar focus';document.querySelector('.song-actions').append(retryGuitarButton);
const renderBeforeRetry=render;render=function(){renderBeforeRetry();retryGuitarButton.disabled=!project.id||!!conversion;};retryGuitarButton.disabled=!project.id;
retryGuitarButton.onclick=async()=>{
 if(!project.id||conversion)return;pause();retryGuitarButton.disabled=true;const original=project;
 modal('Re-transcribe with guitar focus','<p>The original project and edits will be kept. A new project will use guitar-conditioned Muscriptor decoding from the beginning.</p>');
 try{
  const blob=await audioRecord(original.id,'get');if(!blob)throw Error('Original audio is missing. Re-upload the recording.');
  const ac=new AudioContext();let decoded;try{decoded=await ac.decodeAudioData(await blob.arrayBuffer());}finally{await ac.close();}
  if(decoded.duration>300)throw Error('This recording exceeds 5 minutes. Audio will not be trimmed.');
  const offline=new OfflineAudioContext(1,Math.ceil(decoded.duration*22050),22050),node=offline.createBufferSource();node.buffer=decoded;node.connect(offline.destination);node.start();
  const mono=(await offline.startRendering()).getChannelData(0);
  if(project!==original)throw Error('Reopen this project first.');
  await startConversion(blob,mono,{id:crypto.randomUUID(),title:original.title+' [Guitar focus]',bpm:original.bpm,meter:original.meter||4,duration:decoded.duration,recording:'solo'});
 }catch(error){document.querySelector('#modalBody').innerHTML='<p class="error">'+escapeHtml(window.t?window.t(error.message):error.message)+'</p>';}
 finally{retryGuitarButton.disabled=!project.id;}
};

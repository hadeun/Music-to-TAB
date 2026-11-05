(function(root){
const guitarInstruments=['acoustic_guitar','clean_electric_guitar','distorted_electric_guitar'];
function configure(form,recording){
 if(recording==='solo')for(const instrument of guitarInstruments)form.append('instruments',instrument);
 return recording==='solo'?'guitar-conditioned':'all-instruments';
}
const api={configure,guitarInstruments};if(typeof module!=='undefined')module.exports=api;else root.TranscriptionInput=api;
})(globalThis);

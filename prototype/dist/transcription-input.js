(function(root){
const guitarInstruments=['acoustic_guitar','clean_electric_guitar','distorted_electric_guitar'];
const instruments=['acoustic_piano', 'electric_piano', 'chromatic_percussion', 'organ', 'acoustic_guitar', 'clean_electric_guitar', 'distorted_electric_guitar', 'acoustic_bass', 'electric_bass', 'violin', 'viola', 'cello', 'contrabass', 'orchestral_harp', 'timpani', 'string_ensemble', 'synth_strings', 'voice', 'orchestra_hit', 'trumpet', 'trombone', 'tuba', 'french_horn', 'brass_section', 'soprano_and_alto_sax', 'tenor_sax', 'baritone_sax', 'oboe', 'english_horn', 'bassoon', 'clarinet', 'flutes', 'synth_lead', 'synth_pad', 'drums'];
function instrumentName(id){return id[0].toUpperCase()+id.slice(1).replaceAll("_"," ");}
function configure(form,recording,selected=[]){
 if(recording==="custom"){
  const choices=[...new Set(selected)];
  if(!choices.some(id=>guitarInstruments.includes(id))||choices.some(id=>!instruments.includes(id)))throw Error("Select at least one guitar type.");
  for(const id of choices)form.append("instruments",id);
  return "custom-instruments";
 }
 if(recording==='solo')for(const instrument of guitarInstruments)form.append('instruments',instrument);
 return recording==='solo'?'guitar-conditioned':'all-instruments';
}
const api={configure,guitarInstruments,instruments,instrumentName};if(typeof module!=='undefined')module.exports=api;else root.TranscriptionInput=api;
})(globalThis);

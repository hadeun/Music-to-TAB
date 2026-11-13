(function(root){
const symbols={bend:'b',hammer_on:'h',pull_off:'p',slide:'/',vibrato:'~',tapping:'T',alternate_picking:'AP',sweep_picking:'SP',legato:'L',palm_mute:'PM',harmonics:'NH',pinch_harmonics:'PH',normal:''};
const minimumProbability=.70;
function shouldDisplay(note){
 if(note.techniqueSource?.startsWith('user')||!note.techniqueSource?.startsWith('auto-'))return true;
 const candidate=note.techniqueCandidates?.find(c=>symbols[c.label]===note.technique);
 return !!candidate&&candidate.probability>=minimumProbability;
}
function assign(score,result){
 let count=0;
 const pitchSpans=result.backend==='tab_pitch';
 for(const note of score.parts.guitar){
  const gridStart=note.start_tick/(score.bpm*8),end=gridStart+note.duration_ticks/(score.bpm*8);
  const start=pitchSpans?(note.start_seconds??gridStart):gridStart;
  const totals={};let weight=0;
  const matching=pitchSpans?result.candidates.findLast(span=>span.start<=start&&start<span.end):null;
  const windows=pitchSpans?(matching?[matching]:[]):result.candidates;
  for(const window of windows){const overlap=pitchSpans?1:Math.max(0,Math.min(end,window.end)-Math.max(start,window.start));if(!overlap)continue;
   const alternatives=window.alternatives||[];if(!alternatives.length)continue;weight+=overlap;
   for(const candidate of alternatives)if(Object.hasOwn(symbols,candidate.label)&&Number.isFinite(candidate.probability))totals[candidate.label]=(totals[candidate.label]||0)+overlap*candidate.probability;
  }
  if(!weight){
   if(pitchSpans){
    delete note.techniqueCandidates;
    if(note.techniqueSource?.startsWith('auto-')){
     note.technique='';delete note.techniqueLabel;delete note.techniqueSource;delete note.techniqueModel;
    }
   }
   continue;
  }
  note.techniqueCandidates=Object.entries(totals).map(([label,value])=>({label,probability:value/weight})).sort((a,b)=>b.probability-a.probability);
  if(!note.techniqueCandidates.length)continue;
  // Re-analysis refreshes candidates but preserves deliberate user choices.
  if(note.techniqueSource?.startsWith('user')||note.technique&&!note.techniqueSource)continue;
  const best=note.techniqueCandidates[0],accepted=best.probability>=minimumProbability;
  note.technique=accepted?symbols[best.label]:'';note.techniqueLabel=accepted?best.label:'';note.techniqueSource=result.architecture==='crnn'?'auto-crnn':'auto-spectrofusion';if(result.model)note.techniqueModel=result.model;if(note.technique)count++;
 }
 return count;
}
const api={symbols,assign,shouldDisplay,minimumProbability};if(typeof module!=='undefined')module.exports=api;else root.TechniqueAssignment=api;
})(globalThis);

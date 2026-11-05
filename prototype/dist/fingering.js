(function(root){
 const OPEN=[64,59,55,50,45,40];
 // Shapes are written low E to high E; null means an unused string.
 const openShapes=[[0,2,2,1,0,0],[0,2,2,0,0,0],[null,0,2,2,2,0],[null,0,2,2,1,0],[null,3,2,0,1,0],[null,null,0,2,3,2],[null,null,0,2,3,1],[3,2,0,0,0,3]];
 const moveableShapes=[[0,2,2,1,0,0],[0,2,2,0,0,0],[0,2,0,1,0,0],[null,0,2,2,2,0],[null,0,2,2,1,0],[null,0,2,0,2,0],[0,2,2,null,null,null],[null,0,2,2,null,null]];
 function chordMatch(notes){
  if(notes.length<3)return false;
  const matches=(shape,offset)=>notes.every(n=>shape[6-n.string]!==null&&shape[6-n.string]+offset===n.fret);
  return openShapes.some(shape=>matches(shape,0))||moveableShapes.some(shape=>Array.from({length:20},(_,i)=>i+1).some(offset=>matches(shape,offset)));
 }
 function rank(notes,previous){
  const fretted=notes.filter(n=>n.fret>0),frets=fretted.map(n=>n.fret);
  const span=frets.length?Math.max(...frets)-Math.min(...frets):0;
  // Equal frets can share a barre. Prefer compact shapes and nearby strings.
  const fingers=new Set(frets).size;
  const position=frets.length?Math.min(...frets):0;
  const strings=notes.map(n=>n.string),gaps=strings.length?Math.max(...strings)-Math.min(...strings)+1-strings.length:0;
  const previousPosition=typeof previous==='number'?previous:(previous?.position||0);
  // Open strings require no hand shift. Keep the last fretted position across them.
  const travel=frets.length?Math.abs(position-previousPosition):0;
  const previousStrings=previous?.strings||[];
  const stringTravel=previousStrings.length&&strings.length?strings.reduce((sum,s)=>sum+Math.min(...previousStrings.map(p=>Math.abs(s-p))),0)/strings.length:0;
  const sorted=[...notes].sort((a,b)=>a.pitch-b.pitch);
  const [root,fifth,octave]=sorted;
  const powerShape=sorted.length===3&&fifth.pitch-root.pitch===7&&octave.pitch-root.pitch===12
   &&[6,5].includes(root.string)&&fifth.string===root.string-1&&octave.string===root.string-2
   &&fifth.fret===root.fret+2&&octave.fret===root.fret+2;
  return [Math.max(0,travel-4),span,gaps,stringTravel,Math.max(0,fingers-4)*2000+position*.5+travel*3-(chordMatch(notes)?60:0)-(powerShape?5000:0)];
 }
 function compare(a,b){for(let i=0;i<a.length;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;}
 function cost(notes,previous){const r=rank(notes,previous);return r[0]*1e9+r[1]*1e6+r[2]*10000+r[3]*1000+r[4];}
 function distance(a,b){return Math.hypot(a.fret-b.fret,a.string-b.string);}
 // Chords may have different note counts: average nearest-note travel in both directions.
 function movement(a,b){
  if(!a.length||!b.length)return 0;
  const nearest=(from,to)=>from.reduce((sum,n)=>sum+Math.min(...to.map(m=>distance(n,m))),0)/from.length;
  return (nearest(a,b)+nearest(b,a))/2;
 }
 function movementBurden(a,b,seconds){
  // Half a second is neutral; bound the weight for near-simultaneous attacks and long rests.
  const weight=Math.max(.25,Math.min(4,.5/Math.max(.05,seconds)));
  return movement(a,b)*weight;
 }
 function shape(notes){
  const r=rank(notes,0),position=Math.min(...notes.filter(n=>n.fret>0).map(n=>n.fret),24);
  const sorted=[...notes].sort((a,b)=>a.pitch-b.pitch);
  const power=sorted.length===3&&sorted[1].pitch-sorted[0].pitch===7&&sorted[2].pitch-sorted[0].pitch===12;
  const standard=power&&[5,6].includes(sorted[0].string)&&sorted[1].string===sorted[0].string-1&&sorted[2].string===sorted[0].string-2&&sorted[1].fret===sorted[0].fret+2&&sorted[2].fret===sorted[0].fret+2;
  return {violation:Math.max(0,r[1]-4),score:r[1]*2+r[2]*2+(power&&!standard?8:0)+(chordMatch(notes)?-1:0)+(position===24&&notes.every(n=>!n.fret)?0:position*.1)};
 }
 function optimize(input,options={}){
  const bpm=Number.isFinite(options.bpm)&&options.bpm>0?options.bpm:120;
  const ppq=Number.isFinite(options.ppq)&&options.ppq>0?options.ppq:480;
  const notes=input.map(n=>({...n})).sort((a,b)=>a.start_tick-b.start_tick);
  let beam=[{active:[],previous:[],time:null,score:0,violation:0,parent:null,group:[]}];
  for(let i=0;i<notes.length;){
   const start=notes[i].start_tick;let end=i+1;while(end<notes.length&&notes[end].start_tick===start)end++;
   const group=notes.slice(i,end),next=new Map();
   for(const state of beam){
    const active=state.active.filter(n=>n.start_tick+n.duration_ticks>start),used=new Set(active.map(n=>n.string));
    let found=false;
    function emit(chosen){
     found=true;const sounding=[...active,...chosen],local=shape(sounding);
     const seconds=state.time===null?Infinity:(start-state.time)*60/bpm/ppq;
     const candidate={active:sounding,previous:sounding,time:start,score:state.score+local.score+movementBurden(state.previous,sounding,seconds),violation:state.violation+local.violation,parent:state,group:chosen};
     const key=sounding.map(n=>n.id+':'+n.string).join('|'),old=next.get(key);
     if(!old||candidate.violation<old.violation||(candidate.violation===old.violation&&candidate.score<old.score))next.set(key,candidate);
    }
    function search(index,chosen){
     if(index===group.length)return emit(chosen);
     const n=group[index],locked=n.techniqueSource?.startsWith('user');
     const candidates=locked?[{string:n.string,fret:n.fret}]:OPEN.map((open,j)=>({string:j+1,fret:n.pitch-open})).filter(c=>c.fret>=0&&c.fret<=24);
     for(const c of candidates){if(used.has(c.string))continue;used.add(c.string);search(index+1,[...chosen,{...n,...c}]);used.delete(c.string);}
    }
    search(0,[]);
    // An original assignment is feasible only if it does not collide with held notes.
    if(!found&&group.every(n=>!used.has(n.string))&&new Set(group.map(n=>n.string)).size===group.length)emit(group);
   }
   if(!next.size)return input.map(n=>({...n}));
   beam=[...next.values()].sort((a,b)=>a.violation-b.violation||a.score-b.score).slice(0,32);
   i=end;
  }
  if(!notes.length)return [];
  const assignments=new Map();for(let state=beam[0];state;state=state.parent)for(const n of state.group)assignments.set(n.id,n);
  return input.map(n=>({...assignments.get(n.id)}));
 }
 const api={optimize,cost,rank,compare,OPEN,distance,movement,movementBurden};if(typeof module!=='undefined')module.exports=api;else root.GuitarFingering=api;
})(globalThis);

const test=require('node:test'),assert=require('node:assert/strict');
const {optimize,OPEN,cost,distance,movement}=require('../dist/fingering.js');
const {rank,compare}=require('../dist/fingering.js');
const {movementBurden}=require('../dist/fingering.js');
const note=(id,pitch,string,fret,start_tick=0,duration_ticks=480)=>({id,pitch,string,fret,start_tick,duration_ticks,technique:'h'});
test('Fast transitions cost more than equal-distance transitions after a rest',()=>{
 const a=[{fret:1,string:6}],b=[{fret:4,string:2}];
 assert.equal(movementBurden(a,b,.125),20);
 assert.equal(movementBurden(a,b,.5),5);
 assert.equal(movementBurden(a,b,2),1.25);
 assert.ok(Number.isFinite(movementBurden(a,b,0)));
 assert.equal(movementBurden(a,a,.1),0);
});
test('Equivalent seconds at different BPM and PPQ give identical fingering decisions',()=>{
 const input=[note('a',59,2,0,0,120),note('b',64,1,0,240,120),note('c',67,1,3,480,120)];
 const slow=optimize(input,{bpm:120,ppq:480});
 const scaled=input.map(n=>({...n,start_tick:n.start_tick*2,duration_ticks:n.duration_ticks*2}));
 const fast=optimize(scaled,{bpm:240,ppq:480});
 const resolution=optimize(scaled,{bpm:120,ppq:960});
 const positions=notes=>notes.map(n=>[n.string,n.fret]);
 assert.deepEqual(positions(slow),positions(fast));assert.deepEqual(positions(slow),positions(resolution));
});
test('Wide dyad becomes compact without changing pitches, timing or techniques',()=>{
 const source=[note('a',52,6,12),note('b',59,3,4)],snapshot=structuredClone(source),result=optimize(source);
 assert.ok(Math.abs(result[0].fret-result[1].fret)<5);
 assert.notEqual(result[0].string,result[1].string);
 result.forEach((n,i)=>{assert.equal(OPEN[n.string-1]+n.fret,n.pitch);assert.equal(n.start_tick,source[i].start_tick);assert.equal(n.duration_ticks,source[i].duration_ticks);assert.equal(n.technique,'h');});
 assert.deepEqual(source,snapshot);
});
test('Standard tuning handles the four-semitone G to B interval',()=>{
 assert.equal(OPEN[1]-OPEN[2],4);
 for(const n of optimize([note('a',59,3,4),note('b',64,2,5)]))assert.equal(OPEN[n.string-1]+n.fret,n.pitch);
});
test('Open strings do not count towards hand stretch',()=>{
 assert.equal(rank([{string:6,fret:0},{string:1,fret:7}],7)[1],0);
 assert.equal(rank([{string:6,fret:2},{string:1,fret:7}],2)[1],5);
});
test('Sustained notes keep their strings occupied and user edits remain fixed',()=>{
 const held={...note('held',64,1,0,0,960),techniqueSource:'user-edited'};
 const result=optimize([held,note('next',67,2,8,480)]);
 assert.equal(result[0].string,1);assert.equal(result[0].fret,0);assert.notEqual(result[1].string,1);
});
test('Unavoidable wide shape retains every note',()=>{
 const source=[note('low',41,6,1),note('high',88,1,24)];
 const result=optimize(source);assert.equal(result.length,2);result.forEach(n=>assert.equal(OPEN[n.string-1]+n.fret,n.pitch));
});
test('Equal-start six-note chord has no string collisions',()=>{
 const result=optimize([40,47,52,56,59,64].map((pitch,i)=>note(String(i),pitch,6-i,[0,2,2,1,0,0][i])));
 assert.equal(new Set(result.map(n=>n.string)).size,6);assert.deepEqual(result.map(n=>n.fret),[0,2,2,1,0,0]);
});
test('Equivalent spread power chords prefer 133 and 355 on adjacent strings',()=>{
 for(const [root,sourceFrets,expected] of [[46,[6,3,3],[1,3,3]],[48,[8,5,5],[3,5,5]]]){
  const input=[note('root',root,6,sourceFrets[0]),note('fifth',root+7,4,sourceFrets[1]),note('octave',root+12,3,sourceFrets[2])];
  const result=optimize(input);
  assert.deepEqual(result.map(n=>n.string),[5,4,3]);assert.deepEqual(result.map(n=>n.fret),expected);
  assert.deepEqual(result.map(n=>n.pitch),input.map(n=>n.pitch));
 }
});
test('Power chord shape preference does not move manually edited notes',()=>{
 const input=[note('root',46,6,6),note('fifth',53,4,3),note('octave',58,3,3)].map(n=>({...n,techniqueSource:'user-edited'}));
 assert.deepEqual(optimize(input),input);
});
test('Fret span takes precedence over string spacing and power chord bonus',()=>{
 // Compare explicit valid scoring tuples: later preferences never override earlier ones.
 assert.ok(compare([1,3,10000],[2,0,-5000])<0);
 assert.ok(compare([2,0,10000],[2,1,-5000])<0);
 assert.equal(rank([note('a',46,6,6),note('b',53,4,3),note('c',58,3,3)],0)[1],3);
 assert.equal(rank([note('a',46,5,1),note('b',53,4,3),note('c',58,3,3)],0)[1],2);
});
test('Low-position chord progression avoids the open D plus 17/17 jump',()=>{
 const previous=[note('c',48,5,3),note('e',52,4,2),note('g',55,3,0),note('c2',60,2,1)].map(n=>({...n,techniqueSource:'user-edited'}));
 const next=[note('d',50,4,0,480),note('a',57,6,17,480),note('d2',62,5,17,480)];
 const result=optimize([...previous,...next]).slice(4);
 assert.ok(result.every(n=>n.fret<=7));
 assert.ok(movement(previous,result)<movement(previous,next));
 assert.deepEqual(result.map(n=>n.pitch),[50,57,62]);
});
test('Movement uses Euclidean fret and string coordinates, with equal units',()=>{
 assert.equal(distance({fret:1,string:6},{fret:4,string:2}),5);
 assert.equal(distance({fret:2,string:3},{fret:2,string:4}),1);
 assert.equal(movement([{fret:1,string:6}],[{fret:4,string:2}]),5);
 assert.equal(movement([{fret:1,string:6},{fret:3,string:5}],[{fret:1,string:6},{fret:3,string:5}]),0);
});
test('A future fixed note changes the earlier choice instead of greedily committing',()=>{
 const first={...note('first',59,2,0),techniqueSource:'user-edited'};
 const middle=note('middle',64,1,0,480);
 const last={...note('last',64,3,9,960),techniqueSource:'user-edited'};
 const short=optimize([first,middle]),whole=optimize([first,middle,last]);
 assert.equal(short[1].string,1);
 assert.notEqual(whole[1].string,short[1].string);
 const total=path=>movement([path[0]],[path[1]])+movement([path[1]],[path[2]]);
 assert.ok(total(whole)<total([first,short[1],last]));
});
test('Previous strings break ties between equally compact nearby shapes',()=>{
 const near=[note('a',64,1,0),note('b',59,2,0)],far=[note('a',64,3,9),note('b',59,4,9)];
 const before={position:9,strings:[1,2]};
 assert.ok(compare(rank(near,before),rank(far,before))<0);
});

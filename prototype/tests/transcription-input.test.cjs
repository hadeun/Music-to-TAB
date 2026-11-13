const test=require('node:test'),assert=require('node:assert/strict'),{configure}=require('../dist/transcription-input.js');
test('isolated-guitar recordings condition model before decoding, not after deleting notes',()=>{const form=new FormData();assert.equal(configure(form,'solo'),'guitar-conditioned');assert.deepEqual(form.getAll('instruments'),['acoustic_guitar','clean_electric_guitar','distorted_electric_guitar']);});
test('full mix retains multi-instrument detection',()=>{const form=new FormData();assert.equal(configure(form,'mix'),'all-instruments');assert.deepEqual(form.getAll('instruments'),[]);});
test('custom selection sends only the selected Muscriptor groups',()=>{
 const form=new FormData();
 assert.equal(configure(form,'custom',['clean_electric_guitar','drums','electric_bass','drums']),'custom-instruments');
 assert.deepEqual(form.getAll('instruments'),['clean_electric_guitar','drums','electric_bass']);
 assert.throws(()=>configure(new FormData(),'custom',['drums']));
 assert.throws(()=>configure(new FormData(),'custom',['acoustic_guitar','unknown']));
});

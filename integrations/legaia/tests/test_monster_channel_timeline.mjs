import fs from 'node:fs';
import assert from 'node:assert/strict';
import {monsterChannelTrack} from '../editor/monster-channel-timeline.js';
import {qualifyMonsterFrameInspection} from '../editor/monster-motion-authoring.js';
const files=process.argv.slice(2);if(!files.length)throw Error('Provide qualified private monster frame/range fixtures.');
let channels=0,samples=0,refusals=0;
function check(inspection,review){
 const bytes=[inspection.retail_motion_base64??inspection.source_motion_base64,inspection.source_motion_base64,...(review?[review.candidate_motion_base64]:[])].map(s=>Buffer.from(s,'base64'));
 for(let part=0;part<inspection.clip.part_count;part++)for(const field of ['translation','rotation_psx'])for(const axis of 'xyz'){
  const track=monsterChannelTrack(inspection,part,field,axis,review),n='xyz'.indexOf(axis);channels++;
  assert.equal(track.animation_id,inspection.clip.semantic_id);assert.equal(track.samples.length,inspection.clip.frame_count);
  for(const row of track.samples)for(const [layer,b] of review?[['retail',bytes[0]],['current',bytes[1]],['proposed',bytes[2]]]:[['retail',bytes[0]],['current',bytes[1]]]){
   // Independent arithmetic decode from literal source bytes, including all
   // low nibble bits; no production codec or generated channel rows involved.
   const at=2+(row.frame*inspection.clip.part_count+part)*9;
   const words=field==='translation'?[b[at]+(b[at+2]%16)*256,b[at+1]+Math.floor(b[at+2]/16)*256,b[at+3]+(b[at+5]%16)*256]:[b[at+4]+Math.floor(b[at+5]/16)*256,b[at+6]+(b[at+8]%16)*256,b[at+7]+Math.floor(b[at+8]/16)*256];
   assert.equal(row[layer],field==='translation'&&words[n]>=2048?words[n]-4096:words[n]);samples++;
  }
  const all=track.samples.flatMap(s=>review?[s.retail,s.current,s.proposed]:[s.retail,s.current]);assert.equal(track.min,Math.min(...all));assert.equal(track.max,Math.max(...all));assert(Object.isFrozen(track.samples));
  const retailCurrent=monsterChannelTrack(inspection,part,field,axis);assert(retailCurrent.samples.every(row=>!('proposed' in row)));
 }
 for(const args of [[-1,'translation','x'],[inspection.clip.part_count,'translation','x'],[.5,'translation','x'],[0,'foreign','x'],[0,'rotation_psx','q'],[0,'translation',''],[0,'translation','xy'],[0,'translation',undefined]]){assert.throws(()=>monsterChannelTrack(inspection,...args,review));refusals++;}
 for(const modify of [v=>v.source_motion_base64='!',v=>v.source_motion_base64=v.source_motion_base64.slice(4),v=>v.clip.part_count=0,v=>v.clip.frame_count=0,v=>v.clip.part_count=65,v=>v.clip.frame_count=256,v=>v.clip.source_record.byte_length++,v=>v.clip.preview_supported=false,v=>{const b=Buffer.from(v.source_motion_base64,'base64');b[0]++;v.source_motion_base64=b.toString('base64');}]){const bad=structuredClone(inspection);modify(bad);assert.throws(()=>monsterChannelTrack(bad,0,'translation','x'));refusals++;}
 if(review)for(const modify of [v=>v.candidate_motion_base64=v.candidate_motion_base64.slice(4),v=>v.source_motion_base64='AA==',v=>v.clip.semantic_id='foreign',v=>v.projection.animation_id='foreign',v=>v.project_source_key='foreign',v=>v.project_path='foreign',v=>v.catalog_source_key='foreign',v=>v.asset_id='foreign']){const bad=structuredClone(review);modify(bad);assert.throws(()=>monsterChannelTrack(inspection,0,'translation','x',bad));refusals++;}
}
for(const file of files){const value=JSON.parse(fs.readFileSync(file,'utf8'));for(const v of value.cases??[value]){const i=v.inspection;await qualifyMonsterFrameInspection(i,{project_path:i.project_path,project_source_key:i.project_source_key,catalog:{source_key:i.catalog_source_key,animations:[i.clip]}},{id:i.asset_id},{animation_id:i.clip.semantic_id,frame_index:i.frame_index},i.part_index);check(i,v.review);}}
// A literal edge stream exercises signed limits and every rotation's low bits.
const literal=Buffer.from([1,2,0x00,0xff,0x78,0x01,0x03,0x18,0x05,0x07,0x32,0xff,0x00,0x87,0xff,0xff,0xff,0x00,0x01,0x10]);
const fixture={clip:{semantic_id:'literal',preview_supported:true,part_count:1,frame_count:2,source_record:{byte_length:literal.length}},source_motion_base64:literal.toString('base64')};
assert.deepEqual(monsterChannelTrack(fixture,0,'translation','x').samples.map(s=>s.current),[-2048,2047]);
assert.deepEqual(monsterChannelTrack(fixture,0,'translation','y').samples.map(s=>s.current),[2047,-2048]);
assert.deepEqual(monsterChannelTrack(fixture,0,'translation','z').samples.map(s=>s.current),[-2047,-1]);
assert.deepEqual(monsterChannelTrack(fixture,0,'rotation_psx','x').samples.map(s=>s.current),[259,4095]);
assert.deepEqual(monsterChannelTrack(fixture,0,'rotation_psx','y').samples.map(s=>s.current),[517,0]);
assert.deepEqual(monsterChannelTrack(fixture,0,'rotation_psx','z').samples.map(s=>s.current),[775,257]);
console.log(`${channels} monster channel tracks / ${samples} literal Retail/Current/Proposed axis samples / ${refusals} invalid part, axis, stream and owner refusals pass.`);

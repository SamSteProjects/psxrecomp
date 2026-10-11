import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldAnimationEdit,qualifyWorldAnimationCurrent} from '../editor/worldmap-animation-current.js';
import {worldAnimationChannelDraft} from '../editor/worldmap-animation-editor.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let positives=0,refusals=0;
for(const r of rows){const {review:v,held,current,edits}=r;
 await qualifyWorldAnimationEdit(v,held,current,v.entity_id,v.project_path,v.frame_index,edits);positives++;
 for(const mutate of [v=>v.shared_record=false,v=>v.source.edits=[],v=>v.source.audit.proposed_bank_sha256='0'.repeat(64),v=>v.before_binding=null,v=>v.binding={foreign:true},v=>v.current_preview.geometry.vertices[0][0]++,v=>v.proposed_preview.geometry.vertices[0][0]++,v=>v.changed_bytes.push({}),v=>v.proposed_bank_sha256='0'.repeat(64),v=>v.current_bank_sha256='0'.repeat(64),v=>v.project_change=!v.project_change,v=>v.source_key='stale',v=>v.gameplay_verified=true,v=>v.review_key='invalid']){
  const bad=structuredClone(v);mutate(bad);if(JSON.stringify(bad)===JSON.stringify(v))continue;
  await assert.rejects(qualifyWorldAnimationEdit(bad,held,current,v.entity_id,v.project_path,v.frame_index,edits));refusals++;
 }
 await assert.rejects(qualifyWorldAnimationCurrent(held,current,v.entity_id,v.project_path,v.frame_index,null));refusals++;
 const draft=worldAnimationChannelDraft(held,1,{translation:{x:-2048,y:0,z:2047},rotation_psx:{x:0,y:16,z:4080}});
 assert.deepEqual(draft[0],held.binding.entries['0003'].edits[0]);assert.equal(draft[1].object_index,1);
 for(const [obj,values] of [[2,{translation:{x:0,y:0,z:0},rotation_psx:{x:0,y:0,z:0}}],[1,{translation:{x:2048,y:0,z:0},rotation_psx:{x:0,y:0,z:0}}],[1,{translation:{x:0,y:0,z:0},rotation_psx:{x:0,y:1,z:0}}]]){assert.throws(()=>worldAnimationChannelDraft(held,obj,values));refusals++;}
}
assert.equal(positives,6);console.log(`${positives} actual shared edit/reset Reviews, saved sibling-channel retention and ${refusals} refusals passed.`);

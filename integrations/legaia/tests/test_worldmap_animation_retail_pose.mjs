import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldAnimationRetailPoseDraft} from '../editor/worldmap-animation-editor.js';
import {qualifyWorldAnimationEdit} from '../editor/worldmap-animation-current.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const r of cases){
 const original=structuredClone(r.held),edits=worldAnimationRetailPoseDraft(r.held,r.object,r.start,r.end);
 assert.deepEqual(edits,r.edits);assert.deepEqual(r.held,original);
 await qualifyWorldAnimationEdit(r.review,r.held,r.current,r.review.entity_id,r.review.project_path,r.review.frame_index,edits);
 if(r.start===r.end)assert.deepEqual(worldAnimationRetailPoseDraft(r.held,r.object),edits);
 for(const args of [[-1,r.start,r.end],[r.held.preview.channel_count,r.start,r.end],[0.5,r.start,r.end],[r.object,-1,r.end],[r.object,r.start,512],[r.object,NaN,r.end],[r.object,r.start,r.start-1],[r.object,r.held.frame_index+1,r.held.frame_index+1]]){
  assert.throws(()=>worldAnimationRetailPoseDraft(r.held,...args));refusals++;
 }
 if(edits.length){edits[0].frame_index=999;assert.deepEqual(r.held,original);}
}
assert.equal(cases.length,4);assert.equal(cases.at(-1).review.project_change,false);
assert.throws(()=>worldAnimationRetailPoseDraft(null,0));
console.log(`Four native Retail object restoration Reviews, immutable saved rows, exact sibling retention and ${refusals+1} refusals passed.`);

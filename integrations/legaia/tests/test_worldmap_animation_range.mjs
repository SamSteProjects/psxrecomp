import fs from 'node:fs';
import assert from 'node:assert/strict';
import {worldAnimationRangeDraft,worldAnimationChannelDraft} from '../editor/worldmap-animation-editor.js';
import {qualifyWorldAnimationEdit} from '../editor/worldmap-animation-current.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(const r of rows){
  const before=structuredClone(r.held),edits=worldAnimationRangeDraft(r.held,r.object,r.values,r.start,r.end);
  assert.deepEqual(edits,r.edits);assert.deepEqual(r.held,before);
  await qualifyWorldAnimationEdit(r.review,r.held,r.current,r.held.entity_id,r.held.project_path,r.held.frame_index,edits);
  // One-frame mode has the same draft as a one-frame inclusive range.
  assert.deepEqual(worldAnimationRangeDraft(r.held,r.object,r.values,1,1),worldAnimationChannelDraft(r.held,r.object,r.values));
  // Every output row owns its axis objects independently.
  const copy=worldAnimationRangeDraft(r.held,r.object,r.values,r.start,r.end),at=copy.findIndex(e=>e.frame_index===2&&e.object_index===r.object);
  copy[at].translation.x=10;assert.equal(copy.find(e=>e.frame_index===3&&e.object_index===r.object).translation.x,-2048);assert.deepEqual(r.held,before);
  for(const [start,end] of [[-1,1],[2,1],[0,r.held.preview.frame_count],[2,4],[0,.5],[NaN,4],[0,Infinity],[true,4]])assert.throws(()=>worldAnimationRangeDraft(r.held,r.object,r.values,start,end));
  assert.throws(()=>worldAnimationRangeDraft(r.held,r.held.preview.channel_count,r.values,1,4));
  assert.throws(()=>worldAnimationRangeDraft(r.held,r.object,{...r.values,rotation_psx:{x:1,y:0,z:0}},1,4));
  const bad=structuredClone(r.review);bad.edits.pop();await assert.rejects(qualifyWorldAnimationEdit(bad,r.held,r.current,r.held.entity_id,r.held.project_path,1,edits));
}
assert.equal(rows.length,5);
const full=structuredClone(rows[0].held),record=String(full.preview.record_index).padStart(4,'0');
full.preview.frame_count=512;full.preview.channel_count=64;
full.binding={entries:{[record]:{edits:Array.from({length:4096},(_,i)=>({frame_index:Math.floor(i/64),object_index:i%64,translation:{x:1}}))}}};
assert.equal(worldAnimationRangeDraft(full,63,rows[0].values,0,63).length,4096);
assert.throws(()=>worldAnimationRangeDraft(full,63,rows[0].values,0,511));
console.log('5 actual World range drafts and native Reviews, retained siblings, single-frame equivalence and invalid range/receipt refusals passed.');

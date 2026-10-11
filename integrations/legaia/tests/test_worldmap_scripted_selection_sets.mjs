import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {qualifyScriptedWorldSelectionReview} from '../editor/worldmap-scripted-selection-state.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of rows){
 const held=JSON.stringify(row);assert.deepEqual(await qualifyScriptedWorldSelectionReview(row.receipt,row.saved,row.source),row.saved.placement_ids);
 const id=row.saved.placement_ids[0];
 for(const change of [r=>r.receipt.read_only=false,r=>r.receipt.extra=true,r=>r.receipt.source_key='0'.repeat(64),r=>r.receipt.review_key='0'.repeat(64),r=>r.receipt.schema_version='legaia.worldmap-authored-selection-review.v1',r=>r.saved.schema_version='legaia.worldmap-authored-selection.v1',r=>r.source.project_path+='-other',r=>r.source.authored_scripted_placements.shift(),r=>r.source.authored_scripted_placements[0].record_index++,r=>r.source.authored_scripted_placements[0].script_id='script://map01/worldmap/man-p0/ffff',r=>{r.saved.bindings[id].script_id='foreign';r.receipt.selection.bindings[id].script_id='foreign';},r=>{r.saved.name='Different';r.receipt.selection.name='Different';},r=>{r.saved.placement_ids.reverse();r.receipt.selection.placement_ids.reverse();}]){
  const bad=structuredClone(row);change(bad);await assert.rejects(()=>qualifyScriptedWorldSelectionReview(bad.receipt,bad.saved,bad.source));refusals++;
 }
 const moved=structuredClone(row.source);for(const a of moved.authored_scripted_placements){a.target_cell=123;a.native_seed.source_position={x:99,y:55,z:44};}
 assert.deepEqual(await qualifyScriptedWorldSelectionReview(row.receipt,row.saved,moved),row.saved.placement_ids);assert.equal(JSON.stringify(row),held);
}
console.log(`${rows.length} scripted saved group receipts, moved-member continuity and ${refusals} changed ownership/receipt refusals pass.`);

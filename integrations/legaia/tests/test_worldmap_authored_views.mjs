import assert from 'node:assert/strict';
import fs from 'node:fs';
import {qualifyWorldViewReview} from '../editor/worldmap-views.js';
const out=process.argv[2];assert(out,'Pass native authored saved-view evidence directory');
const cases=JSON.parse(fs.readFileSync(`${out}/cases.json`));let refused=0;
for(const row of cases){
 const {review,saved,current}=row,held=structuredClone(row);
 assert.deepEqual(await qualifyWorldViewReview(review,saved,current),saved.display);
 const mutations=[s=>s.binding.authored_owner.record_index++,s=>s.binding.authored_owner.target_cell++,s=>s.binding.authored_owner.native_entity_id='foreign',s=>s.binding.authored_owner.placement_id='foreign',s=>s.binding.authored_owner.model_pool_index++,s=>s.binding.authored_owner.extra=true,s=>s.binding.entity_sha256='0'.repeat(64),s=>s.binding.source_instance_ids.push('foreign'),s=>s.display.layer='retail',s=>s.display.camera.distance=Infinity,s=>s.source_record.map_sha256='0'.repeat(64)];
 for(const mutate of mutations){const bad=structuredClone(saved);mutate(bad);const {review_key,...entry}=bad;await assert.rejects(()=>qualifyWorldViewReview({...review,view:entry},bad,current));refused++;}
 const gone=structuredClone(current);gone.scene_graph.entities=gone.scene_graph.entities.filter(e=>e.entity_id!==saved.display.selected_id);await assert.rejects(()=>qualifyWorldViewReview(review,saved,gone));refused++;
 const proposed=structuredClone(current);proposed.representation='proposed-source';await assert.rejects(()=>qualifyWorldViewReview(review,saved,proposed));refused++;
 assert.deepEqual(row,held);
}
console.log(`${cases.length} native saved-target reviews pass; ${refused} ownership/display/deleted/proposed refusals pass.`);

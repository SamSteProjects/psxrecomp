import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource,qualifyScriptedCreationReview} from '../editor/worldmap-scripted-creation-state.js';
const scenes=JSON.parse(readFileSync(process.argv[2],'utf8')),creations=JSON.parse(readFileSync(process.argv[3],'utf8'));let refusals=0;
const before=JSON.stringify([scenes,creations]);
for(const c of creations){const row=scenes.find(r=>r.name===c.name),o=row.options,args=[row.retail,o.manWitness,o.mapWitness,{path:o.path,key:row.retail.project_source_key,overrides:o.overrides}];
 const qualified=await qualifyScriptedCreationSource(c.source,...args);
 assert.deepEqual(await qualifyScriptedCreationReview(c.review,qualified,c.requests),c.review);
 for(const change of [v=>v.source_key='0'.repeat(64),v=>v.remaining_creation_capacity++,v=>v.free_record_indices.push(0),v=>v.target_cells.pop(),v=>v.donors[0].seed.source_position.x++,v=>v.floor_lut[0]++]){const altered=structuredClone(c.source);change(altered);await assert.rejects(()=>qualifyScriptedCreationSource(altered,...args));refusals++;}
 for(const change of [v=>v.source_key='0'.repeat(64),v=>v.requests[0].shared_script=false,v=>v.proposed_map_sha256='0'.repeat(64),v=>v.audit.allocations[0].target_cell++,v=>v.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.binding.operations[0].requests[0].values.offset.x++,v=>v.relocation_offset+=2]){const altered=structuredClone(c.review);change(altered);await assert.rejects(()=>qualifyScriptedCreationReview(altered,qualified,c.requests));refusals++;}
 console.log(c.name,'complete creation and retained Review qualify');
}
assert.equal(JSON.stringify([scenes,creations]),before);const proof={cases:creations.length,refusals,inputs_unchanged:true,browser_verified:false,gameplay_verified:false};if(process.argv[4])writeFileSync(process.argv[4],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));

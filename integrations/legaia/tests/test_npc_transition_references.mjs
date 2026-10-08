import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeAssetReferences,assetReferenceInstructionSite,assetReferenceRelationLabel} from '../editor/asset-references.js';
if(!process.argv[2])throw new Error('Provide fresh Retail NPC arrival reference reports.');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(const {id,report} of f.reports){
  assert.deepEqual(decodeAssetReferences(report,id,f.source_key),report);
  const edge=[...report.incoming,...report.outgoing].find(e=>e.kind==='npc_script_transition_arrival');assert(edge);
  const site=assetReferenceInstructionSite(edge,new Map(report.nodes.map(n=>[n.id,n])));assert.equal(site.pc,53);assert.equal(site.owner_id,'scene://map02/actors/man-p1/0002');assert(assetReferenceRelationLabel(edge).includes('route activation unknown'));
  for(const mutate of [p=>p.effective_values.direction_encoded=17,p=>p.arrival_reference.x=65,p=>p.native_instruction.relative_operand_offset++,p=>p.native_instruction.target_context=7,p=>p.native_instruction.raw_hex='00',p=>p.reachability='verified',p=>p.operand_id='foreign',p=>p.authored_values={destination:'town01'}]){
    const bad=structuredClone(report),row=[...bad.incoming,...bad.outgoing].find(e=>e.id===edge.id);mutate(row.npc_transition_arrival_evidence);assert.throws(()=>decodeAssetReferences(bad,id,f.source_key));
  }
}
assert.deepEqual(decodeAssetReferences(f.project,f.project_id,f.source_key,'project'),f.project);
console.log('Fresh active/project NPC arrival graphs, inverse clone ownership, native layout, arrival bytes, donor instruction navigation and forged evidence refusal passed.');

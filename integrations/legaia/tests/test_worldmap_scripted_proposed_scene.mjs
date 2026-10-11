import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedCreationSource} from '../editor/worldmap-scripted-creation-state.js';
import {qualifyProposedScriptedWorldScene} from '../editor/worldmap-scripted-placement-scene.js';
const scenes=JSON.parse(readFileSync(process.argv[2],'utf8')),creations=JSON.parse(readFileSync(process.argv[3],'utf8')),proposals=JSON.parse(readFileSync(process.argv[4],'utf8'));const held=JSON.stringify([scenes,creations,proposals]);let refusals=0;
for(const p of proposals){const row=scenes.find(r=>r.name===p.name),c=creations.find(r=>r.name===p.name),o=row.options,creation=await qualifyScriptedCreationSource(c.source,row.retail,o.manWitness,o.mapWitness,{...o,key:row.retail.project_source_key});
 const view=await qualifyProposedScriptedWorldScene(row.retail,p.proposed,c.review,creation,o),id=`scene://${p.name}/worldmap/authored-placements/${c.requests[0].placement_id.split('/').pop()}`;
 assert(view.entities.some(e=>e.entity_id===id&&e.placement_scope==='authored_scripted_seed'&&e.preview_layer==='Proposed authored seeds'));assert.equal(view.entities.length,row.current.scene_graph.entities.length+1);
 for(const change of [v=>v.representation='current-scripted-placement-source',v=>v.scripted_proposal.review_key='0'.repeat(64),v=>v.scripted_proposal.requests[0].values.offset.x++,v=>v.scene_graph.entities.pop(),v=>v.placement_source.binding.operations.at(-1).proposed_map_sha256='0'.repeat(64),v=>v.scene_graph.entities.at(-1).source_position.y++,v=>v.gameplay_verified=true]){const altered=structuredClone(p.proposed);change(altered);await assert.rejects(()=>qualifyProposedScriptedWorldScene(row.retail,altered,c.review,creation,o));refusals++;}
 console.log(p.name,'Proposed scripted scene and native lineage qualify');
}
assert.equal(JSON.stringify([scenes,creations,proposals]),held);const proof={cases:proposals.length,refusals,inputs_unchanged:true,browser_verified:false,gameplay_verified:false};if(process.argv[5])writeFileSync(process.argv[5],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));

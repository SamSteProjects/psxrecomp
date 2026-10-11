import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {qualifyScriptedWorldBind} from '../editor/worldmap-scripted-bind.js';
const scenes=JSON.parse(readFileSync(process.argv[2],'utf8')),cases=JSON.parse(readFileSync(process.argv[3],'utf8')),held=JSON.stringify([scenes,cases]);let refusals=0;
for(const c of cases){const row=scenes.find(r=>r.name===c.scene),entity=row.current.scene_graph.entities.find(e=>e.entity_id===c.entity_id);assert.deepEqual(await qualifyScriptedWorldBind(c.result,row.current,entity,row.options.path),c.result);
 for(const change of [v=>v.entity_id='foreign',v=>v.source_key='0'.repeat(64),v=>v.native_entity_id='foreign',v=>v.anchor.col++,v=>v.trigger.byte_offset+=4,v=>v.trigger.encoded.record_index++,v=>v.script.id='foreign',v=>v.script.entry_pc++,v=>v.script.encoded_animation_selector++,v=>v.script.current_sha256='0'.repeat(64),v=>v.script.retail_sha256='0'.repeat(64),v=>v.shared_script=false,v=>v.runtime_activation='active',v=>v.animation_clip='resolved',v=>v.extra=true]){const altered=structuredClone(c.result);change(altered);await assert.rejects(()=>qualifyScriptedWorldBind(altered,row.current,entity,row.options.path));refusals++;}
 const forged=structuredClone(entity),forgedResult=structuredClone(c.result);forged.entity_id=forgedResult.entity_id='foreign';await assert.rejects(()=>qualifyScriptedWorldBind(forgedResult,row.current,forged,row.options.path));refusals++;
 console.log(c.scene,c.entity_id,'shared Current bind ownership qualifies');
}
assert.equal(JSON.stringify([scenes,cases]),held);const proof={cases:cases.length,refusals,inputs_unchanged:true,gameplay_verified:false};if(process.argv[4])writeFileSync(process.argv[4],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));

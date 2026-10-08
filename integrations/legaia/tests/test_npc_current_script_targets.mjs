import assert from 'node:assert/strict';
import fs from 'node:fs';
import {npcCurrentScriptTargetOverlay} from '../editor/npc-current-script-targets.js';
assert(process.argv[2]&&process.argv[3],'Fresh private movement and branch fixtures required');
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),before=structuredClone(f);
const retail=await npcCurrentScriptTargetOverlay(f.report,'retail',-800,f.state),current=await npcCurrentScriptTargetOverlay(f.report,'authored',-800,f.state);
assert.deepEqual(retail.targets.find(r=>r.pc===35).position,{x:9664,y:null,z:8640});
assert.deepEqual(current.targets.find(r=>r.pc===35).position,{x:64,y:null,z:16384});
assert.equal(current.entity_id,f.entity_id);assert.equal(current.height,-800);assert.equal(current.runtime_dispatch,'not_asserted');assert.equal(current.gameplay_verified,false);assert.equal(current.targets.length,3);assert.deepEqual(f,before);
for(const height of [NaN,Infinity,10000001,true])await assert.rejects(()=>npcCurrentScriptTargetOverlay(f.report,'authored',height,f.state));
await assert.rejects(()=>npcCurrentScriptTargetOverlay(f.report,'live',0,f.state));await assert.rejects(()=>npcCurrentScriptTargetOverlay(f.report,'authored',0,f.state,'executed'));
for(const alter of [r=>r.inspection.instructions.find(n=>n.pc===35).operands.target_position.x+=64,r=>r.inspection.instructions.find(n=>n.pc===35).byte_offset++,r=>r.inspection.instructions.find(n=>n.pc===35).raw_hex='00',r=>r.inspection.instructions.find(n=>n.pc===35).target_context=1,r=>r.inspection.instructions.find(n=>n.pc===35).operands.parked_target=true,r=>r.inspection.instructions.push(structuredClone(r.inspection.instructions.find(n=>n.pc===35)))]){const r=structuredClone(f.report);alter(r);await assert.rejects(()=>npcCurrentScriptTargetOverlay(r,'authored',0,f.state));}
const branch=JSON.parse(fs.readFileSync(process.argv[3],'utf8')),reached=await npcCurrentScriptTargetOverlay(branch.report,'authored',0,branch.state),all=await npcCurrentScriptTargetOverlay(branch.report,'authored',0,branch.state,'all_anchors');
assert.equal(reached.targets.length,2);assert.equal(all.targets.length,3);assert.equal(all.targets.find(t=>t.pc===57).path_status,'source_unvisited');assert(reached.targets.every(t=>t.path_status==='decoded_reached'));
const stale=structuredClone(f.state);stale.project_copy_source_key='0'.repeat(64);await assert.rejects(()=>npcCurrentScriptTargetOverlay(f.report,'authored',0,stale));
console.log('Native Current/Retail destination bytes, absolute coordinate bounds, Y separation, reached/unvisited scope and forged/stale refusal passed.');

import assert from 'node:assert/strict';
import {scriptOwnerComponents} from '../editor/script-owner-inspector.js';
import {scriptComponentResetReview} from '../editor/script-component-reset.js';
const owner='scene://fixture/scripts/man-p2/0000',scene='scene://fixture';
const record={id:owner,scene_id:scene,kind:'script',authored:{Dialogue:{runs:{run:'Edited text'}},Transitions:{entries:{entry:{entry_x_encoded:99}}},ScriptFlags:{entries:{}},Unknown:{entries:{bad:{}}}},component_reviews:[{component:'Transitions',authored:{entries:{entry:{entry_x_encoded:99}}},review_key:'a'.repeat(64)}]};
const before=JSON.stringify(record),components=scriptOwnerComponents(record,scene);
assert.deepEqual(Object.keys(components),['Dialogue','Transitions']);assert.equal(components.Dialogue.authored_run_count,1);assert.equal(components.Transitions.authored_instruction_count,1);
components.Transitions.entries.entry.entry_x_encoded=23;assert.equal(JSON.stringify(record),before);
const state={project:{mode:'edit'},scene:{id:scene,entities:[]},authored_assets:[record]};
assert.equal(scriptComponentResetReview(state,{id:owner},'Transitions').entries.entry.entry_x_encoded,99);
for(const mutate of [r=>r.kind='actor',r=>r.id='scene://fixture/actors/man-p1/0001',r=>r.scene_id='scene://other',r=>r.authored.Transitions.entries=[]]){const copy=JSON.parse(before);mutate(copy);assert.throws(()=>scriptOwnerComponents(copy,scene));}
for(const mutate of [s=>s.scene.id='scene://other',s=>s.authored_assets[0].kind='actor',s=>s.authored_assets[0].component_reviews[0].authored.entries={changed:{}},s=>s.project.mode='live']){const copy=JSON.parse(JSON.stringify(state));mutate(copy);assert.throws(()=>scriptComponentResetReview(copy,{id:owner},'Transitions'));}
console.log('Standalone script Inspector uses detached qualified components and source-bound reset witnesses.');

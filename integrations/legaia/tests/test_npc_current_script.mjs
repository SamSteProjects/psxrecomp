import assert from 'node:assert/strict';
import fs from 'node:fs';
import {decodeNpcCurrentScript} from '../editor/npc-current-script.js';
import {createScriptFlagSandbox} from '../editor/script-sandbox-engine.js';
import {createScriptSandboxScenario,replayScriptSandboxScenario} from '../editor/script-sandbox-scenarios.js';
import {scriptFlowReportHash} from '../editor/script-flow-identity.js';
assert(process.argv[2],'Fresh private Retail preview fixture required');
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),{report,state,entity_id:id}=fixture;
const accepted=await decodeNpcCurrentScript(report,id,state);
assert.equal(accepted.inspection.record.raw_hex.slice(44,48),'7800');
for(const alter of [v=>v.entity_id='authored-actor://other',v=>v.draft.name='changed',v=>v.project_source_key='0'.repeat(64),v=>v.generated_code=true,v=>v.runtime_binding='observed',v=>v.inspection.record.sha256='b'.repeat(64),v=>v.changed_byte_count++,v=>v.inspection.record.raw_hex='00'+v.inspection.record.raw_hex.slice(2),v=>v.inspection.source_record.byte_offset++,v=>v.state_key='bad']){const bad=structuredClone(report);alter(bad);await assert.rejects(()=>decodeNpcCurrentScript(bad,id,state));}
const inspection=accepted.inspection,engine=createScriptFlagSandbox(inspection);engine.start(22,{local:null,global:null,context:null});engine.step();assert.equal(engine.snapshot().state.status,'unknown_flag');engine.assumeFlag('system',2048,true);engine.step();assert.equal(engine.snapshot().state.system_flags['2048'],true);assert.equal(engine.snapshot().state.system_flags['326'],undefined);
const context={project_path:state.project.path,scene_id:state.scene.id,script_id:inspection.semantic_id,project_source_key:state.project_copy_source_key,record_sha256:inspection.record.sha256,representation:'authored_current',flow_proof:{state_key:accepted.state_key,report_sha256:await scriptFlowReportHash(inspection),review_key:null,branch_id:null,branch_value:null}};
const scenario=await createScriptSandboxScenario(inspection,engine.snapshot(),context),replayed=await replayScriptSandboxScenario(scenario,inspection,context);assert.deepEqual(replayed.snapshot(),engine.snapshot());
const another=structuredClone(context);another.flow_proof.state_key='f'.repeat(64);await assert.rejects(()=>replayScriptSandboxScenario(scenario,inspection,another));
assert.deepEqual(fixture.report,report);assert.deepEqual(fixture.state,state);
console.log('Fresh Current NPC script bytes, stale/forged ownership, hypothetical selector2048 and source-bound scenario replay passed.');

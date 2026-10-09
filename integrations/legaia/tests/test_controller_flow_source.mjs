import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {scriptFlowReportHash} from '../editor/script-flow-identity.js';
import {decodeControllerFlowSource,validateControllerFlowProof} from '../editor/controller-flow-source.js';
import {createScriptFlagSandbox} from '../editor/script-sandbox-engine.js';
import {createScriptSandboxScenario,replayScriptSandboxScenario} from '../editor/script-sandbox-scenarios.js';
const rows=JSON.parse(readFileSync(process.argv[2],'utf8'));
assert.equal(rows.length,Number(process.argv[3]??36));
for(const row of rows){
 assert.equal(await scriptFlowReportHash(row.report),row.expected);
 const layer=await decodeControllerFlowSource(row.raw,row),engine=createScriptFlagSandbox(layer.report);
 engine.start(layer.report.entry_pc,{local:null,global:null,context:null});engine.assumeFlag('system',4095,true);engine.step();
 const snapshot=engine.snapshot(),saved=await createScriptSandboxScenario(layer.report,snapshot,layer.context);
 assert.equal(saved.schema_version,'legaia.script-sandbox-scenario.v4');
 assert.deepEqual((await replayScriptSandboxScenario(JSON.parse(JSON.stringify(saved)),layer.report,layer.context)).snapshot(),snapshot);
 for(const mutate of [s=>s.schema_version='legaia.script-sandbox-scenario.v3',s=>s.source.controller_flow_proof.component='ControllerUnknown',s=>s.source.controller_flow_proof.effective_record_sha256='f'.repeat(64),s=>s.source.controller_flow_proof.owner_id='scene://foreign/controllers/man-p1/0000',s=>s.source.controller_flow_proof.review_key='f'.repeat(64),s=>s.source.controller_flow_proof.value={foreign:1},s=>s.source.controller_flow_proof.source_key='f'.repeat(64),s=>s.source.controller_flow_proof.extra=0,s=>s.source.flow_proof={}] ){
  const invalid=structuredClone(saved);mutate(invalid);await assert.rejects(()=>replayScriptSandboxScenario(invalid,layer.report,layer.context));
 }
 for(const mutate of [s=>s.report={},s=>s.component='ControllerUnknown',s=>s.state_key='f'.repeat(64),s=>s.gameplay_verified=true,s=>s.project_changed=true,s=>s.extra=1]){
  const invalid=structuredClone(row.raw);mutate(invalid);await assert.rejects(()=>decodeControllerFlowSource(invalid,row));
 }
 assert.throws(()=>validateControllerFlowProof({...layer.context.controller_flow_proof,source_key:0}));
}
console.log(`${rows.length} controller Current/Proposed/reset report hashes and v4 scenario replay, source/schema/operand tampering refusal passed`);

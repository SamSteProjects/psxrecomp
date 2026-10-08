import {createScriptFlagSandbox} from './script-sandbox-engine.js';
import {validateScriptInspectionSource} from './script-inspection-source.js';
import {canonicalScriptMetadata,scriptFlowReportHash} from './script-flow-identity.js';
const same=(a,b)=>JSON.stringify(canonicalScriptMetadata(a))===JSON.stringify(canonicalScriptMetadata(b));
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
export async function replayScriptSandboxScenario(value,report,context){
 const source=validateScriptInspectionSource(context);
 if(!exact(value,['schema_version','source','report_sha256','initial','steps','result','assumptions','runtime_execution','project_changed'])||value.schema_version!=='legaia.script-sandbox-scenario.v1'||value.assumptions!=='hypothetical_user_inputs'||value.runtime_execution!=='not_asserted'||value.project_changed!==false||!same(validateScriptInspectionSource(value.source),source)||typeof value.report_sha256!=='string'||value.report_sha256!==await scriptFlowReportHash(report)||source.flow_proof&&source.flow_proof.report_sha256!==value.report_sha256)throw Error('Scenario belongs to a different qualified source or flow.');
 if(!exact(value.initial,['pc','inputs','wait_accumulator'])||!Array.isArray(value.steps)||value.steps.length>256)throw Error('Scenario initial state or step bounds are invalid.');
 const engine=createScriptFlagSandbox(report);engine.start(value.initial.pc,value.initial.inputs,{waitAccumulator:value.initial.wait_accumulator});
 for(const event of value.steps){if(exact(event,['kind'])&&event.kind==='instruction')engine.step();else if(exact(event,['kind','delta_ticks'])&&event.kind==='tick')engine.tick(event.delta_ticks);else throw Error('Scenario contains an unsupported step.');}
 if(!same(engine.snapshot().state,value.result)||!same(engine.snapshot().initial,value.initial))throw Error('Scenario result disagrees with independent replay.');return engine;
}
export async function createScriptSandboxScenario(report,snapshot,context){
 if(!snapshot?.state||!snapshot.initial||!Array.isArray(snapshot.history)||snapshot.history.length>256)throw Error('Start a bounded sandbox before saving.');
 const source=validateScriptInspectionSource(context),value={schema_version:'legaia.script-sandbox-scenario.v1',source,report_sha256:await scriptFlowReportHash(report),initial:structuredClone(snapshot.initial),steps:snapshot.history.map(r=>r.effect?.operation==='wait_ticks'&&r.effect.delta_ticks!==null?{kind:'tick',delta_ticks:r.effect.delta_ticks}:{kind:'instruction'}),result:structuredClone(snapshot.state),assumptions:'hypothetical_user_inputs',runtime_execution:'not_asserted',project_changed:false};
 const replayed=await replayScriptSandboxScenario(value,report,source);if(!same(replayed.snapshot(),snapshot))throw Error('Sandbox history disagrees with replay.');return value;
}

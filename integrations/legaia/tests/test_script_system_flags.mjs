import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {createScriptFlagSandbox} from '../editor/script-sandbox-engine.js';
import {createScriptSandboxScenario,replayScriptSandboxScenario} from '../editor/script-sandbox-scenarios.js';
import {scriptFlowReportHash} from '../editor/script-flow-identity.js';
if(!globalThis.crypto)Object.defineProperty(globalThis,'crypto',{value:webcrypto});
const instruction=(op,index,pc=0,delta=2)=>({pc,opcode:({SET:0x50,CLEAR:0x60,TEST:0x70}[op])+(index>>8),length:op==='TEST'?4:2,mnemonic:'SYSFLAG_'+op,target_context:null,operands:{index,...(op==='TEST'?{delta}:{})},successors:op==='TEST'?[{pc:(pc+2+delta)&65535,condition:'flag_set'},{pc:pc+4,condition:'flag_clear'}]:[{pc:pc+2,condition:'encoded_continuation'}]});
const report=rows=>({status:'decoded_supported_paths',entry_pc:rows[0].pc,instructions:rows,dialogues:[],stops:[]}),inputs={local:null,global:0x80000000,context:17};
const values=new Uint8Array(512),known=new Uint8Array(512);
for(let index=0;index<4096;index++){
 const e=createScriptFlagSandbox(report([instruction('SET',index),instruction('CLEAR',index,2)]));e.start(0,inputs,{waitAccumulator:9});
 const before=e.snapshot();let s=e.step();values[index>>3]|=128>>(index&7);known[index>>3]|=128>>(index&7);
 assert.equal(s.state.system_flags[index],!!(values[index>>3]&(128>>(index&7))));assert.equal(Object.keys(s.state.system_flags).length,1);assert.deepEqual(s.state.banks,before.state.banks);assert.equal(s.state.wait_accumulator,9);
 s=e.step();values[index>>3]&=~(128>>(index&7));assert.equal(s.state.system_flags[index],false);assert.equal(e.back().state.system_flags[index],true);assert.deepEqual(e.back(),before);
 const test=createScriptFlagSandbox(report([instruction('TEST',index)]));test.start(0,inputs);const first=test.snapshot();s=test.step();assert.equal(s.state.status,'unknown_flag');assert.equal(s.state.pc,0);assert.equal(s.history[0].effect.tested_value,null);
 test.assumeFlag('system',index,true);s=test.step();assert.equal(s.state.pc,4);assert.equal(s.history.at(-1).effect.successor_index,0);test.back();test.assumeFlag('system',index,false);s=test.step();assert.equal(s.state.pc,4);assert.equal(s.history.at(-1).effect.successor_index,1);
 while(test.snapshot().history.length)test.back();assert.deepEqual(test.snapshot(),first);
}
const r=report([instruction('TEST',4095,10,-12)]),e=createScriptFlagSandbox(r);e.start(10,inputs);e.step();e.assumeFlag('system',4095,true);e.assumeFlag('system',4094,false);e.assumeFlag('system',4094,null);assert.deepEqual(e.snapshot().state.system_flags,{'4095':true});assert.equal(e.step().state.pc,0);
const context={project_path:'C:/private/project',scene_id:'scene://fixture',script_id:'script://fixture/actors/man-p1/0000',project_source_key:'a'.repeat(64),record_sha256:'b'.repeat(64),representation:'retail_source'};
const saved=await createScriptSandboxScenario(r,e.snapshot(),context);assert.equal(saved.schema_version,'legaia.script-sandbox-scenario.v3');assert.deepEqual((await replayScriptSandboxScenario(saved,r,context)).snapshot(),e.snapshot());
for(const representation of ['authored_current','reviewed_proposed']){const proposed=representation==='reviewed_proposed',source={...context,representation,flow_proof:{state_key:'d'.repeat(64),report_sha256:await scriptFlowReportHash(r),review_key:proposed?'e'.repeat(64):null,branch_id:proposed?context.script_id+'/branch/0000':null,branch_value:proposed?{target_pc:0}:null}},scenario=await createScriptSandboxScenario(r,e.snapshot(),source);assert.deepEqual((await replayScriptSandboxScenario(scenario,r,source)).snapshot(),e.snapshot());await assert.rejects(()=>replayScriptSandboxScenario(scenario,r,{...source,flow_proof:{...source.flow_proof,state_key:'f'.repeat(64)}}));}
for(const version of ['v1','v2']){const bad=structuredClone(saved);bad.schema_version='legaia.script-sandbox-scenario.'+version;await assert.rejects(()=>replayScriptSandboxScenario(bad,r,context));}
const bad=structuredClone(saved);bad.result.system_flags['4095']=false;await assert.rejects(()=>replayScriptSandboxScenario(bad,r,context));
for(const mutate of [r=>r.opcode=0x100000070,r=>r.opcode=0x70,r=>r.operands.index=4096,r=>r.operands.index=-1,r=>r.operands.delta=32768,r=>r.target_context=7,r=>r.length=3,r=>r.successors.reverse(),r=>r.successors[0].pc++]){
 const row=instruction('TEST',4095);mutate(row);const sim=createScriptFlagSandbox(report([row]));sim.start(0,inputs);const s=sim.step();assert.equal(s.state.status,'unsupported');assert(!Object.hasOwn(s.state,'system_flags'));assert.equal(s.state.pc,0);
}
for(const index of [-1,4096,1.5]){e.back();assert.throws(()=>e.assumeFlag('system',index,true));}
console.log('System flags: all 4096 selectors, isolated sparse unknowns, both edges, wrapped targets, exact Back, v3 replay/old schema refusal and malformed metadata passed.');

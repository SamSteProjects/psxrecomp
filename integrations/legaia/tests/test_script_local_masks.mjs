import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {createScriptFlagSandbox,mountScriptFlagSandbox} from '../editor/script-flag-sandbox.js';
import {createScriptSandboxScenario,replayScriptSandboxScenario} from '../editor/script-sandbox-scenarios.js';
if(!globalThis.crypto)Object.defineProperty(globalThis,'crypto',{value:webcrypto});
const row=(sub,pc=0)=>({pc,opcode:0x4c,length:2,mnemonic:'FIELD_STATE_CONTROL',target_context:null,operands:{sub_op:sub,can_yield:false,flag_word:'actor_local_flags',and_mask:sub===0x35?0xff7f:0xffff,or_mask:sub===0x35?0x020a:0x028a,runtime_effect:'not_evaluated'},successors:[{pc:pc+2,condition:'encoded_continuation'}]});
const report=rows=>({status:'decoded_supported_paths',entry_pc:0,instructions:rows,dialogues:[],stops:[]}),inputs={local:null,global:0x12345678,context:0x87654321};
for(const sub of [0x35,0x36]){
 const e=createScriptFlagSandbox(report([row(sub)]));
 for(let v=0;v<65536;v++){
  e.start(0,{...inputs,local:v},{waitAccumulator:-17});const s=e.step();
  // Independent bit operations, rather than the decoder's reported masks.
  let expected=v|2|8|512;expected=sub===0x35?expected&~128:expected|128;
  assert.deepEqual(s.state.banks.local,{value:expected,known:65535});assert.equal(s.state.pc,2);assert.equal(s.state.wait_accumulator,-17);
  assert.deepEqual(s.state.banks.global,s.initial.inputs.global===null?{}:{value:inputs.global,known:0xffffffff});
  assert.deepEqual(s.state.banks.context,{value:inputs.context,known:0xffffffff});
 }
 e.start(0,inputs);const before=e.snapshot();const s=e.step();assert.deepEqual(s.state.banks.local,{value:sub===0x35?522:650,known:650});assert.deepEqual(e.back(),before);
 e.assumeFlag('local',15,true);e.step();assert.deepEqual(e.snapshot().state.banks.local,{value:32768+(sub===0x35?522:650),known:32768+650});
}
for(const mutate of [r=>r.operands.sub_op=0x37,r=>r.operands.and_mask=0xffff,r=>r.operands.or_mask=0,r=>r.operands.can_yield=true,r=>r.operands.flag_word='actor_flags',r=>r.operands.runtime_effect='observed',r=>r.target_context=7,r=>r.opcode=0x4d,r=>r.length=3,r=>r.successors[0].pc=3]){
 const bad=row(0x35);mutate(bad);const e=createScriptFlagSandbox(report([bad]));e.start(0,inputs);const s=e.step();assert.equal(s.state.status,'unsupported');assert.deepEqual(s.state.banks,s.history[0].before.banks);assert.equal(s.state.pc,0);
}
const r=report([row(0x35),row(0x36,2)]),e=createScriptFlagSandbox(r);e.start(0,inputs);e.run([2]);assert.equal(e.snapshot().history.length,1);e.step();
const context={project_path:'C:/private/project',scene_id:'scene://fixture',script_id:'script://fixture/actors/man-p1/0000',project_source_key:'a'.repeat(64),record_sha256:'b'.repeat(64),representation:'retail_source'};
const saved=await createScriptSandboxScenario(r,e.snapshot(),context);assert.equal(saved.schema_version,'legaia.script-sandbox-scenario.v1');assert.deepEqual((await replayScriptSandboxScenario(saved,r,context)).snapshot(),e.snapshot());
e.back();e.assumeFlag('local',0,true);e.step();const v2=await createScriptSandboxScenario(r,e.snapshot(),context);assert.equal(v2.schema_version,'legaia.script-sandbox-scenario.v2');assert.deepEqual((await replayScriptSandboxScenario(v2,r,context)).snapshot(),e.snapshot());
const changed=structuredClone(r);delete changed.instructions[0].operands.and_mask;await assert.rejects(()=>replayScriptSandboxScenario(saved,changed,context));
class Element{constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.textContent='';this.value='';}append(...ns){for(const n of ns){n.parent=this;this.children.push(n);}}replaceChildren(...ns){this.children=[];this.append(...ns);}setAttribute(k,v){this[k]=v;}remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}}
globalThis.document={createElement:tag=>new Element(tag)};const tree=n=>[n,...n.children.flatMap(tree)],host=new Element('div');let live=true;
const view=mountScriptFlagSandbox(host,{report:r,selection:()=>0,current:()=>live,busy:()=>false,selectInstruction:()=>{},onError:e=>{throw e;}}),button=t=>tree(host).find(n=>n.tagName==='button'&&n.textContent===t);
button('Start flag sandbox at entry').onclick();button('Simulate one instruction').onclick();assert(tree(host).some(n=>n.textContent.includes('AND 0xFF7F, OR 0x020A')&&n.textContent.includes('known bits 0x028A')));button('Back one simulated instruction').onclick();assert(!tree(host).some(n=>n.textContent.includes('AND 0xFF7F')));live=false;view.update();assert.equal(view.snapshot.state,null);view.dispose();
console.log('Local masks: exhaustive 16-bit values, partial unknown state, ownership refusal, Back, breakpoint, v1/v2 replay and UI trace passed.');

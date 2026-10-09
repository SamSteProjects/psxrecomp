import assert from 'node:assert/strict';
import {decodeControllerFlagBitSnapshot,decodeControllerFlagBitReview,mountControllerFlagBits} from '../editor/controller-flag-bits.js';
const owner='scene://fixture/controllers/man-p1/0000',id='script://fixture/controllers/man-p1/0000/flag-bit/0005',context={projectPath:'C:/private',sceneId:'scene://fixture',mode:'edit',scriptKey:'a'.repeat(64)};
const values=bit=>({bit});
const report=value=>({status:'decoded_supported_paths',instructions:[{pc:5,length:2,byte_offset:105,mnemonic:'GFLAG_SET',opcode:0x2e,raw_hex:'2e'+(224|value).toString(16),target_context:null,operands:{...values(value),raw_operand:224|value},successors:[{pc:7,condition:'encoded_continuation'}]},{pc:7,length:3,byte_offset:107,mnemonic:'JMP_REL',raw_hex:'26fdff',target_context:null,operands:{},successors:[{pc:5,condition:'unconditional'}]}],dialogues:[],stops:[],opaque_regions:[],unvisited_instructions:[],unvisited_dialogues:[]});
const snapshot=()=>({schema_version:'legaia.controller-flag-bits.v1',owner_id:owner,state_key:context.scriptKey,source_record_sha256:'b'.repeat(64),current_record_sha256:'b'.repeat(64),source:{owner_id:owner,record_kind:'man_partition_1_scene_controller',runtime_execution:'not_asserted'},source_report:report(5),current_report:report(5),targets:[{semantic_id:id,owner_id:owner,pc:5,mnemonic:'GFLAG_SET',target_context:null,bit_mask:31,preserved_bits:224,maximum:31,decoded_byte_offset:106,source_record_sha256:'b'.repeat(64),values:values(5),current_values:values(5),authored_values:null}],supported:true,reason:null,limitations:[],gameplay_verified:false});
const proposal=()=>({...snapshot(),operand_id:id,value:values(6),proposed_record_sha256:'c'.repeat(64),review_key:'d'.repeat(64),proposed_report:report(6),changed_decoded_byte_offsets:[106],no_op:false,native_bytes_changed:true,project_changed:false});
assert.equal(decodeControllerFlagBitSnapshot(snapshot(),owner,context).targets.length,1);assert.equal(decodeControllerFlagBitReview(proposal(),snapshot(),id,values(6)).operand_id,id);
for(const mutate of [r=>r.targets=[],r=>r.targets[0].maximum=15,r=>r.targets[0].bit_mask=7,r=>r.targets[0].current_values.bit=6,r=>r.targets[0].preserved_bits=0,r=>r.current_report.instructions.pop(),r=>r.targets.push(r.targets[0]),r=>r.targets[0].decoded_byte_offset++,r=>r.source_record_sha256='bad',r=>r.gameplay_verified=true]){const raw=snapshot();mutate(raw);assert.throws(()=>decodeControllerFlagBitSnapshot(raw,owner,context));}
for(const mutate of [r=>r.value.bit=32,r=>r.changed_decoded_byte_offsets=[105],r=>r.changed_decoded_byte_offsets=[106,106],r=>r.proposed_report.instructions[0].raw_hex='2e06',r=>r.proposed_report.instructions[1].raw_hex='26ffff',r=>r.project_changed=true,r=>r.proposed_record_sha256=r.current_record_sha256]){const raw=proposal();mutate(raw);assert.throws(()=>decodeControllerFlagBitReview(raw,snapshot(),id,values(6)));}
const retained=snapshot();retained.current_report.unvisited_instructions=[retained.current_report.instructions.shift()];assert.equal(decodeControllerFlagBitSnapshot(retained,owner,context).targets.length,1);
const extended=snapshot();extended.targets[0].target_context=7;extended.targets[0].decoded_byte_offset=107;
for(const r of [extended.source_report,extended.current_report]){const n=r.instructions[0];n.target_context=7;n.length=3;n.raw_hex='ae07'+n.raw_hex.slice(2);n.successors[0].pc=8;const jump=r.instructions[1];jump.pc=8;jump.byte_offset=108;jump.raw_hex='26fcff';}
assert.equal(decodeControllerFlagBitSnapshot(extended,owner,context).targets[0].values.bit,5);
class Node{constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.value='';}append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}}replaceChildren(...nodes){this.children=[];this.append(...nodes);}setAttribute(name,value){this[name]=value;}remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}}
globalThis.document={createElement:tag=>new Node(tag)};let queue=[],ctx=structuredClone(context),busy=false,commands=[],reopened=[];
globalThis.fetch=async()=>({ok:true,json:async()=>await queue.shift()});
const tree=n=>[n,...n.children.flatMap(tree)],button=(h,id)=>tree(h).find(n=>n.dataset.controllerFlagBitAction===id),input=h=>tree(h).find(n=>n.tag==='input'&&n['aria-label']==='Proposed Bit Index');
const settings={owner,getContext:()=>ctx,busy:()=>busy,setBusy:v=>busy=v,api:async(route,body)=>{assert.equal(busy,false);commands.push(body);return true;},reopen:pc=>reopened.push(pc)};
async function mount(extra={},initial=snapshot()){ctx=structuredClone(context);const host=new Node();queue=[initial];const controls=mountControllerFlagBits(host,{...settings,...extra});assert(await controls.ready);return {host,controls};}
let {host,controls}=await mount();assert.equal(tree(host).filter(n=>n.tag==='input').length,1);assert(tree(host).some(n=>n.textContent==='Retail: 5 \u00b7 Current: 5 \u00b7 Authored: None'));assert(tree(host).some(n=>n.textContent==='Controller Flag Bit Requests'));input(host).value='6';input(host).oninput();queue=[proposal()];assert(await button(host,'review').onclick());assert.equal(commands.length,0);assert.equal(tree(host).find(n=>'controllerOperandProposed' in n.dataset).hidden,false);assert(!button(host,'apply').disabled);input(host).value='32';input(host).oninput();assert(button(host,'apply').disabled);assert(button(host,'review').disabled);assert.equal(tree(host).find(n=>'controllerOperandProposed' in n.dataset).hidden,true);
button(host,'discard').onclick();input(host).value='6';input(host).oninput();queue=[proposal()];await button(host,'review').onclick();assert(await button(host,'apply').onclick());assert.equal(commands[0].type,'set_controller_flag_bit');assert.deepEqual(commands[0].value,values(6));assert.deepEqual(reopened,[5]);controls.dispose();
({host,controls}=await mount({api:async()=>false}));input(host).value='6';input(host).oninput();queue=[proposal()];await button(host,'review').onclick();assert.equal(await button(host,'apply').onclick(),false);assert(button(host,'apply').disabled);controls.dispose();
({host,controls}=await mount());input(host).value='6';input(host).oninput();let resolve;queue=[new Promise(r=>resolve=r)];const late=button(host,'review').onclick();ctx.scriptKey='f'.repeat(64);controls.updateState();resolve(proposal());assert.equal(await late,false);assert(button(host,'apply').disabled);assert.equal(busy,false);controls.dispose();
const authored=snapshot();authored.current_record_sha256='c'.repeat(64);authored.current_report=report(6);authored.targets[0].current_values=values(6);authored.targets[0].authored_values=values(6);
({host,controls}=await mount({},authored));queue=[{...proposal(),value:null,current_record_sha256:authored.current_record_sha256,current_report:authored.current_report,proposed_record_sha256:'b'.repeat(64),proposed_report:report(5)}];
assert(await button(host,'reset').onclick());assert.equal(input(host).value,'5');assert(!button(host,'apply').disabled);assert(await button(host,'apply').onclick());assert.equal(commands.at(-1).value,null);controls.dispose();
console.log('Controller flag-bit source/Review qualification, retained boundaries, bounded drafts, typed Apply, failed Apply withdrawal and stale-response rejection passed.');

for(const [mnemonic,opcode,maximum,invalid] of [['LFLAG_SET',0x2b,15,'16'],['CFLAG_SET',0x31,31,'8'],['CFLAG_CLEAR',0x32,31,'10']]){
 const raw=snapshot();raw.targets[0].mnemonic=mnemonic;raw.targets[0].maximum=maximum;
 for(const r of [raw.source_report,raw.current_report]){r.instructions[0].mnemonic=mnemonic;r.instructions[0].raw_hex=opcode.toString(16)+'e5';}
 ({host,controls}=await mount({},raw));for(const draft of [invalid,'-1','1.5','32','NaN']){input(host).value=draft;input(host).oninput();assert(button(host,'review').disabled);assert(button(host,'apply').disabled);}controls.dispose();
}
console.log('Local width and context SET8/CLEAR10 draft refusal passed.');

const hiddenMalformed=snapshot();hiddenMalformed.targets=[];hiddenMalformed.supported=false;hiddenMalformed.source_report.instructions[0].raw_hex='2be5';assert.throws(()=>decodeControllerFlagBitSnapshot(hiddenMalformed,owner,context));
console.log('Malformed source bit instructions cannot disappear as unsupported targets.');

({host,controls}=await mount());
const simulationCommandCount=commands.length;const textButton=name=>tree(host).find(n=>n.tag==='button'&&n.textContent===name);
assert(textButton('Simulate reviewed Proposed operands').disabled);textButton('Simulate Current operands').onclick();
textButton('Start flag sandbox at selection').onclick();textButton('Simulate one instruction').onclick();
assert(tree(host).some(n=>n.textContent==='global value 0x00000020 · known mask 0x00000020'));
input(host).value='6';input(host).oninput();queue=[proposal()];await button(host,'review').onclick();
textButton('Simulate reviewed Proposed operands').onclick();textButton('Start flag sandbox at selection').onclick();textButton('Simulate one instruction').onclick();
assert(tree(host).some(n=>n.textContent==='global value 0x00000040 · known mask 0x00000040'));
assert(!textButton('Save sandbox scenario').disabled);assert(!textButton('Load sandbox scenario').disabled);
input(host).value='7';input(host).oninput();assert(textButton('Simulate reviewed Proposed operands').disabled);assert(!tree(host).some(n=>'flagSandbox' in n.dataset));
textButton('Simulate Current operands').onclick();textButton('Start flag sandbox at selection').onclick();textButton('Simulate one instruction').onclick();assert(tree(host).some(n=>n.textContent==='global value 0x00000020 · known mask 0x00000020'));
ctx.scriptKey='f'.repeat(64);controls.updateState();assert(!tree(host).some(n=>'flagSandbox' in n.dataset));controls.dispose();assert.equal(commands.length,simulationCommandCount);
console.log('Current/Reviewed Proposed hypothetical bytes stay separate; drafts, review withdrawal and stale sources dispose simulations without commands.');

import assert from 'node:assert/strict';
import {decodeControllerSystemSelectorSnapshot as decodeSystemSelectorSnapshot,decodeSystemSelectorReview,mountControllerSystemSelectors as mountSystemSelectors} from '../editor/system-flag-selectors.js';
const owner='scene://fixture/controllers/man-p1/0000',operand='script://fixture/controllers/man-p1/0000/system-flag/0016';
const context={projectPath:'C:/private',sceneId:'scene://fixture',mode:'edit',scriptKey:'a'.repeat(64)};
const report=index=>({instructions:[{pc:22,mnemonic:'SYSFLAG_TEST',operands:{index},successors:[{pc:26,condition:'clear'}]}],stops:[]});
const snapshot=()=>({schema_version:'legaia.controller-system-flags.v1',owner_id:owner,state_key:context.scriptKey,source_record_sha256:'b'.repeat(64),current_record_sha256:'c'.repeat(64),gameplay_verified:false,supported:true,current_report:report(326),targets:[{semantic_id:operand,owner_id:owner,pc:22,mnemonic:'SYSFLAG_TEST',target_context:null,byte_length:2,maximum:4095,source_record_sha256:'b'.repeat(64),values:{index:326},current_index:326,authored_values:null,decoded_byte_offset:100}]});
const proposal=()=>({...snapshot(),operand_id:operand,value:{index:4095},review_key:'d'.repeat(64),proposed_record_sha256:'e'.repeat(64),no_op:false,native_bytes_changed:true,project_changed:false,current_report:report(326),proposed_report:report(4095),changed_decoded_byte_offsets:[100,101]});
assert.equal(decodeSystemSelectorSnapshot(snapshot(),owner,context).targets.length,1);
assert.equal(decodeSystemSelectorReview(proposal(),snapshot(),operand,{index:4095}).value.index,4095);
for(const patch of [{state_key:'x'},{owner_id:'other'},{current_record_sha256:null},{gameplay_verified:true},{targets:[snapshot().targets[0],snapshot().targets[0]]}])assert.throws(()=>decodeSystemSelectorSnapshot({...snapshot(),...patch},owner,context));
for(const patch of [{value:{index:0}},{review_key:null},{changed_decoded_byte_offsets:[102]},{proposed_report:report(1)},{gameplay_verified:true},{project_changed:true}])assert.throws(()=>decodeSystemSelectorReview({...proposal(),...patch},snapshot(),operand,{index:4095}));
const different=proposal();different.proposed_report.instructions[0].successors=[];assert.throws(()=>decodeSystemSelectorReview(different,snapshot(),operand,{index:4095}));
// An existing reviewed branch can make a Retail-qualified selector unreachable.
// Its fixed source span still qualifies; no executed path is invented by the UI.
const unreachable=snapshot();unreachable.current_report.instructions=[];
assert.equal(decodeSystemSelectorSnapshot(unreachable,owner,context).targets.length,1);
const unreachableReview=proposal();unreachableReview.current_report.instructions=[];unreachableReview.proposed_report.instructions=[];
assert.equal(decodeSystemSelectorReview(unreachableReview,unreachable,operand,{index:4095}).value.index,4095);
class Node{constructor(tag){this.children=[];this.attributes={};this.style={};this.dataset={};this.value='';this.textContent='';this.disabled=false;}append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}}replaceChildren(...nodes){this.children=[];this.append(...nodes);}setAttribute(k,v){this.attributes[k]=v;}remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}}
const tree=n=>[n,...n.children.flatMap(tree)],button=(host,id)=>tree(host).find(n=>n.dataset.systemAction===id),input=host=>tree(host).find(n=>n.attributes['aria-label']==='Proposed system selector index');
let queue=[],ctx=structuredClone(context),busy=false,commands=[],drafts=[],errors=[],reopened=[];
globalThis.document={createElement:tag=>new Node(tag)};
globalThis.fetch=async(route,options)=>{const raw=await queue.shift();return {ok:true,json:async()=>raw};};
const settings={owner,getContext:()=>ctx,busy:()=>busy,setBusy:v=>{busy=v;},api:async(route,body)=>{assert.equal(busy,false,'The shared mutation API must own its busy lock');commands.push({route,body});return true;},reopen:pc=>reopened.push(pc),onDraftChange:v=>drafts.push(v),onError:e=>errors.push(e)};
async function mount(extra={}){ctx=structuredClone(context);busy=false;const host=new Node('host');queue=[snapshot()];const controls=mountSystemSelectors(host,{...settings,...extra});assert.equal(await controls.ready,true);return {host,controls};}
let {host,controls}=await mount();assert.equal(button(host,'apply').disabled,true);
input(host).value='4095';input(host).oninput();queue=[proposal()];assert.equal(await button(host,'review').onclick(),true);assert.equal(button(host,'apply').disabled,false);assert.equal(commands.length,0);
input(host).value='-1';input(host).oninput();assert.equal(button(host,'apply').disabled,true);assert.equal(button(host,'review').disabled,true);assert.equal(drafts.at(-1).get(operand).index,'-1');
controls.dispose();({host,controls}=await mount({initialDrafts:drafts.at(-1)}));assert.equal(input(host).value,'-1');assert.equal(button(host,'review').disabled,true);
button(host,'discard').onclick();assert.equal(drafts.at(-1).size,0);assert.equal(input(host).value,'326');
input(host).value='4095';input(host).oninput();queue=[proposal()];await button(host,'review').onclick();await button(host,'apply').onclick();assert.deepEqual(commands.at(-1),{route:'/api/command',body:{type:'set_controller_system_flag_selector',entity_id:owner,operand_id:operand,value:{index:4095},review_key:'d'.repeat(64)}});assert.deepEqual(reopened,[22]);assert.equal(drafts.at(-1).size,0);controls.dispose();
({host,controls}=await mount());input(host).value='4095';input(host).oninput();let resolve;queue=[new Promise(done=>resolve=done)];const late=button(host,'review').onclick();input(host).value='0';input(host).oninput();resolve(proposal());assert.equal(await late,false);assert.equal(button(host,'apply').disabled,true);assert.equal(busy,false);
ctx.scriptKey='f'.repeat(64);controls.updateState();assert.equal(input(host).disabled,true);assert.equal(button(host,'apply').disabled,true);controls.dispose();controls.dispose();assert.equal(host.children.length,0);
({host,controls}=await mount());input(host).value='4095';input(host).oninput();queue=[proposal()];await button(host,'review').onclick();ctx.mode='live';controls.updateState();assert.equal(button(host,'apply').disabled,true);controls.dispose();
assert.throws(()=>decodeSystemSelectorSnapshot(snapshot(),owner.replace('/controllers/','/actors/'),context));
console.log('Controller selector qualification, invalid/restored drafts, Review/Apply, late response and stale lifecycle checks passed.');

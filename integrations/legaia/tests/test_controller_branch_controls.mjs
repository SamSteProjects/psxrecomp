import assert from 'node:assert/strict';
import {decodeControllerBranchSnapshot,decodeScriptBranchSnapshot} from '../editor/script-branches.js';
import {decodeControllerBranchReview,mountControllerBranches} from '../editor/controller-branches.js';
const owner='scene://fixture/controllers/man-p1/0000',id='script://fixture/controllers/man-p1/0000/branch/0005';
const context={projectPath:'private',sceneId:'scene://fixture',mode:'edit',scriptKey:'a'.repeat(64)};
const report=target=>({status:'decoded_supported_paths',instructions:[{pc:5,length:3,mnemonic:'JMP_REL',target_context:null,successors:[{pc:target,condition:'always'}]},{pc:8,length:1,mnemonic:'NOP',target_context:null,successors:[]}],dialogues:[],stops:[],opaque_regions:[]});
const snapshot=()=>({schema_version:'legaia.controller-branches.v1',owner_id:owner,state_key:context.scriptKey,source_record_sha256:'b'.repeat(64),current_record_sha256:'b'.repeat(64),source_report:report(8),current_report:report(8),targets:[{semantic_id:id,owner_id:owner,pc:5,mnemonic:'JMP_REL',condition:'always',encoding:'relative_u16',target_context:null,target_pc:8,current_target_pc:8,authored_value:null,decoded_byte_offset:100,source_record_sha256:'b'.repeat(64)}],destinations:[{pc:5,mnemonic:'JMP_REL'},{pc:8,mnemonic:'NOP'}],supported:true,reason:null,limitations:[],gameplay_verified:false});
const proposal=()=>({...snapshot(),operand_id:id,value:{target_pc:5},proposed_record_sha256:'c'.repeat(64),review_key:'d'.repeat(64),proposed_report:report(5),changed_decoded_byte_offsets:[100,101],newly_unreachable_source_pcs:[],newly_reached_source_pcs:[],no_op:false,native_bytes_changed:true,project_changed:false});
assert.equal(decodeControllerBranchSnapshot(snapshot(),owner,context).targets.length,1);
assert.throws(()=>decodeScriptBranchSnapshot({...snapshot(),schema_version:'legaia.script-branches.v1'},owner,context));
assert.equal(decodeControllerBranchReview(proposal(),snapshot(),id,{target_pc:5}).operand_id,id);
for(const patch of [{owner_id:owner.replace('/0000','/0001')},{state_key:'x'},{current_record_sha256:null},{gameplay_verified:true},{targets:[snapshot().targets[0],snapshot().targets[0]]}])assert.throws(()=>decodeControllerBranchSnapshot({...snapshot(),...patch},owner,context));
for(const patch of [{value:{target_pc:8}},{review_key:null},{changed_decoded_byte_offsets:[102]},{changed_decoded_byte_offsets:[100,100]},{proposed_report:report(8)},{newly_reached_source_pcs:[5]},{project_changed:true},{proposed_record_sha256:'b'.repeat(64)}])assert.throws(()=>decodeControllerBranchReview({...proposal(),...patch},snapshot(),id,{target_pc:5}));
class Node{constructor(){this.children=[];this.dataset={};this.style={};this.value='';}append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}}setAttribute(){}remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}}
globalThis.document={createElement:()=>new Node()};
let queue=[],ctx=structuredClone(context),busy=false,commands=[],reopened=[];
globalThis.fetch=async()=>({ok:true,json:async()=>await queue.shift()});
const settings={owner,getContext:()=>ctx,busy:()=>busy,setBusy:v=>busy=v,api:async(route,body)=>{assert.equal(busy,false);commands.push(body);return true;},reopen:pc=>reopened.push(pc)};
const tree=n=>[n,...n.children.flatMap(tree)],button=(h,id)=>tree(h).find(n=>n.dataset.controllerBranchAction===id);
async function mount(){ctx=structuredClone(context);const host=new Node();queue=[snapshot()];const c=mountControllerBranches(host,settings);assert.equal(await c.ready,true);return {host,c};}
let {host,c}=await mount();const selects=tree(host).filter(n=>Object.hasOwn(n,'onchange'));selects[1].value='5';selects[1].onchange();queue=[proposal()];assert.equal(await button(host,'review').onclick(),true);assert.equal(commands.length,0);assert.equal(await button(host,'apply').onclick(),true);assert.equal(commands[0].type,'set_controller_branch');assert.equal(reopened[0],5);c.dispose();
({host,c}=await mount());let resolve;queue=[new Promise(r=>resolve=r)];tree(host).filter(n=>Object.hasOwn(n,'onchange'))[1].value='5';const late=button(host,'review').onclick();ctx.scriptKey='f'.repeat(64);c.updateState();resolve(proposal());assert.equal(await late,false);assert.equal(button(host,'apply').disabled,true);assert.equal(busy,false);c.dispose();
console.log('Controller branch source/Review refusal, actor isolation, typed Apply and stale response checks passed.');

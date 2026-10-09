import {scriptFlowReportHash} from './script-flow-identity.js';
export {scriptFlowReportHash} from './script-flow-identity.js';
import {createScriptWalkthrough,mountScriptWalkthrough} from './script-walkthrough.js';
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const object=v=>v&&typeof v==='object'&&!Array.isArray(v);
async function createLayer({snapshot,review,kind,context,projectSourceKey},controller=false){
 const owner=snapshot?.owner_id,script=typeof owner==='string'?owner.replace(/^scene:\/\//,'script://'):null;
 if(!['current','proposed'].includes(kind)||!hash(projectSourceKey)||!hash(snapshot?.source_record_sha256)||snapshot?.state_key!==context?.scriptKey||!hash(context?.scriptKey)||typeof context?.projectPath!=='string'||!context.projectPath||!/^scene:\/\/[A-Za-z0-9_-]+$/.test(context.sceneId)||typeof owner!=='string'||!owner.startsWith(context.sceneId+'/')||!(controller?owner===context.sceneId+'/controllers/man-p1/0000':/^scene:\/\/[A-Za-z0-9_-]+\/(actors\/man-p1|scripts\/man-p2)\/[0-9]{4}$/.test(owner)))throw Error('Current walkthrough source ownership changed.');
 const report=kind==='current'?snapshot.current_report:review?.proposed_report;
 if(!report||!snapshot.current_report)throw Error('This walkthrough flow layer is unavailable.');
 if(kind==='proposed'&&(!hash(review?.review_key)||!snapshot.targets?.some(r=>r.semantic_id===review.branch_id)||!(review.value===null||object(review.value)&&Object.keys(review.value).length===1&&Number.isSafeInteger(review.value.target_pc)&&review.value.target_pc>=0&&review.value.target_pc<=32767)))throw Error('Choose an independently reviewed branch proposal.');
 createScriptWalkthrough(report);const digest=await scriptFlowReportHash(report);
 return structuredClone({report,context:{project_path:context.projectPath,scene_id:context.sceneId,script_id:script,project_source_key:projectSourceKey,record_sha256:snapshot.source_record_sha256,representation:kind==='current'?'authored_current':'reviewed_proposed',flow_proof:{state_key:snapshot.state_key,report_sha256:digest,review_key:kind==='proposed'?review.review_key:null,branch_id:kind==='proposed'?review.branch_id:null,branch_value:kind==='proposed'?review.value:null}}});
}
export function createBranchWalkthroughLayer(args){return createLayer(args);}
export async function createControllerBranchWalkthroughLayer(args){
 if(args.context?.mode!=='edit'||args.snapshot?.schema_version!=='legaia.controller-branches.v1'||args.snapshot.gameplay_verified!==false||!hash(args.snapshot.current_record_sha256)||args.kind==='proposed'&&(args.review?.schema_version!==args.snapshot.schema_version||args.review.owner_id!==args.snapshot.owner_id||args.review.state_key!==args.snapshot.state_key||args.review.source_record_sha256!==args.snapshot.source_record_sha256||args.review.current_record_sha256!==args.snapshot.current_record_sha256||args.review.project_changed!==false||args.review.gameplay_verified!==false))throw Error('Controller walkthrough source or reviewed proposal changed.');
 return createLayer({...args,review:args.review?{...args.review,branch_id:args.review.operand_id}:null},true);
}
const actorProtocol={layer:createBranchWalkthroughLayer,snapshotRoute:'/api/script-branches',reviewRoute:'/api/script-branch-review',reviewField:'branch_id',projectKey:'project_copy_source_key',stateKey:'script_authoring_state_key',sandbox:true};
const controllerProtocol={layer:createControllerBranchWalkthroughLayer,snapshotRoute:'/api/controller-branches',reviewRoute:'/api/controller-branch-review',reviewField:'operand_id',projectKey:'asset_reference_source_key',stateKey:'controller_branch_source_key',sandbox:false};
export function mountScriptBranchWalkthrough(host,options){return mountBranchWalkthrough(host,options,actorProtocol);}
export function mountControllerBranchWalkthrough(host,options){return mountBranchWalkthrough(host,options,controllerProtocol);}
function mountBranchWalkthrough(host,{owner,getContext,getProjectSourceKey,current,busy,selection,selectInstruction,request,decodeSnapshot,decodeReview,onError=()=>{}},protocol){
 const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;},section=el('section'),tools=el('div'),openCurrent=el('button','Walk through Current flow'),openProposed=el('button','Walk through reviewed Proposed flow'),status=el('p'),body=el('div');section.dataset.branchWalkthrough='';tools.className='script-walkthrough-tools';openCurrent.type=openProposed.type='button';status.setAttribute('role','status');tools.append(openCurrent,openProposed);section.append(tools,status,body);host.append(section);
 let snapshot=null,review=null,view=null,held=null,disposed=false,pending=false,generation=0;
 function available(){return !disposed&&current()&&hash(getProjectSourceKey());}
 function updateState(){const enabled=available()&&!busy()&&!pending;openCurrent.disabled=!enabled||!snapshot?.current_report;openProposed.disabled=!enabled||!review;}
 function clear(message){generation++;view?.dispose();view=null;held=null;body.replaceChildren();if(message)status.textContent=message;}
 function sync(nextSnapshot,nextReview){
  if(disposed)return;if(held&&(!available()||held.snapshot!==nextSnapshot||held.kind==='proposed'&&held.reviewKey!==nextReview?.review_key))clear('The inspected flow or review changed. Start a new walkthrough.');
  snapshot=nextSnapshot;review=nextReview;updateState();
 }
 async function open(kind){
  updateState();if((kind==='current'?openCurrent:openProposed).disabled)return;const ticket=++generation,s=snapshot,r=kind==='proposed'?review:null,ctx=structuredClone(getContext()),key=getProjectSourceKey();pending=true;updateState();
  try{const descriptor=await protocol.layer({snapshot:s,review:r,kind,context:ctx,projectSourceKey:key});if(disposed||ticket!==generation||!available()||s!==snapshot||kind==='proposed'&&r?.review_key!==review?.review_key)return;
   view?.dispose();body.replaceChildren();held={snapshot:s,kind,reviewKey:r?.review_key??null};
   const owns=()=>available()&&snapshot===s&&(kind!=='proposed'||review?.review_key===r.review_key);
   const context=()=>({...descriptor.context,project_path:getContext().projectPath,scene_id:getContext().sceneId,project_source_key:getProjectSourceKey(),flow_proof:{...descriptor.context.flow_proof,state_key:getContext().scriptKey}});
   view=mountScriptWalkthrough(body,{report:descriptor.report,getContext:context,current:owns,busy,selection,selectInstruction,includeFlagSandbox:protocol.sandbox,label:kind==='current'?'Walk through Current instructions':'Walk through reviewed Proposed instructions',onError,
    requalify:async({signal})=>{
     const fresh=decodeSnapshot(await request(protocol.snapshotRoute,{entity:owner},signal),owner,getContext());let report=fresh.current_report;
     if(kind==='proposed'){const value=decodeReview(await request(protocol.reviewRoute,{entity:owner,[protocol.reviewField]:r.branch_id??r.operand_id,value:r.value},signal),fresh,r.branch_id??r.operand_id,r.value,getContext());if(value.review.review_key!==r.review_key)throw Error('Reviewed branch recipe changed.');report=value.review.proposed_report;}
     if(!owns()||fresh.source_record_sha256!==descriptor.context.record_sha256||await scriptFlowReportHash(report)!==descriptor.context.flow_proof.report_sha256)throw Error('Authored walkthrough flow changed.');
     const response=await fetch('/api/state',{signal}),state=await response.json();if(!response.ok||!owns()||state.project?.path!==descriptor.context.project_path||state.scene?.id!==descriptor.context.scene_id||state.project?.mode!==ctx.mode||state[protocol.projectKey]!==descriptor.context.project_source_key||state[protocol.stateKey]!==descriptor.context.flow_proof.state_key)throw Error('Authoritative walkthrough project changed.');return true;
    }});view.section.open=true;status.textContent=kind==='current'?'Current decoded flow includes inherited and authored values. Retail record hash is retained as provenance.':'Independently reviewed Proposed decoded flow. Apply has not occurred.';
  }catch(error){if(!disposed&&ticket===generation){clear('Walkthrough flow could not be qualified.');onError(error);}}finally{pending=false;if(!disposed)updateState();}
 }
 openCurrent.onclick=()=>open('current');openProposed.onclick=()=>open('proposed');updateState();
 return {sync,updateState,dispose(){if(disposed)return;disposed=true;clear();section.remove();}};
}

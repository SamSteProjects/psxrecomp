import {CONTROLLER_SNAPSHOT_SCHEMAS} from './controller-workspace-snapshot.js';
import {canonicalScriptMetadata,scriptFlowReportHash} from './script-flow-identity.js';
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const same=(a,b)=>JSON.stringify(canonicalScriptMetadata(a))===JSON.stringify(canonicalScriptMetadata(b));
const int=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const words=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(w=>int(w,-32768,32767));
const operands={
 ControllerSystemFlags:['system-flag',v=>exact(v,['index'])&&int(v.index,0,4095)],
 ControllerBranches:['branch',v=>exact(v,['target_pc'])&&int(v.target_pc,0,32767)],
 ControllerTileRects:['tile-rect',v=>exact(v,['column_start','row_start','column_end','row_end','value'])&&['column_start','row_start','column_end','row_end','value'].every(k=>int(v[k],0,255))],
 ControllerFades:['fade',v=>exact(v,['selector','signed_words'])&&int(v.selector,0,255)&&words(v.signed_words,3)],
 ControllerTableCopies:['table-copy',v=>exact(v,['signed_words'])&&words(v.signed_words,16)],
 ControllerWordTriplets:['word-triplet',v=>exact(v,['selector','signed_words'])&&int(v.selector,0,255)&&words(v.signed_words,3)],
 ControllerThreeWords:['three-word',v=>exact(v,['signed_words'])&&words(v.signed_words,3)],
 ControllerFiveWords:['five-word',v=>exact(v,['signed_words'])&&words(v.signed_words,5)],
 ControllerGlobalBytes:['global-byte',v=>exact(v,['byte_values','parameters_i16'])&&Array.isArray(v.byte_values)&&v.byte_values.length===4&&v.byte_values.every(b=>int(b,0,255))&&words(v.parameters_i16,2)],
 ControllerBgm:['bgm',v=>exact(v,['encoded_id'])&&int(v.encoded_id,0,65535)],
 ControllerSceneBytes:['scene-byte',v=>exact(v,['value'])&&int(v.value,0,255)],
 ControllerPartySelectors:['party-selector',v=>exact(v,['party_selector'])&&int(v.party_selector,0,7)],
 ControllerFlagBits:['flag-bit',v=>exact(v,['bit'])&&int(v.bit,0,31)],
};
const keys=['schema_version','owner_id','scene_id','component','representation','state_key','source_import_sha256','source_record_sha256','current_record_sha256','effective_record_sha256','operand_id','value','review_key','report_sha256','read_only','project_changed','runtime_execution','gameplay_verified','source_key'];
export function validateControllerFlowProof(value){
 const fail=()=>{throw Error('Controller operand flow provenance is invalid.');};
 if(!exact(value,keys)||value.schema_version!=='legaia.controller-flow-source.v1'||!/^scene:\/\/[A-Za-z0-9_-]+$/.test(value.scene_id)||value.owner_id!==value.scene_id+'/controllers/man-p1/0000'||!Object.hasOwn(operands,value.component)||!Object.hasOwn(CONTROLLER_SNAPSHOT_SCHEMAS,value.component)||!['authored_current','reviewed_proposed'].includes(value.representation)||!['state_key','source_import_sha256','source_record_sha256','current_record_sha256','effective_record_sha256','report_sha256','source_key'].every(k=>hash(value[k]))||value.read_only!==true||value.project_changed!==false||value.runtime_execution!=='not_asserted'||value.gameplay_verified!==false)fail();
 if(value.representation==='authored_current'){
  if(value.operand_id!==null||value.value!==null||value.review_key!==null||value.effective_record_sha256!==value.current_record_sha256)fail();
 }else{
  const [suffix,valid]=operands[value.component],prefix=value.owner_id.replace('scene://','script://')+'/'+suffix+'/';
  if(!hash(value.review_key)||typeof value.operand_id!=='string'||!value.operand_id.startsWith(prefix)||!/^[a-f0-9]{4}$/.test(value.operand_id.slice(prefix.length))||!(value.value===null||valid(value.value)))fail();
 }
 return structuredClone(value);
}
export async function decodeControllerFlowSource(raw,{snapshot,review=null,kind,context,projectSourceKey}){
 if(!exact(raw,[...keys,'report']))throw Error('Controller flow source response has unexpected fields.');
 const {report,...receipt}=raw,proof=validateControllerFlowProof(receipt);
 const component=Object.keys(CONTROLLER_SNAPSHOT_SCHEMAS).find(k=>CONTROLLER_SNAPSHOT_SCHEMAS[k]===snapshot?.schema_version),proposed=kind==='proposed';
 if(!['current','proposed'].includes(kind)||context?.mode!=='edit'||!hash(projectSourceKey)||proof.owner_id!==snapshot.owner_id||proof.scene_id!==context.sceneId||proof.component!==component||proof.state_key!==context.scriptKey||proof.state_key!==snapshot.state_key||proof.source_record_sha256!==snapshot.source_record_sha256||proof.current_record_sha256!==snapshot.current_record_sha256||proof.representation!==(proposed?'reviewed_proposed':'authored_current')||proof.report_sha256!==await scriptFlowReportHash(report)||!same(report,proposed?review?.proposed_report:snapshot.current_report))throw Error('Controller flow source differs from the selected layer.');
 if(proposed&&(review?.owner_id!==snapshot.owner_id||review?.schema_version!==snapshot.schema_version||review?.state_key!==snapshot.state_key||review?.source_record_sha256!==snapshot.source_record_sha256||review?.current_record_sha256!==snapshot.current_record_sha256||review?.project_changed!==false||review?.gameplay_verified!==false||proof.operand_id!==review?.operand_id||!same(proof.value,review?.value)||proof.review_key!==review?.review_key||proof.effective_record_sha256!==review?.proposed_record_sha256))throw Error('Controller flow source differs from its reviewed operands.');
 return {report:structuredClone(report),context:{project_path:context.projectPath,scene_id:proof.scene_id,script_id:proof.owner_id.replace('scene://','script://'),project_source_key:projectSourceKey,record_sha256:proof.source_record_sha256,representation:proof.representation,controller_flow_proof:proof}};
}

// Obtain provenance on Save/Load, leaving ordinary hypothetical stepping local.
export function controllerScenarioBindings({snapshot,review,kind,getContext,current}){
 let descriptor=null;
 const component=Object.keys(CONTROLLER_SNAPSHOT_SCHEMAS).find(k=>CONTROLLER_SNAPSHOT_SCHEMAS[k]===snapshot.schema_version);
 async function request(url,options){const response=await fetch(url,options),raw=await response.json();if(!response.ok||raw.error)throw Error(raw.error||'Controller scenario source could not be verified.');return raw;}
 async function qualify(signal){
  if(!current())throw Error('Controller simulation source changed.');
  const context=structuredClone(getContext()),state=await request('/api/state',{signal});
  const owns=s=>current()&&s.project?.mode==='edit'&&context.mode==='edit'&&s.project?.path===context.projectPath&&s.scene?.id===context.sceneId&&s.controller_branch_source_key===context.scriptKey&&same(context,getContext());
  if(!owns(state)||!hash(state.asset_reference_source_key))throw Error('Authoritative controller scenario project changed.');
  const body={entity:snapshot.owner_id,component,layer:kind,expected_source_key:context.scriptKey,...(kind==='proposed'?{operand_id:review.operand_id,value:review.value,review_key:review.review_key}:{})};
  const raw=await request('/api/controller-flow-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
  const value=await decodeControllerFlowSource(raw,{snapshot,review,kind,context,projectSourceKey:state.asset_reference_source_key});
  const after=await request('/api/state',{signal});
  if(!owns(after)||after.asset_reference_source_key!==state.asset_reference_source_key)throw Error('Controller scenario source changed during qualification.');
  return value;
 }
 return {getContext:()=>descriptor?.context??null,prepareScenario:async({signal})=>{const value=await qualify(signal);descriptor=value;return structuredClone(value.context);},requalify:async({signal})=>{const value=await qualify(signal);if(!descriptor||!same(value.context,descriptor.context))throw Error('Controller scenario receipt changed.');return true;}};
}

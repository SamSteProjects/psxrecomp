import {mountControllerSystemSelectors} from './system-flag-selectors.js';
import {mountScriptWalkthrough} from './script-walkthrough.js';
import {mountScriptFlowOverview} from './script-flow-overview.js';
import {decodeControllerFlags,renderControllerFlags} from './controller-flags.js';
export function decodeSceneController(value,scene,key){
 const fail=()=>{throw Error('Scene controller source or record ownership changed.');},int=v=>Number.isSafeInteger(v)&&v>=0,hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),source=value?.source_record,record=value?.record;
 if(value?.schema_version!=='legaia.scene-controller-inspection.v1'||value.scene_id!==scene||value.source_key!==key||!hash(key)||value.semantic_id!=='script://'+scene.slice(8)+'/controllers/man-p1/0000'||value.read_only!==true||value.representation!=='retail'||value.runtime_execution!=='not_asserted'||source?.record_kind!=='man_partition_1_scene_controller'||source.record_index!==0||source.byte_coordinate_space!=='decoded_man_payload'||source.iso_file!=='PROT.DAT'||!/^sha256:[a-f0-9]{64}$/.test(source.disc_identity)||!hash(source.sha256)||!int(source.byte_offset)||!int(source.byte_length)||!source.byte_length||source.byte_length>65536||!int(source.containing_decoded_size)||source.byte_offset+source.byte_length>source.containing_decoded_size||!int(record?.local_count)||record.local_count>255||record.script_offset!==1+record.local_count*2+4||value.entry_pc!==record.script_offset||value.entry_pc>=source.byte_length||typeof record.raw_hex!=='string'||record.raw_hex.length!==source.byte_length*2||!/^[a-f0-9]+$/.test(record.raw_hex)||parseInt(record.raw_hex.slice(0,2),16)!==record.local_count||!Array.isArray(value.instructions)||value.instructions.length>4096||!Array.isArray(value.dialogues)||value.dialogues.length>4096||!Array.isArray(value.stops)||!Array.isArray(value.limitations))fail();
 decodeControllerFlags(value);
 return structuredClone(value);
}

export function qualifySceneControllerAsset(report,asset){
 const data=asset?.data,source=data?.source_record;
 if(asset?.type!=='controller'||asset.id!==report.semantic_id||asset.sceneId!==report.scene_id||data?.owner_scene_id!==report.scene_id||data?.read_only!==true||data?.runtime_binding!=='not_asserted'||data?.entry_pc!==report.entry_pc||data?.local_count!==report.record.local_count||data?.inspection_status!==report.status||data?.decoded_instruction_count!==report.instructions.length||data?.dialogue_segment_count!==report.dialogues.length||data?.flag_reference_count!==report.flag_reference_count||JSON.stringify(data?.flag_references)!==JSON.stringify(report.flag_references)||data?.reference_commit!==report.reference_commit||!source||Object.entries(report.source_record).some(([key,value])=>source[key]!==value))throw Error('Controller asset source changed. Refresh resources.');
 return true;
}

export async function openSceneController({getState,busy,expectedAsset=null,focusFlagPc=null,api=null,setBusy=null,onError=()=>{}}){
 const initial=getState(),scene=initial.scene?.id,key=initial.asset_reference_source_key,projectPath=initial.project?.path;
 if(busy()||!scene||initial.project?.mode!=='edit'||!key)return;
 const dialog=document.createElement('dialog');dialog.id='scene-controller-dialog';dialog.style.cssText='width:min(850px,calc(100vw - 32px));max-height:90vh;overflow:auto';
 const heading=document.createElement('h2');heading.textContent='Retail Scene Entry Controller';
 const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying the scene controller source…';
 const content=document.createElement('div');content.style.overflowWrap='anywhere';dialog.append(heading,close,status,content);document.body.append(dialog);dialog.showModal();
 let flow=null,walkthrough=null,selectors=null,selectedSource=null;const sourceRows=new Map();
 const controller=new AbortController(),fresh=()=>dialog.open&&getState().project?.path===projectPath&&getState().scene?.id===scene&&getState().asset_reference_source_key===key&&getState().project?.mode==='edit';
 const timer=setInterval(()=>{if(!fresh()&&!busy()){selectors?.dispose();selectors=null;flow?.dispose();flow=null;walkthrough?.dispose();walkthrough=null;sourceRows.clear();selectedSource=null;content.replaceChildren();status.textContent='Scene sources changed. Reopen controller inspection.';}selectors?.updateState();},250);
 dialog.addEventListener('close',()=>{clearInterval(timer);controller.abort();selectors?.dispose();flow?.dispose();walkthrough?.dispose();sourceRows.clear();dialog.remove();},{once:true});
 try{
  const response=await fetch('/api/scene-controller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Controller inspection failed');if(!fresh())return;
  const report=decodeSceneController(value,scene,key);if(expectedAsset)qualifySceneControllerAsset(report,expectedAsset);status.textContent=`${report.semantic_id} · Decoder status: ${report.status} · ${report.instructions.length} decoded instructions · ${report.dialogues.length} dialogue segments`;
  for(const note of report.limitations){const p=document.createElement('p');p.textContent=note;content.append(p);}
  const source=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Controller source and entry evidence';pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify({source_record:report.source_record,man_source:report.man_source,entry_pc:report.entry_pc,local_count:report.record.local_count,reference_commit:report.reference_commit},null,2);source.append(summary,pre);content.append(source);
  const sourceSelection=document.createElement('p');sourceSelection.setAttribute('role','status');sourceSelection.dataset.controllerSourceSelection='';sourceSelection.textContent='Select a decoded source boundary to inspect its evidence.';content.append(sourceSelection);
  const selectSource=(pc,reveal=true)=>{if(!fresh()||busy())return false;const target=sourceRows.get(pc);if(!target)return false;if(selectedSource){selectedSource.open=false;selectedSource.removeAttribute('data-controller-source-selected');selectedSource.style.borderLeft='';}selectedSource=target;target.dataset.controllerSourceSelected='true';target.style.borderLeft='3px solid #62c0b4';target.open=true;sourceSelection.textContent='Selected source PC 0x'+pc.toString(16).padStart(4,'0')+' · encoded evidence only';if(reveal){target.querySelector('summary')?.scrollIntoView({block:'start'});target.querySelector('summary')?.focus({preventScroll:true});}return true;};
  flow=mountScriptFlowOverview(content,{label:'Retail controller encoded flow · '+(report.status==='partial'?'partial source':'supported decoded paths'),selectInstruction:selectSource});if(!flow.update(report))throw Error('Controller decoded flow boundaries are not qualified.');
  const context=()=>({project_path:getState().project?.path,scene_id:getState().scene?.id,script_id:report.semantic_id,project_source_key:getState().asset_reference_source_key,record_sha256:report.source_record.sha256,representation:'retail_source'});
  walkthrough=mountScriptWalkthrough(content,{report,getContext:context,selection:()=>selectedSource?Number(selectedSource.dataset.controllerSourcePc):null,selectInstruction:selectSource,current:fresh,busy,includeFlagSandbox:false,label:'Walk through Retail controller source',onError,
   requalify:async({signal})=>{
    if(!fresh())return false;
    const response=await fetch('/api/scene-controller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal}),value=await response.json();
    if(!response.ok||value.error||!fresh())return false;
    const verified=decodeSceneController(value,scene,key);if(expectedAsset)qualifySceneControllerAsset(verified,expectedAsset);
    if(JSON.stringify(verified)!==JSON.stringify(report))return false;
    const stateResponse=await fetch('/api/state',{signal}),state=await stateResponse.json();
    return stateResponse.ok&&fresh()&&state.project?.path===projectPath&&state.project?.mode==='edit'&&state.scene?.id===scene&&state.asset_reference_source_key===key;
   }});
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_selector_authoring){
   selectors=mountControllerSystemSelectors(content,{owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_selector_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
  }
  const focusedFlag=renderControllerFlags(content,report,focusFlagPc);
  for(const [title,rows] of [['Encoded instructions',report.instructions],['Dialogue segments',report.dialogues],['Opaque regions',report.opaque_regions],['Inspection stops',report.stops]]){const heading=document.createElement('h3');heading.textContent=title;content.append(heading);if(!rows?.length){const p=document.createElement('p');p.textContent='None reported';content.append(p);}for(const row of rows??[]){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');const pc=Number.isSafeInteger(row.pc)?'PC 0x'+row.pc.toString(16).padStart(4,'0'):'Source region';summary.textContent=pc+' · '+(row.mnemonic??row.reason??(title==='Dialogue segments'?'Dialogue segment':'Source evidence'));pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify(row,null,2);details.append(summary,pre);if(['Encoded instructions','Dialogue segments'].includes(title)){details.dataset.controllerSourcePc=row.pc;sourceRows.set(row.pc,details);}content.append(details);}}
  focusedFlag?.scrollIntoView({block:'nearest'});
 }catch(error){if(dialog.open&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
}

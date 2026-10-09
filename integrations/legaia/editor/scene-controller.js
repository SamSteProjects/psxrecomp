import {mountSourceBuildScript} from './source-build-script.js';
import {mountControllerOperandComparison} from './controller-operand-comparison.js';
import {mountScriptBookmarks,qualifyScriptBookmark} from './script-bookmarks.js';
import {mountControllerOperandFiles} from './controller-operand-files.js';
import {mountControllerComponentReset} from './controller-component-reset.js';
import {mountControllerPartySelectors} from './controller-party-selectors.js';
import {mountControllerFlagBits} from './controller-flag-bits.js';
import {mountControllerAuthoringNavigator} from './controller-authoring-navigator.js';
import {decodeControllerWorkspaceSnapshot} from './controller-workspace-snapshot.js';
import {mountControllerGlobalBytes} from './controller-global-bytes.js';
import {mountControllerFiveWords} from './controller-five-words.js';
import {mountControllerBgm} from './controller-bgm.js';
import {mountControllerSceneBytes} from './controller-scene-bytes.js';
import {mountControllerThreeWords} from './controller-three-words.js';
import {mountControllerWordTriplets} from './controller-word-triplets.js';
import {mountControllerBranches} from './controller-branches.js';
import {mountControllerTables} from './controller-tables.js';
import {mountControllerFades} from './controller-fades.js';
import {mountControllerTileRects} from './controller-tile-rects.js';
import {mountControllerSystemSelectors} from './system-flag-selectors.js';
import {mountScriptWalkthrough} from './script-walkthrough.js';
import {mountScriptFlowOverview} from './script-flow-overview.js';
import {decodeControllerFlags,renderControllerFlags} from './controller-flags.js';
import {appendCaptureSummary} from './script-capture.js';
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

export function renderControllerInstruction(row,report,selectSource,authoring=[]){
 const pc=value=>'0x'+value.toString(16).toUpperCase().padStart(4,'0');
 const create=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
 if(!Number.isSafeInteger(row.pc)||row.pc<report.entry_pc||!Number.isSafeInteger(row.length)||row.length<1||row.pc+row.length>report.source_record.byte_length||row.byte_offset!==report.source_record.byte_offset+row.pc||row.raw_hex!==report.record.raw_hex.slice(row.pc*2,(row.pc+row.length)*2))throw Error('Controller instruction bytes differ from their source record.');
 const details=create('details'),summary=create('summary',`PC ${pc(row.pc)} · ${row.mnemonic}`),fields=create('dl');details.dataset.controllerInstructionPc=row.pc;fields.dataset.controllerInstructionFields='';
 const field=(name,value)=>{const label=create('dt',name),text=create('dd',String(value));label.style.fontWeight='600';text.style.cssText='margin:0 0 8px;overflow-wrap:anywhere';fields.append(label,text);};
 field('Record PC',`${pc(row.pc)} (${row.pc})`);field('Decoded MAN Offset',`${pc(row.byte_offset)} (${row.byte_offset})`);field('Encoded Length',`${row.length} bytes`);field('Dispatch Context',row.target_context===null?'Current controller context':`Extended target ${row.target_context} · runtime binding unresolved`);
 const human=value=>value.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()).replace(/\bPc\b/g,'PC').replace(/\bVram\b/g,'VRAM');
 const flatten=(value,path,depth=0)=>{
  if(depth>8)throw Error('Controller operand nesting exceeds inspector bounds.');
  if(Array.isArray(value)){field(path,value.map(item=>typeof item==='object'?JSON.stringify(item):String(item)).join(', ')||'None');return;}
  if(value!==null&&typeof value==='object'){for(const [name,child] of Object.entries(value)){if(name==='encoded_hex')continue;flatten(child,path?path+' / '+human(name):human(name),depth+1);}return;}
  field(path,value===null?'Unresolved':typeof value==='boolean'?(value?'Yes':'No'):typeof value==='string'?value.replaceAll('_',' '):value);
 };
 flatten(row.operands,'');details.append(summary,create('p','Retail encoded source. Runtime execution and effects have not been verified.'),fields);
 appendCaptureSummary(details,row);
 const navigation=create('div');navigation.dataset.controllerInstructionSuccessors='';navigation.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
 const boundaries=new Set([...report.instructions,...report.dialogues].map(node=>node.pc));
 for(const edge of row.successors){
  const button=create('button',`Inspect ${pc(edge.pc)} · ${(edge.condition??'Encoded successor').replaceAll('_',' ')}`);button.type='button';button.dataset.controllerInstructionNextPc=edge.pc;button.disabled=!boundaries.has(edge.pc);button.onclick=()=>{if(!button.disabled)selectSource(edge.pc);};navigation.append(button);
  if(button.disabled)navigation.append(create('p',`Boundary ${pc(edge.pc)} is not decoded. No instruction is inferred.`));
 }
 if(!row.successors.length)navigation.append(create('p','No encoded successors reported. Runtime resumption remains unresolved.'));
 for(const control of authoring){if(!control.canFocus(row.pc))continue;const edit=create('button','Open '+control.label+' Controls');edit.type='button';edit.dataset.controllerInstructionEditPc=row.pc;edit.dataset.controllerInstructionEditKind=control.kind;edit.onclick=()=>control.focusPc(row.pc);navigation.append(edit);}
 const evidence=create('details'),pre=create('pre',JSON.stringify(row,null,2));evidence.dataset.controllerInstructionEvidence='';pre.style.whiteSpace='pre-wrap';evidence.append(create('summary','Raw Instruction Evidence'),pre);details.append(navigation,evidence);return details;
}

export function controllerInstructionMatches(row,query){
 const terms=query.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const operands=JSON.stringify(row.operands, (key,value)=>key==='encoded_hex'?undefined:value);
 const text=`${row.mnemonic} ${operands}`.toLowerCase().replaceAll('_',' ');
 return terms.every(term=>{
  if(term.startsWith('pc:')){const value=term.slice(3);return /^(?:0x[a-f0-9]+|\d+)$/.test(value)&&Number(value)===row.pc;}
  return text.includes(term.replaceAll('_',' '));
 });
}

export function mountControllerInstructionFilter(host,{rows,rowElements,current,busy,onHidden=()=>{}}){
 const input=document.createElement('input'),label=document.createElement('label'),count=document.createElement('p'),clear=document.createElement('button'),note=document.createElement('p');
 input.type='search';input.maxLength=256;input.id='controller-instruction-search';input.style.cssText='width:100%;box-sizing:border-box';input.placeholder='Mnemonic or operand; pc:0x0091 for an exact PC';label.htmlFor=input.id;label.textContent='Search Decoded Instructions';
 clear.type='button';clear.textContent='Clear Instruction Filter';count.setAttribute('role','status');count.dataset.controllerInstructionCount='';note.textContent='Search covers decoded instructions only. Dialogue, opaque regions and inspection stops remain separate. Flow navigation clears the filter to reveal its target.';host.append(label,input,clear,count,note);
 const render=()=>{let visible=0;for(const row of rows){const element=rowElements.get(row.pc);element.hidden=!controllerInstructionMatches(row,input.value);if(!element.hidden)visible++;else onHidden(row.pc);}count.textContent=`Showing ${visible} of ${rows.length} decoded instructions`;clear.disabled=!input.value||!current()||busy();};
 const reset=()=>{if(!current()||busy())return false;input.value='';render();return true;};
 input.oninput=()=>{if(current()&&!busy())render();};clear.onclick=reset;
 const updateState=()=>{input.disabled=!current()||busy();clear.disabled=!input.value||input.disabled;};
 render();updateState();return {reset,updateState};
}

export async function openSceneController({getState,busy,expectedAsset=null,focusFlagPc=null,focusBookmark=null,api=null,setBusy=null,onError=()=>{}}){
 const initial=getState(),scene=initial.scene?.id,key=initial.asset_reference_source_key,projectPath=initial.project?.path;
 if(busy()||!scene||initial.project?.mode!=='edit'||!key)return;
 const dialog=document.createElement('dialog');dialog.id='scene-controller-dialog';dialog.style.cssText='width:min(850px,calc(100vw - 32px));max-height:90vh;overflow:auto';
 const heading=document.createElement('h2');heading.textContent='Retail Scene Entry Controller';
 const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying the scene controller source…';
 const content=document.createElement('div');content.style.overflowWrap='anywhere';dialog.append(heading,close,status,content);document.body.append(dialog);dialog.showModal();
 let flow=null,walkthrough=null,selectors=null,branches=null,tiles=null,fades=null,tables=null,triplets=null,threeWords=null,bgm=null,sceneBytes=null,partySelectors=null,flagBits=null,fiveWords=null,globalBytes=null,instructionFilter=null,authoringNavigator=null,componentReset=null,operandFiles=null,bookmarks=null,comparison=null,savedBuild=null,selectedSource=null;const sourceRows=new Map(),authoringButtons=new Map();
 const controller=new AbortController(),fresh=()=>dialog.open&&getState().project?.path===projectPath&&getState().scene?.id===scene&&getState().asset_reference_source_key===key&&getState().project?.mode==='edit';
 const timer=setInterval(()=>{if(!fresh()&&!busy()){savedBuild?.dispose();savedBuild=null;comparison?.dispose();comparison=null;bookmarks?.dispose();bookmarks=null;operandFiles?.dispose();operandFiles=null;componentReset?.dispose();componentReset=null;selectors?.dispose();selectors=null;branches?.dispose();branches=null;tiles?.dispose();tiles=null;fades?.dispose();fades=null;tables?.dispose();tables=null;triplets?.dispose();triplets=null;threeWords?.dispose();threeWords=null;bgm?.dispose();sceneBytes?.dispose();bgm=null;sceneBytes=null;partySelectors?.dispose();partySelectors=null;flagBits?.dispose();flagBits=null;fiveWords?.dispose();fiveWords=null;globalBytes?.dispose();globalBytes=null;flow?.dispose();flow=null;walkthrough?.dispose();walkthrough=null;sourceRows.clear();authoringButtons.clear();selectedSource=null;instructionFilter=null;authoringNavigator=null;content.replaceChildren();status.textContent='Scene sources changed. Reopen controller inspection.';}selectors?.updateState();branches?.updateState();tiles?.updateState();fades?.updateState();tables?.updateState();triplets?.updateState();threeWords?.updateState();bgm?.updateState();sceneBytes?.updateState();partySelectors?.updateState();flagBits?.updateState();fiveWords?.updateState();globalBytes?.updateState();instructionFilter?.updateState();authoringNavigator?.updateState();componentReset?.updateState();operandFiles?.updateState();bookmarks?.updateState();comparison?.updateState();savedBuild?.updateState();for(const [button,control] of authoringButtons)button.disabled=!fresh()||busy()||!control.canFocus(Number(button.dataset.controllerInstructionEditPc));},250);
 dialog.addEventListener('close',()=>{clearInterval(timer);controller.abort();savedBuild?.dispose();comparison?.dispose();bookmarks?.dispose();operandFiles?.dispose();componentReset?.dispose();selectors?.dispose();branches?.dispose();tiles?.dispose();fades?.dispose();tables?.dispose();triplets?.dispose();threeWords?.dispose();bgm?.dispose();sceneBytes?.dispose();partySelectors?.dispose();flagBits?.dispose();fiveWords?.dispose();globalBytes?.dispose();flow?.dispose();walkthrough?.dispose();sourceRows.clear();authoringButtons.clear();dialog.remove();},{once:true});
 try{
  const response=await fetch('/api/scene-controller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Controller inspection failed');if(!fresh())return;
  const report=decodeSceneController(value,scene,key);if(expectedAsset)qualifySceneControllerAsset(report,expectedAsset);status.textContent=`${report.semantic_id} · Decoder status: ${report.status} · ${report.instructions.length} decoded instructions · ${report.dialogues.length} dialogue segments`;
  for(const note of report.limitations){const p=document.createElement('p');p.textContent=note;content.append(p);}
  const source=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Controller source and entry evidence';pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify({source_record:report.source_record,man_source:report.man_source,entry_pc:report.entry_pc,local_count:report.record.local_count,reference_commit:report.reference_commit},null,2);source.append(summary,pre);content.append(source);
  const sourceSelection=document.createElement('p');sourceSelection.setAttribute('role','status');sourceSelection.dataset.controllerSourceSelection='';sourceSelection.textContent='Select a decoded source boundary to inspect its evidence.';content.append(sourceSelection);
  const selectSource=(pc,reveal=true)=>{if(!fresh()||busy())return false;const target=sourceRows.get(pc);if(!target)return false;instructionFilter?.reset();if(selectedSource){selectedSource.open=false;selectedSource.removeAttribute('data-controller-source-selected');selectedSource.style.borderLeft='';}selectedSource=target;target.dataset.controllerSourceSelected='true';target.style.borderLeft='3px solid #62c0b4';target.open=true;sourceSelection.textContent='Selected source PC 0x'+pc.toString(16).padStart(4,'0')+' · encoded evidence only';bookmarks?.updateState();if(reveal){target.querySelector('summary')?.scrollIntoView({block:'start'});target.querySelector('summary')?.focus({preventScroll:true});}return true;};
  flow=mountScriptFlowOverview(content,{label:'Retail controller encoded flow · '+(report.status==='partial'?'partial source':'supported decoded paths'),selectInstruction:selectSource});if(!flow.update(report))throw Error('Controller decoded flow boundaries are not qualified.');
  const context=()=>({project_path:getState().project?.path,scene_id:getState().scene?.id,script_id:report.semantic_id,project_source_key:getState().asset_reference_source_key,record_sha256:report.source_record.sha256,representation:'retail_source'});
  walkthrough=mountScriptWalkthrough(content,{report,getContext:context,selection:()=>selectedSource?Number(selectedSource.dataset.controllerSourcePc):null,selectInstruction:selectSource,current:fresh,busy,includeFlagSandbox:true,label:'Walk through Retail controller source',onError,
   requalify:async({signal})=>{
    if(!fresh())return false;
    const response=await fetch('/api/scene-controller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal}),value=await response.json();
    if(!response.ok||value.error||!fresh())return false;
    const verified=decodeSceneController(value,scene,key);if(expectedAsset)qualifySceneControllerAsset(verified,expectedAsset);
    if(JSON.stringify(verified)!==JSON.stringify(report))return false;
    const stateResponse=await fetch('/api/state',{signal}),state=await stateResponse.json();
    return stateResponse.ok&&fresh()&&state.project?.path===projectPath&&state.project?.mode==='edit'&&state.scene?.id===scene&&state.asset_reference_source_key===key;
   }});
  let preloaded=null;
  if(typeof api==='function'&&typeof setBusy==='function'&&initial.capabilities?.controller_workspace_snapshot){
   if(busy())return;
   setBusy(true);
   try{
    const response=await fetch('/api/controller-workspace-snapshot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity:scene+'/controllers/man-p1/0000',expected_source_key:initial.controller_selector_source_key}),signal:controller.signal}),value=await response.json();
    if(!fresh())return;
    if(!response.ok||value.error)throw Error(value.error||'Controller workspace preload failed.');
    if(getState().controller_selector_source_key!==initial.controller_selector_source_key)throw Error('Controller workspace source changed during preload.');
    preloaded=decodeControllerWorkspaceSnapshot(value,scene+'/controllers/man-p1/0000',initial.controller_selector_source_key);
   }finally{setBusy(false);}
  }
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_selector_authoring){
   selectors=mountControllerSystemSelectors(content,{initialSnapshot:preloaded?.ControllerSystemFlags??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_selector_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
  }
  if(selectors)await selectors.ready;
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_branch_authoring){
   branches=mountControllerBranches(content,{initialSnapshot:preloaded?.ControllerBranches??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getProjectSourceKey:()=>getState().asset_reference_source_key,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_branch_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
  }
  if(branches)await branches.ready;
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_tile_authoring){
   tiles=mountControllerTileRects(content,{initialSnapshot:preloaded?.ControllerTileRects??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_tile_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await tiles.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_fade_authoring){
   fades=mountControllerFades(content,{initialSnapshot:preloaded?.ControllerFades??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_fade_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await fades.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_table_authoring){
   tables=mountControllerTables(content,{initialSnapshot:preloaded?.ControllerTableCopies??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_table_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await tables.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_word_triplet_authoring){
   triplets=mountControllerWordTriplets(content,{initialSnapshot:preloaded?.ControllerWordTriplets??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_word_triplet_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await triplets.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_three_word_authoring){
   threeWords=mountControllerThreeWords(content,{initialSnapshot:preloaded?.ControllerThreeWords??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_three_word_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await threeWords.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_party_selector_authoring){
   partySelectors=mountControllerPartySelectors(content,{initialSnapshot:preloaded?.ControllerPartySelectors??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_party_selector_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await partySelectors.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_flag_bit_authoring){
   flagBits=mountControllerFlagBits(content,{initialSnapshot:preloaded?.ControllerFlagBits??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_flag_bit_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await flagBits.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_bgm_authoring){
   bgm=mountControllerBgm(content,{initialSnapshot:preloaded?.ControllerBgm??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_bgm_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await bgm.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_scene_byte_authoring){
   sceneBytes=mountControllerSceneBytes(content,{initialSnapshot:preloaded?.ControllerSceneBytes??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_scene_byte_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await sceneBytes.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_five_word_authoring){
   fiveWords=mountControllerFiveWords(content,{initialSnapshot:preloaded?.ControllerFiveWords??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_five_word_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await fiveWords.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_global_byte_authoring){
   globalBytes=mountControllerGlobalBytes(content,{initialSnapshot:preloaded?.ControllerGlobalBytes??null,owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_global_byte_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await globalBytes.ready;
  }
  if(!fresh())return;
  const authoring=[[selectors,'selector','Selector'],[branches,'branch','Branch'],[tiles,'tile','Tile Request'],[fades,'fade','Fade'],[tables,'table','Table Copy'],[triplets,'word-triplet','Word-Triplet'],[threeWords,'three-word','Three-Word'],[bgm,'bgm','BGM Argument'],[sceneBytes,'scene-byte','Scene-State Byte'],[partySelectors,'party-selector','Party Selector'],[flagBits,'flag-bit','Flag Bit'],[fiveWords,'five-word','Five-Word'],[globalBytes,'global-byte','Global-Byte']].filter(([control])=>control).map(([control,kind,label])=>({kind,label,canFocus:pc=>fresh()&&!busy()&&control.canFocus(pc),focusPc:pc=>fresh()&&!busy()?control.focusPc(pc):false}));
  const focusedFlag=renderControllerFlags(content,report,focusFlagPc);
  const searchHost=document.createElement('section');content.append(searchHost);
  for(const [title,rows] of [['Encoded Instructions',report.instructions],['Dialogue Segments',report.dialogues],['Opaque Regions',report.opaque_regions],['Inspection Stops',report.stops]]){const heading=document.createElement('h3');heading.textContent=title;content.append(heading);if(!rows?.length){const p=document.createElement('p');p.textContent='None reported';content.append(p);}for(const row of rows??[]){let details;if(title==='Encoded Instructions')details=renderControllerInstruction(row,report,selectSource,authoring);else{details=document.createElement('details');const summary=document.createElement('summary'),pre=document.createElement('pre');const pc=Number.isSafeInteger(row.pc)?'PC 0x'+row.pc.toString(16).padStart(4,'0'):'Source region';summary.textContent=pc+' · '+(row.reason??(title==='Dialogue Segments'?'Dialogue segment':'Source evidence'));pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify(row,null,2);details.append(summary,pre);}if(['Encoded Instructions','Dialogue Segments'].includes(title)){details.dataset.controllerSourcePc=row.pc;sourceRows.set(row.pc,details);details.querySelector('summary').addEventListener('click',event=>{event.preventDefault();if(fresh()&&!busy())selectSource(row.pc,false);});}for(const edit of details.querySelectorAll('[data-controller-instruction-edit-pc]'))authoringButtons.set(edit,authoring.find(control=>control.kind===edit.dataset.controllerInstructionEditKind));content.append(details);}}
  instructionFilter=mountControllerInstructionFilter(searchHost,{rows:report.instructions,rowElements:sourceRows,current:fresh,busy,onHidden:pc=>{if(selectedSource&&Number(selectedSource.dataset.controllerSourcePc)===pc){selectedSource.open=false;selectedSource.removeAttribute('data-controller-source-selected');selectedSource.style.borderLeft='';selectedSource=null;sourceSelection.textContent='Selection hidden by the instruction filter. Select a visible source boundary.';bookmarks?.updateState();}}});
  authoringNavigator=mountControllerAuthoringNavigator(content,{rows:report.instructions,controls:authoring,current:fresh,busy,selectSource});
  if(preloaded)comparison=mountControllerOperandComparison(content,{snapshots:preloaded,owner:scene+'/controllers/man-p1/0000',context:{projectPath,sceneId:scene,mode:'edit',scriptKey:initial.controller_selector_source_key},current:fresh,busy,controls:authoring,sourcePcs:[...sourceRows.keys()],selectSource});
  if(preloaded&&getState().capabilities?.controller_component_reset)componentReset=mountControllerComponentReset(content,{families:preloaded,owner:scene+'/controllers/man-p1/0000',getKey:()=>getState().controller_selector_source_key,current:fresh,busy,setBusy,api,onError,reopen:async()=>{dialog.close();await openSceneController({getState,busy,api,setBusy,onError});}});
  if(preloaded&&getState().capabilities?.controller_operand_files)operandFiles=mountControllerOperandFiles(content,{families:preloaded,owner:scene+'/controllers/man-p1/0000',getKey:()=>getState().controller_selector_source_key,current:fresh,busy,setBusy,api,onError,reopen:async()=>{dialog.close();await openSceneController({getState,busy,api,setBusy,onError});}});
  if(typeof setBusy==='function'){const buildHost=document.createElement('details'),buildTitle=document.createElement('summary');buildTitle.textContent='Retail versus Saved Build Controller';buildHost.append(buildTitle);content.prepend(buildHost);savedBuild=mountSourceBuildScript(buildHost,{owner:scene+'/controllers/man-p1/0000',getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().script_authoring_state_key}),current:fresh,busy,setBusy});}
  const bookmarkReport={...report,record:{...report.record,sha256:report.source_record.sha256}},bookmarkOwner=scene+'/controllers/man-p1/0000';
  if(typeof api==='function'&&getState().capabilities?.saved_script_bookmarks)bookmarks=mountScriptBookmarks(content,{owner:bookmarkOwner,report:bookmarkReport,getState,getRows:()=>getState().script_bookmarks??[],getSelected:()=>selectedSource?Number(selectedSource.dataset.controllerSourcePc):null,select:selectSource,current:fresh,
   afterCommandCurrent:()=>dialog.open&&getState().project?.path===projectPath&&getState().scene?.id===scene&&getState().project?.mode==='edit'&&getState().scene_view_source_key===initial.scene_view_source_key,
   busy,editable:()=>getState().project?.mode==='edit',draftPending:()=>[selectors,branches,tiles,fades,tables,triplets,threeWords,bgm,sceneBytes,partySelectors,flagBits,fiveWords,globalBytes,componentReset,operandFiles].some(control=>control?.hasDraft?.()),command:body=>api('/api/command',body),selectedBookmarkId:focusBookmark?.id??null,onError,
   reopen:async(pc,bookmark=null)=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,focusBookmark:bookmark,onError});}});
  if(focusBookmark){if(focusBookmark.scene_id!==scene||focusBookmark.import_sha256!==initial.scene_view_source_key)throw Error('Controller bookmark imported source changed.');const pc=qualifyScriptBookmark(focusBookmark,bookmarkOwner,bookmarkReport);if(!selectSource(pc))throw Error('Controller bookmark source boundary is unavailable.');}
  else if(Number.isInteger(focusFlagPc))selectSource(focusFlagPc,false);
  focusedFlag?.scrollIntoView({block:'nearest'});
 }catch(error){if(dialog.open&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
}

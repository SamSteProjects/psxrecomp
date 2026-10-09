import {mountControllerBranches} from './controller-branches.js';
import {mountControllerTables} from './controller-tables.js';
import {mountControllerFades} from './controller-fades.js';
import {mountControllerTileRects} from './controller-tile-rects.js';
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

export function renderControllerInstruction(row,report,selectSource){
 const pc=value=>'0x'+value.toString(16).toUpperCase().padStart(4,'0');
 const create=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
 if(!Number.isSafeInteger(row.pc)||row.pc<report.entry_pc||!Number.isSafeInteger(row.length)||row.length<1||row.pc+row.length>report.source_record.byte_length||row.byte_offset!==report.source_record.byte_offset+row.pc||row.raw_hex!==report.record.raw_hex.slice(row.pc*2,(row.pc+row.length)*2))throw Error('Controller instruction bytes differ from their source record.');
 const details=create('details'),summary=create('summary',`PC ${pc(row.pc)} · ${row.mnemonic}`),fields=create('dl');details.dataset.controllerInstructionPc=row.pc;fields.dataset.controllerInstructionFields='';
 const field=(name,value)=>{const label=create('dt',name),text=create('dd',String(value));label.style.fontWeight='600';text.style.cssText='margin:0 0 8px;overflow-wrap:anywhere';fields.append(label,text);};
 field('Record PC',`${pc(row.pc)} (${row.pc})`);field('Decoded MAN Offset',`${pc(row.byte_offset)} (${row.byte_offset})`);field('Encoded Length',`${row.length} bytes`);field('Dispatch Context',row.target_context===null?'Current controller context':`Extended target ${row.target_context} · runtime binding unresolved`);
 const human=value=>value.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()).replace(/\bPc\b/g,'PC');
 const flatten=(value,path,depth=0)=>{
  if(depth>8)throw Error('Controller operand nesting exceeds inspector bounds.');
  if(Array.isArray(value)){field(path,value.map(item=>typeof item==='object'?JSON.stringify(item):String(item)).join(', ')||'None');return;}
  if(value!==null&&typeof value==='object'){for(const [name,child] of Object.entries(value)){if(name==='encoded_hex')continue;flatten(child,path?path+' / '+human(name):human(name),depth+1);}return;}
  field(path,value===null?'Unresolved':typeof value==='boolean'?(value?'Yes':'No'):typeof value==='string'?value.replaceAll('_',' '):value);
 };
 flatten(row.operands,'');details.append(summary,create('p','Retail encoded source. Runtime execution and effects have not been verified.'),fields);
 const navigation=create('div');navigation.dataset.controllerInstructionSuccessors='';navigation.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
 const boundaries=new Set([...report.instructions,...report.dialogues].map(node=>node.pc));
 for(const edge of row.successors){
  const button=create('button',`Inspect ${pc(edge.pc)} · ${(edge.condition??'Encoded successor').replaceAll('_',' ')}`);button.type='button';button.dataset.controllerInstructionNextPc=edge.pc;button.disabled=!boundaries.has(edge.pc);button.onclick=()=>{if(!button.disabled)selectSource(edge.pc);};navigation.append(button);
  if(button.disabled)navigation.append(create('p',`Boundary ${pc(edge.pc)} is not decoded. No instruction is inferred.`));
 }
 if(!row.successors.length)navigation.append(create('p','No encoded successors reported. Runtime resumption remains unresolved.'));
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

export async function openSceneController({getState,busy,expectedAsset=null,focusFlagPc=null,api=null,setBusy=null,onError=()=>{}}){
 const initial=getState(),scene=initial.scene?.id,key=initial.asset_reference_source_key,projectPath=initial.project?.path;
 if(busy()||!scene||initial.project?.mode!=='edit'||!key)return;
 const dialog=document.createElement('dialog');dialog.id='scene-controller-dialog';dialog.style.cssText='width:min(850px,calc(100vw - 32px));max-height:90vh;overflow:auto';
 const heading=document.createElement('h2');heading.textContent='Retail Scene Entry Controller';
 const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying the scene controller source…';
 const content=document.createElement('div');content.style.overflowWrap='anywhere';dialog.append(heading,close,status,content);document.body.append(dialog);dialog.showModal();
 let flow=null,walkthrough=null,selectors=null,branches=null,tiles=null,fades=null,tables=null,instructionFilter=null,selectedSource=null;const sourceRows=new Map();
 const controller=new AbortController(),fresh=()=>dialog.open&&getState().project?.path===projectPath&&getState().scene?.id===scene&&getState().asset_reference_source_key===key&&getState().project?.mode==='edit';
 const timer=setInterval(()=>{if(!fresh()&&!busy()){selectors?.dispose();selectors=null;branches?.dispose();branches=null;tiles?.dispose();tiles=null;fades?.dispose();fades=null;tables?.dispose();tables=null;flow?.dispose();flow=null;walkthrough?.dispose();walkthrough=null;sourceRows.clear();selectedSource=null;instructionFilter=null;content.replaceChildren();status.textContent='Scene sources changed. Reopen controller inspection.';}selectors?.updateState();branches?.updateState();tiles?.updateState();fades?.updateState();tables?.updateState();instructionFilter?.updateState();},250);
 dialog.addEventListener('close',()=>{clearInterval(timer);controller.abort();selectors?.dispose();branches?.dispose();tiles?.dispose();fades?.dispose();tables?.dispose();flow?.dispose();walkthrough?.dispose();sourceRows.clear();dialog.remove();},{once:true});
 try{
  const response=await fetch('/api/scene-controller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id:scene,expected_source_key:key}),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Controller inspection failed');if(!fresh())return;
  const report=decodeSceneController(value,scene,key);if(expectedAsset)qualifySceneControllerAsset(report,expectedAsset);status.textContent=`${report.semantic_id} · Decoder status: ${report.status} · ${report.instructions.length} decoded instructions · ${report.dialogues.length} dialogue segments`;
  for(const note of report.limitations){const p=document.createElement('p');p.textContent=note;content.append(p);}
  const source=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Controller source and entry evidence';pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify({source_record:report.source_record,man_source:report.man_source,entry_pc:report.entry_pc,local_count:report.record.local_count,reference_commit:report.reference_commit},null,2);source.append(summary,pre);content.append(source);
  const sourceSelection=document.createElement('p');sourceSelection.setAttribute('role','status');sourceSelection.dataset.controllerSourceSelection='';sourceSelection.textContent='Select a decoded source boundary to inspect its evidence.';content.append(sourceSelection);
  const selectSource=(pc,reveal=true)=>{if(!fresh()||busy())return false;const target=sourceRows.get(pc);if(!target)return false;instructionFilter?.reset();if(selectedSource){selectedSource.open=false;selectedSource.removeAttribute('data-controller-source-selected');selectedSource.style.borderLeft='';}selectedSource=target;target.dataset.controllerSourceSelected='true';target.style.borderLeft='3px solid #62c0b4';target.open=true;sourceSelection.textContent='Selected source PC 0x'+pc.toString(16).padStart(4,'0')+' · encoded evidence only';if(reveal){target.querySelector('summary')?.scrollIntoView({block:'start'});target.querySelector('summary')?.focus({preventScroll:true});}return true;};
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
  if(selectors)await selectors.ready;
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_branch_authoring){
   branches=mountControllerBranches(content,{owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getProjectSourceKey:()=>getState().asset_reference_source_key,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_branch_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
  }
  if(branches)await branches.ready;
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_tile_authoring){
   tiles=mountControllerTileRects(content,{owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_tile_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await tiles.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_fade_authoring){
   fades=mountControllerFades(content,{owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_fade_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await fades.ready;
  }
  if(!fresh())return;
  if(typeof api==='function'&&typeof setBusy==='function'&&getState().capabilities?.controller_table_authoring){
   tables=mountControllerTables(content,{owner:scene+'/controllers/man-p1/0000',focusPc:focusFlagPc,getContext:()=>({projectPath:getState().project?.path,sceneId:getState().scene?.id,mode:getState().project?.mode,scriptKey:getState().controller_table_source_key}),busy,setBusy,api,onError,
    reopen:async pc=>{dialog.close();await openSceneController({getState,busy,api,setBusy,focusFlagPc:pc,onError});}});
   await tables.ready;
  }
  if(!fresh())return;
  const focusedFlag=renderControllerFlags(content,report,focusFlagPc);
  const searchHost=document.createElement('section');content.append(searchHost);
  for(const [title,rows] of [['Encoded Instructions',report.instructions],['Dialogue Segments',report.dialogues],['Opaque Regions',report.opaque_regions],['Inspection Stops',report.stops]]){const heading=document.createElement('h3');heading.textContent=title;content.append(heading);if(!rows?.length){const p=document.createElement('p');p.textContent='None reported';content.append(p);}for(const row of rows??[]){let details;if(title==='Encoded Instructions')details=renderControllerInstruction(row,report,selectSource);else{details=document.createElement('details');const summary=document.createElement('summary'),pre=document.createElement('pre');const pc=Number.isSafeInteger(row.pc)?'PC 0x'+row.pc.toString(16).padStart(4,'0'):'Source region';summary.textContent=pc+' · '+(row.reason??(title==='Dialogue Segments'?'Dialogue segment':'Source evidence'));pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify(row,null,2);details.append(summary,pre);}if(['Encoded Instructions','Dialogue Segments'].includes(title)){details.dataset.controllerSourcePc=row.pc;sourceRows.set(row.pc,details);}content.append(details);}}
  instructionFilter=mountControllerInstructionFilter(searchHost,{rows:report.instructions,rowElements:sourceRows,current:fresh,busy,onHidden:pc=>{if(selectedSource&&Number(selectedSource.dataset.controllerSourcePc)===pc){selectedSource.open=false;selectedSource.removeAttribute('data-controller-source-selected');selectedSource.style.borderLeft='';selectedSource=null;sourceSelection.textContent='Selection hidden by the instruction filter. Select a visible source boundary.';}}});
  focusedFlag?.scrollIntoView({block:'nearest'});
 }catch(error){if(dialog.open&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}}
}

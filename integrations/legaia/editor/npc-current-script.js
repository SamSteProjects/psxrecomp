import {decodeNpcDonorScript,renderNpcScriptContents} from './npc-donor-script.js';
import {canonicalScriptMetadata,scriptFlowReportHash} from './script-flow-identity.js';
import {decodeNpcMovementSource,openNpcMovement} from './npc-movement.js';
import {decodeNpcSystemFlagsSource,openNpcSystemFlags} from './npc-system-flags.js';
import {decodeNpcWaitSource,openNpcWaits} from './npc-waits.js';
import {decodeNpcFacingSource,openNpcFacing} from './npc-facing.js';
import {decodeNpcFlagsSource,openNpcFlags} from './npc-flags.js';
const same=(a,b)=>JSON.stringify(canonicalScriptMetadata(a))===JSON.stringify(canonicalScriptMetadata(b));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
async function recordHash(hex){if(typeof hex!=='string'||!hex.length||hex.length>131072||hex.length%2||!/^[a-f0-9]+$/.test(hex))throw Error('Current NPC record bytes are invalid.');const bytes=Uint8Array.from(hex.match(/../g),v=>parseInt(v,16));return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');}
export async function decodeNpcCurrentScript(value,entityId,state){
 const draft=state.actor_drafts?.[entityId],report=value?.inspection,source=value?.donor;
 decodeNpcDonorScript(source,entityId,state);
 if(value.schema_version!=='legaia.npc-current-script.v1'||value.entity_id!==entityId||value.scene_id!==state.scene?.id||value.project_source_key!==state.project_copy_source_key||!same(value.draft,draft)||!hash(value.state_key)||value.representation!=='npc_authored_script_source'||value.generated_code!==false||value.runtime_binding!=='not_asserted'||value.gameplay_verified!==false||report?.schema_version!=='legaia.actor-script-inspection.v1'||report.read_only!==true||report.semantic_id!==source.inspection.semantic_id||report.actor_semantic_id!==draft.donor_entity_id||!same(report.source_record,source.inspection.source_record)||['record_index','byte_offset','byte_length','script_offset','local_count'].some(k=>report.record?.[k]!==source.inspection.record[k])||!Array.isArray(report.instructions)||report.instructions.length>4096||!Array.isArray(report.dialogues)||report.dialogues.length>1024||!hash(report.record?.sha256)||!Number.isSafeInteger(value.changed_byte_count)||value.changed_byte_count<0||!Array.isArray(value.limitations))throw Error('Current NPC script differs from its authored draft or Retail binding.');
 if(await recordHash(report.record.raw_hex)!==report.record.sha256||report.record.raw_hex.length!==source.inspection.record.raw_hex.length||report.record.raw_hex.slice(0,report.record.script_offset*2)!==source.inspection.record.raw_hex.slice(0,report.record.script_offset*2))throw Error('Current NPC script bytes or inherited header differ.');
 let changed=0;for(let at=0;at<report.record.raw_hex.length;at+=2)if(report.record.raw_hex.slice(at,at+2)!==source.inspection.record.raw_hex.slice(at,at+2))changed++;
 if(changed!==value.changed_byte_count)throw Error('Current NPC changed-byte count differs.');
 return structuredClone(value);
}
export function npcCurrentMovementSelection(value,source,pc,state){
 const movement=decodeNpcMovementSource(source,value.entity_id,state),row=movement.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.actor_movement_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==movement.project_source_key||!same(value.draft,movement.draft)||!row||!instruction||!['MOVE_TO','NPC_RUN'].includes(row.mnemonic)||row.mnemonic!==instruction.mnemonic||row.source_record_sha256!==value.donor.inspection.record.sha256||row.effective_values.x!==instruction.operands?.target_position?.x||row.effective_values.z!==instruction.operands?.target_position?.z)throw Error('Select an independently qualified Current NPC movement destination in Edit mode.');
 return {entity_id:value.entity_id,movement_id:row.semantic_id,pc:row.pc,values:structuredClone(row.effective_values)};
}
export function npcCurrentSystemSelection(value,source,pc,state){
 const selectors=decodeNpcSystemFlagsSource(source,value.entity_id,state),row=selectors.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.npc_system_selector_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==selectors.project_source_key||!same(value.draft,selectors.draft)||!row||!instruction||row.mnemonic!==instruction.mnemonic||row.source_record_sha256!==value.donor.inspection.record.sha256||row.effective_values.index!==instruction.operands?.index||instruction.target_context!==null)throw Error('Select an independently qualified Current NPC system selector in Edit mode.');
 return {entity_id:value.entity_id,system_flag_id:row.semantic_id,pc:row.pc,values:structuredClone(row.effective_values)};
}
const operandFamilies={
 waits:{label:'Edit selected NPC wait',route:'/api/npc-waits-source',capability:'actor_wait_authoring',decode:decodeNpcWaitSource,open:openNpcWaits,field:'duration_ticks'},
 facing:{label:'Edit selected NPC facing',route:'/api/npc-facing-source',capability:'actor_facing_authoring',decode:decodeNpcFacingSource,open:openNpcFacing,field:'sector'},
 flags:{label:'Edit selected NPC flag bit',route:'/api/npc-flags-source',capability:'actor_flag_authoring',decode:decodeNpcFlagsSource,open:openNpcFlags,field:'bit'}
};
export function npcCurrentOperandSelection(value,source,pc,state,family){
 const editor=operandFamilies[family];if(!editor)throw Error('Unsupported Current NPC operand family.');
 const accepted=editor.decode(source,value.entity_id,state),row=accepted.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.[editor.capability]!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==accepted.project_source_key||!same(value.draft,accepted.draft)||!row||!instruction||row.mnemonic!==instruction.mnemonic||row.source_record_sha256!==value.donor.inspection.record.sha256||row.target_context!==instruction.target_context)throw Error('Select an independently qualified Current NPC operand in Edit mode.');
 const raw=instruction.raw_hex,known=value.donor.inspection.instructions.find(r=>r.pc===pc);
 if(!known||known.mnemonic!==instruction.mnemonic||known.length!==instruction.length||typeof raw!=='string'||!/^[a-f0-9]+$/.test(raw)||raw.length!==instruction.length*2||raw!==value.inspection.record.raw_hex.slice(pc*2,(pc+instruction.length)*2))throw Error('Current operand span differs from its source instruction.');
 const bytes=Uint8Array.from(raw.match(/../g),v=>parseInt(v,16)),header=bytes[0]&128?2:1,op=bytes[0]&127;
 if(instruction.target_context!==(header===2?bytes[1]:null))throw Error('Current operand dispatch differs from its native header.');
 let operand;
 if(family==='waits'){
  if(op!==0x4a||bytes.length!==header+2)throw Error('Current wait encoding is unresolved.');operand=bytes[header]|bytes[header+1]<<8;
 }else if(family==='flags'){
  const [bank,operation]=instruction.mnemonic.split('_'),opcode=0x2b+['LFLAG','GFLAG','CFLAG'].indexOf(bank)*3+['SET','CLEAR','TEST'].indexOf(operation);
  if(op!==opcode||bytes.length!==header+1||(bytes[header]&224)!==(row.before_raw&224))throw Error('Current flag preservation bits or opcode differ.');operand=bytes[header]&31;
 }else{
  if(!row.effective_supported||instruction.operands?.parked_target)throw Error('Current facing operand is unsupported.');
  const npc=instruction.mnemonic==='NPC_RUN',relative=header+(npc?3:0);
  if(op!==(npc?0x4c:0x38)||bytes.length!==header+(npc?5:2)||npc&&(bytes[header]!==0x51||(bytes[header+1]&127)===127&&(bytes[header+2]&127)===127)||!npc&&(bytes[header+1]&127)!==0||(bytes[relative]&240)!==(row.before_raw&240))throw Error('Current facing preservation bits or opcode differ.');operand=bytes[relative]&15;
 }
 if(family!=='facing'&&operand!==instruction.operands?.[editor.field])throw Error('Current decoded operand differs from its native bytes.');
 if(operand!==row.effective_values[editor.field])throw Error('Current NPC operand differs from its qualified authoring source.');
 return {entity_id:value.entity_id,operand_id:row.semantic_id,pc:row.pc,values:structuredClone(row.effective_values)};
}
export function openNpcCurrentScript({entityId,getState,isBusy,renderInstructions,showTargets,focusPc,targetSettings=null,canEdit=()=>false,api}){
 if(isBusy())return;const state=getState(),key=state.project_copy_source_key,draft=structuredClone(state.actor_drafts?.[entityId]);if(!draft||draft.scene_id!==state.scene?.id)return;
 const dialog=document.createElement('dialog');dialog.id='npc-current-script-dialog';dialog.style.cssText='width:min(900px,calc(100vw - 32px));max-height:calc(100vh - 32px);overflow:auto;overflow-wrap:anywhere';
 dialog.innerHTML='<h2>Current NPC script preview</h2><p class="field-note">Qualified clone-owned script changes at Retail donor offsets. No generated allocation, initial appearance or placement is represented. Simulation uses hypothetical inputs; execution and gameplay remain unverified.</p><p data-status role="status">Qualifying Current NPC script…</p><div data-content></div><button data-close>Close Current NPC script</button>';document.body.append(dialog);
 const controller=new AbortController(),bound=()=>getState().project_copy_source_key===key&&same(getState().actor_drafts?.[entityId],draft),current=()=>dialog.open&&bound();let targetTimer=null,editTimer=null,selectedPc=null,updateEdit=()=>{};
 const post=async signal=>{const response=await fetch('/api/npc-current-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entityId}),signal});const text=await response.text();if(text.length>4*1024*1024)throw Error('Current NPC inspection exceeds4 MiB.');const value=JSON.parse(text);if(!response.ok)throw Error(value.error??'Current NPC inspection failed.');const accepted=await decodeNpcCurrentScript(value,entityId,getState());if(!current())throw Error('Project or NPC changed. Reopen Current preview.');return accepted;};
 dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();clearInterval(targetTimer);clearInterval(editTimer);dialog.remove();});dialog.showModal();
 const ready=(async()=>{try{const value=await post(controller.signal),report=value.inspection,reportHash=await scriptFlowReportHash(report);if(!current())return;
 const context={project_path:getState().project?.path,scene_id:value.scene_id,script_id:report.semantic_id,project_source_key:key,record_sha256:report.record.sha256,representation:'authored_current',flow_proof:{state_key:value.state_key,report_sha256:reportHash,review_key:null,branch_id:null,branch_value:null}};
 dialog.querySelector('[data-status]').textContent=`Retail ${value.donor.inspection.record.sha256} · Current ${report.record.sha256} · ${value.changed_byte_count} changed bytes. Project unchanged.`;
 renderNpcScriptContents(dialog.querySelector('[data-content]'),report,(host,r)=>renderInstructions(host,r,r.semantic_id,null,pc=>{selectedPc=pc;updateEdit();},{label:'Walk through Current NPC instructions',current,getContext:()=>structuredClone(context),requalify:async({signal})=>{const fresh=await post(signal);if(!same(fresh,value))throw Error('Current NPC source qualification changed.');return true;}}),value,'npc_authored_script_source');
 if(typeof api==='function'){
  const tools=document.createElement('section');tools.dataset.currentNpcEdit='';dialog.querySelector('[data-content]').before(tools);
  const editors=[
   {label:'Edit selected NPC destination',route:'/api/npc-movement-source',capability:'actor_movement_authoring',decode:decodeNpcMovementSource,select:npcCurrentMovementSelection,open:openNpcMovement},
   {label:'Edit selected NPC system selector',route:'/api/npc-system-flags-source',capability:'npc_system_selector_authoring',decode:decodeNpcSystemFlagsSource,select:npcCurrentSystemSelection,open:openNpcSystemFlags},
   ...Object.entries(operandFamilies).map(([family,editor])=>({...editor,select:(value,source,pc,state)=>npcCurrentOperandSelection(value,source,pc,state,family)}))
  ];
  for(const editor of editors){editor.button=document.createElement('button');editor.button.type='button';editor.button.textContent=editor.label;editor.note=document.createElement('p');editor.note.className='field-note';editor.pending=true;editor.source=null;editor.failure='';tools.append(editor.button,editor.note);
   editor.selection=()=>{try{if(current()&&canEdit()&&!isBusy()&&!editor.pending&&editor.source)return editor.select(value,editor.source,selectedPc,getState());}catch{}return null;};
   editor.button.onclick=()=>{const selection=editor.selection();if(!selection)return;const pc=selection.pc,returnCurrent=()=>{const next=getState().actor_drafts?.[entityId];if(!isBusy()&&next?.scene_id===draft.scene_id&&next?.donor_entity_id===draft.donor_entity_id)openNpcCurrentScript({entityId,getState,isBusy,renderInstructions,showTargets,focusPc:pc,targetSettings,canEdit,api});};dialog.close();editor.open({entityId,getState,isBusy,canEdit,api,showTargets,focusPc:pc,onReturn:returnCurrent,onApplied:returnCurrent});};
  }
  updateEdit=()=>{for(const editor of editors){const selection=editor.selection();editor.button.disabled=!selection;editor.note.textContent=!current()?'Source changed. Reopen Current inspection.':editor.pending?'Qualifying authoring source…':editor.failure||(selection?'Qualified instruction at0x'+selection.pc.toString(16)+'. Review clone-owned operands before Apply.':'Select a supported instruction in Edit mode.');}};
  editTimer=setInterval(updateEdit,300);updateEdit();
  await Promise.all(editors.map(async editor=>{if(canEdit()&&getState().capabilities?.[editor.capability]===true){try{const response=await fetch(editor.route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entity_id:entityId}),signal:controller.signal}),raw=await response.json();if(!response.ok)throw Error(raw.error??'Authoring source unavailable.');editor.source=editor.decode(raw,entityId,getState());}catch(error){if(!controller.signal.aborted)editor.failure=error.message;}}editor.pending=false;if(current())updateEdit();}));
 }
 if(typeof showTargets==='function'){
  const tools=document.createElement('section');tools.dataset.currentNpcTargets='';tools.innerHTML='<h3>Inspect destinations in scene</h3><p class="field-note">Absolute script X/Z coordinates; actor placement is unchanged. Reference Y only places markers. Unvisited source anchors, extended dispatch and parked destinations do not establish gameplay execution.</p><label>Target layer<select aria-label="Current NPC target layer"><option value="authored">Current NPC script</option><option value="retail">Retail donor script</option></select></label><label>Path scope<select aria-label="Current NPC target paths"><option value="reached">Decoded reached paths</option><option value="all_anchors">All qualified source anchors</option></select></label><label>Marker reference Y<input aria-label="Current NPC target reference Y" type="number" min="-10000000" max="10000000" step="any" required></label><button type="button" data-show>Show Current NPC script targets</button><p data-target-status role="status"></p>';dialog.querySelector('[data-content]').before(tools);
  const layer=tools.querySelector('[aria-label="Current NPC target layer"]'),paths=tools.querySelector('[aria-label="Current NPC target paths"]'),height=tools.querySelector('input'),show=tools.querySelector('[data-show]'),status=tools.querySelector('[data-target-status]');let pending=false,generation=0,errorMessage='';
  if(targetSettings){layer.value=targetSettings.layer;paths.value=targetSettings.paths;height.value=String(targetSettings.height);}
  const settings=()=>({layer:layer.value,paths:paths.value,height:height.value});
  const update=()=>{const r=layer.value==='retail'?value.donor.inspection:report,count=[...r.instructions,...(paths.value==='all_anchors'?r.unvisited_instructions??[]:[])].filter(n=>['MOVE_TO','NPC_RUN'].includes(n.mnemonic)).length;show.disabled=pending||!current()||isBusy()||!count||!height.value.trim()||!height.validity.valid;status.textContent=!current()?'Source changed. Reopen Current NPC inspection.':errorMessage|| (pending?'Qualifying source and native target bytes…':count+' decoded X/Z destinations in this scope. Execution remains unknown.');};
  for(const control of [layer,paths,height])control.oninput=()=>{generation++;errorMessage='';update();};targetTimer=setInterval(update,300);update();
  show.onclick=async()=>{if(show.disabled||!height.reportValidity())return;const chosen=settings(),token=++generation;pending=true;update();try{
   const fresh=await post(controller.signal);if(!same(fresh,value))throw Error('Current NPC source changed. Reopen inspection.');
   const {npcCurrentScriptTargetOverlay}=await import('./npc-current-script-targets.js'),overlay=await npcCurrentScriptTargetOverlay(fresh,chosen.layer,Number(chosen.height),getState(),chosen.paths);
   if(!current()||token!==generation||!same(chosen,settings()))return;let withdrawn=false;
   const isCurrent=()=>!withdrawn&&bound(),reopen=pc=>{if(isCurrent()&&!isBusy())openNpcCurrentScript({entityId,getState,isBusy,renderInstructions,showTargets,focusPc:pc,targetSettings:{...chosen,height:Number(chosen.height)},canEdit,api});};
   showTargets(overlay,reopen,isCurrent,()=>{withdrawn=true;});dialog.close();
  }catch(error){if(current()){errorMessage=error.message;status.textContent=error.message;}}finally{pending=false;if(dialog.open)update();}};
 }
 if(Number.isSafeInteger(focusPc))dialog.querySelector('button[aria-label="Select instruction 0x'+focusPc.toString(16).toUpperCase()+'"]')?.click();
 }catch(error){if(!controller.signal.aborted&&dialog.open){dialog.querySelector('[data-content]').replaceChildren();dialog.querySelector('[data-status]').textContent=error.message;}}})();return {dialog,ready};
}

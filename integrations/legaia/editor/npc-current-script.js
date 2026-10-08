import {decodeNpcDonorScript,renderNpcScriptContents} from './npc-donor-script.js';
import {canonicalScriptMetadata,scriptFlowReportHash} from './script-flow-identity.js';
import {decodeNpcMovementSource,openNpcMovement} from './npc-movement.js';
import {decodeNpcSystemFlagsSource,openNpcSystemFlags} from './npc-system-flags.js';
import {decodeNpcWaitSource,openNpcWaits} from './npc-waits.js';
import {decodeNpcFacingSource,openNpcFacing} from './npc-facing.js';
import {decodeNpcFlagsSource,openNpcFlags} from './npc-flags.js';
import {decodeNpcModelSelectorsSource,openNpcModelSelectors} from './npc-model-selectors.js';
import {decodeNpcBranchesSource,openNpcBranches} from './npc-branches.js';
import {decodeNpcDialogueSource,openNpcDialogue} from './npc-dialogue.js';
import {decodeNpcAnimationOperandSource,openNpcAnimationOperands,npcCurrentAnimationSelection} from './npc-animation-operands.js';
import {decodeNpcEffectColorSource,openNpcEffectColors} from './npc-effect-colors.js';
import {decodeNpcTransitionsSource,openNpcTransitions} from './npc-transitions.js';
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
 model_selectors:{label:'Edit selected NPC model selector',route:'/api/npc-model-selectors-source',capability:'actor_model_selector_authoring',decode:decodeNpcModelSelectorsSource,open:openNpcModelSelectors,field:'model_selector_signed'},
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
 if(family==='model_selectors'){
  if(op!==0x4c||bytes.length!==header+3||bytes[header]!==0x50)throw Error('Current model-selector encoding is unresolved.');const word=bytes[header+1]|bytes[header+2]<<8;operand=word&32768?word-65536:word;
 }else if(family==='waits'){
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
const branchWords={JMP_REL:[0,'unconditional'],COND_JMP:[2,'test_passed'],BBOX_TEST:[4,'outside_box'],SYSFLAG_TEST:[1,'flag_set'],FLAG_WORD_BRANCH:[2,'flag_bit_set'],FIELD_68_BRANCH:[1,'field_68_zero'],ACTOR_SEARCH_BRANCH:[3,'search_match'],VALUE_COMPARE_BRANCH:[4,'comparison_true']};
export function npcCurrentBranchSelection(value,source,pc,state){
 const accepted=decodeNpcBranchesSource(source,value.entity_id,state),row=accepted.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc),known=value.donor.inspection.instructions.find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.actor_branch_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==accepted.project_source_key||!same(value.draft,accepted.draft)||!row||!instruction||!known||instruction.mnemonic!==row.mnemonic||known.mnemonic!==row.mnemonic||instruction.length!==known.length||row.source_record_sha256!==value.donor.inspection.record.sha256||row.target_context!==instruction.target_context)throw Error('Select a qualified Current NPC branch in Edit mode.');
 const layout=branchWords[row.mnemonic],raw=instruction.raw_hex,record=value.inspection.record.raw_hex;
 if(!layout||typeof raw!=='string'||!/^[a-f0-9]+$/.test(raw)||raw.length!==instruction.length*2||record.slice(pc*2,(pc+instruction.length)*2)!==raw)throw Error('Current branch bytes differ from their record.');
 const bytes=Uint8Array.from(raw.match(/../g),v=>parseInt(v,16)),header=bytes[0]&128?2:1,relative=header+layout[0],operand=pc+relative;
 if(row.operand_pc!==operand||row.condition!==layout[1]||relative+2>bytes.length||instruction.target_context!==(header===2?bytes[1]:null)||row.mnemonic==='SYSFLAG_TEST'&&(header!==1||(bytes[0]&240)!==112))throw Error('Current branch target-word layout differs.');
 if(row.mnemonic!=='SYSFLAG_TEST'&&raw.slice(0,relative*2)!==known.raw_hex.slice(0,relative*2))throw Error('Current branch condition bytes changed.');
 const target=(operand+(bytes[relative]|bytes[relative+1]<<8))&65535,edges=instruction.successors?.filter(e=>e.condition===layout[1]);
 if(target!==row.effective_values.target_pc||edges?.length!==1||edges[0].pc!==target)throw Error('Current branch destination differs from its native target word.');
 return {entity_id:value.entity_id,operand_id:row.semantic_id,pc,values:structuredClone(row.effective_values)};
}
export function npcCurrentDialogueSelection(value,source,pc,state){
 const accepted=decodeNpcDialogueSource(source,value.entity_id,state);
 if(state.project?.mode!=='edit'||state.capabilities?.actor_dialogue_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==accepted.project_source_key||!same(value.draft,accepted.draft))throw Error('Select qualified Current NPC text in Edit mode.');
 const runs=accepted.options.runs.filter(r=>r.kind==='menu_label'?r.menu_pc===pc:r.dialogue_pc===pc),messages=[...value.inspection.dialogues,...(value.inspection.unvisited_dialogues??[])],instructions=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])];
 if(!runs.length)throw Error('Selected instruction has no qualified text runs.');
 for(const run of runs){const menu=run.kind==='menu_label',parent=(menu?instructions:messages).find(r=>r.pc===pc),known=(menu?value.donor.inspection.instructions:value.donor.inspection.dialogues).find(r=>r.pc===pc);
  if(!parent||!known||parent.length!==known.length||menu&&parent.mnemonic!=='DIALOGUE_PICKER'||run.pc<=pc||run.pc+run.byte_length>pc+parent.length||run.decoded_byte_offset!==value.donor.inspection.record.byte_offset+run.pc)throw Error('Current text run escapes its qualified source boundary.');
  const menuOption=menu?known.operands?.options?.find(option=>run.dialogue_id===`script://${accepted.draft.donor_entity_id.slice(8)}/menu/${pc.toString(16).padStart(4,'0')}/option/${option.index}`):null,tokens=menu?menuOption?.label_tokens:known.tokens;
  if(!menu&&run.dialogue_id!==known.semantic_id||run.semantic_id!==run.dialogue_id+'/run/'+run.pc.toString(16).padStart(4,'0')||!Array.isArray(tokens)||Array.from(run.text).some((character,index)=>!tokens.some(token=>token.pc===run.pc+index&&token.kind==='glyph'&&token.length===1&&token.text===character)))throw Error('Current text run includes an unqualified control or glyph span.');
  const ascii=text=>Array.from(text,c=>c.charCodeAt(0).toString(16).padStart(2,'0')).join('');
  if(/[^\x20-\x7e]|[\^|]/.test(run.text+run.effective_text)||value.donor.inspection.record.raw_hex.slice(run.pc*2,(run.pc+run.byte_length)*2)!==ascii(run.text)||value.inspection.record.raw_hex.slice(run.pc*2,(run.pc+run.byte_length)*2)!==ascii(run.effective_text))throw Error('Current text differs from its native equal-span glyph bytes.');
 }
 return {entity_id:value.entity_id,pc,run_ids:runs.map(r=>r.semantic_id)};
}
export function npcCurrentEffectSelection(value,source,pc,state){
 const accepted=decodeNpcEffectColorSource(source,value.entity_id,state),row=accepted.options.targets.find(r=>r.pc===pc),instruction=[...value.inspection.instructions,...(value.inspection.unvisited_instructions??[])].find(r=>r.pc===pc),known=value.donor.inspection.instructions.find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.actor_effect_color_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.project_source_key!==accepted.project_source_key||!same(value.draft,accepted.draft)||!row||!instruction||!known||instruction.mnemonic!==row.mnemonic||known.mnemonic!==row.mnemonic||instruction.length!==known.length||row.source_record_sha256!==value.donor.inspection.record.sha256||row.target_context!==instruction.target_context)throw Error('Select a qualified Current NPC effect-color instruction in Edit mode.');
 const raw=instruction.raw_hex;if(typeof raw!=='string'||!/^[a-f0-9]+$/.test(raw)||raw.length!==instruction.length*2||raw!==value.inspection.record.raw_hex.slice(pc*2,(pc+instruction.length)*2))throw Error('Current effect-color span differs from its record.');
 const bytes=Uint8Array.from(raw.match(/../g),v=>parseInt(v,16)),header=bytes[0]&128?2:1,start=header+1;
 if((bytes[0]&127)!==0x34||bytes.length!==header+6||bytes[header]>>4!==0||instruction.target_context!==(header===2?bytes[1]:null)||raw.slice(0,start*2)!==known.raw_hex.slice(0,start*2)||row.decoded_byte_offset!==value.donor.inspection.record.byte_offset+pc+start)throw Error('Current effect-color opcode, selector or dispatch changed.');
 const word=bytes[start+3]|bytes[start+4]<<8,values={red:bytes[start],green:bytes[start+1],blue:bytes[start+2],intensity:word&32768?word-65536:word};
 if(!same(values,row.effective_values)||!same(instruction.operands?.rgb,[values.red,values.green,values.blue])||instruction.operands?.intensity!==values.intensity||instruction.operands?.raw_selector!==bytes[header])throw Error('Current effect-color operands differ from their native bytes.');
 return {entity_id:value.entity_id,operand_id:row.semantic_id,pc,values};
}
export function npcCurrentTransitionSelection(value,source,pc,state){
 const accepted=decodeNpcTransitionsSource(source,value.entity_id,state),row=accepted.options.transitions.find(r=>r.pc===pc),node=value.inspection.instructions.find(r=>r.pc===pc),retail=value.donor.inspection.instructions.find(r=>r.pc===pc);
 if(state.project?.mode!=='edit'||state.capabilities?.npc_transition_authoring!==true||value.schema_version!=='legaia.npc-current-script.v1'||value.representation!=='npc_authored_script_source'||value.generated_code!==false||value.gameplay_verified!==false||value.runtime_binding!=='not_asserted'||value.project_source_key!==accepted.project_source_key||!same(value.draft,accepted.draft)||!row||!node||!retail||node.mnemonic!=='SCENE_CHANGE'||node.target_context!==row.target_context||node.operands?.scene_name_ascii!==row.destination||node.length!==row.instruction_length||retail.raw_hex!==row.raw_instruction_hex||row.source_record_sha256!==value.donor.inspection.record.sha256||row.record_byte_offset!==value.donor.inspection.record.byte_offset)throw Error('Select a qualified Current NPC arrival in Edit mode.');
 const raw=node.raw_hex,bytes=typeof raw==='string'&&/^(?:[a-f0-9]{2})+$/.test(raw)?raw.match(/../g).map(v=>parseInt(v,16)):[],original=row.raw_instruction_hex.match(/../g).map(v=>parseInt(v,16)),fields=['entry_x_encoded','entry_z_encoded','direction_encoded'];
 if(bytes.length!==original.length||raw!==value.inspection.record.raw_hex.slice(pc*2,(pc+bytes.length)*2)||bytes.slice(0,-3).some((v,i)=>v!==original[i])||fields.some((k,i)=>row.effective_values[k]!==bytes[bytes.length-3+i]))throw Error('Current arrival differs from its fixed native destination or bytes.');
 return {entity_id:value.entity_id,operand_id:row.semantic_id,pc,values:structuredClone(row.effective_values)};
}
export function openNpcCurrentScript({entityId,getState,isBusy,renderInstructions,showTargets,onPreviewArrival,focusPc,targetSettings=null,canEdit=()=>false,api}){
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
  const tools=document.createElement('section'),actions=document.createElement('div'),note=document.createElement('p');tools.dataset.currentNpcEdit='';actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px';note.className='field-note';note.setAttribute('role','status');tools.append(actions,note);dialog.querySelector('[data-content]').before(tools);
  const editors=[
   {label:'Edit selected NPC destination',route:'/api/npc-movement-source',capability:'actor_movement_authoring',decode:decodeNpcMovementSource,select:npcCurrentMovementSelection,open:openNpcMovement},
   {label:'Edit selected NPC system selector',route:'/api/npc-system-flags-source',capability:'npc_system_selector_authoring',decode:decodeNpcSystemFlagsSource,select:npcCurrentSystemSelection,open:openNpcSystemFlags},
   {label:'Edit selected NPC branch',route:'/api/npc-branches-source',capability:'actor_branch_authoring',decode:decodeNpcBranchesSource,select:npcCurrentBranchSelection,open:openNpcBranches},
   {label:'Edit selected NPC dialogue',route:'/api/npc-dialogue-source',capability:'actor_dialogue_authoring',decode:decodeNpcDialogueSource,select:npcCurrentDialogueSelection,open:openNpcDialogue},
   {label:'Edit Selected NPC Animation Arguments',route:'/api/npc-animation-operands-source',capability:'npc_animation_operand_authoring',decode:decodeNpcAnimationOperandSource,select:npcCurrentAnimationSelection,open:openNpcAnimationOperands},
   {label:'Edit selected NPC effect color',route:'/api/npc-effect-colors-source',capability:'actor_effect_color_authoring',decode:decodeNpcEffectColorSource,select:npcCurrentEffectSelection,open:openNpcEffectColors},
   {label:'Edit selected NPC arrival',route:'/api/npc-transitions-source',capability:'npc_transition_authoring',decode:decodeNpcTransitionsSource,select:npcCurrentTransitionSelection,open:openNpcTransitions},
   ...Object.entries(operandFamilies).map(([family,editor])=>({...editor,select:(value,source,pc,state)=>npcCurrentOperandSelection(value,source,pc,state,family)}))
  ];
  for(const editor of editors){editor.button=document.createElement('button');editor.button.type='button';editor.button.textContent=editor.label;editor.pending=true;editor.source=null;editor.failure='';actions.append(editor.button);
   editor.selection=()=>{try{if(current()&&canEdit()&&!isBusy()&&!editor.pending&&editor.source)return editor.select(value,editor.source,selectedPc,getState());}catch{}return null;};
   editor.button.onclick=()=>{const selection=editor.selection();if(!selection)return;const pc=selection.pc,returnCurrent=()=>{const next=getState().actor_drafts?.[entityId];if(!isBusy()&&next?.scene_id===draft.scene_id&&next?.donor_entity_id===draft.donor_entity_id)openNpcCurrentScript({entityId,getState,isBusy,renderInstructions,showTargets,onPreviewArrival,focusPc:pc,targetSettings,canEdit,api});};dialog.close();editor.open({entityId,getState,isBusy,canEdit,api,showTargets,onPreview:onPreviewArrival,focusPc:pc,onReturn:returnCurrent,onApplied:returnCurrent});};
  }
  updateEdit=()=>{let qualified=false;for(const editor of editors){const selection=editor.selection();editor.button.disabled=!selection;qualified ||=!!selection;}note.textContent=!current()?'Source changed. Reopen Current inspection.':!canEdit()?'Switch to Edit mode to edit selected script content.':editors.some(e=>e.pending)?'Qualifying authoring sources…':qualified?'Selected content is qualified. Review clone-owned edits before Apply.':editors.filter(e=>e.failure).map(e=>e.failure).join(' · ')||'Select a supported instruction or dialogue segment to edit its clone-owned content.';};
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

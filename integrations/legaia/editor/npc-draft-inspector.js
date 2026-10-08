import {npcDonorModel} from './asset-inspector.js';
import {componentDefinition,renderComponentProperties,renderComponentDetails,renderComponentActions,bindComponentActions} from './component-inspector.js';
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Read SDK snapshots only. The NPC authoring adapter owns commands and validation.
export function renderNpcDraftInspector(schema,snapshot,previewState){
  if(typeof snapshot?.entity_id!=='string'||!snapshot.draft||!['current','pending','source-during-proposal','unavailable'].includes(previewState))throw new Error('NPC draft inspector requires source and preview state.');
  const status={current:'Current authored scene preview snapshot.',pending:'Previous preview snapshot — refresh pending. Current source is not yet qualified.','source-during-proposal':'Source preview snapshot while a detached scene proposal is active. Proposed viewport coordinates are not substituted; authored placement remains separate.',unavailable:'No NPC draft preview snapshot in this view. Missing values remain unknown.'};
  return ['NpcDraftIdentity','NpcDraftTransform',...(schema.components?.NpcDraftScriptBinding?['NpcDraftScriptBinding']:[]),'NpcDraftPreview'].map(id=>{
    const definition=componentDefinition(schema,id);
    if(definition.layout!=='read-only-properties'||definition.properties.some(p=>p.authoring))throw new Error('NPC draft snapshot properties must be read only.');
    const note=id==='NpcDraftPreview'?`<p class="field-note" data-npc-preview-state="${previewState}" role="status">${escape(status[previewState])}</p>`:'';
    return `<section class="component" data-npc-draft-component="${id}"><h3>${escape(definition.label)}${definition.units?` <small>${escape(definition.units)}</small>`:''}</h3>${note}${renderComponentProperties(schema,id,snapshot)}${renderComponentDetails(schema,id,snapshot)}</section>`;
  }).join('');
}

export const npcScriptActionButtons={
  'edit-npc-dialogue':'npc-dialogue-button','edit-npc-facing':'npc-facing-button',
  'edit-npc-model-selectors':'npc-model-selectors-button','edit-npc-flags':'npc-flags-button',
  'edit-npc-system-flags':'npc-system-flags-button','edit-npc-branches':'npc-branches-button','edit-npc-effect-colors':'npc-effect-colors-button',
  'edit-npc-waits':'npc-waits-button','edit-npc-movement':'npc-movement-button',
  'inspect-npc-current-script':'npc-current-script-button',
  'inspect-npc-build-script':'npc-build-script-button','inspect-npc-donor-script':'npc-donor-script-button',
  'reset-npc-script':'npc-script-reset-button'};
export const npcDraftActionContext=(state,id)=>JSON.stringify([state.project?.path,state.scene?.id,state.mode??state.project?.mode,state.asset_reference_source_key,state.actor_drafts?.[id]??null]);
export function npcScriptBindingSnapshot(state,id){
  const draft=state.actor_drafts?.[id],row=state.npc_script_bindings?.[id],families=['dialogue','waits','movement','facing','flags','system_flags','branches','model_selectors','effect_colors','transitions'];
  const keys=['schema_version','entity_id','scene_id','donor_entity_id','source_script_id','authored_draft_sha256','authored_counts','source_qualification','generated_qualification','runtime_binding'];
  if(typeof draft?.donor_entity_id!=='string'||!row||Array.isArray(row)||Object.keys(row).length!==keys.length||keys.some(k=>!Object.hasOwn(row,k))||Array.isArray(row.authored_counts))throw Error('Unsupported NPC script ownership metadata. Reselect the NPC.');
  if(!draft||!row||row.schema_version!=='legaia.npc-script-binding.v1'||row.entity_id!==id||row.scene_id!==draft.scene_id||row.donor_entity_id!==draft.donor_entity_id||row.source_script_id!=='script://'+draft.donor_entity_id.slice(8)||!/^scene:\/\/[A-Za-z0-9_-]+\/actors\/man-p1\/[0-9]{4}$/.test(row.donor_entity_id)||! /^[0-9a-f]{64}$/.test(row.authored_draft_sha256)||row.source_qualification!=='inspect_retail_donor_script'||row.generated_qualification!=='inspect_saved_build_script'||row.runtime_binding!=='not_asserted'||!row.authored_counts||Object.keys(row.authored_counts).length!==families.length||families.some(f=>!Number.isSafeInteger(row.authored_counts[f])||row.authored_counts[f]<0||row.authored_counts[f]>1024||row.authored_counts[f]!==Object.keys(draft[f]?.[f==='dialogue'?'runs':'entries']??{}).length))throw Error('NPC script ownership snapshot differs from its authored draft. Reselect the NPC.');
  return structuredClone(row);
}
export function mountNpcDraftScriptActions(host,{schema,snapshot,getState,busy,editable,current,handlers,onError}){
  const definition=componentDefinition(schema,'NpcDraftScriptBinding'),key=npcDraftActionContext(getState(),snapshot.entity_id);
  const registry=Object.fromEntries(definition.actions.filter(a=>Object.hasOwn(npcScriptActionButtons,a.id)&&typeof handlers[a.id]==='function').map(a=>[a.id,{
    requiresEdit:a.id.startsWith('edit-npc-')||a.id==='reset-npc-script',canRun:()=>getState().capabilities?.[a.capability]===true,
    run:()=>handlers[a.id]()}]));
  const actions=document.createElement('div');actions.className='npc-script-actions';actions.dataset.npcScriptActions='true';
  actions.innerHTML=renderComponentActions(schema,'NpcDraftScriptBinding',snapshot,getState().capabilities,registry,editable());
  for(const button of actions.querySelectorAll('[data-inspector-action]')){button.id=npcScriptActionButtons[button.dataset.inspectorAction];button.disabled ||= busy();}
  host.append(actions);
  bindComponentActions(actions,registry,{current:()=>current()&&key===npcDraftActionContext(getState(),snapshot.entity_id),editable,busy,onError});
  return actions;
}

// The source clip belongs to the retail donor; the NPC has no runtime animation identity.
export function npcDonorAnimationBinding(state,entityId,preview){
  if(!['imported_scene_animation_frame0','authored_scene_animation_frame0'].includes(preview?.pose_kind))return null;
  const draft=state.actor_drafts?.[entityId],authored=state.authored_assets?.find(row=>row.id===entityId);
  if(!draft||draft.scene_id!==state.scene?.id||!authored)return null;
  const assetId=npcDonorModel({id:entityId,type:'actor',sceneId:state.scene.id,authoredRecord:authored});
  if(!assetId)return null;
  if(preview.entity_id!==entityId||preview.kind!=='actor_draft'||preview.donor_entity_id!==draft.donor_entity_id||preview.asset_id!==assetId||authored.donor_entity_id!==draft.donor_entity_id||authored.name!==draft.name)throw new Error('NPC animation snapshot differs from its retail donor assignment.');
  return {assetId,entityId:draft.appearance?.donor_entity_id??draft.donor_entity_id,clipId:preview.pose_kind==='authored_scene_animation_frame0'?'authored-channels':'scene-header',representation:preview.pose_kind==='authored_scene_animation_frame0'?'authored':'imported'};
}

export function npcAnimationSceneTarget(state,scene,preview,sourceEntityId,entityId){
  const draft=state.actor_drafts?.[entityId],authored=state.authored_assets?.find(row=>row.id===entityId);
  if(!draft||draft.scene_id!==state.scene?.id||scene?.scene_id!==state.scene.id||scene.source_key!==state.scene_preview_source_key||!authored)throw new Error('NPC animation scene source changed. Refresh the scene.');
  const assetId=npcDonorModel({id:entityId,type:'actor',sceneId:state.scene.id,authoredRecord:authored}),targets=scene.entities?.filter(row=>row.entity_id===entityId);
  if(!assetId||preview?.semantic_id!==assetId||sourceEntityId!==null&&sourceEntityId!==(draft.appearance?.donor_entity_id??draft.donor_entity_id)||targets?.length!==1)throw new Error('NPC animation scene target differs from its recorded donor model.');
  const target=targets[0];
  if(target.kind!=='actor_draft'||target.donor_entity_id!==draft.donor_entity_id||target.asset_id!==assetId||['x','z'].some(axis=>target.authored_position?.[axis]!==draft.position?.[axis]))throw new Error('NPC animation scene target differs from authored placement.');
  return entityId;
}

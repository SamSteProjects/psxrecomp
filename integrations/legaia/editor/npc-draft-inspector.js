import {npcDonorModel} from './asset-inspector.js';
import {componentDefinition,renderComponentProperties,renderComponentDetails} from './component-inspector.js';
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Read SDK snapshots only. The NPC authoring adapter owns commands and validation.
export function renderNpcDraftInspector(schema,snapshot,previewState){
  if(typeof snapshot?.entity_id!=='string'||!snapshot.draft||!['current','pending','source-during-proposal','unavailable'].includes(previewState))throw new Error('NPC draft inspector requires source and preview state.');
  const status={current:'Current authored scene preview snapshot.',pending:'Previous preview snapshot — refresh pending. Current source is not yet qualified.','source-during-proposal':'Source preview snapshot while a detached scene proposal is active. Proposed viewport coordinates are not substituted; authored placement remains separate.',unavailable:'No NPC draft preview snapshot in this view. Missing values remain unknown.'};
  return ['NpcDraftIdentity','NpcDraftTransform','NpcDraftPreview'].map(id=>{
    const definition=componentDefinition(schema,id);
    if(definition.layout!=='read-only-properties'||definition.properties.some(p=>p.authoring))throw new Error('NPC draft snapshot properties must be read only.');
    const note=id==='NpcDraftPreview'?`<p class="field-note" data-npc-preview-state="${previewState}" role="status">${escape(status[previewState])}</p>`:'';
    return `<section class="component" data-npc-draft-component="${id}"><h3>${escape(definition.label)}${definition.units?` <small>${escape(definition.units)}</small>`:''}</h3>${note}${renderComponentProperties(schema,id,snapshot)}${renderComponentDetails(schema,id,snapshot)}</section>`;
  }).join('');
}

// The source clip belongs to the retail donor; the NPC has no runtime animation identity.
export function npcDonorAnimationBinding(state,entityId,preview){
  if(!['imported_scene_animation_frame0','authored_scene_animation_frame0'].includes(preview?.pose_kind))return null;
  const draft=state.actor_drafts?.[entityId],authored=state.authored_assets?.find(row=>row.id===entityId);
  if(!draft||draft.scene_id!==state.scene?.id||!authored)return null;
  const assetId=npcDonorModel({id:entityId,type:'actor',sceneId:state.scene.id,authoredRecord:authored});
  if(!assetId)return null;
  if(preview.entity_id!==entityId||preview.kind!=='actor_draft'||preview.donor_entity_id!==draft.donor_entity_id||preview.asset_id!==assetId||authored.donor_entity_id!==draft.donor_entity_id||authored.name!==draft.name)throw new Error('NPC animation snapshot differs from its retail donor assignment.');
  return {assetId,entityId:draft.donor_entity_id,clipId:preview.pose_kind==='authored_scene_animation_frame0'?'authored-channels':'scene-header',representation:preview.pose_kind==='authored_scene_animation_frame0'?'authored':'imported'};
}

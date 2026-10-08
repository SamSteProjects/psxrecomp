// Selection uses the Project command result, never array order or a guessed UUID.
export function captureNpcCreation(state,command){
  if(state.project?.mode!=='edit'||!state.project?.path||!state.scene?.id||command?.type!=='create_actor_draft'||!state.scene.entities?.some(entity=>entity.id===command.donor_entity_id))throw Error('NPC creation source is unavailable');
  return structuredClone({projectPath:state.project.path,sceneId:state.scene.id,donorId:command.donor_entity_id,name:command.name,position:command.position,existing:state.actor_drafts??{}});
}
export function createdNpcSelection(state,capture){
  if(state.project?.mode!=='edit'||state.project?.path!==capture.projectPath||state.scene?.id!==capture.sceneId)throw Error('NPC created; Project or scene changed before selection');
  const drafts=state.actor_drafts??{},ids=Object.keys(drafts).filter(id=>!Object.hasOwn(capture.existing,id));
  const id=ids[0],draft=drafts[id];
  if(ids.length!==1||!id.startsWith('authored-actor://')||draft.scene_id!==capture.sceneId||draft.donor_entity_id!==capture.donorId||draft.name!==capture.name||draft.position?.x!==capture.position?.x||draft.position?.z!==capture.position?.z||Object.keys(capture.existing).some(old=>JSON.stringify(capture.existing[old])!==JSON.stringify(drafts[old])))throw Error('NPC created; returned draft identity is ambiguous or differs from the requested creation. Select it in the hierarchy.');
  return id;
}

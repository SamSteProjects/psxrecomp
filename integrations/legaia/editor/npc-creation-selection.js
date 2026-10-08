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
const canonical=value=>JSON.stringify(value&&typeof value==='object'?Array.isArray(value)?value.map(v=>JSON.parse(canonical(v))):Object.fromEntries(Object.keys(value).sort().map(k=>[k,JSON.parse(canonical(value[k]))])):value);
export function captureNpcPresetCreation(state,report){
  if(report?.schema_version!=='legaia.npc-preset-review.v1'||report.project_source_key!==state.project_copy_source_key||report.scene_preview_source_key!==state.scene_preview_source_key||report.scene_id!==state.scene?.id||report.gameplay_verified!==false||!/^authored-actor:\/\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(report.entity_id??'')||Object.hasOwn(state.actor_drafts??{},report.entity_id)||report.draft?.scene_id!==report.scene_id)throw Error('NPC preset creation source is unavailable');
  const capture=captureNpcCreation(state,{type:'create_actor_draft',donor_entity_id:report.draft.donor_entity_id,name:report.draft.name,position:report.draft.position});
  return {...capture,plannedId:report.entity_id,draft:structuredClone(report.draft)};
}
export function createdNpcPresetSelection(state,capture){
  const id=createdNpcSelection(state,capture);
  if(id!==capture.plannedId||canonical(state.actor_drafts[id])!==canonical(capture.draft))throw Error('NPC preset created; returned identity or components differ from the reviewed instance. Select it in the hierarchy.');
  return id;
}

export const modelUsageContext=state=>JSON.stringify([state.project?.path,state.scenes,state.model_references]);
export function effectiveModelUsers(state,modelId,sceneId){
  if(typeof modelId!=='string'||!state.scenes?.some(scene=>scene.id===sceneId)||!Array.isArray(state.model_references))throw new Error('Model usage source scene is unavailable');
  const rows=state.model_references.filter(row=>row.target_id===modelId&&row.scene_id===sceneId&&row.kind==='initial_model_assignment'&&row.effective===true);
  const ids=rows.map(row=>row.source_id).sort();
  if(new Set(ids).size!==ids.length||ids.some(id=>typeof id!=='string'||!id.startsWith(sceneId+'/actors/')))throw new Error('Effective model users have ambiguous source identities');
  return ids;
}
export function validateModelUserSelection(state,modelId,sceneId,expected){
  const ids=effectiveModelUsers(state,modelId,sceneId),entities=state.scene?.entities??[];
  if(state.scene?.id!==sceneId||ids.length<2||ids.length>128||JSON.stringify(ids)!==JSON.stringify(expected)||ids.some(id=>{const entity=entities.find(row=>row.id===id);return !entity||(entity.components?.ActorAppearance?.effective?.asset_id??entity.components?.ModelRenderer?.asset_id)!==modelId;}))throw new Error('Model users changed or differ from the active imported scene');
  return ids.slice();
}

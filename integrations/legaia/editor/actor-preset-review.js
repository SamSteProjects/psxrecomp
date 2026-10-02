import {decodeGroupAppearanceScene} from './group-appearance.js';
import {decodeActorPlacementScene} from './actor-placement-batch.js';
import {ANIMATION_PRESET_SCOPE,presetReviewContext,validatePresetComponentChange,decodePresetAnimationScene,appendPresetAnimationLayers,presetScopeLabel} from './preset-animation.js';
export function decodeActorPresetReview(value,template,entity,state){
  const layers=value?.layers,transform=entity.components?.Transform,axes=template.components.Transform?.position??{};
  if(value?.schema_version!=='legaia.actor-preset-review.v1'||value.template_id!==template.id||value.entity_id!==entity.id||value.scope!==template.scope||!['authored-actor-preset-v1',ANIMATION_PRESET_SCOPE].includes(value.scope)||!/^[0-9a-f]{64}$/.test(value.review_key)||typeof value.changed!=='boolean'||!layers||!Array.isArray(value.build_issues)||!Array.isArray(value.limitations))throw new Error('Preset review differs from the selected source/target');
  for(const axis of ['x','y','z']){const imported=transform?.imported?.position?.[axis],effective=transform?.effective?.position?.[axis]??imported,proposed=Object.hasOwn(axes,axis)?axes[axis]:effective;
    if(layers.imported_position?.[axis]!==imported||layers.effective_position?.[axis]!==effective||layers.proposed_position?.[axis]!==proposed)throw new Error('Preset position layers differ from the current actor');}
  const authored=entity.components?.ActorAppearance?.authored?.donor_entity_id??null,donor=template.components.ActorAppearance?.donor_entity_id??authored;
  if(layers.authored_donor!==authored||layers.proposed_donor!==donor||template.components.ActorAppearance&&value.appearance?.donor_entity_id!==donor||!template.components.ActorAppearance&&value.appearance!==null)throw new Error('Preset appearance differs from the captured component');
  validatePresetComponentChange(value,template,entity,state.scene.id);
  return structuredClone(value);
}
export function decodeActorPresetScene(response,report,current){
  if(response?.schema_version!=='legaia.actor-preset-scene.v1'||response.review_key!==report.review_key||response.project_source_key!==current?.source_key||response.scene_id!==current.scene_id)throw new Error('Preset scene identity differs from review');
  const proposed=response.scene,target=proposed?.entities?.find(row=>row.entity_id===report.entity_id),original=current.entities.find(row=>row.entity_id===report.entity_id);
  if(!target||!original)throw new Error('Preset scene target is missing');
  const placement={scene_id:current.scene_id,review_key:report.review_key,targets:[{entity_id:report.entity_id,proposed:report.layers.proposed_position}]};
  decodeActorPlacementScene({schema_version:'legaia.actor-placement-scene.v1',scene_id:current.scene_id,project_source_key:response.project_source_key,review_key:report.review_key,positions:[target]},placement,current.source_key);
  const expectedMatrix=[1,0,0,target.display_position.x,0,-1,0,target.display_position.y,0,0,1,target.display_position.z,0,0,0,1];
  if(JSON.stringify(target.model_to_scene)!==JSON.stringify(expectedMatrix)||JSON.stringify(target.authored_position)!==JSON.stringify(report.after?.Transform?.position??{})||
    (target.preview_ground_sample!==null&&(target.preview_height_status!=='source_surface'||target.preview_ground_sample?.y!==target.preview_position.y)))throw new Error('Preset scene placement layers differ from review');
  // After verifying placement, reuse the donor/unchanged-owner geometry checks.
  const normalized=structuredClone(proposed),normalizedTarget=normalized.entities.find(row=>row.entity_id===report.entity_id);
  for(const key of ['position','preview_position','preview_ground_sample','display_position','preview_height_status','model_to_scene','authored_position'])normalizedTarget[key]=structuredClone(original[key]);
  if(JSON.stringify(target.evidence?.heading)!==JSON.stringify(original.evidence?.heading)||JSON.stringify(target.evidence?.scale)!==JSON.stringify(original.evidence?.scale)||target.evidence?.position!==original.evidence?.position)throw new Error('Preset changed unrelated placement evidence');
  normalizedTarget.evidence=structuredClone(original.evidence);
  if(report.scope===ANIMATION_PRESET_SCOPE||report.animation)decodePresetAnimationScene(normalized,current,[{...report,proposed_donor:report.layers.proposed_donor}]);
  else decodeGroupAppearanceScene({...response,schema_version:'legaia.actor-appearance-scene.v1',scene:normalized},
    {scene_id:current.scene_id,review_key:report.review_key,donor_entity_id:report.layers.proposed_donor,targets:[{entity_id:report.entity_id}],options:[report.appearance]},current);
  return structuredClone(proposed);
}
export async function openActorPresetReview({template,entity,getState,canEdit,isBusy,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  if(!canEdit()||isBusy())return;
  const context=()=>presetReviewContext(getState(),[entity.id],template.id),key=context();
  const dialog=document.createElement('dialog');dialog.id='actor-preset-review';dialog.className='project-dialog';
  dialog.innerHTML='<h2>Review actor preset</h2><p data-summary>Verifying source and target…</p><div data-result></div><p class="dialog-error" role="alert"></p><button data-inspect disabled>Inspect actor preset in scene</button><button data-apply disabled>Apply reviewed actor preset</button><button data-close>Close</button>';
  document.body.append(dialog);const controller=new AbortController();let report=null,keepClose=false;
  const current=()=>dialog.open&&canEdit()&&key===context();
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}controller.abort();dialog.remove();});dialog.showModal();setBusy(true);
  try{
    const response=await fetch('/api/actor-preset-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id,entity_id:entity.id}),signal:controller.signal}),value=await response.json();
    if(!response.ok||value.error)throw new Error(value.error??'Preset review failed');if(!current())return;
    report=decodeActorPresetReview(value,template,entity,getState());dialog.querySelector('[data-summary]').textContent=`${template.name} · ${presetScopeLabel(template.scope)} → ${entity.name}: ${value.changed?'one Apply / Undo entry':'already matches; no command needed'}`;
    const table=document.createElement('table'),header=document.createElement('tr');for(const text of ['Property','Imported','Authored','Effective','Proposed']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
    for(const axis of ['x','y','z']){const row=document.createElement('tr');for(const text of [axis.toUpperCase(),value.layers.imported_position[axis],value.layers.authored_position[axis],value.layers.effective_position[axis],value.layers.proposed_position[axis]]){const cell=document.createElement('td');cell.textContent=text??'Unknown / inherit';row.append(cell);}table.append(row);}
    const result=dialog.querySelector('[data-result]');result.append(table);const donor=document.createElement('p');donor.textContent=`Authored appearance donor: ${value.layers.authored_donor??'inherit'} → ${value.layers.proposed_donor??'inherit'}`;result.append(donor);appendPresetAnimationLayers(result,report.animation);
    for(const note of [...value.build_issues,...value.limitations]){const p=document.createElement('p');p.className='field-note';p.textContent=note;result.append(p);}
    dialog.querySelector('[data-apply]').disabled=!value.changed;dialog.querySelector('[data-inspect]').disabled=!canInspectScene();
  }catch(error){if(error.name!=='AbortError'&&dialog.open)dialog.querySelector('[role="alert"]').textContent=error.message;}
  finally{setBusy(false);}
  dialog.querySelector('[data-inspect]')?.addEventListener('click',async()=>{
    if(!current()||isBusy()||!report||!canInspectScene())return;
    const accepted=report,base=getScenePreview();setBusy(true);dialog.querySelector('[data-inspect]').disabled=true;dialog.querySelector('[data-apply]').disabled=true;
    try{
      const response=await fetch('/api/actor-preset-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id,entity_id:entity.id,review_key:accepted.review_key}),signal:controller.signal}),value=await response.json();
      if(!response.ok||value.error)throw new Error(value.error??'Preset scene inspection failed');
      if(!current()||report!==accepted)return;
      if(!canInspectScene()||getScenePreview()!==base)throw new Error('Current scene changed during preset inspection');
      const proposed=decodeActorPresetScene(value,accepted,base);
      const isCurrent=()=>canEdit()&&key===context()&&report===accepted&&!controller.signal.aborted;
      const returnToReview=()=>{if(!isCurrent())return false;dialog.showModal();dialog.querySelector('[data-apply]').disabled=!report.changed;dialog.querySelector('[data-inspect]').disabled=!canInspectScene();return true;};
      inspectScene(proposed,accepted,returnToReview,isCurrent,()=>{report=null;controller.abort();dialog.remove();});keepClose=true;dialog.close();
    }catch(error){if(error.name!=='AbortError'&&current())dialog.querySelector('[role="alert"]').textContent=error.message;}
    finally{setBusy(false);if(dialog.open){dialog.querySelector('[data-inspect]').disabled=!current()||!canInspectScene();dialog.querySelector('[data-apply]').disabled=!current()||!report?.changed;}}
  });
  dialog.querySelector('[data-apply]')?.addEventListener('click',async()=>{if(!current()||isBusy()||!report?.changed)return;const accepted=report;report=null;dialog.querySelector('[data-apply]').disabled=true;if(await api('/api/command',{type:'apply_actor_template',template_id:template.id,entity_id:entity.id,review_key:accepted.review_key}))dialog.close();else if(dialog.open)dialog.querySelector('[role="alert"]').textContent='Preset or target changed. Close and review again.';});
}

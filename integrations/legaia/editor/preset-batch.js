import {decodeGroupAppearanceScene} from './group-appearance.js';
import {decodeActorPlacementScene} from './actor-placement-batch.js';
import {ANIMATION_PRESET_SCOPE,presetReviewContext,validatePresetComponentChange,decodePresetAnimationScene,appendPresetAnimationLayers,presetScopeLabel} from './preset-animation.js';
export function decodePresetBatchScene(response,report,current){
  const scene=response?.scene;
  if(response?.schema_version!=='legaia.actor-preset-batch-scene.v1'||response.review_key!==report.review_key||response.project_source_key!==current?.source_key||response.scene_id!==report.scene_id||scene?.schema!=='legaia.scene-preview.v1'||scene.scene_id!==current.scene_id||scene.representation!=='authored'||scene.coordinate_system!==current.coordinate_system||JSON.stringify(scene.position_to_display)!==JSON.stringify(current.position_to_display)||!Array.isArray(scene.entities)||scene.entities.length!==current.entities.length||scene.entities.length>512||!Array.isArray(scene.assets)||scene.assets.length>128)throw new Error('Group preset scene differs from the reviewed source');
  const owners=new Map(scene.entities.map(row=>[row.entity_id,row])),originals=new Map(current.entities.map(row=>[row.entity_id,row]));if(owners.size!==scene.entities.length||new Set(scene.assets.map(row=>row.geometry_key)).size!==scene.assets.length)throw new Error('Group preset scene has ambiguous owners or geometry');
  const targets=report.targets.map(row=>owners.get(row.entity_id));if(targets.some(row=>!row))throw new Error('Group preset scene target is missing');
  decodeActorPlacementScene({schema_version:'legaia.actor-placement-scene.v1',scene_id:scene.scene_id,project_source_key:response.project_source_key,review_key:report.review_key,positions:targets},{scene_id:report.scene_id,review_key:report.review_key,targets:report.targets.map(row=>({entity_id:row.entity_id,proposed:row.proposed_position}))},current.source_key);
  const normalized=structuredClone(scene);
  for(const row of report.targets){const target=owners.get(row.entity_id),original=originals.get(row.entity_id),copy=normalized.entities.find(item=>item.entity_id===row.entity_id);
    const matrix=[1,0,0,target.display_position.x,0,-1,0,target.display_position.y,0,0,1,target.display_position.z,0,0,0,1];
    if(!original||JSON.stringify(target.model_to_scene)!==JSON.stringify(matrix)||JSON.stringify(target.authored_position)!==JSON.stringify(row.after?.Transform?.position??{})||(target.preview_ground_sample!==null&&(target.preview_height_status!=='source_surface'||target.preview_ground_sample?.y!==target.preview_position.y))||JSON.stringify(target.evidence?.heading)!==JSON.stringify(original.evidence?.heading)||JSON.stringify(target.evidence?.scale)!==JSON.stringify(original.evidence?.scale)||target.evidence?.position!==original.evidence?.position)throw new Error('Group preset placement layers differ from review');
    for(const key of ['position','preview_position','preview_ground_sample','display_position','preview_height_status','model_to_scene','authored_position','evidence'])copy[key]=structuredClone(original[key]);
  }
  if(report.scope===ANIMATION_PRESET_SCOPE||report.targets.some(row=>row.animation)){
    decodePresetAnimationScene(normalized,current,report.targets);
  }else if(report.scope==='authored-position-v1'){
    if(JSON.stringify(normalized.entities)!==JSON.stringify(current.entities)||JSON.stringify(normalized.assets)!==JSON.stringify(current.assets))throw new Error('Position preset changed unrelated owners or geometry');
  }else{
    const donor=report.targets[0]?.proposed_donor,options=report.targets.map(row=>row.appearance);
    if(options.some(option=>!option||option.donor_entity_id!==donor||option.asset_id!==options[0].asset_id)||report.targets.some(row=>row.proposed_donor!==donor))throw new Error('Group preset donor options differ from review');
    decodeGroupAppearanceScene({...response,schema_version:'legaia.actor-appearance-scene.v1',scene:normalized},{scene_id:report.scene_id,review_key:report.review_key,donor_entity_id:donor,targets:report.targets,options},current);
  }
  return structuredClone(scene);
}
export function decodePresetBatch(value,template,ids,state){
  const ordered=[...ids].sort(),targets=value?.targets,actors=new Map((state.scene?.entities??[]).map(row=>[row.id,row]));
  if(value?.schema_version!=='legaia.actor-preset-batch.v1'||value.scene_id!==state.scene?.id||value.template_id!==template.id||value.scope!==template.scope||value.source_scene_id!==template.source.scene_id||!/^[0-9a-f]{64}$/.test(value.review_key)||!/^[0-9a-f]{64}$/.test(value.source_import_sha256)||!Array.isArray(targets)||ordered.length<2||ordered.length>128||new Set(ordered).size!==ordered.length||JSON.stringify(targets.map(row=>row.entity_id))!==JSON.stringify(ordered)||!Number.isInteger(value.changed_count)||value.changed_count!==targets.filter(row=>row.changed===true).length)throw new Error('Preset group response differs from the selected source and targets');
  for(const row of targets){const actor=actors.get(row.entity_id),transform=actor?.components?.Transform,axes=template.components.Transform?.position??{};
    if(!actor||typeof row.changed!=='boolean'||!Array.isArray(row.build_issues))throw new Error('Preset group target is unavailable');
    for(const axis of ['x','y','z']){const imported=transform?.imported?.position?.[axis],effective=transform?.effective?.position?.[axis]??imported,proposed=Object.hasOwn(axes,axis)?axes[axis]:effective;
      if(row.imported_position?.[axis]!==imported||row.effective_position?.[axis]!==effective||row.proposed_position?.[axis]!==proposed)throw new Error('Preset group position layers differ from the current scene');}
    if(template.components.ActorAppearance&&row.proposed_donor!==template.components.ActorAppearance.donor_entity_id)throw new Error('Preset group donor differs from the selected preset');
    if(!template.components.ActorAppearance&&row.proposed_donor!==row.authored_donor)throw new Error('Position preset changed appearance');
    if(template.scope===ANIMATION_PRESET_SCOPE||row.animation)validatePresetComponentChange(row,template,actor,state.scene.id);
  }
  return structuredClone(value);
}
export function mountPresetBatch({after,getState,getSelection,isBusy,canEdit,canAuthor=canEdit,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  const button=document.createElement('button');button.dataset.groupPresets='';button.textContent='Apply preset to group';after.append(button);let session=null;
  const signature=()=>presetReviewContext(getState(),getSelection());
  const eligible=()=>canAuthor()&&getState().capabilities?.actor_preset_batch&&getSelection().length>=2&&getSelection().length<=128&&getState().actor_templates?.length;
  const sync=()=>{button.disabled=isBusy()||!eligible();if(session?.dialog.open&&session.key!==signature())session.dialog.close();};
  button.onclick=()=>{
    if(button.disabled)return;const state=getState(),ids=getSelection().slice(),key=signature(),controller=new AbortController(),dialog=document.createElement('dialog');dialog.id='preset-batch-dialog';dialog.className='project-dialog';
    dialog.innerHTML='<h2>Apply actor preset to group</h2><p>Review every target before one Apply / Undo command. Saved position axes are absolute for each actor and may overlap the group.</p><label>Actor preset<select data-preset aria-label="Group actor preset"></select></label><button data-review>Review group preset</button><p data-summary></p><div data-results></div><p class="dialog-error" role="alert"></p><button data-inspect disabled>Inspect group preset in scene</button><button data-apply disabled>Apply reviewed preset to group</button><button data-close>Close</button>';document.body.append(dialog);
    session={dialog,key};let report=null,keepClose=false;
    const dispose=()=>{report=null;controller.abort();dialog.remove();if(session?.dialog===dialog)session=null;};
    const current=()=>dialog.open&&key===signature()&&canAuthor()&&!controller.signal.aborted;
    const select=dialog.querySelector('[data-preset]');for(const template of state.actor_templates){const option=document.createElement('option');option.value=template.id;option.textContent=`${template.name} · ${presetScopeLabel(template.scope)}`;select.append(option);}
    select.onchange=()=>{report=null;dialog.querySelector('[data-inspect]').disabled=true;dialog.querySelector('[data-apply]').disabled=true;dialog.querySelector('[data-results]').replaceChildren();dialog.querySelector('[data-summary]').textContent='Review the selected preset.';};
    dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;return;}dispose();});
    dialog.querySelector('[data-review]').onclick=async()=>{
      if(isBusy()||!current())return;report=null;dialog.querySelector('[data-inspect]').disabled=true;dialog.querySelector('[data-results]').replaceChildren();dialog.querySelector('[data-summary]').textContent='Verifying preset source and every target…';const template=getState().actor_templates.find(row=>row.id===select.value);if(!template)return;
      dialog.querySelector('[data-apply]').disabled=true;dialog.querySelector('[data-review]').disabled=true;select.disabled=true;dialog.querySelector('[role="alert"]').textContent='';setBusy(true);
      try{const response=await fetch('/api/actor-preset-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id,actor_ids:ids}),signal:controller.signal}),value=await response.json();
        if(!response.ok||value.error)throw new Error(value.error??'Group preset review failed');if(!current())return;report=decodePresetBatch(value,template,ids,getState());
        dialog.querySelector('[data-summary]').textContent=`${template.name}: ${report.changed_count} of ${ids.length} actors change in one command.`;
        const result=dialog.querySelector('[data-results]');result.replaceChildren();const table=document.createElement('table'),header=document.createElement('tr');for(const text of ['Actor','Imported XYZ','Effective XYZ','Proposed XYZ','Authored → proposed donor']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
        const xyz=p=>['x','y','z'].map(axis=>p[axis]??'Unknown').join(' / ');
        for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,xyz(row.imported_position),xyz(row.effective_position),xyz(row.proposed_position),`${row.authored_donor??'inherit'} → ${row.proposed_donor??'inherit'}`]){const cell=document.createElement('td');cell.textContent=text;tr.append(cell);}table.append(tr);}result.append(table);
        for(const row of report.targets)if(row.animation){const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=row.entity_id;section.append(heading);appendPresetAnimationLayers(section,row.animation);result.append(section);}
        for(const note of [...new Set([...report.limitations,...report.targets.flatMap(row=>row.build_issues)])]){const p=document.createElement('p');p.className='field-note';p.textContent=note;result.append(p);}
        const details=document.createElement('details');details.innerHTML='<summary>Complete authored component changes</summary><pre></pre>';details.querySelector('pre').textContent=JSON.stringify(report.targets,null,2);result.append(details);dialog.querySelector('[data-apply]').disabled=!report.changed_count;dialog.querySelector('[data-inspect]').disabled=!canInspectScene();
      }catch(error){if(error.name!=='AbortError'&&current())dialog.querySelector('[role="alert"]').textContent=error.message;}
      finally{setBusy(false);if(dialog.open){select.disabled=false;dialog.querySelector('[data-review]').disabled=!current();}}
    };
    dialog.querySelector('[data-inspect]').onclick=async()=>{
      if(isBusy()||!current()||!report||!canInspectScene())return;const accepted=report,base=getScenePreview();setBusy(true);dialog.querySelector('[data-review]').disabled=true;dialog.querySelector('[data-inspect]').disabled=true;dialog.querySelector('[data-apply]').disabled=true;select.disabled=true;
      try{const response=await fetch('/api/actor-preset-batch-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:accepted.template_id,actor_ids:ids,review_key:accepted.review_key}),signal:controller.signal}),value=await response.json();
        if(!response.ok||value.error)throw new Error(value.error??'Group preset scene inspection failed');if(!current()||report!==accepted)return;
        if(!canInspectScene()||getScenePreview()!==base)throw new Error('Current scene changed during group preset inspection');const proposed=decodePresetBatchScene(value,accepted,base);
        const isCurrent=()=>key===signature()&&canEdit()&&report===accepted&&!controller.signal.aborted;
        const returnToReview=()=>{if(!isCurrent())return false;dialog.showModal();dialog.querySelector('[data-review]').disabled=false;dialog.querySelector('[data-apply]').disabled=!report.changed_count;dialog.querySelector('[data-inspect]').disabled=!canInspectScene();select.disabled=false;return true;};
        inspectScene(proposed,accepted,returnToReview,isCurrent,dispose);keepClose=true;dialog.close();
      }catch(error){if(error.name!=='AbortError'&&current())dialog.querySelector('[role="alert"]').textContent=error.message;}
      finally{setBusy(false);if(dialog.open){select.disabled=false;dialog.querySelector('[data-review]').disabled=!current();dialog.querySelector('[data-inspect]').disabled=!current()||!report||!canInspectScene();dialog.querySelector('[data-apply]').disabled=!current()||!report?.changed_count;}}
    };
    dialog.querySelector('[data-apply]').onclick=async()=>{if(isBusy()||!current()||!report?.changed_count)return;const accepted=report;report=null;dialog.querySelector('[data-apply]').disabled=true;if(await api('/api/command',{type:'apply_actor_preset_batch',template_id:accepted.template_id,actor_ids:ids,review_key:accepted.review_key},{success:'Group preset applied in one Undo command.'}))dialog.close();else{await api('/api/state',undefined);if(dialog.open)dialog.querySelector('[role="alert"]').textContent='Preset or group changed. Review again.';}};
    dialog.showModal();
  };
  return {synchronize:sync};
}

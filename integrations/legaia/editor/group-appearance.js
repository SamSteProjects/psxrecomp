import {MAX_PREVIEW_ENTITIES} from './scene-limits.js';
// Accept a complete SDK projection only when owners and placement remain bound.
function sharedGeometryContent(preview){
  const value=structuredClone(preview);
  // Deduplicated initial poses can name a different first source actor while
  // retaining the same model, animation, frame, vertices and texture content.
  if(value?.pose){delete value.pose.actor_semantic_id;if(value.pose.association)delete value.pose.association.actor_source_record;}
  return value;
}

export function decodeGroupAppearanceScene(response, report, current){
  const proposed=response?.scene;
  if(response?.schema_version!=='legaia.actor-appearance-scene.v1'||response.review_key!==report.review_key||response.project_source_key!==current?.source_key||response.scene_id!==report.scene_id||proposed?.schema!=='legaia.scene-preview.v1'||proposed.scene_id!==current.scene_id||proposed.representation!=='authored'||proposed.coordinate_system!==current.coordinate_system||JSON.stringify(proposed.position_to_display)!==JSON.stringify(current.position_to_display)||!Array.isArray(proposed.entities)||proposed.entities.length!==current.entities.length||proposed.entities.length>MAX_PREVIEW_ENTITIES||!Array.isArray(proposed.assets)||proposed.assets.length>128)throw new Error('Group appearance scene identity differs from review');
  const selected=new Set(report.targets.map(row=>row.entity_id)),donor=report.options.find(row=>row.donor_entity_id===report.donor_entity_id),owners=new Map(proposed.entities.map(row=>[row.entity_id,row])),assets=new Map(proposed.assets.map(row=>[row.geometry_key,row])),sourceAssets=new Map(current.assets.map(row=>[row.geometry_key,row]));
  if([...selected].some(id=>!owners.has(id))||!donor||selected.size!==report.targets.length||owners.size!==proposed.entities.length||assets.size!==proposed.assets.length)throw new Error('Ambiguous group appearance scene');
  const binding=new Set(['geometry_key','asset_id','source_actor_id','source_record','model_reference','appearance_authored','pose_kind','reason','renderable']);
  for(const original of current.entities){
    const target=owners.get(original.entity_id);if(!target)throw new Error('Group appearance scene owner is missing');
    const strip=row=>Object.fromEntries(Object.entries(row).filter(([key])=>key!=='geometry_key'&&(!selected.has(row.entity_id)||!binding.has(key))));
    if(JSON.stringify(strip(original))!==JSON.stringify(strip(target)))throw new Error('Group appearance proposal changed placement or unrelated content');
    const geometry=assets.get(target.geometry_key);
    if(target.renderable&&(!geometry||geometry.asset_id!==target.asset_id))throw new Error('Group appearance geometry is missing');
    if(selected.has(target.entity_id)){
      const retainedAnimation=original.animation_assignment_authored===true&&target.animation_assignment_authored===true&&target.source_actor_id===original.source_actor_id&&JSON.stringify(target.source_record)===JSON.stringify(original.source_record)&&JSON.stringify(target.model_reference)===JSON.stringify(original.model_reference);
      if((target.source_actor_id!==report.donor_entity_id&&!retainedAnimation)||target.asset_id!==donor.asset_id||target.appearance_authored!==true)throw new Error('Group appearance donor binding differs from review');
    }else if(target.renderable&&JSON.stringify(sharedGeometryContent(geometry?.preview))!==JSON.stringify(sharedGeometryContent(sourceAssets.get(original.geometry_key)?.preview)))throw new Error('Group appearance changed unrelated geometry');
  }
  return structuredClone(proposed);
}

export function groupAppearanceChoices(options,modelAssetId=null){
  if(modelAssetId!==null&&(typeof modelAssetId!=='string'||!modelAssetId.startsWith('asset://')||modelAssetId.length>1024))throw Error('Choose a qualified model asset identity.');
  return structuredClone(options.filter(row=>modelAssetId===null||row.asset_id===modelAssetId));
}
// Group initial-pair authoring consumes source-qualified SDK reports only.
export function mountGroupAppearance({after,getState,getSelection,isBusy,canEdit,setBusy,api,canInspectScene,getScenePreview,inspectScene}){
  const button=document.createElement('button');button.dataset.groupAppearance='';button.textContent='Group appearance…';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='group-appearance-dialog';document.body.append(dialog);
  let generation=0,controller=null,review=null,keepClose=false,timer=null;
  const key=()=>{const s=getState();return JSON.stringify([s.project?.path,s.scene?.id,s.scene_preview_source_key,s.project_copy_source_key,getSelection()]);};
  dialog.addEventListener('close',()=>{if(keepClose){keepClose=false;clearInterval(timer);return;}clearInterval(timer);generation++;review=null;if(controller){controller.abort();controller=null;setBusy(false);}});
  const open=(modelAssetId=null)=>{
    if(isBusy()||!canEdit()||getSelection().length<2||dialog.open)return;
    groupAppearanceChoices([],modelAssetId);
    const ids=getSelection().slice(),context=key();let options=[];
    dialog.replaceChildren();const heading=document.createElement('h2'),note=document.createElement('p'),select=document.createElement('select'),preview=document.createElement('button'),apply=document.createElement('button'),inspect=document.createElement('button'),result=document.createElement('div'),error=document.createElement('p'),close=document.createElement('button');
    heading.textContent='Actor group appearance';note.textContent=`${ids.length} actors · assign one source-verified initial model/animation pair. Runtime script scheduling and gameplay compatibility remain unverified.`;if(modelAssetId!==null)note.textContent+=' Model asset: '+modelAssetId+'. Choose a shared verified witness explicitly.';select.setAttribute('aria-label','Group appearance donor');preview.textContent='Preview group appearance';preview.disabled=true;apply.textContent='Apply reviewed group appearance';apply.disabled=true;inspect.textContent='Inspect group appearance in scene';inspect.disabled=true;error.className='dialog-error';error.setAttribute('role','alert');close.textContent='Close group appearance';close.onclick=()=>dialog.close();dialog.append(heading,note,select,preview,inspect,apply,result,error,close);
    const current=()=>dialog.open&&canEdit()&&context===key();
    const withdraw=()=>{if(!dialog.open||current())return;generation++;review=null;controller?.abort();options=[];select.replaceChildren();result.replaceChildren();for(const control of [select,preview,inspect,apply])control.disabled=true;error.textContent='Project, scene or actor group changed. Reopen group appearance review.';};
    clearInterval(timer);timer=setInterval(withdraw,200);
    select.onchange=()=>{generation++;review=null;apply.disabled=true;inspect.disabled=true;preview.disabled=isBusy()||!current()||!options.some(o=>o.donor_entity_id===select.value);result.replaceChildren();};
    async function load(donor){
      const token=++generation;controller?.abort();const active=new AbortController();controller=active;review=null;apply.disabled=true;inspect.disabled=true;preview.disabled=true;select.disabled=true;setBusy(true);error.textContent='';result.replaceChildren();
      try{const response=await fetch('/api/actor-appearance-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({actor_ids:ids,donor_entity_id:donor}),signal:active.signal}),report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Group appearance preview failed');
        if(token!==generation||!current())return;
        if(report.schema_version!=='legaia.actor-appearance-batch.v1'||report.scene_id!==getState().scene.id||report.donor_entity_id!==donor||!Array.isArray(report.options)||report.options.some(o=>typeof o.donor_entity_id!=='string'||typeof o.asset_id!=='string')||!Array.isArray(report.targets)||report.targets.length!==ids.length||report.targets.some((row,index)=>row.entity_id!==ids[index])||typeof report.review_key!=='string'||!/^[0-9a-f]{64}$/.test(report.review_key))throw new Error('Invalid group appearance report');
        if(donor===null){options=groupAppearanceChoices(report.options,modelAssetId);select.replaceChildren();if(modelAssetId!==null){const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Choose a verified witness...';placeholder.disabled=true;placeholder.selected=true;select.append(placeholder);}for(const option of options){const item=document.createElement('option');item.value=option.donor_entity_id;item.textContent=option.label??option.donor_entity_id;select.append(item);}note.textContent+=` ${options.length} donors compatible with every actor.`;if(!options.length){if(modelAssetId!==null){const p=document.createElement('p');p.textContent='No shared verified donor pair uses this model.';result.append(p);}for(const row of (modelAssetId!==null&&report.options.length?[]:report.support??[])){const p=document.createElement('p');p.textContent=`${row.entity_id}: ${row.reason??'No common initial donor pair'}`;result.append(p);}}}
        else{if(!options.some(o=>o.donor_entity_id===donor)||report.targets.some(row=>row.proposed?.donor_entity_id!==donor))throw new Error('Proposal differs from the selected donor');review=report;const option=options.find(o=>o.donor_entity_id===donor),summary=document.createElement('p');summary.textContent=`Proposed model ${option.asset_id} · animation ${option.animation_id} · ${report.changed_count} actors change · not applied`;result.append(summary);
          for(const row of report.targets){const details=document.createElement('details'),title=document.createElement('summary'),data=document.createElement('pre');title.textContent=row.entity_id;data.className='diagnostic-detail';data.textContent=JSON.stringify({retail:row.retail,authored:row.authored,effective:row.effective,proposed:row.proposed},null,2);details.append(title,data);result.append(details);}}
      }catch(e){if(e.name!=='AbortError'&&token===generation&&current())error.textContent=e.message;}
      finally{if(controller===active){controller=null;setBusy(false);}select.disabled=isBusy()||!current()||!options.length;preview.disabled=isBusy()||!current()||!options.some(o=>o.donor_entity_id===select.value);apply.disabled=isBusy()||!current()||!review?.changed_count;inspect.disabled=isBusy()||!current()||!review||!canInspectScene();}
    }
    preview.onclick=()=>{if(!isBusy()&&current()&&options.some(o=>o.donor_entity_id===select.value))load(select.value);};
    inspect.onclick=async()=>{
      if(isBusy()||!current()||!review||!canInspectScene())return;
      const accepted=review,token=++generation,base=getScenePreview(),active=new AbortController();controller=active;setBusy(true);inspect.disabled=true;apply.disabled=true;preview.disabled=true;select.disabled=true;error.textContent='';
      try{
        const response=await fetch('/api/actor-appearance-batch-scene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({actor_ids:ids,donor_entity_id:accepted.donor_entity_id,review_key:accepted.review_key}),signal:active.signal}),body=await response.json();
        if(!response.ok||body.error)throw new Error(body.error||'Group appearance scene inspection failed');
        if(token!==generation||!current()||review!==accepted)return;
        const scene=decodeGroupAppearanceScene(body,accepted,base);
        if(!canInspectScene()||getScenePreview()!==base)throw new Error('Current scene changed during appearance inspection');
        const returnToReview=()=>{if(token!==generation||context!==key()||review!==accepted||!canEdit())return false;dialog.showModal();timer=setInterval(withdraw,200);select.disabled=false;preview.disabled=false;apply.disabled=!review.changed_count;inspect.disabled=!canInspectScene();return true;};
        inspectScene(scene,accepted,returnToReview);keepClose=true;dialog.close();
      }catch(e){if(e.name!=='AbortError'&&token===generation&&current())error.textContent=e.message;}
      finally{if(controller===active){controller=null;setBusy(false);}if(dialog.open){select.disabled=!current();preview.disabled=!current();apply.disabled=!current()||!review?.changed_count;inspect.disabled=!current()||!review||!canInspectScene();}}
    };
    apply.onclick=async()=>{if(isBusy()||!current()||!review?.changed_count)return;const accepted=review;review=null;apply.disabled=true;inspect.disabled=true;preview.disabled=true;select.disabled=true;
      if(await api('/api/command',{type:'set_actor_group_appearance',scene_id:accepted.scene_id,actor_ids:ids,donor_entity_id:accepted.donor_entity_id,review_key:accepted.review_key},{success:`Appearance assigned to ${accepted.changed_count} actors. Undo restores the group.`})){dialog.close();}
      else if(dialog.open){error.textContent='Group appearance rejected. Close and review the current group again.';}
    };
    dialog.showModal();load(null);
  };
  button.onclick=()=>open();return {open,button,dialog};
}

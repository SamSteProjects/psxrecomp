export function decodePresetBatch(value,template,ids,state){
  const ordered=[...ids].sort(),targets=value?.targets,actors=new Map((state.scene?.entities??[]).map(row=>[row.id,row]));
  if(value?.schema_version!=='legaia.actor-preset-batch.v1'||value.scene_id!==state.scene?.id||value.template_id!==template.id||value.scope!==template.scope||value.source_scene_id!==template.source.scene_id||!/^[0-9a-f]{64}$/.test(value.review_key)||!/^[0-9a-f]{64}$/.test(value.source_import_sha256)||!Array.isArray(targets)||ordered.length<2||ordered.length>128||new Set(ordered).size!==ordered.length||JSON.stringify(targets.map(row=>row.entity_id))!==JSON.stringify(ordered)||!Number.isInteger(value.changed_count)||value.changed_count!==targets.filter(row=>row.changed===true).length)throw new Error('Preset group response differs from the selected source and targets');
  for(const row of targets){const actor=actors.get(row.entity_id),transform=actor?.components?.Transform,axes=template.components.Transform?.position??{};
    if(!actor||typeof row.changed!=='boolean'||!Array.isArray(row.build_issues))throw new Error('Preset group target is unavailable');
    for(const axis of ['x','y','z']){const imported=transform?.imported?.position?.[axis],effective=transform?.effective?.position?.[axis]??imported,proposed=Object.hasOwn(axes,axis)?axes[axis]:effective;
      if(row.imported_position?.[axis]!==imported||row.effective_position?.[axis]!==effective||row.proposed_position?.[axis]!==proposed)throw new Error('Preset group position layers differ from the current scene');}
    if(template.components.ActorAppearance&&row.proposed_donor!==template.components.ActorAppearance.donor_entity_id)throw new Error('Preset group donor differs from the selected preset');
    if(!template.components.ActorAppearance&&row.proposed_donor!==row.authored_donor)throw new Error('Position preset changed appearance');
  }
  return structuredClone(value);
}
export function mountPresetBatch({after,getState,getSelection,isBusy,canEdit,setBusy,api}){
  const button=document.createElement('button');button.dataset.groupPresets='';button.textContent='Apply preset to group';after.append(button);let session=null;
  const signature=()=>JSON.stringify([getState().project?.path,getState().scene?.id,getState().scene_preview_source_key,getState().scene?.entities,getState().actor_templates,[...getSelection()].sort()]);
  const eligible=()=>canEdit()&&getState().capabilities?.actor_preset_batch&&getSelection().length>=2&&getSelection().length<=128&&getState().actor_templates?.length;
  const sync=()=>{button.disabled=isBusy()||!eligible();if(session?.dialog.open&&session.key!==signature())session.dialog.close();};
  button.onclick=()=>{
    if(button.disabled)return;const state=getState(),ids=getSelection().slice(),key=signature(),controller=new AbortController(),dialog=document.createElement('dialog');dialog.id='preset-batch-dialog';dialog.className='project-dialog';
    dialog.innerHTML='<h2>Apply actor preset to group</h2><p>Review every target before one Apply / Undo command. Saved position axes are absolute for each actor and may overlap the group.</p><label>Actor preset<select data-preset aria-label="Group actor preset"></select></label><button data-review>Review group preset</button><p data-summary></p><div data-results></div><p class="dialog-error" role="alert"></p><button data-apply disabled>Apply reviewed preset to group</button><button data-close>Close</button>';document.body.append(dialog);
    session={dialog,key};let report=null;
    const current=()=>dialog.open&&key===signature()&&canEdit()&&!controller.signal.aborted;
    const select=dialog.querySelector('[data-preset]');for(const template of state.actor_templates){const option=document.createElement('option');option.value=template.id;option.textContent=template.name;select.append(option);}
    select.onchange=()=>{report=null;dialog.querySelector('[data-apply]').disabled=true;dialog.querySelector('[data-results]').replaceChildren();dialog.querySelector('[data-summary]').textContent='Review the selected preset.';};
    dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();if(session?.dialog===dialog)session=null;});
    dialog.querySelector('[data-review]').onclick=async()=>{
      if(isBusy()||!current())return;report=null;dialog.querySelector('[data-results]').replaceChildren();dialog.querySelector('[data-summary]').textContent='Verifying preset source and every target…';const template=getState().actor_templates.find(row=>row.id===select.value);if(!template)return;
      dialog.querySelector('[data-apply]').disabled=true;dialog.querySelector('[data-review]').disabled=true;select.disabled=true;dialog.querySelector('[role="alert"]').textContent='';setBusy(true);
      try{const response=await fetch('/api/actor-preset-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:template.id,actor_ids:ids}),signal:controller.signal}),value=await response.json();
        if(!response.ok||value.error)throw new Error(value.error??'Group preset review failed');if(!current())return;report=decodePresetBatch(value,template,ids,getState());
        dialog.querySelector('[data-summary]').textContent=`${template.name}: ${report.changed_count} of ${ids.length} actors change in one command.`;
        const result=dialog.querySelector('[data-results]');result.replaceChildren();const table=document.createElement('table'),header=document.createElement('tr');for(const text of ['Actor','Imported XYZ','Effective XYZ','Proposed XYZ','Authored → proposed donor']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
        const xyz=p=>['x','y','z'].map(axis=>p[axis]??'Unknown').join(' / ');
        for(const row of report.targets){const tr=document.createElement('tr');for(const text of [row.entity_id,xyz(row.imported_position),xyz(row.effective_position),xyz(row.proposed_position),`${row.authored_donor??'inherit'} → ${row.proposed_donor??'inherit'}`]){const cell=document.createElement('td');cell.textContent=text;tr.append(cell);}table.append(tr);}result.append(table);
        for(const note of [...new Set([...report.limitations,...report.targets.flatMap(row=>row.build_issues)])]){const p=document.createElement('p');p.className='field-note';p.textContent=note;result.append(p);}
        const details=document.createElement('details');details.innerHTML='<summary>Complete authored component changes</summary><pre></pre>';details.querySelector('pre').textContent=JSON.stringify(report.targets,null,2);result.append(details);dialog.querySelector('[data-apply]').disabled=!report.changed_count;
      }catch(error){if(error.name!=='AbortError'&&current())dialog.querySelector('[role="alert"]').textContent=error.message;}
      finally{setBusy(false);if(dialog.open){select.disabled=false;dialog.querySelector('[data-review]').disabled=!current();}}
    };
    dialog.querySelector('[data-apply]').onclick=async()=>{if(isBusy()||!current()||!report?.changed_count)return;const accepted=report;report=null;dialog.querySelector('[data-apply]').disabled=true;if(await api('/api/command',{type:'apply_actor_preset_batch',template_id:accepted.template_id,actor_ids:ids,review_key:accepted.review_key},{success:'Group preset applied in one Undo command.'}))dialog.close();else{await api('/api/state',undefined);if(dialog.open)dialog.querySelector('[role="alert"]').textContent='Preset or group changed. Review again.';}};
    dialog.showModal();
  };
  return {synchronize:sync};
}

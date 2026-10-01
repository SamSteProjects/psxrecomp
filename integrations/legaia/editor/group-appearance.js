// Group initial-pair authoring consumes source-qualified SDK reports only.
export function mountGroupAppearance({after,getState,getSelection,isBusy,canEdit,setBusy,api}){
  const button=document.createElement('button');button.dataset.groupAppearance='';button.textContent='Group appearance…';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='group-appearance-dialog';document.body.append(dialog);
  let generation=0,controller=null,review=null;
  const key=()=>{const s=getState();return JSON.stringify([s.project?.path,s.scene?.id,s.scene_preview_source_key,getSelection()]);};
  dialog.addEventListener('close',()=>{generation++;review=null;if(controller){controller.abort();controller=null;setBusy(false);}});
  button.onclick=()=>{
    if(isBusy()||!canEdit()||getSelection().length<2)return;
    const ids=getSelection().slice(),context=key();let options=[];
    dialog.replaceChildren();const heading=document.createElement('h2'),note=document.createElement('p'),select=document.createElement('select'),preview=document.createElement('button'),apply=document.createElement('button'),result=document.createElement('div'),error=document.createElement('p'),close=document.createElement('button');
    heading.textContent='Actor group appearance';note.textContent=`${ids.length} actors · assign one source-verified initial model/animation pair. Runtime script scheduling and gameplay compatibility remain unverified.`;select.setAttribute('aria-label','Group appearance donor');preview.textContent='Preview group appearance';preview.disabled=true;apply.textContent='Apply reviewed group appearance';apply.disabled=true;error.className='dialog-error';error.setAttribute('role','alert');close.textContent='Close group appearance';close.onclick=()=>dialog.close();dialog.append(heading,note,select,preview,apply,result,error,close);
    const current=()=>dialog.open&&canEdit()&&context===key();
    select.onchange=()=>{generation++;review=null;apply.disabled=true;result.replaceChildren();};
    async function load(donor){
      const token=++generation;controller?.abort();const active=new AbortController();controller=active;review=null;apply.disabled=true;preview.disabled=true;select.disabled=true;setBusy(true);error.textContent='';result.replaceChildren();
      try{const response=await fetch('/api/actor-appearance-batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({actor_ids:ids,donor_entity_id:donor}),signal:active.signal}),report=await response.json();if(!response.ok||report.error)throw new Error(report.error||'Group appearance preview failed');
        if(token!==generation||!current())return;
        if(report.schema_version!=='legaia.actor-appearance-batch.v1'||report.scene_id!==getState().scene.id||report.donor_entity_id!==donor||!Array.isArray(report.options)||report.options.some(o=>typeof o.donor_entity_id!=='string'||typeof o.asset_id!=='string')||!Array.isArray(report.targets)||report.targets.length!==ids.length||report.targets.some((row,index)=>row.entity_id!==ids[index])||typeof report.review_key!=='string'||!/^[0-9a-f]{64}$/.test(report.review_key))throw new Error('Invalid group appearance report');
        if(donor===null){options=report.options;select.replaceChildren();for(const option of options){const item=document.createElement('option');item.value=option.donor_entity_id;item.textContent=option.label??option.donor_entity_id;select.append(item);}note.textContent+=` ${options.length} donors compatible with every actor.`;if(!options.length){for(const row of report.support??[]){const p=document.createElement('p');p.textContent=`${row.entity_id}: ${row.reason??'No common initial donor pair'}`;result.append(p);}}}
        else{if(!options.some(o=>o.donor_entity_id===donor)||report.targets.some(row=>row.proposed?.donor_entity_id!==donor))throw new Error('Proposal differs from the selected donor');review=report;const option=options.find(o=>o.donor_entity_id===donor),summary=document.createElement('p');summary.textContent=`Proposed model ${option.asset_id} · animation ${option.animation_id} · ${report.changed_count} actors change · not applied`;result.append(summary);
          for(const row of report.targets){const details=document.createElement('details'),title=document.createElement('summary'),data=document.createElement('pre');title.textContent=row.entity_id;data.className='diagnostic-detail';data.textContent=JSON.stringify({retail:row.retail,authored:row.authored,effective:row.effective,proposed:row.proposed},null,2);details.append(title,data);result.append(details);}}
      }catch(e){if(e.name!=='AbortError'&&token===generation&&current())error.textContent=e.message;}
      finally{if(controller===active){controller=null;setBusy(false);}select.disabled=isBusy()||!current()||!options.length;preview.disabled=isBusy()||!current()||!options.length;apply.disabled=isBusy()||!current()||!review?.changed_count;}
    }
    preview.onclick=()=>{if(!isBusy()&&current()&&options.some(o=>o.donor_entity_id===select.value))load(select.value);};
    apply.onclick=async()=>{if(isBusy()||!current()||!review?.changed_count)return;const accepted=review;review=null;apply.disabled=true;preview.disabled=true;select.disabled=true;
      if(await api('/api/command',{type:'set_actor_group_appearance',scene_id:accepted.scene_id,actor_ids:ids,donor_entity_id:accepted.donor_entity_id,review_key:accepted.review_key},{success:`Appearance assigned to ${accepted.changed_count} actors. Undo restores the group.`})){dialog.close();}
      else if(dialog.open){error.textContent='Group appearance rejected. Close and review the current group again.';}
    };
    dialog.showModal();load(null);
  };
}

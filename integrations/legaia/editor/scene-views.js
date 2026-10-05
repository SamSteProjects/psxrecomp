// Saved cameras are editor display metadata, never guest coordinates.
export function decodeSavedSceneView(value,state){
  const display=value?.display,c=display?.camera,t=c?.target,l=display?.layers;
  const number=(v,lo,hi)=>typeof v==='number'&&Number.isFinite(v)&&v>=lo&&v<=hi;
  const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===keys.sort().join('|');
  if(value?.scene_id!==state.scene?.id||value.import_sha256!==state.scene_view_source_key||!exact(display,['camera','representation','layers'])||!exact(c,['projection','yaw','pitch','distance','target'])||!['perspective','orthographic'].includes(c.projection)||!number(c.yaw,-1e12,1e12)||!number(c.pitch,c.projection==='orthographic'?0:.12,Math.PI/2)||!number(c.distance,20,1e8)||!exact(t,['x','y','z'])||Object.values(t).some(v=>!number(v,-1e12,1e12))||!['authored','retail'].includes(display.representation)||!exact(l,['actors','scenery','ground'])||Object.values(l).some(v=>typeof v!=='boolean'))throw new Error('Saved view differs from the current imported scene or supported camera');
  return structuredClone(display);
}

export function mountSceneViews({after,getState,getDisplay,isBusy,canEdit,canRecall,api,recall}){
  const button=document.createElement('button');button.id='scene-views-button';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='scene-views-dialog';document.body.append(dialog);
  let context=null,signature=null,revision=0;
  const chosen=()=>getState().scene_views?.find(row=>row.id===dialog.querySelector('[data-saved-views]')?.value);
  function update(){
    const state=getState(),busy=isBusy(),value=chosen();button.textContent=`Saved scene views (${state.scene_views?.length??0})`;button.disabled=busy||!canRecall()||!state.scene?.id;
    if(!dialog.open)return;
    const ok=canEdit()&&state.project.path===context;
    dialog.querySelectorAll('input,select,button').forEach(control=>{if(!control.matches('[data-close]'))control.disabled=busy||!ok;});
    dialog.querySelector('[data-create]').disabled=busy||!ok||!dialog.querySelector('[data-new-name]').value.trim();
    dialog.querySelector('[data-recall]').disabled=busy||!canRecall()||!value;
    dialog.querySelector('[data-rename]').disabled=busy||!ok||!value||!dialog.querySelector('[data-name]').value.trim();
    dialog.querySelector('[data-update]').disabled=busy||!ok||!value||value.scene_id!==state.scene.id;
    dialog.querySelector('[data-delete]').disabled=busy||!ok||!value;
    dialog.querySelector('[data-current-group]').textContent='Stores camera, representation and scene layers in editor display coordinates. Individual hidden objects and model filters are not stored.';
  }
  function list(preferred=null){
    if(!dialog.open)return;const state=getState(),select=dialog.querySelector('[data-saved-views]'),old=preferred??select.value;select.replaceChildren();
    for(const value of state.scene_views??[]){const option=document.createElement('option');option.value=value.id;option.textContent=`${state.scenes.find(scene=>scene.id===value.scene_id)?.name??value.scene_id} - ${value.name}`;select.append(option);}
    if([...select.options].some(item=>item.value===old))select.value=old;
    show();
  }
  function show(){
    const value=chosen();dialog.querySelector('[data-name]').value=value?.name??'';dialog.querySelector('[data-members]').textContent=value?JSON.stringify(value.display,null,2):'No saved views. Navigate the scene and save a camera view.';update();
  }
  async function command(type,extra={}){
    if(isBusy()||!canEdit()||context!==getState().project.path)return;
    const value=chosen();if(!value)return;
    dialog.querySelector('[data-error]').textContent='';
    if(!await api('/api/command',{type,view_id:value.id,review_key:value.review_key,...extra},{success:'Saved scene view updated. Undo restores the previous view.'})){await api('/api/state',undefined);if(dialog.open)dialog.querySelector('[data-error]').textContent='Saved view command rejected. Review the refreshed view before retrying.';}
    update();
  }
  button.onclick=async()=>{
    if(button.disabled||!await api('/api/state',undefined))return;context=getState().project.path;signature=null;revision++;
    dialog.innerHTML='<h2>Saved scene views</h2><p>Save a camera view for later inspection. Recall changes the editor display; it does not edit actors or control the game.</p><p data-current-group></p><label>New view name<input data-new-name maxlength="80" aria-label="New scene view name"></label><button type="button" data-create>Save current view</button><hr><label>Saved view<select data-saved-views aria-label="Saved scene view"></select></label><label>View name<input data-name maxlength="80" aria-label="Scene view name"></label><div class="dialog-actions"><button type="button" data-recall>Recall scene view</button><button type="button" data-rename>Rename view</button><button type="button" data-update>Replace with current view</button><button type="button" data-delete>Delete view</button></div><details><summary>Saved camera and layers</summary><pre data-members class="diagnostic-detail"></pre></details><p data-error class="dialog-error" role="alert"></p><button type="button" data-close>Close saved views</button>';
    dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.querySelector('[data-saved-views]').onchange=show;
    for(const input of dialog.querySelectorAll('input'))input.oninput=update;
    dialog.querySelector('[data-create]').onclick=async()=>{
      if(isBusy()||!canEdit()||context!==getState().project.path)return;
      const state=getState(),name=dialog.querySelector('[data-new-name]').value.trim(),display=getDisplay();
      if(await api('/api/command',{type:'create_scene_view',scene_id:state.scene.id,import_sha256:state.scene_view_source_key,name,display},{success:'Scene view saved. Save project to retain it across sessions.'})){
        const added=getState().scene_views.find(row=>row.scene_id===state.scene.id&&row.name===name);list(added?.id);
      }else dialog.querySelector('[data-error]').textContent='Saving the scene view was rejected.';update();
    };
    dialog.querySelector('[data-rename]').onclick=()=>command('rename_scene_view',{name:dialog.querySelector('[data-name]').value});
    dialog.querySelector('[data-update]').onclick=()=>command('update_scene_view',{display:getDisplay()});
    dialog.querySelector('[data-delete]').onclick=()=>command('delete_scene_view');
    dialog.querySelector('[data-recall]').onclick=async()=>{
      if(isBusy()||!canRecall()||context!==getState().project.path)return;const value=chosen();if(!value)return;
      const token=revision;try{if(await recall(structuredClone(value),context,()=>dialog.open&&revision===token&&context===getState().project.path))dialog.close();else throw new Error('Saved scene view could not be recalled.');}
      catch(error){if(dialog.open)dialog.querySelector('[data-error]').textContent=error.message;}update();
    };
    dialog.showModal();list();
  };
  return {synchronize(){
    const state=getState();if(dialog.open&&(state.project.path!==context||!canRecall()))dialog.close();
    const next=JSON.stringify([state.project?.path,state.scene_views]);if(dialog.open&&next!==signature){signature=next;list();}update();
  }};
}

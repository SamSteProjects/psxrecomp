// Source-bound saved selections are editor metadata, never game parenting.
export function decodeSavedActorSelection(value,state){
  const allowed=new Set(state.scene?.entities?.map(row=>row.id)??[]),ids=value?.actor_ids;
  if(value?.scene_id!==state.scene?.id||value.import_sha256!==state.actor_selection_source_key||!Array.isArray(ids)||ids.length<2||ids.length>128||new Set(ids).size!==ids.length||ids.some(id=>typeof id!=='string'||!allowed.has(id))||JSON.stringify([...ids].sort())!==JSON.stringify(ids))throw new Error('Saved selection differs from the current imported scene');
  return ids.slice();
}

export function mountActorSelectionSets({after,getState,getSelection,isBusy,canEdit,canRecall,api,recall}){
  const button=document.createElement('button');button.id='actor-selection-sets-button';after.after(button);
  const dialog=document.createElement('dialog');dialog.id='actor-selection-sets-dialog';document.body.append(dialog);
  let context=null,signature=null;
  const chosen=()=>getState().actor_selection_sets?.find(row=>row.id===dialog.querySelector('[data-saved-selections]')?.value);
  function update(){
    const state=getState(),busy=isBusy(),members=getSelection(),value=chosen();button.textContent=`Saved actor selections (${state.actor_selection_sets?.length??0})`;button.disabled=busy||!canRecall()||!state.scene?.id;
    if(!dialog.open)return;
    const ok=canEdit()&&state.project.path===context;
    dialog.querySelectorAll('input,select,button').forEach(control=>{if(!control.matches('[data-close]'))control.disabled=busy||!ok;});
    dialog.querySelector('[data-create]').disabled=busy||!ok||members.length<2||members.length>128||!dialog.querySelector('[data-new-name]').value.trim();
    dialog.querySelector('[data-recall]').disabled=busy||!canRecall()||!value;
    dialog.querySelector('[data-rename]').disabled=busy||!ok||!value||!dialog.querySelector('[data-name]').value.trim();
    dialog.querySelector('[data-update]').disabled=busy||!ok||!value||value.scene_id!==state.scene.id||members.length<2||members.length>128;
    dialog.querySelector('[data-delete]').disabled=busy||!ok||!value;
    dialog.querySelector('[data-current-group]').textContent=`Current group: ${members.length} actors. Saving or updating retains these actor IDs.`;
  }
  function list(preferred=null){
    if(!dialog.open)return;const state=getState(),select=dialog.querySelector('[data-saved-selections]'),old=preferred??select.value;select.replaceChildren();
    for(const value of state.actor_selection_sets??[]){const option=document.createElement('option');option.value=value.id;option.textContent=`${state.scenes.find(scene=>scene.id===value.scene_id)?.name??value.scene_id} - ${value.name} (${value.actor_ids.length})`;select.append(option);}
    if([...select.options].some(item=>item.value===old))select.value=old;
    show();
  }
  function show(){
    const value=chosen();dialog.querySelector('[data-name]').value=value?.name??'';dialog.querySelector('[data-members]').textContent=value?value.actor_ids.join('\n'):'No saved selections. Select two or more actors and save the group.';update();
  }
  async function command(type,extra={}){
    if(isBusy()||!canEdit()||context!==getState().project.path)return;
    const value=chosen();if(!value)return;
    dialog.querySelector('[data-error]').textContent='';
    if(!await api('/api/command',{type,selection_set_id:value.id,review_key:value.review_key,...extra},{success:'Saved actor selection updated. Undo restores the previous selection.'})){await api('/api/state',undefined);if(dialog.open)dialog.querySelector('[data-error]').textContent='Saved selection command rejected. Review the refreshed selection before retrying.';}
    update();
  }
  button.onclick=async()=>{
    if(button.disabled||!await api('/api/state',undefined))return;context=getState().project.path;signature=null;
    dialog.innerHTML='<h2>Saved actor selections</h2><p>Save source-bound actor IDs for later group edits. These selections do not move actors, parent game objects or change game data.</p><p data-current-group></p><label>New selection name<input data-new-name maxlength="80" aria-label="New actor selection name"></label><button type="button" data-create>Save current actor group</button><hr><label>Saved selection<select data-saved-selections aria-label="Saved actor selection"></select></label><label>Selection name<input data-name maxlength="80" aria-label="Actor selection name"></label><div class="dialog-actions"><button type="button" data-recall>Recall actor group</button><button type="button" data-rename>Rename selection</button><button type="button" data-update>Replace with current group</button><button type="button" data-delete>Delete selection</button></div><pre data-members class="diagnostic-detail"></pre><p data-error class="dialog-error" role="alert"></p><button type="button" data-close>Close saved selections</button>';
    dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.querySelector('[data-saved-selections]').onchange=show;
    for(const input of dialog.querySelectorAll('input'))input.oninput=update;
    dialog.querySelector('[data-create]').onclick=async()=>{
      if(isBusy()||!canEdit()||context!==getState().project.path)return;
      const state=getState(),name=dialog.querySelector('[data-new-name]').value.trim(),ids=getSelection().slice();
      if(await api('/api/command',{type:'create_actor_selection_set',scene_id:state.scene.id,import_sha256:state.actor_selection_source_key,name,actor_ids:ids},{success:'Actor selection saved. Save project to retain it across sessions.'})){
        const added=getState().actor_selection_sets.find(row=>row.scene_id===state.scene.id&&row.name===name);list(added?.id);
      }else dialog.querySelector('[data-error]').textContent='Saving the actor selection was rejected.';update();
    };
    dialog.querySelector('[data-rename]').onclick=()=>command('rename_actor_selection_set',{name:dialog.querySelector('[data-name]').value});
    dialog.querySelector('[data-update]').onclick=()=>command('update_actor_selection_set',{actor_ids:getSelection().slice()});
    dialog.querySelector('[data-delete]').onclick=()=>command('delete_actor_selection_set');
    dialog.querySelector('[data-recall]').onclick=async()=>{
      if(isBusy()||!canRecall()||context!==getState().project.path)return;const value=chosen();if(!value)return;
      try{if(await recall(structuredClone(value),context))dialog.close();else throw new Error('Saved actor selection could not be recalled.');}
      catch(error){if(dialog.open)dialog.querySelector('[data-error]').textContent=error.message;}update();
    };
    dialog.showModal();list();
  };
  return {synchronize(){
    const state=getState();if(dialog.open&&(state.project.path!==context||!canRecall()))dialog.close();
    const next=JSON.stringify([state.project?.path,state.actor_selection_sets]);if(dialog.open&&next!==signature){signature=next;list();}update();
  }};
}

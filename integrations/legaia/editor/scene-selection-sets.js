// Saved placements retain source-bound IDs; they do not alter game transforms.
const canonicalIds=ids=>Array.isArray(ids)&&ids.length>=1&&ids.length<=128&&ids.every(id=>typeof id==='string'&&id.length>0)&&new Set(ids).size===ids.length&&JSON.stringify(ids)===JSON.stringify([...ids].sort());
export function decodeSavedSceneSelection(value,state){
  const ids=value?.entity_ids,allowed=new Set(state.scene_selection_eligible_ids??[]),actors=new Set(state.scene?.entities?.map(row=>row.id)??[]),npcs=new Set(Object.entries(state.actor_drafts??{}).filter(([,draft])=>draft.scene_id===state.scene?.id).map(([id])=>id));
  if(typeof state.actor_selection_source_key!=='string'||!state.actor_selection_source_key||value?.scene_id!==state.scene?.id||value.import_sha256!==state.actor_selection_source_key||!canonicalIds(ids)||ids.some(id=>!allowed.has(id)||id.startsWith('authored-actor://')&&!npcs.has(id))||ids.some(id=>!actors.has(id)&&!npcs.has(id))&&(typeof state.scene_selection_map_sha256!=='string'||!state.scene_selection_map_sha256||value.map_sha256!==state.scene_selection_map_sha256))throw new Error('Saved placements differ from the current imported scene or source files');
  return ids.slice();
}
export function unavailableSelectionNpcs(value,state){
  return (value?.entity_ids??[]).filter(id=>id.startsWith('authored-actor://')&&state.actor_drafts?.[id]?.scene_id!==value.scene_id);
}
export function mountSceneSelectionSets({host,getState,getSelection,isBusy,canEdit,canRecall,api,recall,onError=()=>{}}){
  const button=document.createElement('button');button.id='scene-selection-sets-button';host.append(button);
  const dialog=document.createElement('dialog');dialog.id='scene-selection-sets-dialog';document.body.append(dialog);
  let context=null,signature=null,pending=null,recalling=false,generation=0;
  const rows=()=>getState().scene_selection_sets??[];
  const chosen=()=>rows().find(row=>row.id===dialog.querySelector('[data-selections]')?.value);
  const members=()=>getSelection().slice().sort();
  const selectionKey=()=>JSON.stringify([getState().project?.path,getState().project_copy_source_key,getState().scene?.id,getState().actor_selection_source_key,getState().scene_selection_map_sha256,members()]);
  const validMembers=()=>{try{const s=getState();decodeSavedSceneSelection({scene_id:s.scene?.id,import_sha256:s.actor_selection_source_key,map_sha256:s.scene_selection_map_sha256,entity_ids:members()},s);return true;}catch{return false;}};
  function cancel(){generation++;pending?.abort();pending=null;recalling=false;}
  function close(){cancel();dialog.close();update();}
  function error(value){if(dialog.open)dialog.querySelector('[data-error]').textContent=value.message??String(value);onError(value);}
  function update(){
    const s=getState(),busy=isBusy()||!!pending||recalling;button.textContent=`Saved scene selections (${rows().length})`;button.disabled=busy||!canRecall()||!s.scene?.id;
    if(!dialog.open)return;
    const editable=canEdit()&&context===s.project?.path,value=chosen(),valid=validMembers();
    dialog.querySelectorAll('input,select,button').forEach(c=>c.disabled=!c.matches('[data-close]')&&(busy||!editable));
    dialog.querySelector('[data-create]').disabled=busy||!editable||!valid||!dialog.querySelector('[data-new-name]').value.trim();
    dialog.querySelector('[data-recall]').disabled=busy||!canRecall()||!value;
    dialog.querySelector('[data-rename]').disabled=busy||!editable||!value||!dialog.querySelector('[data-name]').value.trim();
    dialog.querySelector('[data-update]').disabled=busy||!editable||!value||value.scene_id!==s.scene?.id||!valid;
    dialog.querySelector('[data-delete]').disabled=busy||!editable||!value;
    const missing=unavailableSelectionNpcs(value,s),repair=dialog.querySelector('[data-repair-note]');repair.hidden=!missing.length;repair.textContent=`${missing.length} saved NPC ${missing.length===1?'is':'drafts are'} unavailable. Select valid placements in the saved scene, then choose Replace with current placements to repair this set. Undo restores its previous membership.`;
    dialog.querySelector('[data-current]').textContent=`Current selection: ${members().length} placements. Save 1-128 imported actors, NPC drafts or static decorations.`;
  }
  function show(){const v=chosen();dialog.querySelector('[data-name]').value=v?.name??'';dialog.querySelector('[data-members]').textContent=v?v.entity_ids.join('\n'):'No saved scene selections.';update();}
  function list(preferred){
    if(!dialog.open)return;const select=dialog.querySelector('[data-selections]'),old=preferred??select.value;select.replaceChildren();
    for(const v of rows()){const option=document.createElement('option');option.value=v.id;option.textContent=`${getState().scenes?.find(s=>s.id===v.scene_id)?.name??v.scene_id} — ${v.name} (${v.entity_ids.length})`;select.append(option);}
    if([...select.options].some(o=>o.value===old))select.value=old;show();
  }
  async function command(type,extra={}){
    if(isBusy()||pending||recalling||!canEdit()||context!==getState().project?.path)return;const v=chosen();if(!v)return;
    dialog.querySelector('[data-error]').textContent='';
    try{if(!await api('/api/command',{type,selection_set_id:v.id,review_key:v.review_key,...extra},{success:'Saved scene selection updated. Undo restores the previous selection.'}))throw new Error('Selection command rejected. Refresh and review the selection before retrying.');list();}catch(e){error(e);}update();
  }
  async function create(){
    if(isBusy()||pending||recalling||!canEdit()||context!==getState().project?.path||!validMembers())return;
    const s=getState(),name=dialog.querySelector('[data-new-name]').value.trim();if(!name)return;
    const ids=members(),scene_id=s.scene.id,key=selectionKey(),token=++generation,controller=new AbortController();controller.selectionKey=key;pending=controller;update();
    try{
      const response=await fetch('/api/scene-selection-binding',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene_id,entity_ids:ids}),signal:controller.signal});
      const binding=await response.json();
      if(token!==generation||!dialog.open||controller.signal.aborted||key!==selectionKey()||isBusy()||!canEdit())return;
      if(!response.ok)throw new Error(binding.error??'Placement source binding was rejected.');
      if(binding.schema_version!=='legaia.scene-selection-binding.v1'||binding.read_only!==true||binding.project_source_key!==s.project_copy_source_key||binding.scene_id!==scene_id||binding.import_sha256!==s.actor_selection_source_key||JSON.stringify(binding.entity_ids)!==JSON.stringify(ids))throw new Error('Placement source binding changed. Review the current selection before saving.');
      decodeSavedSceneSelection(binding,s);
      pending=null;
      if(!await api('/api/command',{type:'create_scene_selection_set',scene_id,import_sha256:binding.import_sha256,map_sha256:binding.map_sha256,name,entity_ids:ids},{success:'Scene selection saved. Save the project to retain it across sessions.'}))throw new Error('Saving the scene selection was rejected.');
      if(dialog.open&&context===getState().project?.path)list(rows().find(v=>v.scene_id===scene_id&&v.name===name)?.id);
    }catch(e){if(token===generation&&e.name!=='AbortError')error(e);}finally{if(token===generation){pending=null;update();}}
  }
  button.onclick=async()=>{
    if(button.disabled)return;const path=getState().project?.path;
    if(!await api('/api/state',undefined)||path!==getState().project?.path||!canRecall())return;context=path;signature=null;
    dialog.innerHTML='<h2>Saved scene selections</h2><p>Save imported actors, authored NPC drafts and static decorations for later placement edits. These selections retain IDs without moving objects or changing game data.</p><p data-current></p><label>New scene selection name<input data-new-name maxlength="80" aria-label="New scene selection name"></label><button type="button" data-create>Save current placements</button><hr><label>Scene selection<select data-selections aria-label="Scene selection"></select></label><label>Scene selection name<input data-name maxlength="80" aria-label="Scene selection name"></label><div class="dialog-actions"><button type="button" data-recall>Recall placements</button><button type="button" data-rename>Rename selection</button><button type="button" data-update>Replace with current placements</button><button type="button" data-delete>Delete selection</button></div><pre data-members class="diagnostic-detail"></pre><p data-repair-note class="field-note" hidden></p><p data-error class="dialog-error" role="alert"></p><button type="button" data-close>Close saved scene selections</button>';
    dialog.querySelector('[data-close]').onclick=close;dialog.querySelector('[data-selections]').onchange=show;
    for(const input of dialog.querySelectorAll('input'))input.oninput=update;
    dialog.querySelector('[data-create]').onclick=create;
    dialog.querySelector('[data-rename]').onclick=()=>command('rename_scene_selection_set',{name:dialog.querySelector('[data-name]').value.trim()});
    dialog.querySelector('[data-update]').onclick=()=>command('update_scene_selection_set',{entity_ids:members()});
    dialog.querySelector('[data-delete]').onclick=()=>command('delete_scene_selection_set');
    dialog.querySelector('[data-recall]').onclick=async()=>{if(isBusy()||pending||recalling||!canRecall()||context!==getState().project?.path)return;const v=chosen();if(!v)return;const token=++generation,path=context,current=()=>token===generation&&dialog.open&&context===path&&getState().project?.path===path;recalling=true;update();try{const restored=await recall(structuredClone(v),path,current);if(!current())return;if(restored)close();else throw new Error('Saved placements could not be recalled.');}catch(e){if(current())error(e);}finally{if(token===generation){recalling=false;update();}}};
    dialog.showModal();list();
  };
  dialog.addEventListener('cancel',()=>cancel());dialog.addEventListener('close',()=>{cancel();update();});
  return {synchronize(){const s=getState();if(dialog.open&&(s.project?.path!==context||!canRecall()))close();if(pending&&pending.selectionKey!==selectionKey())cancel();const next=JSON.stringify([s.project?.path,s.scene_selection_sets]);if(dialog.open&&signature!==next){signature=next;list();}update();}};
}

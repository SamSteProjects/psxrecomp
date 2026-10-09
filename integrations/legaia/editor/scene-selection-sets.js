// Saved placements retain source-bound IDs; they do not alter game transforms.
const canonicalIds=ids=>Array.isArray(ids)&&ids.length>=1&&ids.length<=128&&ids.every(id=>typeof id==='string'&&id.length>0)&&new Set(ids).size===ids.length&&JSON.stringify(ids)===JSON.stringify([...ids].sort());
export function decodeSavedSceneSelection(value,state){
  const ids=value?.entity_ids,allowed=new Set(state.scene_selection_eligible_ids??[]),actors=new Set(state.scene?.entities?.map(row=>row.id)??[]),npcs=new Set(Object.entries(state.actor_drafts??{}).filter(([,draft])=>draft.scene_id===state.scene?.id).map(([id])=>id));
  if(typeof state.actor_selection_source_key!=='string'||!state.actor_selection_source_key||value?.scene_id!==state.scene?.id||value.import_sha256!==state.actor_selection_source_key||!canonicalIds(ids)||ids.some(id=>!allowed.has(id)||id.startsWith('authored-actor://')&&!npcs.has(id))||ids.some(id=>!actors.has(id)&&!npcs.has(id))&&(typeof state.scene_selection_map_sha256!=='string'||!state.scene_selection_map_sha256||value.map_sha256!==state.scene_selection_map_sha256))throw new Error('Saved placements differ from the current imported scene or source files');
  return ids.slice();
}
export function savedSelectionMemberIds(value,state,memberId){
  const ids=decodeSavedSceneSelection(value,state);
  if(typeof memberId!=='string'||!ids.includes(memberId))throw Error('Placement is not a member of the current saved scene selection.');
  return [memberId];
}
export function unavailableSelectionNpcs(value,state){
  return (value?.entity_ids??[]).filter(id=>id.startsWith('authored-actor://')&&state.actor_drafts?.[id]?.scene_id!==value.scene_id);
}
export const SCENE_SELECTION_TRANSFER_BYTES=256*1024;
const selectionTransferName=value=>{if(typeof value!=='string'||!value.trim()||Array.from(value.trim()).length>80||/[\u0000-\u001f\u007f\ud800-\udfff]/u.test(value))throw Error('Scene selection name requires 1–80 printable characters.');return value.trim();};
function transferSelection(value,state){
  if(!value||!/^scene-selection:\/\/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(value.id)||!/^scene:\/\/[a-z0-9]{1,12}$/.test(value.scene_id)||!/^([a-f0-9]{64})$/.test(value.import_sha256))throw Error('Scene selection transfer requires a stable imported source.');
  const ids=decodeSavedSceneSelection(value,state),decorations=ids.filter(id=>id.startsWith('environment://'));
  if(decorations.length?typeof value.map_sha256!=='string'||!/^([a-f0-9]{64})$/.test(value.map_sha256)||value.map_sha256!==state.scene_selection_map_sha256:value.map_sha256!==null)throw Error('Scene selection MAP binding differs from its placement types.');
  if(ids.some(id=>id.length>1024||!state.scene.entities.some(row=>row.id===id)&&!id.startsWith('authored-actor://')&&!id.startsWith('environment://'+value.scene_id.slice(8)+'/field-map/decorations/')))throw Error('Scene selection transfer contains unsupported placement identities.');
  return {id:value.id,name:selectionTransferName(value.name),scene_id:value.scene_id,import_sha256:value.import_sha256,map_sha256:value.map_sha256,entity_ids:ids};
}
export function exportSceneSelection(value,state){
  if(!state.scene_selection_sets?.some(row=>row.id===value?.id&&row.review_key===value.review_key&&JSON.stringify(row)===JSON.stringify(value)))throw Error('Choose a current saved scene selection.');
  const transfer={schema_version:'legaia.scene-selection-transfer.v1',editor_metadata_only:true,source_selection:transferSelection(value,state)};
  if(new TextEncoder().encode(JSON.stringify(transfer,null,2)).byteLength>SCENE_SELECTION_TRANSFER_BYTES)throw Error('Scene selection transfer exceeds 256 KiB.');return structuredClone(transfer);
}
export function importSceneSelection(value,state,name){
  const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===keys.sort().join('|');
  if(!exact(value,['schema_version','editor_metadata_only','source_selection'])||value.schema_version!=='legaia.scene-selection-transfer.v1'||value.editor_metadata_only!==true||!exact(value.source_selection,['id','name','scene_id','import_sha256','map_sha256','entity_ids']))throw Error('Choose a supported editor scene-selection transfer.');
  if(new TextEncoder().encode(JSON.stringify(value)).byteLength>SCENE_SELECTION_TRANSFER_BYTES)throw Error('Scene selection transfer exceeds 256 KiB.');
  const source=transferSelection(value.source_selection,state),selected=selectionTransferName(name);
  if(state.scene_selection_sets?.some(row=>row.scene_id===source.scene_id&&row.name.toLowerCase()===selected.toLowerCase()))throw Error('Choose a distinct saved selection name in this scene.');
  return {type:'create_scene_selection_set',scene_id:source.scene_id,import_sha256:source.import_sha256,map_sha256:source.map_sha256,name:selected,entity_ids:source.entity_ids.slice()};
}
export function mountSceneSelectionSets({host,getState,getSelection,isBusy,canEdit,canRecall,api,recall,onError=()=>{}}){
  const button=document.createElement('button');button.id='scene-selection-sets-button';host.append(button);
  const dialog=document.createElement('dialog');dialog.id='scene-selection-sets-dialog';document.body.append(dialog);
  let context=null,signature=null,pending=null,recalling=false,generation=0,transfer=null,reading=false,memberPage=0;
  const rows=()=>getState().scene_selection_sets??[];
  const chosen=()=>rows().find(row=>row.id===dialog.querySelector('[data-selections]')?.value);
  const members=()=>getSelection().slice().sort();
  const selectionKey=()=>JSON.stringify([getState().project?.path,getState().project_copy_source_key,getState().scene?.id,getState().actor_selection_source_key,getState().scene_selection_map_sha256,members()]);
  const validMembers=()=>{try{const s=getState();decodeSavedSceneSelection({scene_id:s.scene?.id,import_sha256:s.actor_selection_source_key,map_sha256:s.scene_selection_map_sha256,entity_ids:members()},s);return true;}catch{return false;}};
  function cancel(){generation++;pending?.abort();pending=null;recalling=false;transfer=null;reading=false;}
  function close(){cancel();dialog.close();update();}
  function error(value){if(dialog.open)dialog.querySelector('[data-error]').textContent=value.message??String(value);onError(value);}
  function update(){
    const s=getState(),busy=isBusy()||!!pending||recalling||reading;button.textContent=`Saved scene selections (${rows().length})`;button.disabled=busy||!canRecall()||!s.scene?.id;
    if(!dialog.open)return;
    const editable=canEdit()&&context===s.project?.path,value=chosen(),valid=validMembers();
    dialog.querySelectorAll('input,select,button').forEach(c=>c.disabled=!c.matches('[data-close]')&&(busy||!editable));
    dialog.querySelector('[data-create]').disabled=busy||!editable||!valid||!dialog.querySelector('[data-new-name]').value.trim();
    dialog.querySelector('[data-recall]').disabled=busy||!canRecall()||!value;
    dialog.querySelector('[data-rename]').disabled=busy||!editable||!value||!dialog.querySelector('[data-name]').value.trim();
    dialog.querySelector('[data-update]').disabled=busy||!editable||!value||value.scene_id!==s.scene?.id||!valid;
    dialog.querySelector('[data-delete]').disabled=busy||!editable||!value;
    let exportOk=false,importOk=false;try{if(value){exportSceneSelection(value,s);exportOk=true;}}catch{}try{if(transfer){importSceneSelection(transfer,s,dialog.querySelector('[data-import-name]').value);importOk=true;}}catch{}
    dialog.querySelector('[data-export-selection]').disabled=busy||!exportOk;
    dialog.querySelector('[data-import-selection]').disabled=busy||!editable||!importOk;
    dialog.querySelectorAll('[data-inspect-member]').forEach(b=>b.disabled=busy||!canRecall()||!value);
    dialog.querySelector('[data-members-previous]').disabled=busy||!value||memberPage===0;
    dialog.querySelector('[data-members-next]').disabled=busy||!value||(memberPage+1)*16>=value.entity_ids.length;
    const missing=unavailableSelectionNpcs(value,s),repair=dialog.querySelector('[data-repair-note]');repair.hidden=!missing.length;repair.textContent=`${missing.length} saved NPC ${missing.length===1?'is':'drafts are'} unavailable. Select valid placements in the saved scene, then choose Replace with current placements to repair this set. Undo restores its previous membership.`;
    dialog.querySelector('[data-current]').textContent=`Current selection: ${members().length} placements. Save 1-128 imported actors, NPC drafts or static decorations.`;
  }
  function renderMembers(){
    const value=chosen(),host=dialog.querySelector('[data-member-list]');if(!host)return;host.replaceChildren();
    const ids=value?.entity_ids??[],pages=Math.max(1,Math.ceil(ids.length/16));memberPage=Math.min(memberPage,pages-1);
    dialog.querySelector('[data-member-page]').textContent=`Page ${memberPage+1} / ${pages}`;
    dialog.querySelector('[data-members-previous]').disabled=memberPage===0||isBusy()||pending||recalling||reading;
    dialog.querySelector('[data-members-next]').disabled=memberPage===pages-1||isBusy()||pending||recalling||reading;
    for(const id of ids.slice(memberPage*16,(memberPage+1)*16)){
      const row=document.createElement('section'),label=document.createElement('p'),identity=document.createElement('code'),inspect=document.createElement('button');
      const entity=getState().scene?.entities?.find(e=>e.id===id),draft=getState().actor_drafts?.[id];
      label.textContent=entity?.name??draft?.name??id.split('/').at(-1);identity.textContent=id;identity.style.overflowWrap='anywhere';inspect.type='button';inspect.textContent='Inspect placement';inspect.setAttribute('data-inspect-member',id);inspect.disabled=isBusy()||!!pending||recalling||reading||!canRecall();
      inspect.onclick=()=>recallSelection(id);row.append(label,identity,inspect);host.append(row);
    }
  }
  function show(){const v=chosen();dialog.querySelector('[data-name]').value=v?.name??'';dialog.querySelector('[data-members]').textContent=v?v.entity_ids.join('\n'):'No saved scene selections.';memberPage=0;renderMembers();update();}
  async function recallSelection(memberId=null){
    if(isBusy()||pending||recalling||reading||!canRecall()||context!==getState().project?.path)return;
    const v=chosen();if(!v||memberId!==null&&!v.entity_ids.includes(memberId))return;
    const token=++generation,path=context,current=()=>token===generation&&dialog.open&&context===path&&getState().project?.path===path&&chosen()?.id===v.id&&chosen()?.review_key===v.review_key;
    recalling=true;update();renderMembers();
    try{const restored=await recall(structuredClone(v),path,current,memberId);if(!current())return;if(restored)close();else throw Error('Saved placements could not be recalled.');}
    catch(e){if(current())error(e);}finally{if(token===generation){recalling=false;update();if(dialog.open)renderMembers();}}
  }
  function list(preferred){
    if(!dialog.open)return;const select=dialog.querySelector('[data-selections]'),old=preferred??select.value;select.replaceChildren();
    for(const v of rows()){const option=document.createElement('option');option.value=v.id;option.textContent=`${getState().scenes?.find(s=>s.id===v.scene_id)?.name??v.scene_id} — ${v.name} (${v.entity_ids.length})`;select.append(option);}
    if([...select.options].some(o=>o.value===old))select.value=old;show();
  }
  async function command(type,extra={}){
    if(isBusy()||pending||recalling||reading||!canEdit()||context!==getState().project?.path)return;const v=chosen();if(!v)return;
    dialog.querySelector('[data-error]').textContent='';
    try{if(!await api('/api/command',{type,selection_set_id:v.id,review_key:v.review_key,...extra},{success:'Saved scene selection updated. Undo restores the previous selection.'}))throw new Error('Selection command rejected. Refresh and review the selection before retrying.');list();}catch(e){error(e);}update();
  }
  async function create(){
    if(isBusy()||pending||recalling||reading||!canEdit()||context!==getState().project?.path||!validMembers())return;
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
    if(!await api('/api/state',undefined)||path!==getState().project?.path||!canRecall())return;cancel();context=path;signature=null;
    dialog.innerHTML='<h2>Saved scene selections</h2><p>Save imported actors, authored NPC drafts and static decorations for later placement edits. These selections retain IDs without moving objects or changing game data.</p><p data-current></p><label>New scene selection name<input data-new-name maxlength="80" aria-label="New scene selection name"></label><button type="button" data-create>Save current placements</button><hr><label>Scene selection<select data-selections aria-label="Scene selection"></select></label><label>Scene selection name<input data-name maxlength="80" aria-label="Scene selection name"></label><div class="dialog-actions"><button type="button" data-recall>Recall placements</button><button type="button" data-rename>Rename selection</button><button type="button" data-update>Replace with current placements</button><button type="button" data-delete>Delete selection</button></div><h3>Inspect one saved placement</h3><p class="field-note">Select one placement after verifying the complete saved group. This changes editor selection only.</p><div><button type="button" data-members-previous>Previous placements</button><span data-member-page></span><button type="button" data-members-next>Next placements</button></div><div data-member-list></div><details><summary>All saved placement IDs</summary><pre data-members class="diagnostic-detail"></pre></details><p data-repair-note class="field-note" hidden></p><hr><h3>Transfer a scene selection</h3><p>Export source-bound placement IDs as editor metadata. Import creates a new group for this exact scene source and requires every placement to be available.</p><button type="button" data-export-selection>Export selected scene selection JSON</button><label>Scene selection JSON<input type="file" accept=".json,application/json" data-import-file aria-label="Import scene selection JSON"></label><label>Imported selection name<input maxlength="160" data-import-name aria-label="Imported scene selection name"></label><button type="button" data-import-selection>Import as new scene selection</button><details><summary>Imported scene selection metadata</summary><pre data-import-preview class="diagnostic-detail"></pre></details><p data-error class="dialog-error" role="alert"></p><button type="button" data-close>Close saved scene selections</button>';
    dialog.querySelector('[data-export-selection]').onclick=()=>{try{if(isBusy()||pending||recalling||reading||context!==getState().project?.path)return;const value=exportSceneSelection(chosen(),getState()),url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='scene-selection-'+getState().scene.id.slice(8)+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error(e);}};
    dialog.querySelector('[data-import-file]').onchange=async()=>{
      if(isBusy()||pending||recalling||reading||!canEdit()||context!==getState().project?.path)return;
      const file=dialog.querySelector('[data-import-file]').files?.[0],token=++generation,key=selectionKey();transfer=null;dialog.querySelector('[data-import-preview]').textContent='';if(!file){update();return;}
      reading=true;update();try{
        if(file.size>SCENE_SELECTION_TRANSFER_BYTES)throw Error('Scene selection transfer exceeds 256 KiB.');const text=await file.text();if(!dialog.open||token!==generation)return;if(key!==selectionKey())throw Error('Scene selection source changed while reading. Choose the file again.');
        const value=JSON.parse(text),s=getState(),base=Array.from(selectionTransferName(value.source_selection?.name)).slice(0,70).join('');let name=base+' Copy',number=2;while(rows().some(row=>row.scene_id===s.scene?.id&&row.name.toLowerCase()===name.toLowerCase()))name=base+' Copy '+number++;
        const command=importSceneSelection(value,s,name);transfer=structuredClone(value);dialog.querySelector('[data-import-name]').value=command.name;dialog.querySelector('[data-import-preview]').textContent=JSON.stringify(transfer,null,2);dialog.querySelector('[data-error]').textContent='';
      }catch(e){if(dialog.open&&token===generation)error(e);}finally{if(token===generation){reading=false;update();}}
    };
    dialog.querySelector('[data-import-selection]').onclick=async()=>{
      if(isBusy()||pending||recalling||reading||!canEdit()||context!==getState().project?.path||!transfer)return;
      const token=++generation;try{const payload=importSceneSelection(transfer,getState(),dialog.querySelector('[data-import-name]').value),before=new Set(rows().map(row=>row.id));if(!await api('/api/command',payload,{success:'Imported editor selection saved. Save project to persist.'}))throw Error('Scene selection import rejected. Review the current source before retrying.');if(!dialog.open||token!==generation||context!==getState().project?.path)return;
        transfer=null;dialog.querySelector('[data-import-file]').value='';dialog.querySelector('[data-import-preview]').textContent='';const copied=rows().filter(row=>!before.has(row.id)&&row.scene_id===payload.scene_id&&row.import_sha256===payload.import_sha256&&row.map_sha256===payload.map_sha256&&row.name===payload.name&&JSON.stringify(row.entity_ids)===JSON.stringify(payload.entity_ids));if(copied.length!==1)throw Error('Selection imported; choose its new identity in the saved selection list.');list(copied[0].id);
      }catch(e){if(dialog.open&&token===generation)error(e);}update();
    };
    dialog.querySelector('[data-close]').onclick=close;dialog.querySelector('[data-selections]').onchange=show;
    for(const input of dialog.querySelectorAll('input'))input.oninput=update;
    dialog.querySelector('[data-create]').onclick=create;
    dialog.querySelector('[data-rename]').onclick=()=>command('rename_scene_selection_set',{name:dialog.querySelector('[data-name]').value.trim()});
    dialog.querySelector('[data-update]').onclick=()=>command('update_scene_selection_set',{entity_ids:members()});
    dialog.querySelector('[data-delete]').onclick=()=>command('delete_scene_selection_set');
    dialog.querySelector('[data-recall]').onclick=()=>recallSelection();
    dialog.querySelector('[data-members-previous]').onclick=()=>{if(isBusy()||pending||recalling||reading||memberPage===0)return;memberPage--;renderMembers();};
    dialog.querySelector('[data-members-next]').onclick=()=>{if(isBusy()||pending||recalling||reading)return;memberPage++;renderMembers();};
    dialog.showModal();list();
  };
  dialog.addEventListener('cancel',()=>cancel());dialog.addEventListener('close',()=>{cancel();update();});
  return {synchronize(){const s=getState();if(dialog.open&&(s.project?.path!==context||!canRecall()))close();if(pending&&pending.selectionKey!==selectionKey())cancel();const next=JSON.stringify([s.project?.path,s.scene_selection_sets]);if(dialog.open&&signature!==next){signature=next;list();}update();}};
}

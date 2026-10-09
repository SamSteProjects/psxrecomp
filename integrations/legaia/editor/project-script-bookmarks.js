const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
export function projectScriptBookmarks(state){
  const rows=state?.script_bookmarks,scenes=new Set((state?.scenes??[]).map(row=>row.id)),ids=new Set();
  if(!Array.isArray(rows)||rows.length>256)throw new Error('Invalid project script bookmark catalog.');
  for(const row of rows){
    if(!row||typeof row.id!=='string'||!/^bookmark:\/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(row.id)||ids.has(row.id)||typeof row.name!=='string'||!row.name.trim()||row.name!==row.name.trim()||row.name.length>80||!scenes.has(row.scene_id)||!hash(row.import_sha256)||!hash(row.source_record_sha256)||!hash(row.review_key)||!Number.isInteger(row.pc)||row.pc<0||row.pc>65535||typeof row.mnemonic!=='string'||!row.mnemonic||row.mnemonic.length>128||typeof row.owner_id!=='string'||!row.owner_id.startsWith(row.scene_id+'/')||!(/(\/actors\/man-p1\/|\/scripts\/man-p2\/)\d{4}$/.test(row.owner_id)||row.owner_id===row.scene_id+'/controllers/man-p1/0000'))throw new Error('Project script bookmark has invalid identity or source metadata.');
    ids.add(row.id);
  }
  return rows.map(row=>structuredClone(row)).sort((a,b)=>a.scene_id.localeCompare(b.scene_id)||a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
}
export function findProjectScriptBookmarks(rows,query='',scene=''){
  const terms=String(query).slice(0,256).trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return rows.filter(row=>(!scene||row.scene_id===scene)&&terms.every(term=>`${row.name} ${row.scene_id} ${row.owner_id} 0x${row.pc.toString(16)} 0x${row.pc.toString(16).padStart(4,'0')} ${row.mnemonic} ${row.source_record_sha256}`.toLocaleLowerCase().includes(term)));
}
export function mountProjectScriptBookmarks({after,getState,busy,onOpen,onError}){
  const document=after.ownerDocument,button=document.createElement('button');button.type='button';button.id='project-script-bookmarks';button.textContent='Script bookmarks';after.after(button);
  let dialog=null,refresh=null;
  const key=()=>JSON.stringify([getState().project?.path,getState().project_copy_source_key,getState().capabilities?.saved_script_bookmarks]);
  button.onclick=()=>{
    if(busy()||!getState().capabilities?.saved_script_bookmarks)return;
    dialog?.close();const opened=document.createElement('dialog');dialog=opened;opened.id='project-script-bookmarks-dialog';opened.className='project-bookmarks-dialog';
    const heading=document.createElement('div');heading.className='dialog-heading';const title=document.createElement('h2');title.textContent='Project script bookmarks';const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Close project script bookmarks');close.onclick=()=>opened.close();heading.append(title,close);
    const note=document.createElement('p');note.textContent='Open a saved original script boundary. Changing scenes updates the editor navigation context. Source verification happens before focusing the instruction; game execution remains unknown.';
    const tools=document.createElement('div');tools.className='dialog-actions';const search=document.createElement('input');search.type='search';search.maxLength=256;search.placeholder='Name, scene, owner, offset or mnemonic';search.setAttribute('aria-label','Find project script bookmarks');
    const scope=document.createElement('select');scope.setAttribute('aria-label','Script bookmark scene');const all=document.createElement('option');all.value='';all.textContent='All imported scenes';scope.append(all);for(const scene of getState().scenes??[]){const option=document.createElement('option');option.value=scene.id;option.textContent=scene.name;scope.append(option);}
    const reload=document.createElement('button');reload.type='button';reload.textContent='Refresh bookmark list';tools.append(search,scope,reload);
    const status=document.createElement('p');status.setAttribute('role','status');const list=document.createElement('div');list.className='project-bookmark-list';const error=document.createElement('p');error.className='dialog-error';error.setAttribute('role','alert');opened.append(heading,note,tools,status,list,error);document.body.append(opened);
    let acceptedKey=null,rows=[];const current=()=>opened.open&&dialog===opened&&acceptedKey===key();
    function draw(){
      const stale=!current(),blocked=stale||busy();search.disabled=scope.disabled=blocked;reload.disabled=busy();for(const item of list.querySelectorAll('button'))item.disabled=blocked;
      if(stale){status.textContent='Project inputs changed. Refresh this list before opening a bookmark.';return;}
      const matches=findProjectScriptBookmarks(rows,search.value,scope.value);status.textContent=busy()?'Finish the active request or pending edit before navigating.':`${matches.length} / ${rows.length} bookmarks`;list.replaceChildren();
      for(const row of matches){
        const card=document.createElement('section');card.className='project-bookmark-card';const title=document.createElement('h3');title.textContent=row.name;const summary=document.createElement('p');summary.textContent=`${row.scene_id.slice(8)} · 0x${row.pc.toString(16).toUpperCase()} · ${row.mnemonic}`;const owner=document.createElement('code');owner.textContent=row.owner_id;const provenance=document.createElement('details'),label=document.createElement('summary');label.textContent='Original source witness';const source=document.createElement('pre');source.textContent=`Record SHA256: ${row.source_record_sha256}\nImported scene SHA256: ${row.import_sha256}`;provenance.append(label,source);
        const open=document.createElement('button');open.type='button';open.textContent='Open bookmarked instruction';open.disabled=blocked;open.onclick=async()=>{if(busy()||!current())return;try{const latest=projectScriptBookmarks(getState()).find(value=>value.id===row.id);if(!latest||JSON.stringify(latest)!==JSON.stringify(row))throw new Error('Bookmark changed; refresh the list.');opened.close();await onOpen(structuredClone(row));}catch(exc){onError(exc);}};
        card.append(title,summary,owner,provenance,open);list.append(card);
      }
      if(!matches.length){const empty=document.createElement('p');empty.textContent=rows.length?'No bookmarks match these filters.':'Select an original decoded boundary in Script and dialogue, then Save script bookmark.';list.append(empty);}
    }
    function load(){if(busy()||dialog!==opened)return;try{rows=projectScriptBookmarks(getState());acceptedKey=key();error.textContent='';draw();}catch(exc){error.textContent=exc.message;acceptedKey=null;list.replaceChildren();}}
    search.oninput=scope.onchange=draw;reload.onclick=load;refresh=draw;
    opened.addEventListener('close',()=>{if(dialog===opened){dialog=null;refresh=null;}opened.remove();},{once:true});opened.showModal();load();
  };
  return {updateState(){button.disabled=busy()||!getState().capabilities?.saved_script_bookmarks;button.title=busy()?'Finish the active request or pending edit before browsing bookmarks.':'Browse saved original script locations across imported scenes.';refresh?.();},dispose(){dialog?.close();button.remove();}};
}

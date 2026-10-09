import {qualifyScriptBookmark} from './script-bookmark-source.js';
export {qualifyScriptBookmark} from './script-bookmark-source.js';
import {SCRIPT_BOOKMARK_TRANSFER_BYTES,exportScriptBookmark,importScriptBookmark} from './script-bookmark-transfer.js';
const offset=pc=>'0x'+pc.toString(16).padStart(4,'0');
export function mountScriptBookmarks(host,{owner,report,getState,getRows,getSelected,select,current,afterCommandCurrent=current,busy,editable,draftPending,command,reopen,onError,selectedBookmarkId=null}){
  const document=host.ownerDocument,section=document.createElement('section');section.className='script-bookmarks';
  const heading=document.createElement('h3');heading.textContent='Saved script bookmarks';
  const note=document.createElement('p');note.className='field-note';note.textContent='Save a selected Retail instruction or dialogue boundary. Bookmarks are project navigation metadata; they do not change instructions or prove execution.';
  const name=document.createElement('input');name.maxLength=160;name.setAttribute('aria-label','Script bookmark name');name.placeholder='For example, greeting branch';
  const list=document.createElement('select');list.setAttribute('aria-label','Saved script bookmarks');
  const status=document.createElement('p');status.setAttribute('role','status');status.className='field-note';
  const actions=document.createElement('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';
  const buttons={};for(const [id,label] of Object.entries({save:'Save script bookmark',recall:'Recall script bookmark',rename:'Rename script bookmark',update:'Update bookmark offset',delete:'Delete script bookmark'})){
    const button=document.createElement('button');button.type='button';button.textContent=label;buttons[id]=button;actions.append(button);
  }
  section.append(heading,note,name,list,status,actions);const anchor=host.querySelector('.script-instructions');if(anchor)anchor.before(section);else host.append(section);
  const transfer=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Transfer a script bookmark';transfer.append(summary);
  const transferNote=document.createElement('p');transferNote.className='field-note';transferNote.textContent='Export navigation metadata. Import creates a new bookmark for this exact Retail scene, script and decoded boundary.';
  const file=document.createElement('input');file.type='file';file.accept='.json,application/json';file.setAttribute('aria-label','Import script bookmark JSON');
  const importedName=document.createElement('input');importedName.maxLength=160;importedName.setAttribute('aria-label','Imported script bookmark name');importedName.placeholder='Name for imported bookmark';
  const exportButton=document.createElement('button');exportButton.type='button';exportButton.textContent='Export selected script bookmark JSON';
  const importButton=document.createElement('button');importButton.type='button';importButton.textContent='Import as new script bookmark';
  const clearButton=document.createElement('button');clearButton.type='button';clearButton.textContent='Clear bookmark transfer';
  const transferStatus=document.createElement('p');transferStatus.className='field-note';transferStatus.setAttribute('role','status');
  transfer.append(transferNote,exportButton,file,importedName,importButton,clearButton,transferStatus);section.append(transfer);
  let disposed=false,selectedId=selectedBookmarkId,imported=null,reading=false,generation=0;
  const rows=()=>getRows().filter(row=>row.owner_id===owner),row=()=>rows().find(value=>value.id===list.value);
  function selection(){const pc=getSelected();if(!Number.isInteger(pc))return null;try{qualifyScriptBookmark({owner_id:owner,pc,source_record_sha256:report.record?.sha256,mnemonic:(report.instructions??[]).find(v=>v.pc===pc)?.mnemonic??'DIALOGUE_SEGMENT'},owner,report);return pc;}catch{return null;}}
  function updateState(){
    if(disposed)return;const available=current(),blocked=!available||busy()||reading,editing=!blocked&&editable()&&!draftPending(),pc=selection(),saved=row();let recall=false;
    try{if(saved){qualifyScriptBookmark(saved,owner,report);recall=true;}}catch{}
    name.disabled=blocked||!editable();list.disabled=blocked;
    buttons.save.disabled=!editing||pc===null||!name.value.trim();buttons.rename.disabled=!editing||!saved||!name.value.trim();buttons.update.disabled=!editing||!saved||pc===null;buttons.delete.disabled=!editing||!saved;buttons.recall.disabled=blocked||!recall;
    status.textContent=!available?'Script context changed; reopen inspection.':pc===null?'Select a decoded Retail boundary to save.':`Selected ${offset(pc)} · ${saved?`${saved.name}: ${offset(saved.pc)} ${saved.mnemonic}`:'No saved bookmark selected'}`;
    if(saved&&!recall)status.textContent+=' · Saved source is unavailable in this report; recall is disabled.';
    if(draftPending())status.textContent+=' · Apply or discard script drafts before editing bookmarks.';
    let exportOk=false,importOk=false;try{if(saved&&getState){exportScriptBookmark(saved,getState(),owner,report);exportOk=true;}}catch{}
    try{if(imported&&getState){importScriptBookmark(imported,getState(),owner,report,importedName.value);importOk=true;}}catch{}
    exportButton.disabled=blocked||!exportOk;importButton.disabled=!editing||!importOk;file.disabled=!editing;importedName.disabled=blocked||!editable();clearButton.disabled=!reading&&!imported;
  }
  function refresh(){const records=rows();list.replaceChildren();for(const value of records){const option=document.createElement('option');option.value=value.id;option.textContent=`${value.name} · ${offset(value.pc)} ${value.mnemonic}`;list.append(option);}if(records.some(v=>v.id===selectedId))list.value=selectedId;selectedId=list.value;updateState();}
  async function mutate(kind){
    updateState();if(disposed||buttons[kind].disabled||!current()||busy())return;
    const saved=row(),pc=selection(),body={type:kind==='save'?'create_script_bookmark':`${kind==='update'?'update':kind}_script_bookmark`};
    if(kind==='save')Object.assign(body,{owner_id:owner,name:name.value,pc,source_record_sha256:report.record.sha256});
    else{Object.assign(body,{bookmark_id:saved.id,review_key:saved.review_key});if(kind==='rename')body.name=name.value;if(kind==='update')Object.assign(body,{pc,source_record_sha256:report.record.sha256});}
    try{if(await command(body)){if(afterCommandCurrent()&&!disposed)await reopen(pc);}}catch(error){onError(error);}finally{if(!disposed)refresh();}
  }
  for(const kind of ['save','rename','update','delete'])buttons[kind].onclick=()=>mutate(kind);
  buttons.recall.onclick=()=>{if(disposed||!current()||busy())return;try{const pc=qualifyScriptBookmark(row(),owner,report);if(!select(pc))throw new Error('Bookmark offset is absent from this inspection.');updateState();}catch(error){onError(error);}};
  list.onchange=()=>{selectedId=list.value;name.value=row()?.name??'';updateState();};name.oninput=updateState;
  exportButton.onclick=()=>{if(disposed||exportButton.disabled||!current()||busy())return;try{const value=exportScriptBookmark(row(),getState(),owner,report),url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='script-bookmark.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){onError(error);}};
  clearButton.onclick=()=>{generation++;reading=false;imported=null;file.value='';importedName.value='';transferStatus.textContent='';updateState();};
  file.onchange=async()=>{const chosen=file.files?.[0];if(disposed||file.disabled||!chosen||!current()||busy())return;const token=++generation;imported=null;reading=true;transferStatus.textContent='Reading bookmark metadata…';updateState();try{
    if(chosen.size>SCRIPT_BOOKMARK_TRANSFER_BYTES)throw Error('Bookmark transfer exceeds 64 KiB.');
    const text=await chosen.text();if(disposed||token!==generation||!current()||busy()||!editable()||draftPending())return;
    if(new TextEncoder().encode(text).byteLength>SCRIPT_BOOKMARK_TRANSFER_BYTES)throw Error('Bookmark transfer exceeds 64 KiB.');
    const value=JSON.parse(text),base=Array.from(value.source_bookmark?.name??'Bookmark'),used=new Set(rows().map(row=>row.name.toLowerCase()));let proposed=base.slice(0,75).join('')+' Copy';
    for(let index=2;used.has(proposed.toLowerCase())&&index<=257;index++)proposed=base.slice(0,70).join('')+' Copy '+index;
    importScriptBookmark(value,getState(),owner,report,proposed);imported=value;importedName.value=proposed;transferStatus.textContent=`Verified ${offset(value.source_bookmark.pc)} ${value.source_bookmark.mnemonic}. Choose a distinct name and import.`;
  }catch(error){if(!disposed&&token===generation){transferStatus.textContent=error.message;onError(error);}}finally{if(!disposed&&token===generation){reading=false;updateState();}}};
  importedName.oninput=updateState;
  importButton.onclick=async()=>{updateState();if(disposed||importButton.disabled||!current()||busy())return;try{const body=importScriptBookmark(imported,getState(),owner,report,importedName.value),before=new Set(getRows().map(row=>row.id));if(await command(body)){if(afterCommandCurrent()&&!disposed){const copies=getRows().filter(row=>!before.has(row.id)&&row.owner_id===body.owner_id&&row.name===body.name&&row.pc===body.pc&&row.source_record_sha256===body.source_record_sha256);if(copies.length!==1)throw Error('Bookmark saved; reopen the script to inspect its new identity.');qualifyScriptBookmark(copies[0],owner,report);await reopen(body.pc,copies[0]);}}}catch(error){onError(error);}finally{if(!disposed)refresh();}};
  refresh();return {updateState,dispose(){disposed=true;generation++;imported=null;section.remove();}};
}

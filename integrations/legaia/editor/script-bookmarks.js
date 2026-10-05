const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const offset=pc=>'0x'+pc.toString(16).padStart(4,'0');
export function qualifyScriptBookmark(row,owner,report){
  if(!row||row.owner_id!==owner||!hash(row.source_record_sha256)||row.source_record_sha256!==report?.record?.sha256||report.read_only!==true||!Number.isInteger(row.pc)||row.pc<0||row.pc>65535)throw new Error('Bookmark differs from this verified Retail script record.');
  const matches=(report.instructions??[]).filter(item=>item.pc===row.pc).map(item=>item.mnemonic).concat((report.dialogues??[]).filter(item=>item.pc===row.pc).map(()=>'DIALOGUE_SEGMENT'));
  if(matches.length!==1||matches[0]!==row.mnemonic)throw new Error('Bookmark no longer identifies a unique decoded Retail boundary.');
  return row.pc;
}
export function mountScriptBookmarks(host,{owner,report,getRows,getSelected,select,current,busy,editable,draftPending,command,reopen,onError}){
  const document=host.ownerDocument,section=document.createElement('section');section.className='script-bookmarks';
  const heading=document.createElement('h3');heading.textContent='Saved script bookmarks';
  const note=document.createElement('p');note.className='field-note';note.textContent='Save a selected Retail instruction or dialogue boundary. Bookmarks are project navigation metadata; they do not change instructions or prove execution.';
  const name=document.createElement('input');name.maxLength=80;name.setAttribute('aria-label','Script bookmark name');name.placeholder='For example, greeting branch';
  const list=document.createElement('select');list.setAttribute('aria-label','Saved script bookmarks');
  const status=document.createElement('p');status.setAttribute('role','status');status.className='field-note';
  const actions=document.createElement('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';
  const buttons={};for(const [id,label] of Object.entries({save:'Save script bookmark',recall:'Recall script bookmark',rename:'Rename script bookmark',update:'Update bookmark offset',delete:'Delete script bookmark'})){
    const button=document.createElement('button');button.type='button';button.textContent=label;buttons[id]=button;actions.append(button);
  }
  section.append(heading,note,name,list,status,actions);host.querySelector('.script-instructions')?.before(section);
  let disposed=false,selectedId=null;
  const rows=()=>getRows().filter(row=>row.owner_id===owner),row=()=>rows().find(value=>value.id===list.value);
  function selection(){const pc=getSelected();if(!Number.isInteger(pc))return null;try{qualifyScriptBookmark({owner_id:owner,pc,source_record_sha256:report.record?.sha256,mnemonic:(report.instructions??[]).find(v=>v.pc===pc)?.mnemonic??'DIALOGUE_SEGMENT'},owner,report);return pc;}catch{return null;}}
  function updateState(){
    if(disposed)return;const available=current(),blocked=!available||busy(),editing=!blocked&&editable()&&!draftPending(),pc=selection(),saved=row();let recall=false;
    try{if(saved){qualifyScriptBookmark(saved,owner,report);recall=true;}}catch{}
    name.disabled=blocked||!editable();list.disabled=blocked;
    buttons.save.disabled=!editing||pc===null||!name.value.trim();buttons.rename.disabled=!editing||!saved||!name.value.trim();buttons.update.disabled=!editing||!saved||pc===null;buttons.delete.disabled=!editing||!saved;buttons.recall.disabled=blocked||!recall;
    status.textContent=!available?'Script context changed; reopen inspection.':pc===null?'Select a decoded Retail boundary to save.':`Selected ${offset(pc)} · ${saved?`${saved.name}: ${offset(saved.pc)} ${saved.mnemonic}`:'No saved bookmark selected'}`;
    if(saved&&!recall)status.textContent+=' · Saved source is unavailable in this report; recall is disabled.';
    if(draftPending())status.textContent+=' · Apply or discard script drafts before editing bookmarks.';
  }
  function refresh(){const records=rows();list.replaceChildren();for(const value of records){const option=document.createElement('option');option.value=value.id;option.textContent=`${value.name} · ${offset(value.pc)} ${value.mnemonic}`;list.append(option);}if(records.some(v=>v.id===selectedId))list.value=selectedId;selectedId=list.value;updateState();}
  async function mutate(kind){
    updateState();if(disposed||buttons[kind].disabled||!current()||busy())return;
    const saved=row(),pc=selection(),body={type:kind==='save'?'create_script_bookmark':`${kind==='update'?'update':kind}_script_bookmark`};
    if(kind==='save')Object.assign(body,{owner_id:owner,name:name.value,pc,source_record_sha256:report.record.sha256});
    else{Object.assign(body,{bookmark_id:saved.id,review_key:saved.review_key});if(kind==='rename')body.name=name.value;if(kind==='update')Object.assign(body,{pc,source_record_sha256:report.record.sha256});}
    try{if(await command(body)){if(current()&&!disposed)await reopen(pc);}}catch(error){onError(error);}finally{if(!disposed)refresh();}
  }
  for(const kind of ['save','rename','update','delete'])buttons[kind].onclick=()=>mutate(kind);
  buttons.recall.onclick=()=>{if(disposed||!current()||busy())return;try{const pc=qualifyScriptBookmark(row(),owner,report);if(!select(pc))throw new Error('Bookmark offset is absent from this inspection.');updateState();}catch(error){onError(error);}};
  list.onchange=()=>{selectedId=list.value;name.value=row()?.name??'';updateState();};name.oninput=updateState;
  refresh();return {updateState,dispose(){disposed=true;section.remove();}};
}

const families=new Set(['ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','ScriptFacing','ScriptBranches','Dialogue','Transitions']);

// Uses the existing source-bound removal witness; never accepts arbitrary component writes.
export function scriptComponentResetReview(state,entity,component){
  if(!families.has(component)||state?.project?.mode!=='edit')throw new Error('Choose an authored script component in Edit mode');
  const current=state.scene?.entities?.find(row=>row.id===entity?.id);
  const script=state.authored_assets?.find(row=>row.id===entity?.id&&row.kind==='script'&&row.scene_id===state.scene?.id&&typeof row.id==='string'&&/^scene:\/\/[A-Za-z0-9_-]{1,128}\/scripts\/man-p2\/[0-9]{4}$/.test(row.id)&&row.id.startsWith(state.scene.id+'/scripts/man-p2/'));
  const review=state.authored_assets?.find(row=>row.id===entity?.id)?.component_reviews?.find(row=>row.component===component);
  const field=component==='Dialogue'?'runs':'entries';
  const entries=component==='Dialogue'?current?.components?.Dialogue?.authored?.runs:current?.components?.[component]?.entries;
  const scriptEntries=script?.authored?.[component]?.[field];
  const reviewedEntries=entries??scriptEntries;
  if(!reviewedEntries||Array.isArray(reviewedEntries)||typeof reviewedEntries!=='object'||!Object.keys(reviewedEntries).length||Object.keys(reviewedEntries).length>1024||
      !review||typeof review.review_key!=='string'||!/^[a-f0-9]{64}$/.test(review.review_key)||
      JSON.stringify(review.authored?.[field])!==JSON.stringify(reviewedEntries))throw new Error('Authored component review is unavailable or stale; refresh the Inspector');
  return JSON.parse(JSON.stringify({component,owner:entity.id,entries:reviewedEntries,review_key:review.review_key}));
}

export function openScriptComponentReset({entity,component,getState,current,editable,busy,api,onError,onReset=()=>{}}){
  if(busy()||!editable()||!current())return;
  const review=scriptComponentResetReview(getState(),entity,component);
  const dialog=document.createElement('dialog');dialog.className='script-component-reset';
  const title=document.createElement('h2'),owner=document.createElement('code'),note=document.createElement('p'),data=document.createElement('pre');
  title.textContent=`Reset ${component}`;owner.textContent=review.owner;
  note.textContent=`Remove all ${Object.keys(review.entries).length} authored ${component==='Dialogue'?'text runs':'instruction entries'} shown below and inherit their imported source ${component==='Dialogue'?'text':'operands'}. Other components stay authored. This is one undoable project change; gameplay remains unverified.`;
  data.className='diagnostic-detail';data.textContent=JSON.stringify(review.entries,null,2);
  const actions=document.createElement('div'),cancel=document.createElement('button'),apply=document.createElement('button');
  actions.className='dialog-actions';cancel.type=apply.type='button';cancel.textContent='Cancel component reset';apply.textContent='Reset reviewed component';
  cancel.onclick=()=>dialog.close();
  let applying=false;
  apply.onclick=async()=>{
    if(applying||busy()||!editable()||!current()||!dialog.open)return;
    try{
      const latest=scriptComponentResetReview(getState(),entity,component);
      if(latest.review_key!==review.review_key)throw new Error('Authored component changed; cancel and review it again');
      applying=true;apply.disabled=true;
      if(await api('/api/command',{type:'revert_authored_component',entity_id:review.owner,component:review.component,review_key:review.review_key},{success:`${review.component} reset. Undo restores its authored entries.`})){dialog.close();await onReset(review.component);}
    }catch(error){onError(error);}finally{applying=false;apply.disabled=false;}
  };
  actions.append(cancel,apply);dialog.append(title,owner,note,data,actions);
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);dialog.showModal();cancel.focus();
}

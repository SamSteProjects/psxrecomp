const families=new Set(['ScriptMovement','ScriptFlags','ScriptWaits','ScriptModelSelectors','ScriptFacing','ScriptBranches']);

// Uses the existing source-bound removal witness; never accepts arbitrary component writes.
export function scriptComponentResetReview(state,entity,component){
  if(!families.has(component)||state?.project?.mode!=='edit')throw new Error('Choose an authored script component in Edit mode');
  const current=state.scene?.entities?.find(row=>row.id===entity?.id);
  const review=state.authored_assets?.find(row=>row.id===entity?.id)?.component_reviews?.find(row=>row.component===component);
  const entries=current?.components?.[component]?.entries;
  if(!entries||Array.isArray(entries)||typeof entries!=='object'||!Object.keys(entries).length||Object.keys(entries).length>1024||
      !review||typeof review.review_key!=='string'||!/^[a-f0-9]{64}$/.test(review.review_key)||
      JSON.stringify(review.authored?.entries)!==JSON.stringify(entries))throw new Error('Authored component review is unavailable or stale; refresh the Inspector');
  return JSON.parse(JSON.stringify({component,owner:entity.id,entries,review_key:review.review_key}));
}

export function openScriptComponentReset({entity,component,getState,current,editable,busy,api,onError}){
  if(busy()||!editable()||!current())return;
  const review=scriptComponentResetReview(getState(),entity,component);
  const dialog=document.createElement('dialog');dialog.className='script-component-reset';
  const title=document.createElement('h2'),owner=document.createElement('code'),note=document.createElement('p'),data=document.createElement('pre');
  title.textContent=`Reset ${component}`;owner.textContent=review.owner;
  note.textContent=`Remove all ${Object.keys(review.entries).length} authored instruction entries shown below and inherit their imported source operands. Other components stay authored. This is one undoable project change; gameplay remains unverified.`;
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
      if(await api('/api/command',{type:'revert_authored_component',entity_id:review.owner,component:review.component,review_key:review.review_key},{success:`${review.component} reset. Undo restores its authored entries.`}))dialog.close();
    }catch(error){onError(error);}finally{applying=false;apply.disabled=false;}
  };
  actions.append(cancel,apply);dialog.append(title,owner,note,data,actions);
  dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);dialog.showModal();cancel.focus();
}

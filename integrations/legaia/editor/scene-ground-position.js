export function sceneGroundPositionCommand(kind,id,position){
  if(!['actor','npc'].includes(kind)||typeof id!=='string'||!id||!position||Object.keys(position).sort().join(',')!=='x,z'||Object.values(position).some(v=>!Number.isInteger(v)||v<64||v>16384||v%64))throw Error('Choose a supported native source-ground X/Z position.');
  return {type:kind==='npc'?'set_actor_draft_position':'set_transform',entity_id:id,position:{x:position.x,z:position.z}};
}
// The Inspector owns the proposal; the existing Project command owns application/history.
export function mountSceneGroundPosition({host,kind,id,getContext,busy,canEdit,beginPick,apply,onError}){
  const root=document.createElement('div'),choose=document.createElement('button'),note=document.createElement('p'),review=document.createElement('div'),accept=document.createElement('button'),discard=document.createElement('button');
  choose.type=accept.type=discard.type='button';choose.textContent='Choose position from scene ground';accept.textContent='Apply picked X/Z';discard.textContent='Discard picked position';note.className='field-note';review.hidden=true;review.append(accept,discard);root.append(choose,note,review);host.append(root);
  const context=structuredClone(getContext()),key=JSON.stringify(context);let proposed=null,withdrawn=false;
  const fresh=()=>!withdrawn&&root.isConnected&&canEdit()&&key===JSON.stringify(getContext());
  const refresh=()=>{if(!root.isConnected){clearInterval(timer);return;}if(!fresh()){withdrawn=true;proposed=null;review.hidden=true;note.textContent='Position source or selection changed. Reopen the Inspector.';}choose.disabled=busy()||!fresh();accept.disabled=busy()||!fresh()||!proposed;discard.disabled=busy()||!proposed;};
  choose.onclick=()=>{refresh();if(choose.disabled)return;try{beginPick(result=>{if(!fresh()){refresh();return;}if(result){sceneGroundPositionCommand(kind,id,result.position);proposed=structuredClone(result.position);note.textContent=`Current X ${context.position.x}, Z ${context.position.z}. Proposed X ${proposed.x}, Z ${proposed.z}. Height and other properties stay unchanged; Apply is required.`;review.hidden=false;}refresh();},{current:fresh,returnLabel:'Return to position Inspector',note:'Choose a visible source-ground corner within 24 pixels. Drag to orbit; right-drag to pan. Only X/Z will be proposed in the Inspector.'});}catch(error){onError(error);}};
  discard.onclick=()=>{proposed=null;review.hidden=true;note.textContent='Picked position discarded; Project unchanged.';refresh();};
  accept.onclick=async()=>{refresh();if(accept.disabled)return;try{await apply(sceneGroundPositionCommand(kind,id,proposed));}catch(error){onError(error);}};
  const timer=setInterval(refresh,250);refresh();return {root};
}

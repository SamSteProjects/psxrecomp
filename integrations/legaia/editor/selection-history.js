// Ephemeral scene inspection history; no project command or native data belongs here.
export function selectionHistoryValue(value){
  if(!value||Object.keys(value).sort().join()!=='focus,ids,kind'||!['placements','resource','environment'].includes(value.kind)||typeof value.focus!=='string'||!value.focus||value.focus.length>1024||!Array.isArray(value.ids)||value.ids.length<1||value.ids.length>128||value.kind!=='placements'&&value.ids.length!==1||new Set(value.ids).size!==value.ids.length||JSON.stringify(value.ids)!==JSON.stringify([...value.ids].sort())||!value.ids.includes(value.focus))throw Error('Invalid inspection history selection.');
  for(let i=0;i<value.ids.length;i++)if(typeof value.ids[i]!=='string'||!value.ids[i]||value.ids[i].length>1024)throw Error('Invalid inspection history identity.');
  return structuredClone(value);
}
export function createSelectionHistory(limit=64){
  if(!Number.isSafeInteger(limit)||limit<2||limit>256)throw Error('Invalid inspection history limit.');
  let scope=null,rows=[],cursor=-1,version=0;
  const resetScope=next=>{if(typeof next!=='string'||!next||next.length>4096)throw Error('Invalid inspection history scope.');if(next===scope)return false;scope=next;rows=[];cursor=-1;version++;return true;};
  const record=(next,value)=>{resetScope(next);if(value===null)return;value=selectionHistoryValue(value);if(JSON.stringify(rows[cursor])===JSON.stringify(value))return;rows=rows.slice(0,cursor+1);rows.push(value);if(rows.length>limit)rows.shift();cursor=rows.length-1;version++;};
  const candidate=direction=>{if(![-1,1].includes(direction))throw Error('Invalid inspection history direction.');const index=cursor+direction;return index>=0&&index<rows.length?{scope,version,index,value:structuredClone(rows[index])}:null;};
  const commit=token=>{if(!token||!Number.isSafeInteger(token.index)||token.scope!==scope||token.version!==version||Math.abs(token.index-cursor)!==1||JSON.stringify(token.value)!==JSON.stringify(rows[token.index]))return false;cursor=token.index;version++;return true;};
  return {resetScope,record,candidate,commit};
}
export function mountSelectionHistory(host,{getScope,getSelection,available,busy,navigate,onError=()=>{}}){
  const model=createSelectionHistory(),bar=document.createElement('div');bar.className='hierarchy-history';const buttons=[-1,1].map(direction=>{const b=document.createElement('button');b.type='button';b.textContent=direction===-1?'Back selection':'Forward selection';b.setAttribute('aria-label',b.textContent);bar.append(b);return {b,direction};});host.after(bar);let moving=false;
  const refresh=()=>{for(const {b,direction} of buttons){const token=model.candidate(direction);b.disabled=moving||busy()||!available()||!token;b.title=token?'Inspect '+token.value.focus+(token.value.ids.length>1?' and '+(token.value.ids.length-1)+' other placements':''):'No inspection selection in this direction';}};
  const observe=()=>{try{model.resetScope(getScope());if(!moving)model.record(getScope(),getSelection());}catch(error){onError(error);}refresh();};
  for(const {b,direction} of buttons)b.onclick=async()=>{if(b.disabled||moving||busy()||!available())return;const token=model.candidate(direction);if(!token)return;moving=true;refresh();try{if(await navigate(structuredClone(token.value))!==true||getScope()!==token.scope||!model.commit(token)){if(getScope()===token.scope)throw Error('Previous inspection selection is unavailable or changed.');}}catch(error){if(getScope()===token.scope)onError(error);}finally{moving=false;observe();}};
  return {observe,refresh};
}

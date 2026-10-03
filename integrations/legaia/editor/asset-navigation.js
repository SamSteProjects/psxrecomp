// Native buttons retain activation; arrows move focus without selecting assets.
export function mountAssetNavigation(list,getContext,onPage=()=>false){
  const doc=list.ownerDocument,stamp=()=>JSON.stringify(getContext());
  let remembered=null,disposed=false,renderedContext=stamp();
  const allRows=()=>Array.from(list.children).filter(row=>row.dataset?.assetKey&&!row.hidden).map(row=>({key:row.dataset.assetKey,buttons:Array.from(row.querySelectorAll('button[data-asset-action]'))}));
  const rows=()=>allRows().map(row=>({...row,buttons:row.buttons.filter(button=>!button.disabled&&!button.hidden)})).filter(row=>row.buttons.length);
  const locate=button=>{for(const row of rows()){const index=row.buttons.indexOf(button);if(index>=0)return {row,index};}return null;};
  const current=()=>{const found=locate(doc.activeElement);return found?{key:found.row.key,action:doc.activeElement.dataset.assetAction}:null;};
  const choose=(available,point)=>{const row=available.find(row=>row.key===point?.key)??available[0];return row?.buttons.find(button=>button.dataset.assetAction===point?.action)??row?.buttons[0];};
  function entry(button){for(const row of Array.from(list.children))for(const item of row.querySelectorAll('button[data-asset-action]'))item.tabIndex=item===button?0:-1;list.tabIndex=button?-1:0;}
  function focus(button){if(!button)return;entry(button);remembered={context:renderedContext,key:locate(button).row.key,action:button.dataset.assetAction};button.focus({preventScroll:true});button.scrollIntoView({block:'nearest',inline:'nearest'});}
  function beforeRender(){return {context:renderedContext,inside:list.contains(doc.activeElement),point:current()};}
  function afterRender(snapshot){
    if(disposed)return;const context=stamp(),same=snapshot?.context===context,point=same?snapshot.point:null,preferred=point??(remembered?.context===context?remembered:null),button=choose(rows(),preferred);entry(button);
    renderedContext=context;
    if(button)remembered={context,key:locate(button).row.key,action:button.dataset.assetAction};else remembered=allRows().some(row=>row.key===preferred?.key)?{context,key:preferred.key,action:preferred.action}:null;
    if(snapshot?.inside&&same){if(button)focus(button);else list.focus({preventScroll:true});}
  }
  const focusin=event=>{const found=locate(event.target);if(found){entry(event.target);remembered={context:renderedContext,key:found.row.key,action:event.target.dataset.assetAction};}};
  const keydown=event=>{
    if(disposed||renderedContext!==stamp()||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;const found=locate(event.target);if(!found)return;
    const available=rows(),index=available.findIndex(row=>row.key===found.row.key),action=event.target.dataset.assetAction;
    if(event.key==='PageDown'||event.key==='PageUp'){
      const delta=event.key==='PageDown'?1:-1,context=stamp();if(onPage(delta)!==true)return;event.preventDefault();if(context!==stamp())return;const next=rows(),row=delta>0?next[0]:next.at(-1);if(row)focus(row.buttons.find(button=>button.dataset.assetAction===action)??row.buttons[0]);return;
    }
    let target;
    if(event.key==='ArrowLeft'||event.key==='ArrowRight')target=found.row.buttons[Math.max(0,Math.min(found.row.buttons.length-1,found.index+(event.key==='ArrowRight'?1:-1)))];
    else if(['ArrowUp','ArrowDown','Home','End'].includes(event.key)){
      const next=event.key==='Home'?0:event.key==='End'?available.length-1:Math.max(0,Math.min(available.length-1,index+(event.key==='ArrowDown'?1:-1))),row=available[next];target=row.buttons.find(button=>button.dataset.assetAction===action)??row.buttons[0];
    }else return;
    event.preventDefault();focus(target);
  };
  list.setAttribute('role','group');list.setAttribute('aria-label','Asset database results');list.addEventListener('focusin',focusin);list.addEventListener('keydown',keydown);afterRender();
  return {beforeRender,afterRender,dispose(){disposed=true;list.removeEventListener('focusin',focusin);list.removeEventListener('keydown',keydown);}};
}

// Flat SDK hierarchy: focus browsing never changes project selection or authors data.
export function mountHierarchyNavigation(host,getScope){
  let activeId=null;
  const rows=()=>Array.from(host.querySelectorAll('[role="treeitem"]')).filter(row=>!row.hidden&&!row.disabled);
  const scope=()=>JSON.stringify(getScope());
  function mark(row){activeId=row?.title??null;for(const item of rows())item.tabIndex=item===row?0:-1;host.tabIndex=row?-1:0;}
  function beforeRender(){const focused=host.ownerDocument.activeElement;return {scope:scope(),focused:host.contains(focused),id:focused?.getAttribute?.('role')==='treeitem'?focused.title:activeId};}
  function afterRender(snapshot){const items=rows(),same=snapshot?.scope===scope();const row=(same?items.find(item=>item.title===snapshot.id):null)??items.find(item=>item.getAttribute('aria-selected')==='true')??items[0];mark(row);if(snapshot?.focused&&same)(row??host).focus({preventScroll:true});}
  function focus(event){const row=event.target.closest('[role="treeitem"]');if(row&&host.contains(row))mark(row);}
  function key(event){if(event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;const items=rows();if(!items.length)return;const current=items.indexOf(event.target.closest('[role="treeitem"]'));const index=event.key==='Home'?0:event.key==='End'?items.length-1:event.key==='ArrowDown'?Math.min(items.length-1,current+1):Math.max(0,current-1);event.preventDefault();mark(items[index]);items[index].focus();}
  host.addEventListener('focusin',focus);host.addEventListener('keydown',key);
  return {beforeRender,afterRender,dispose(){host.removeEventListener('focusin',focus);host.removeEventListener('keydown',key);}};
}

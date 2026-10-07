// SDK hierarchy: focus browsing never changes project selection or authors data.
export function mountHierarchyNavigation(host,getScope,{now=()=>Date.now()}={}){
  let activeId=null,typed='',typedAt=0,typedScope=null;
  const rows=()=>Array.from(host.querySelectorAll('[role="treeitem"]')).filter(row=>!row.hidden&&!row.disabled);
  const scope=()=>JSON.stringify(getScope());
  function mark(row){activeId=row?.title??null;for(const item of rows())item.tabIndex=item===row?0:-1;host.tabIndex=row?-1:0;}
  function beforeRender(){const focused=host.ownerDocument.activeElement;return {scope:scope(),focused:host.contains(focused),id:focused?.getAttribute?.('role')==='treeitem'?focused.title:activeId};}
  function afterRender(snapshot){typed='';const items=rows(),same=snapshot?.scope===scope();const row=(same?items.find(item=>item.title===snapshot.id):null)??items.find(item=>item.getAttribute('aria-selected')==='true')??items[0];mark(row);if(snapshot?.focused&&same)(row??host).focus({preventScroll:true});}
  function focus(event){const row=event.target.closest('[role="treeitem"]');if(row&&host.contains(row))mark(row);}
  function key(event){
    if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
    const target=event.target.closest('[role="treeitem"]');
    if(!event.isComposing&&/^[\p{L}\p{N}]$/u.test(event.key)&&(target||event.target===host)){
      const items=rows(),stamp=now(),currentScope=scope(),letter=event.key.toLowerCase();
      if(!items.length)return;
      if(typedScope!==currentScope||stamp-typedAt>1000||stamp<typedAt)typed='';
      const repeat=typed.length===1&&typed===letter;typed=repeat?letter:(typed+letter).slice(-64);typedAt=stamp;typedScope=currentScope;
      const current=items.indexOf(target),offset=typed.length===1?1:0;
      const label=row=>String(row.querySelector?.('.entity-name')?.textContent??row.textContent??'').trim().replace(/^[^\p{L}\p{N}]+/u,'').toLowerCase();
      for(let n=0;n<items.length;n++){const index=((current<0?-offset:current)+offset+n)%items.length;if(label(items[index]).startsWith(typed)){event.preventDefault();mark(items[index]);items[index].focus();return;}}
      return;
    }
    if(['ArrowLeft','ArrowRight','ArrowDown','ArrowUp','Home','End'].includes(event.key))typed='';
    if(event.key==='ArrowLeft'&&target?.getAttribute('aria-level')==='2'){
      let parent=target.previousElementSibling;
      while(parent&&!parent.dataset?.hierarchyGroup)parent=parent.previousElementSibling;
      if(parent&&host.contains(parent)&&!parent.hidden&&!parent.disabled){event.preventDefault();mark(parent);parent.focus();}
      return;
    }
    if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
    const items=rows();if(!items.length)return;const current=items.indexOf(target);const index=event.key==='Home'?0:event.key==='End'?items.length-1:event.key==='ArrowDown'?Math.min(items.length-1,current+1):Math.max(0,current-1);event.preventDefault();mark(items[index]);items[index].focus();
  }
  host.addEventListener('focusin',focus);host.addEventListener('keydown',key);
  return {beforeRender,afterRender,dispose(){host.removeEventListener('focusin',focus);host.removeEventListener('keydown',key);}};
}

const groups=new Set(['actors','npc-drafts','environment','transition','trigger','region','collision','script']);
export function revealHierarchyEntity(root,id){
  if(typeof id!=='string'||!id||id.length>1024)return false;
  const row=[...root.querySelectorAll('.entity-row')].find(item=>item.title===id);if(!row||row.disabled)return false;
  let heading=row.previousElementSibling;
  while(heading&&!heading.dataset.hierarchyGroup)heading=heading.previousElementSibling;
  if(row.hidden&&heading?.getAttribute('aria-expanded')==='false')heading.click();
  if(row.hidden)return false;
  row.scrollIntoView({block:'nearest'});row.focus({preventScroll:true});return true;
}

export function hierarchyGroupExpanded(id,state,filter=''){
  if(!groups.has(id)||!(state?.collapsed instanceof Set))throw new Error('Invalid hierarchy group state');
  return Boolean(String(filter).trim())||!state.collapsed.has(id);
}

// Group folds affect tree presentation only; scene visibility and SDK selection are separate.
export function mountHierarchyGroups(root,{state,scope,filter='',current,onVisibility}){
  if(state.scope!==scope){state.scope=scope;state.collapsed=new Set();}
  for(const heading of [...root.querySelectorAll('[data-hierarchy-group-heading]')]){
    const id=heading.dataset.hierarchyGroupHeading;if(!groups.has(id))continue;
    const members=[];
    for(let row=heading.nextElementSibling;row&&!row.hasAttribute('data-hierarchy-group-heading');row=row.nextElementSibling){if(row.classList.contains('entity-row'))members.push(row);}
    const button=document.createElement('button'),label=heading.textContent;
    button.type='button';button.className='hierarchy-group';button.dataset.hierarchyGroup=id;button.title=`${label.replace(/ \([0-9]+\)$/,'')} group`;button.setAttribute('role','treeitem');button.setAttribute('aria-level','1');
    button.disabled=Boolean(String(filter).trim());if(button.disabled)button.title+=' · Clear search to collapse';
    const update=()=>{
      const expanded=hierarchyGroupExpanded(id,state,filter);button.setAttribute('aria-expanded',String(expanded));button.textContent=`${expanded?'▾':'▸'} ${label}`;
      for(const row of members){row.hidden=!expanded;row.setAttribute('aria-level','2');}
    };
    const set=expanded=>{if(button.disabled||!current())return;if(expanded)state.collapsed.delete(id);else state.collapsed.add(id);update();onVisibility();};
    button.onclick=()=>set(!hierarchyGroupExpanded(id,state,filter));
    button.onkeydown=event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key)||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;event.preventDefault();set(event.key==='ArrowRight');};
    heading.replaceWith(button);update();
  }
}

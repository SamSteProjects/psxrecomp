export const HIERARCHY_GROUP_IDS=Object.freeze(['actors','npc-drafts','environment','transition','trigger','region','collision','script']);
const groups=new Set(HIERARCHY_GROUP_IDS);
export function revealHierarchyEntities(root,ids,focusId=ids?.[0]){
  if(!Array.isArray(ids)||ids.length<1||ids.length>128||new Set(ids).size!==ids.length||!ids.includes(focusId))return false;
  for(let index=0;index<ids.length;index++)if(typeof ids[index]!=='string'||!ids[index]||ids[index].length>1024)return false;
  const all=[...root.querySelectorAll('.entity-row')],rows=ids.map(id=>all.filter(row=>row.title===id));
  if(rows.some(matches=>matches.length!==1||matches[0].disabled))return false;
  const selected=rows.map(matches=>matches[0]),headings=new Set();
  for(const row of selected){
    let heading=row.previousElementSibling;while(heading&&!heading.dataset.hierarchyGroup)heading=heading.previousElementSibling;
    if(row.hidden&&heading?.getAttribute('aria-expanded')==='false')headings.add(heading);
  }
  for(const heading of headings)heading.click();
  if(selected.some(row=>row.hidden))return false;
  const focus=selected.find(row=>row.title===focusId);focus.scrollIntoView({block:'nearest'});focus.focus({preventScroll:true});return true;
}
export function revealHierarchyEntity(root,id){return revealHierarchyEntities(root,[id],id);}

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
    button.onkeydown=event=>{
      if(!['ArrowLeft','ArrowRight'].includes(event.key)||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||button.disabled||!current())return;
      event.preventDefault();
      if(event.key==='ArrowRight'&&hierarchyGroupExpanded(id,state,filter)){
        members.find(row=>!row.hidden&&!row.disabled)?.focus();
      }else set(event.key==='ArrowRight');
    };
    heading.replaceWith(button);update();
  }
}

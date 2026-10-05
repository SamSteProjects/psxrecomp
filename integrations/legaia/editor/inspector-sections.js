// Session-only display state. Component values and project commands are untouched.
export function inspectorSectionSnapshot(root,scope){
  const active=root.ownerDocument.activeElement;
  return {scope,key:root.contains(active)?active?.dataset?.inspectorSectionToggle:null};
}
export function mountInspectorSections(root,{state,project,scope,snapshot,current=()=>true}){
  if(state.project!==project){state.project=project;state.collapsed=new Set();}
  const document=root.ownerDocument,seen=new Set();
  const records=[...root.querySelectorAll(':scope > section.component')].map((section,index)=>{
    const heading=section.querySelector(':scope > h3');
    if(!heading)return null;
    const identity=section.dataset.componentContent??section.querySelector('[data-component-content]')?.dataset.componentContent;
    const key=identity?`component:${identity}`:`display:${heading.textContent}`;
    // Ambiguous display keys are not shared between sections.
    if(seen.has(key))return null;seen.add(key);
    const button=document.createElement('button');button.type='button';button.className='inspector-section-toggle';button.dataset.inspectorSectionToggle=key;
    while(heading.firstChild)button.append(heading.firstChild);heading.append(button);
    const body=document.createElement('div');body.className='inspector-section-body';body.id=`inspector-section-body-${index}`;
    while(heading.nextSibling)body.append(heading.nextSibling);section.append(body);
    button.setAttribute('aria-controls',body.id);
    function update(){body.hidden=state.collapsed.has(key);section.classList.toggle('inspector-section-collapsed',body.hidden);button.setAttribute('aria-expanded',String(!body.hidden));}
    function set(expanded){if(!current())return;expanded?state.collapsed.delete(key):state.collapsed.add(key);update();}
    button.onclick=()=>set(body.hidden);update();
    return {section,button,key,set};
  }).filter(Boolean);
  const visible=()=>records.filter(row=>!row.section.hidden);
  for(const row of records)row.button.onkeydown=event=>{
    if(!current()||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
    if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();row.set(event.key==='ArrowRight');return;}
    if(!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
    const rows=visible(),index=rows.indexOf(row);if(index<0)return;
    event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?rows.length-1:event.key==='ArrowUp'?Math.max(0,index-1):Math.min(rows.length-1,index+1);rows[next].button.focus();
  };
  const tools=document.createElement('div');tools.className='inspector-section-tools';
  for(const [label,expanded] of [['Collapse visible components',false],['Expand visible components',true]]){
    const button=document.createElement('button');button.type='button';button.textContent=label;button.onclick=()=>{if(current())for(const row of visible())row.set(expanded);};tools.append(button);
  }
  tools.title='Component headers: Left/Right collapse/expand; Up/Down, Home/End move focus. Layout is remembered for this project in this editor session.';
  root.querySelector('.inspector-component-filter')?.after(tools);
  if(snapshot?.scope===scope&&snapshot.key)visible().find(row=>row.key===snapshot.key)?.button.focus({preventScroll:true});
  return {records};
}

// Display filtering uses explicit SDK authored-component identities, never guesses from values.
export function matchesInspectorComponent({id,label,text,propertyCategories=[]},state,authored){
  if(!Array.isArray(authored)||authored.length>128||authored.some(v=>typeof v!=='string'))throw new Error('Invalid authored component identities.');
  if(state.authoredOnly===true&&!authored.includes(id))return false;
  if(state.propertyCategory&&!propertyCategories.includes(state.propertyCategory))return false;
  const query=String(state.query??'').slice(0,256).trim().toLocaleLowerCase();
  return !query||[id,label,text].some(value=>String(value??'').toLocaleLowerCase().includes(query));
}
export function mountInspectorComponentFilter(root,{authored=[],state={query:'',authoredOnly:false},current=()=>true}){
  const records=[...root.querySelectorAll(':scope > section.component')].map(section=>({section,id:section.dataset.componentContent??section.querySelector('[data-component-content]')?.dataset.componentContent??'',label:section.querySelector('h3')?.textContent??'',text:(section.textContent??'').slice(0,65536),propertyCategories:[...new Set([...section.querySelectorAll('[data-property-state]')].map(node=>(node.textContent??'').trim()).filter(Boolean))]}));
  const tools=document.createElement('div');tools.className='inspector-component-filter';const query=document.createElement('input');query.type='search';query.maxLength=256;query.placeholder='Filter components or values';query.setAttribute('aria-label','Filter Inspector components');query.value=state.query??'';
  const label=document.createElement('label'),authoredOnly=document.createElement('input');authoredOnly.type='checkbox';authoredOnly.checked=state.authoredOnly===true;authoredOnly.setAttribute('aria-label','Show authored components only');label.append(authoredOnly,document.createTextNode('Authored only'));
  const categoryLabel=document.createElement('label'),category=document.createElement('select');category.setAttribute('aria-label','Filter Inspector property category');categoryLabel.append(document.createTextNode('Property category'),category);
  const categories=[...new Set(records.flatMap(record=>record.propertyCategories))].sort((a,b)=>a.localeCompare(b));
  if(state.propertyCategory&&!categories.includes(state.propertyCategory))categories.push(state.propertyCategory);
  for(const value of ['',...categories]){const option=document.createElement('option');option.value=value;option.textContent=value||'All categories';category.append(option);}category.value=state.propertyCategory??'';
  const reset=document.createElement('button');reset.type='button';reset.textContent='Reset filter';const status=document.createElement('span');status.setAttribute('role','status');tools.append(query,categoryLabel,label,reset,status);root.querySelector('.entity-heading')?.after(tools);
  function update(){if(!current())return;state.query=query.value.slice(0,256);state.authoredOnly=authoredOnly.checked;state.propertyCategory=category.value;let visible=0;for(const record of records){record.section.hidden=!matchesInspectorComponent(record,state,authored);if(!record.section.hidden)visible++;}status.textContent=`${visible} / ${records.length} components`;}
  query.oninput=authoredOnly.onchange=category.onchange=update;reset.onclick=()=>{if(!current())return;query.value='';authoredOnly.checked=false;category.value='';update();query.focus();};update();return {update};
}

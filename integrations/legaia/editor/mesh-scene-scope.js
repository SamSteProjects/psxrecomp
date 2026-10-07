// Scene inspection chooses a view scope; native Apply still edits the shared asset.
const ALL='all-model-instances';
export function meshSceneScopeChoice(rows,value){
  if(!Array.isArray(rows)||rows.length>4096)throw Error('Invalid mesh scene instance inventory.');
  const ids=new Set();for(const row of rows){if(!row||typeof row.entity_id!=='string'||!row.entity_id||row.entity_id.length>512||ids.has(row.entity_id))throw Error('Ambiguous mesh scene instance identity.');ids.add(row.entity_id);}
  if(!rows.length)return null;
  if(value===ALL)return {entity_id:rows[0].entity_id,all_instances:true};
  return ids.has(value)?{entity_id:value,all_instances:false}:null;
}
export function meshSceneScope({getInstances=()=>[],enabled=false,initial=null,onChange=()=>{}}={}){
  const host=document.createElement('section'),label=document.createElement('label'),select=document.createElement('select'),note=document.createElement('p');
  label.textContent='Scene inspection scope';select.setAttribute('aria-label','Mesh scene inspection scope');label.append(select);host.append(label,note);host.hidden=!enabled;
  let selected=initial?.all_instances===false?initial.entity_id:ALL,rows=[],signature=null;
  const choice=()=>meshSceneScopeChoice(rows,select.value);
  function refresh(blocked=false){
    rows=enabled?structuredClone(getInstances()):[];meshSceneScopeChoice(rows,ALL);
    const next=JSON.stringify(rows);if(next!==signature){signature=next;select.replaceChildren();const all=document.createElement('option');all.value=ALL;all.textContent='All supported model instances';select.append(all);for(const row of rows){const option=document.createElement('option');option.value=row.entity_id;option.textContent=typeof row.name==='string'&&row.name?row.name:row.entity_id;select.append(option);}if(selected!==ALL&&!rows.some(row=>row.entity_id===selected)){const missing=document.createElement('option');missing.value=selected;missing.textContent='Selected instance unavailable';missing.disabled=true;select.append(missing);}select.value=selected;}
    select.disabled=blocked||!rows.length;note.textContent=rows.length?`${rows.length} supported scene instances. This choice only limits inspection; Apply changes the shared model asset.`:'Load the current authored scene to inspect supported model instances.';
    return choice();
  }
  select.onchange=()=>{selected=select.value;onChange();};refresh();
  return {host,select,refresh,choice};
}

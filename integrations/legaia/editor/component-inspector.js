const escape=value=>String(value??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const at=(value,path)=>path.reduce((item,key)=>item?.[key],value);
const propertyValue=(value,p)=>[p.path,...(p.fallback_paths??[])].map(path=>at(value,path)).find(item=>item!==null&&item!==undefined)??p.empty_label??'—';
export const navigableComponentReference=(value,type)=>['asset-reference','entity-reference'].includes(type)&&typeof value==='string'&&value.length<=1024&&/^[a-z][a-z0-9-]*:\/\/[^\s\x00-\x20\x7f<>"']+$/.test(value);
export function propertyStateBadge(schema,state){
  if(!schema.property_states)return '';
  const definition=Object.hasOwn(schema.property_states,state??'')?schema.property_states[state]:null;
  const valid=definition&&typeof definition.label==='string'&&definition.label.length<=80&&typeof definition.note==='string'&&definition.note.length<=600;
  const label=valid?definition.label:'Unclassified',note=valid?definition.note:'No registered property state. No edit or runtime capability is inferred.';
  return `<small class="property-state" data-property-state="${escape(valid?state:'unclassified')}" title="${escape(note)}" aria-label="${escape(label+': '+note)}">${escape(label)}</small>`;
}
const propertyRow=(schema,p,value,navigation=false,layer=null)=>{
  const target=propertyValue(value,p),label=[layer?.label,p.label].filter(Boolean).join(' ');
  const state=layer?.id==='authored'&&p.state?.startsWith('authored-')?p.state:layer?.state??p.state;
  const content=navigation&&navigableComponentReference(target,p.type)?`<button type="button" data-component-reference="${escape(target)}" data-reference-type="${escape(p.type)}" aria-label="Inspect ${escape(label)} reference: ${escape(target)}"><code>${escape(target)}</code></button>`:`<code>${escape(target)}</code>`;
  return `<div class="property"><span class="property-label">${escape(p.label)}${propertyStateBadge(schema,state)}</span>${content}</div>`;
};
const notes=definition=>(definition.notes??[]).map(note=>`<p class="field-note">${escape(note)}</p>`).join('');
export function componentDefinition(schema,id){
  if(schema?.schema_version!=='legaia.inspector-schema.v1'||schema.live_writes!==false)throw new Error('Unsupported inspector schema');
  const definition=schema.components?.[id];
  if(!definition||!Array.isArray(definition.properties)||definition.properties.length>32||new Set(definition.properties.map(p=>p.id)).size!==definition.properties.length)throw new Error('Invalid inspector component definition');
  return definition;
}
export function renderComponentProperties(schema,id,component,editable=false,referenceNavigation=false){
  return `<div data-component-content="${escape(id)}">${renderPropertyContent(schema,id,component,editable,referenceNavigation)}</div>`;
}
function renderPropertyContent(schema,id,component,editable=false,referenceNavigation=false){
  const definition=componentDefinition(schema,id);
  if(definition.layout==='read-only-properties')return definition.properties.map(p=>propertyRow(schema,p,component,referenceNavigation)).join('')+notes(definition);
  if(definition.layout==='layered-properties'){
    if(!Array.isArray(definition.layers)||definition.layers.length>8||new Set(definition.layers.map(row=>row.id)).size!==definition.layers.length)throw new Error('Invalid property layers');
    return definition.layers.map(layer=>`<div class="appearance-layer" data-property-layer="${escape(layer.id)}"><h4>${escape(layer.label)}</h4>${definition.properties.filter(p=>p.layers?.includes(layer.id)).map(p=>propertyRow(schema,p,component[layer.id],referenceNavigation,layer)).join('')}</div>`).join('')+notes(definition);
  }
  if(definition.layout!=='layered-number'||JSON.stringify(definition.layers)!==JSON.stringify(['imported','authored','effective']))throw new Error('Unsupported property layout');
  let html='<div class="transform-table"><span></span>'+definition.layers.map(layer=>`<span class="column-title">${escape(layer[0].toUpperCase()+layer.slice(1))}${propertyStateBadge(schema,definition.layer_states?.[layer])}</span>`).join('');
  for(const p of definition.properties){
    if(p.type!=='number'||!p.authoring||!Array.isArray(p.path)||p.path.length!==2)throw new Error('Unsupported numeric property');
    const values=definition.layers.map(layer=>at(component[layer],p.path)),bounds=p.authoring;
    const title=p.build.note+(p.retail_status==='unresolved'?' · Retail value unresolved':'');
    html+=`<span class="axis-${escape(p.id)}">${escape(p.label)}</span><output>${escape(values[0])}</output><input data-component-property="${escape(p.id)}" aria-label="Authored ${escape(p.label)}" type="number" min="${escape(bounds.minimum)}" max="${escape(bounds.maximum)}" step="${escape(bounds.step)}" title="${escape(title)}" placeholder="—" value="${typeof values[1]==='number'&&Number.isFinite(values[1])?values[1]:''}" ${editable?'':'disabled'}><output class="effective">${escape(values[2])}</output>`;
    const stateNotes=[...(p.retail_status==='unresolved'?[`<span>Retail ${escape(p.label)}: ${propertyStateBadge(schema,'unresolved')}</span>`]:[]),...(p.build.supported===false?[`<span>Build ${escape(p.label)}: ${propertyStateBadge(schema,'unsupported')}</span>`]:[])];
    if(schema.property_states&&stateNotes.length)html+=`<span class="transform-property-states">${stateNotes.join('')}</span>`;
  }
  return html+'</div>'+definition.notes.map(note=>`<p class="field-note">${escape(note)}</p>`).join('');
}
export function propertyCommand(schema,componentId,propertyId,entityId,text){
  const definition=componentDefinition(schema,componentId),p=definition.properties.find(p=>p.id===propertyId);
  // Registry adapter limits commands even if a schema response is malformed.
  if(componentId!=='Transform'||!['x','y','z'].includes(propertyId)||JSON.stringify(p?.path)!==JSON.stringify(['position',propertyId])||p?.authoring?.set_command!=='set_transform'||p.authoring.clear_command!=='clear_transform')throw new Error('Unsupported property command');
  if(text==='')return {type:'clear_transform',entity_id:entityId,axes:[propertyId]};
  if(typeof text!=='string'||!text.trim())throw new Error('Enter a finite number or clear the field');
  const value=Number(text);if(!Number.isFinite(value)||value<p.authoring.minimum||value>p.authoring.maximum)throw new Error('Coordinate is outside the SDK authoring bounds');
  return {type:'set_transform',entity_id:entityId,position:{[propertyId]:value}};
}

export function renderUnregisteredComponents(schema,components,handled){
  if(schema?.unknown_component_policy!=='read-only-details')throw new Error('Unsupported component fallback');
  return Object.entries(components).filter(([id])=>!handled.includes(id)).map(([id,value])=>`<section class="component" data-component-content="${escape(id)}"><h3>${escape(schema.components?.[id]?.label??id)} <small>Read only · no registered editor</small></h3><p class="field-note">Properties are displayed as supplied by the SDK. No authoring or runtime-write capability is inferred.</p><details><summary>SDK component details</summary><pre>${escape(JSON.stringify(value,null,2))}</pre></details></section>`).join('');
}

export function renderComponentDetails(schema,id,component){
  const definition=componentDefinition(schema,id);
  return (definition.details??[]).map(detail=>`<details><summary>${escape(detail.label)}</summary><pre>${escape(JSON.stringify(at(component,detail.path),null,2))}</pre></details>`).join('');
}

export function registeredActions(schema,id,component,capabilities,registry,editable=false){
  const definition=componentDefinition(schema,id),actions=definition.actions??[];
  if(actions.length>32||new Set(actions.map(a=>a.id)).size!==actions.length)throw new Error('Invalid inspector actions');
  return actions.filter(a=>Object.hasOwn(registry,a.id)&&capabilities?.[a.capability]===true&&(!a.when||at(component,a.when))).map(a=>({id:a.id,label:a.label,requiresEdit:a.requires_edit===true||registry[a.id].requiresEdit===true,disabled:(a.requires_edit===true||registry[a.id].requiresEdit===true)&&!editable}));
}
export function renderComponentActions(schema,id,component,capabilities,registry,editable=false){
  return registeredActions(schema,id,component,capabilities,registry,editable).map(a=>`<button id="${escape(a.id)}" class="model-preview-button" data-inspector-component="${escape(id)}" data-inspector-action="${escape(a.id)}" data-inspector-edit="${a.requiresEdit}" ${a.disabled?'disabled':''}>${escape(a.label)}</button>`).join('');
}
export function bindComponentActions(root,registry,{current,editable,busy,onError}){
  for(const button of root.querySelectorAll('[data-inspector-action]')){
    const action=registry[button.dataset.inspectorAction];
    if(!action||typeof action.run!=='function'){button.disabled=true;continue;}
    button.onclick=async()=>{
      if(busy()||!current()||(action.requiresEdit&&!editable())||(action.canRun&&!action.canRun()))return;
      try{await action.run({componentId:button.dataset.inspectorComponent??null,actionId:button.dataset.inspectorAction});}catch(error){onError(error);}
    };
  }
}

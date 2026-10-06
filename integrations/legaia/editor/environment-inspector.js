import {componentDefinition,renderComponentProperties,renderComponentDetails} from './component-inspector.js';
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Display SDK preview metadata only. Specialized authoring adapters own commands.
export function renderEnvironmentInspector(schema,environment,current){
  if(environment?.kind!=='environment'||typeof current!=='boolean')throw new Error('Environment inspector requires an SDK environment snapshot and freshness state.');
  return ['EnvironmentPlacement','EnvironmentRetailTransform','EnvironmentPreviewTransform','EnvironmentMetadata'].map(id=>{
    const definition=componentDefinition(schema,id);
    if(definition.layout!=='read-only-properties'||definition.properties.some(p=>p.authoring))throw new Error('Environment snapshot properties must be read only.');
    const stale=id==='EnvironmentPreviewTransform'&&!current?'<p class="field-note" role="status">Previous preview snapshot — refresh pending. Current source is not yet qualified.</p>':'';
    const frame=id==='EnvironmentPlacement'?'<button id="frame-environment">Frame object</button>':'';
    return `<section class="component" data-environment-component="${id}"><h3>${escape(definition.label)}${definition.units?` <small>${escape(definition.units)}</small>`:''}</h3>${stale}${renderComponentProperties(schema,id,environment)}${frame}${renderComponentDetails(schema,id,environment)}</section>`;
  }).join('');
}

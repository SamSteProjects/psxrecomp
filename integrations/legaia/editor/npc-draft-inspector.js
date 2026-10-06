import {componentDefinition,renderComponentProperties,renderComponentDetails} from './component-inspector.js';
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Read SDK snapshots only. The NPC authoring adapter owns commands and validation.
export function renderNpcDraftInspector(schema,snapshot,previewState){
  if(typeof snapshot?.entity_id!=='string'||!snapshot.draft||!['current','pending','source-during-proposal','unavailable'].includes(previewState))throw new Error('NPC draft inspector requires source and preview state.');
  const status={current:'Current authored scene preview snapshot.',pending:'Previous preview snapshot — refresh pending. Current source is not yet qualified.','source-during-proposal':'Source preview snapshot while a detached scene proposal is active. Proposed viewport coordinates are not substituted; authored placement remains separate.',unavailable:'No NPC draft preview snapshot in this view. Missing values remain unknown.'};
  return ['NpcDraftIdentity','NpcDraftTransform','NpcDraftPreview'].map(id=>{
    const definition=componentDefinition(schema,id);
    if(definition.layout!=='read-only-properties'||definition.properties.some(p=>p.authoring))throw new Error('NPC draft snapshot properties must be read only.');
    const note=id==='NpcDraftPreview'?`<p class="field-note" data-npc-preview-state="${previewState}" role="status">${escape(status[previewState])}</p>`:'';
    return `<section class="component" data-npc-draft-component="${id}"><h3>${escape(definition.label)}${definition.units?` <small>${escape(definition.units)}</small>`:''}</h3>${note}${renderComponentProperties(schema,id,snapshot)}${renderComponentDetails(schema,id,snapshot)}</section>`;
  }).join('');
}

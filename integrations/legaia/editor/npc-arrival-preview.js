import {decodeNpcTransitionsSource,npcArrivalReference} from './npc-transitions.js';
import {drawTransitionArrival} from './transition-arrival-preview.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const equal=(a,b)=>JSON.stringify(a,sorted)===JSON.stringify(b,sorted);
function sorted(_,v){return v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v;}
export function decodeNpcArrivalPreview(value,request,state){
 const keys=['schema_version','read_only','entity_id','transition_id','source_scene_id','project_source_key','project_inputs_key','destination_scene_id','destination_source_key','source','reference_y','height_known','runtime_verified','transition_activation'];
 if(state?.project?.mode!=='edit'||!request||Object.keys(request).length!==3||!['entity_id','transition_id','project_source_key'].every(k=>Object.hasOwn(request,k))||!value||Object.keys(value).length!==keys.length||keys.some(k=>!Object.hasOwn(value,k))||value.schema_version!=='legaia.npc-arrival-preview.v1'||value.read_only!==true||value.entity_id!==request.entity_id||value.transition_id!==request.transition_id||value.project_source_key!==request.project_source_key||value.project_source_key!==state.project_copy_source_key||value.project_inputs_key!==state.npc_arrival_preview_state_key||![value.project_source_key,value.project_inputs_key,value.destination_source_key].every(hash)||value.source_scene_id!==state.scene?.id||value.reference_y!==0||value.height_known!==false||value.runtime_verified!==false||value.transition_activation!=='not_asserted'||!(state.scenes??[]).some(s=>s.id===value.destination_scene_id))throw Error('NPC arrival preview changed or has invalid destination evidence.');
 const source=decodeNpcTransitionsSource(value.source,value.entity_id,state),row=source.options.transitions.find(r=>r.semantic_id===value.transition_id);
 if(!row||value.destination_scene_id!=='scene://'+row.destination)throw Error('NPC arrival destination differs from its qualified donor instruction.');
 return structuredClone({...value,source});
}
export function npcArrivalPreviewCurrent(report,state){
 return !!report&&state?.project?.mode==='edit'&&state.scene?.id===report.destination_scene_id&&state.scene_preview_source_key===report.destination_source_key&&state.npc_arrival_preview_state_key===report.project_inputs_key&&equal(state.actor_drafts?.[report.entity_id],report.source.draft);
}
export function npcArrivalPreviewMarkers(report,height=0,proposal=null){
 if(!Number.isFinite(height)||Math.abs(height)>1e7)throw Error('NPC arrival reference Y must be finite and within 10000000 units.');
 const row=report.source.options.transitions.find(r=>r.semantic_id===report.transition_id);if(!row)throw Error('NPC arrival instruction is unavailable.');
 const markers=[['Retail',row.values,'#84c9ff'],['NPC Current',row.effective_values,'#ffd878']].map(([layer,bytes,color])=>{const v=npcArrivalReference(bytes);return {layer,color,x:v.x,y:height,z:v.z,facing_angle_12bit:v.facing_sector*512};});
 if(proposal)markers.push({layer:proposal.draft?'Draft':'Proposed',color:proposal.draft?'#e9abff':'#91efa6',...proposal.proposed_arrival,y:height});return markers;
}
export function drawNpcArrivalPreview(ctx,report,height,project,displayPosition,bounds,proposal=null){
 const markers=npcArrivalPreviewMarkers(report,height);
 // Share the established marker renderer without representing a donor actor override as NPC Current.
 const layers={imported:markers[0],effective:markers[1]};
 drawTransitionArrival(ctx,{resource:{arrival_layers:layers}},height,project,displayPosition,bounds,proposal);
}

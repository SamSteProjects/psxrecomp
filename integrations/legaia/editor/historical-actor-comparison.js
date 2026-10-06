import {historicalRuntimePositions,historicalRuntimeComparisonPositions} from './runtime-review.js';

const axes=['x','y','z'];
function position(value,partial=false){
 if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Actor coordinate layer is unavailable.');
 const result={};for(const axis of axes){
  if(partial&&!Object.hasOwn(value,axis))continue;
  const number=value[axis]??null;
  if(number!==null&&(!Number.isFinite(number)||Math.abs(number)>1e8))throw new Error('Actor coordinates exceed display bounds.');
  result[axis]=number;
 }return result;
}
const delta=(sample,reference)=>Object.fromEntries(axes.map(axis=>[axis,sample[axis]===null||reference[axis]===null?null:sample[axis]-reference[axis]]));

// Explicit numeric comparison only. Files cannot select, bind or move an actor.
export function historicalActorComparison(context){
 const {scene_id,mode,representation,source_key,actor,preview,node_id,overlay}=context??{};
 if(mode!=='edit'||!['retail','authored'].includes(representation)||typeof source_key!=='string'||!source_key||source_key.length>256)throw new Error('Choose a current scene in Edit mode.');
 if(typeof scene_id!=='string'||!scene_id.startsWith('scene://')||typeof actor?.id!=='string'||!actor.id.startsWith(scene_id+'/actors/man-p1/')||!/^\d{4}$/.test(actor.id.slice((scene_id+'/actors/man-p1/').length)))throw new Error('Select an imported actor in this scene.');
 if(typeof node_id!=='string'||!node_id||!overlay?.review)throw new Error('Choose a displayed historical node sample.');
 const decoded=overlay.comparison?historicalRuntimeComparisonPositions(overlay.comparison.before,overlay.comparison.after,{scene_id,mode},overlay.layer):historicalRuntimePositions(overlay.review,{scene_id,mode});
 const nodes=decoded.nodes.filter(node=>node.runtime_node_id===node_id);if(!nodes.length)throw new Error('The selected key has no complete coordinates in this historical layer.');
 const transform=actor.components?.Transform;
 const imported=position(transform?.imported?.position),effective=position(transform?.effective?.position),authored=position(transform?.authored?.position??{},true);
 if(preview?.entity_id!==actor.id)throw new Error('Current viewport actor is unavailable.');
 const viewport_native=position(preview.position),viewport_surface=position(preview.preview_position);
 const expected=representation==='retail'?imported:effective;
 if(axes.some(axis=>viewport_native[axis]!==expected[axis]))throw new Error('Viewport coordinate layer differs from the selected actor. Refresh the scene.');
 if(!['explicit','source_surface','unresolved_no_source_surface'].includes(preview.preview_height_status))throw new Error('Viewport height evidence is unavailable.');
 const samples=nodes.map(node=>({layer:node.sample_layer??'file',runtime_node_id:node.runtime_node_id,observed_position:position(node.observed_position),position_capture_frames:node.position_capture_frames,
  candidate_entity_ids:node.candidate_entity_ids,listed_actor_candidate:node.candidate_entity_ids.includes(actor.id),
  delta_from_imported:delta(node.observed_position,imported),delta_from_effective:delta(node.observed_position,effective),delta_from_viewport_surface:delta(node.observed_position,viewport_surface),identity_confirmed:false}));
 return structuredClone({schema_version:'legaia.historical-actor-coordinate-comparison.v1',historical:true,read_only:true,identity_confirmed:false,scene_id,project_source_key:source_key,representation,
  epoch_id:decoded.review.epoch_id,profile_id:decoded.review.profile_id,actor_id:actor.id,node_id,
  actor:{imported_position:imported,effective_position:effective,authored_position:authored,viewport_native_position:viewport_native,viewport_surface_position:viewport_surface,preview_height_status:preview.preview_height_status},samples,
  limitations:['This is an explicitly selected numeric comparison, not an actor binding or nearest-position match.',
   'Saved files do not authenticate a process, executable, session or coordinate convention. Matching numbers and candidate IDs do not confirm identity.',
   'Native imported/current Y remains unknown when absent. Viewport surface Y is derived preview evidence, not a native placement or runtime measurement.',
   'Deltas are captured minus reference in guest-coordinate numbers; no alignment, axis conversion, movement or runtime write is inferred. Capture frames are file metadata.']});
}

const text=value=>value===null?'unknown':String(value);
export function createHistoricalActorComparisonDialog({getContext,notify,download}){
 const dialog=document.createElement('dialog');dialog.className='project-dialog';dialog.id='historical-actor-comparison';dialog.style.width='min(900px, calc(100vw - 32px))';dialog.style.maxWidth='calc(100vw - 32px)';document.body.append(dialog);
 let binding=null,boundOverlay=null,exportButton=null,staleNote=null;
 const key=context=>JSON.stringify([context?.key,context?.source_key,context?.scene_id,context?.mode,context?.representation,context?.actor?.id,context?.node_id,context?.overlay?.layer]);
 const element=(tag,value)=>{const node=document.createElement(tag);node.textContent=value;return node;};
 function table(headers,rows){const wrap=document.createElement('div');wrap.style.overflowX='auto';const grid=document.createElement('table');grid.style.width='100%';grid.style.minWidth='600px';grid.style.borderCollapse='collapse';const cell=(tag,value)=>{const node=element(tag,value);node.style.padding='6px 10px';node.style.textAlign='left';return node;};const head=document.createElement('thead'),tr=document.createElement('tr');for(const value of headers)tr.append(cell('th',value));head.append(tr);grid.append(head);const body=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');for(const value of row)tr.append(cell('td',value));body.append(tr);}grid.append(body);wrap.append(grid);return wrap;}
 function refresh(){if(!dialog.open||!binding)return;const context=getContext();if(key(context)!==binding||!context?.overlay||context.overlay!==boundOverlay){staleNote.textContent='Editor context changed. Close this snapshot and compare again for current values.';exportButton.disabled=true;}}
 function open(){try{
  const context=getContext(),report=historicalActorComparison(context);binding=key(context);boundOverlay=context.overlay;dialog.replaceChildren();
  const heading=document.createElement('div');heading.className='dialog-heading';heading.append(element('h2','Historical sample / actor coordinates'));const close=element('button','Close');close.setAttribute('aria-label','Close coordinate comparison');close.type='button';close.onclick=()=>dialog.close();heading.append(close);dialog.append(heading);
  dialog.append(element('p',report.actor_id+' · '+report.node_id+' · '+report.representation+' viewport · identity unconfirmed'));
  dialog.append(element('p','Guest-coordinate numbers. Unknown native heights stay unknown; surface height is a separate preview layer.'));
  dialog.append(table(['Axis','Retail native','Current native','Authored override','Viewport native','Viewport surface'],axes.map(axis=>[axis.toUpperCase(),text(report.actor.imported_position[axis]),text(report.actor.effective_position[axis]),Object.hasOwn(report.actor.authored_position,axis)?text(report.actor.authored_position[axis]):'inherit',text(report.actor.viewport_native_position[axis]),text(report.actor.viewport_surface_position[axis])])));
  dialog.append(element('p','Viewport height evidence: '+report.actor.preview_height_status));
  for(const sample of report.samples){dialog.append(element('h3',sample.layer+' sample'));dialog.append(element('p','Position capture frames: '+(sample.position_capture_frames?sample.position_capture_frames.before+' → '+sample.position_capture_frames.after:'unknown')+' · file lists selected actor as candidate: '+(sample.listed_actor_candidate?'yes (unconfirmed)':'no')));dialog.append(table(['Axis','Captured','Δ retail','Δ current','Δ viewport surface'],axes.map(axis=>[axis.toUpperCase(),text(sample.observed_position[axis]),text(sample.delta_from_imported[axis]),text(sample.delta_from_effective[axis]),text(sample.delta_from_viewport_surface[axis])])));}
  const evidence=document.createElement('details');evidence.append(element('summary','Evidence and coordinate conventions'));for(const note of report.limitations)evidence.append(element('p',note));dialog.append(evidence);staleNote=element('p','');staleNote.setAttribute('role','status');dialog.append(staleNote);exportButton=element('button','Download coordinate comparison');exportButton.type='button';exportButton.onclick=()=>{refresh();if(!exportButton.disabled)download(report,'historical-actor-coordinate-comparison.json');};dialog.append(exportButton);
  if(!dialog.open)dialog.showModal();refresh();
 }catch(error){notify(error.message,true);}}
 return {open,refresh};
}

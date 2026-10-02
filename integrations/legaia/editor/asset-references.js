const kinds=new Set(['scene','actor','model','texture','animation','script','dialogue','collision','trigger','region','worldmap']);
const relations=new Set(['scene_actor','scene_model_catalog','draft_donor','initial_model','effective_initial_model','actor_script_record','encoded_scene_change','script_dialogue_segment','initial_animation_binding','recorded_model_clip_binding','field_map_table_source','landmark_destination_source','static_material_texture_source']);
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const identity=value=>typeof value==='string'&&value.length>0&&value.length<=1024;
export function decodeAssetReferences(value,assetId,sourceKey){
  if(value?.schema_version!=='legaia.asset-references.v1'||value.read_only!==true||value.asset_id!==assetId||value.source_key!==sourceKey||!hash(sourceKey))throw new Error('Asset references changed or have an unsupported contract. Reopen the asset.');
  if(!Array.isArray(value.nodes)||value.nodes.length>4097||!Array.isArray(value.incoming)||!Array.isArray(value.outgoing)||value.incoming.length+value.outgoing.length>4096)throw new Error('Invalid asset reference bounds.');
  const nodes=new Map();for(const node of value.nodes){if(!identity(node.id)||nodes.has(node.id)||!kinds.has(node.kind)||!identity(node.scene_id)||!identity(node.label)||typeof node.available!=='boolean')throw new Error('Invalid asset reference node.');nodes.set(node.id,node);}
  if(!nodes.has(assetId))throw new Error('Missing asset reference root.');
  const edges=new Set();for(const [direction,rows] of [['incoming',value.incoming],['outgoing',value.outgoing]])for(const edge of rows){
    if(!hash(edge.id)||edges.has(edge.id)||!nodes.has(edge.source_id)||!nodes.has(edge.target_id)||!relations.has(edge.kind)||!['imported','effective','authored','decoded'].includes(edge.layer)||edge.runtime_binding!=='not_asserted'||!hash(edge.source_import_sha256)||!identity(edge.scene_id)||direction==='incoming'&&edge.target_id!==assetId||direction==='outgoing'&&edge.source_id!==assetId||edge.layer==='decoded'&&!hash(edge.source_catalog_key)||edge.pc!==undefined&&(!Number.isSafeInteger(edge.pc)||edge.pc<0))throw new Error('Invalid asset reference edge.');
    edges.add(edge.id);
    if(edge.kind==='static_material_texture_source'){
      const e=edge.material_evidence;if(edge.layer!=='decoded'||nodes.get(edge.source_id).kind!=='model'||nodes.get(edge.target_id).kind!=='texture'||!e||!Number.isSafeInteger(e.material_index)||e.material_index<0||e.material_index>=32||!Number.isSafeInteger(e.tpage)||e.tpage<0||e.tpage>511||!Number.isSafeInteger(e.clut)||e.clut<0||e.clut>32767||!hash(e.model_source_sha256)||e.evidence!=='static_vram_addresses_not_runtime_residency'||!Array.isArray(e.uv_bounds)||e.uv_bounds.length!==4||e.uv_bounds.some(v=>!Number.isSafeInteger(v)||v<0||v>255)||e.uv_bounds[0]>e.uv_bounds[2]||e.uv_bounds[1]>e.uv_bounds[3])throw new Error('Invalid material address evidence.');
    }
  }
  const coverage=value.coverage;if(!coverage||!Array.isArray(coverage.verified_scene_ids)||coverage.verified_scene_ids.length<1||coverage.verified_scene_ids.length>64||coverage.verified_scene_ids.some(id=>!identity(id))||new Set(coverage.verified_scene_ids).size!==coverage.verified_scene_ids.length||!coverage.verified_scene_ids.includes(coverage.resource_scene_id)||!Number.isSafeInteger(coverage.unresolved_reference_count)||coverage.unresolved_reference_count<0||!Array.isArray(value.limitations)||value.limitations.length>256||value.limitations.some(item=>typeof item!=='string'||item.length>8192))throw new Error('Invalid asset reference coverage.');
  for(const edge of [...value.incoming,...value.outgoing])if(!coverage.verified_scene_ids.includes(edge.scene_id))throw new Error('Unverified reference source scene.');
  for(const node of value.nodes)if(node.available&&!coverage.verified_scene_ids.includes(node.scene_id))throw new Error('Unavailable navigation source scene.');
  const diagnostic=value.material_diagnostics;if(diagnostic!=null){if(nodes.get(assetId).kind!=='model'||diagnostic.model_id!==assetId||diagnostic.source_sha256!==undefined&&!hash(diagnostic.source_sha256)||diagnostic.unavailable_reason!==undefined&&(typeof diagnostic.unavailable_reason!=='string'||diagnostic.unavailable_reason.length>8192)||!Array.isArray(diagnostic.materials)||diagnostic.materials.length>256||diagnostic.materials.some(row=>!Number.isSafeInteger(row.material_index)||row.material_index<0||row.material_index>255||!['address_match','missing','ambiguous','unsupported'].includes(row.status)||!Array.isArray(row.source_ids)||row.source_ids.length>1024||row.source_ids.some(id=>!identity(id))))throw new Error('Invalid material diagnostics.');}
  return structuredClone(value);
}
export function openAssetReferences({record,getState,busy,onNavigate,onError=()=>{}}){
  if(busy()||!getState().capabilities?.asset_references)return;
  const key=getState().asset_reference_source_key,dialog=document.createElement('dialog'),controller=new AbortController();dialog.id='asset-references-dialog';dialog.className='project-dialog';
  const current=()=>dialog.open&&key===getState().asset_reference_source_key&&getState().capabilities?.asset_references===true;
  const title=document.createElement('h2');title.textContent=`Asset references · ${record.label}`;
  const content=document.createElement('div'),status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying recorded references…';
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();});dialog.append(title,status,content,close);document.body.append(dialog);dialog.showModal();
  const navigate=async node=>{if(busy())return;if(!current()){status.textContent='Project sources changed. Reopen asset references.';return;}try{dialog.close();await onNavigate(node);}catch(error){onError(error);}};
  (async()=>{try{
    const response=await fetch('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:record.id}),signal:controller.signal}),value=await response.json();
    if(controller.signal.aborted||!dialog.open)return;if(!current())throw new Error('Project sources changed. Reopen asset references.');if(!response.ok||value.error)throw new Error(value.error||'Asset reference verification failed.');
    const result=decodeAssetReferences(value,record.id,key),nodes=new Map(result.nodes.map(node=>[node.id,node]));status.textContent=`Recorded references only · ${result.coverage.unresolved_reference_count} unresolved references across the graph · derived resources: ${result.coverage.resource_scene_id}`;
    for(const [heading,rows,target] of [['Dependencies',result.outgoing,'target_id'],['Referenced by',result.incoming,'source_id']]){
      const section=document.createElement('section'),label=document.createElement('h3');label.textContent=heading;section.append(label);
      if(!rows.length){const empty=document.createElement('p');empty.textContent='No recorded relationships in this coverage.';section.append(empty);}
      for(const edge of rows){const node=nodes.get(edge[target]),row=document.createElement('div'),button=document.createElement('button'),description=document.createElement('p');button.textContent=node.label;button.title=node.id;button.dataset.referenceTarget=node.id;button.disabled=!node.available;button.onclick=()=>navigate(node);description.textContent=`${edge.kind.replaceAll('_',' ')} · ${edge.layer}${edge.pc===undefined?'':` · instruction PC ${edge.pc}`}${edge.material_evidence?` · material ${edge.material_evidence.material_index}`:''}${node.available?'':node.kind==='scene'?' · source scene not imported':' · outside navigable resource catalog'}`;
        const evidence=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Recorded provenance';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(edge,null,2);evidence.append(summary,pre);row.append(button,description,evidence);section.append(row);
      }content.append(section);
    }
    if(result.material_diagnostics){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Imported material address results';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(result.material_diagnostics,null,2);details.append(summary,pre);content.append(details);}
    const limitations=document.createElement('ul');for(const text of result.limitations){const li=document.createElement('li');li.textContent=text;limitations.append(li);}content.append(limitations);
  }catch(error){if(error.name!=='AbortError'&&dialog.open)status.textContent=error.message;}})();
  return dialog;
}

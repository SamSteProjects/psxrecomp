const kinds=new Set(['scene','actor','model','texture','animation','script','dialogue','flag','transition','collision','trigger','region','worldmap']);
const relations=new Set(['scene_actor','scene_model_catalog','draft_donor','initial_model','effective_initial_model','actor_script_record','encoded_scene_change','script_dialogue_segment','initial_animation_binding','recorded_model_clip_binding','field_map_table_source','landmark_destination_source','static_material_texture_source']);
relations.add('effective_initial_animation_binding');relations.add('draft_initial_animation_binding');relations.add('appearance_donor');
relations.add('reference_pinned_model_clip');
relations.add('script_flag_reference');
relations.add('script_transition_reference');relations.add('transition_destination_source');
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const identity=value=>typeof value==='string'&&value.length>0&&value.length<=1024;
const canonicalScenes=(ids,minimum=1)=>Array.isArray(ids)&&ids.length>=minimum&&ids.length<=64&&ids.every(id=>identity(id)&&id.startsWith('scene://')&&id.length>8)&&new Set(ids).size===ids.length&&JSON.stringify(ids)===JSON.stringify([...ids].sort());
const exactKeys=(value,keys)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const boundedInteger=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const referenceModels=Array.from({length:5},(_,slot)=>`asset://legaia/models/global-special/${(0xf0+slot).toString(16).padStart(4,'0')}`);
const transitionRelations=new Set(['script_transition_reference','transition_destination_source']);
const transitionProofKeys=['transition_id','source_record_sha256','destination_scene_id','extended_target','name_sha256','status','reachability'];
function validTransitionReference(edge,nodes){
  const proof=edge.transition_reference_evidence,transitionId=edge.kind==='script_transition_reference'?edge.target_id:edge.source_id;
  const match=/^transition:\/\/([A-Za-z0-9_-]+)\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})\/([0-9a-f]{4})$/.exec(transitionId);
  if(!match||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','pc','transition_reference_evidence'])||!exactKeys(proof,transitionProofKeys)||edge.layer!=='decoded'||!boundedInteger(edge.pc,0,65535)||edge.pc!==Number.parseInt(match[4],16)||edge.scene_id!=='scene://'+match[1]||nodes.get(transitionId).kind!=='transition'||nodes.get(transitionId).scene_id!==edge.scene_id||!hash(proof.source_record_sha256)||!hash(proof.name_sha256)||proof.extended_target!==null&&!boundedInteger(proof.extended_target,0,255)||proof.reachability!=='not_evaluated')return false;
  const scriptId=`script://${match[1]}/${match[2]}/${match[3]}`;
  if(proof.transition_id!==`${scriptId}/transition/${match[4]}`||!['encoded_named_reference','unsupported_name_encoding'].includes(proof.status)||(proof.destination_scene_id===null?proof.status!=='unsupported_name_encoding':typeof proof.destination_scene_id!=='string'||!/^scene:\/\/[a-z0-9]{1,12}$/.test(proof.destination_scene_id)||proof.status!=='encoded_named_reference'))return false;
  if(edge.kind==='script_transition_reference')return edge.source_id===scriptId&&nodes.get(edge.source_id).kind==='script'&&nodes.get(edge.source_id).scene_id===edge.scene_id;
  return proof.destination_scene_id!==null&&edge.target_id===proof.destination_scene_id&&nodes.get(edge.target_id).kind==='scene'&&nodes.get(edge.target_id).scene_id===edge.target_id;
}
function validReferenceClip(edge,nodes){
  const evidence=edge.reference_clip_evidence,source=evidence?.source_record;
  if(!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','reference_clip_evidence'])||!exactKeys(evidence,['reference_commit','model_id','clip_id','record_index','frame_count','channel_count','source_record'])||!exactKeys(source,['disc','iso_file','prot_entry_index','container_section','compressed_stream_offset','compressed_bytes_consumed','record_index','byte_offset','byte_length','byte_coordinate_space','containing_size'])||!exactKeys(source.disc,['sha256','serial']))return false;
  const slot=referenceModels.indexOf(evidence.model_id),party=slot>=0&&slot<3;
  if(slot<0||edge.layer!=='decoded'||nodes.get(edge.source_id).kind!=='animation'||nodes.get(edge.target_id).kind!=='model'||evidence.model_id!==edge.target_id||evidence.reference_commit!=='d6e64c68ede25813d35db20980da82a1a025549b'||!(party?['idle','walk']:['loop']).includes(evidence.clip_id))return false;
  const recordIndex=party?slot*7+(evidence.clip_id==='idle'?1:0):slot+18,channels=party?10:slot===3?3:2;
  return edge.source_id===`animation://legaia/field-locomotion/${String(recordIndex).padStart(4,'0')}`&&evidence.record_index===recordIndex&&boundedInteger(evidence.frame_count,1,512)&&evidence.channel_count===channels&&hash(source.disc.sha256)&&source.disc.serial==='SCUS-94254'&&source.iso_file==='PROT.DAT'&&source.prot_entry_index===874&&source.container_section===1&&boundedInteger(source.compressed_stream_offset,0,0xffffffff)&&boundedInteger(source.compressed_bytes_consumed,1,0xffffffff-source.compressed_stream_offset)&&source.record_index===recordIndex&&boundedInteger(source.containing_size,96,4*1024*1024)&&boundedInteger(source.byte_offset,96,source.containing_size)&&source.byte_length===16+evidence.frame_count*channels*8&&source.byte_length<=source.containing_size-source.byte_offset&&source.byte_coordinate_space==='decoded_lzs_section';
}
export function decodeAssetReferences(value,assetId,sourceKey,scope='active'){
  if(!['active','project'].includes(scope))throw new Error('Invalid asset reference scope.');
  if(value?.schema_version!==(scope==='project'?'legaia.project-asset-references.v1':'legaia.asset-references.v1')||value.read_only!==true||value.asset_id!==assetId||value.source_key!==sourceKey||!hash(sourceKey))throw new Error('Asset references changed or have an unsupported contract. Reopen the asset.');
  if(!Array.isArray(value.nodes)||value.nodes.length>4097||!Array.isArray(value.incoming)||!Array.isArray(value.outgoing)||value.incoming.length+value.outgoing.length>4096)throw new Error('Invalid asset reference bounds.');
  const nodes=new Map();for(const node of value.nodes){if(!identity(node.id)||nodes.has(node.id)||!kinds.has(node.kind)||!identity(node.scene_id)||!identity(node.label)||typeof node.available!=='boolean')throw new Error('Invalid asset reference node.');nodes.set(node.id,node);}
  if(!nodes.has(assetId))throw new Error('Missing asset reference root.');
  const edges=new Set(),transitionProofs=new Map(),transitionSites=new Set();for(const [direction,rows] of [['incoming',value.incoming],['outgoing',value.outgoing]])for(const edge of rows){
    if(!hash(edge.id)||edges.has(edge.id)||!nodes.has(edge.source_id)||!nodes.has(edge.target_id)||!relations.has(edge.kind)||!['imported','effective','authored','decoded'].includes(edge.layer)||edge.runtime_binding!=='not_asserted'||!hash(edge.source_import_sha256)||!identity(edge.scene_id)||direction==='incoming'&&edge.target_id!==assetId||direction==='outgoing'&&edge.source_id!==assetId||edge.layer==='decoded'&&!hash(edge.source_catalog_key)||edge.pc!==undefined&&(!Number.isSafeInteger(edge.pc)||edge.pc<0))throw new Error('Invalid asset reference edge.');
    edges.add(edge.id);
    if(Object.hasOwn(edge,'transition_reference_evidence')&&!transitionRelations.has(edge.kind))throw new Error('Transition evidence cannot assert another relationship.');
    if(transitionRelations.has(edge.kind)){
      if(!validTransitionReference(edge,nodes))throw new Error('Invalid source-scoped transition reference evidence.');
      const transitionId=edge.kind==='script_transition_reference'?edge.target_id:edge.source_id,key=`${transitionId}/${edge.kind}`;
      if(transitionSites.has(key))throw new Error('Duplicate transition instruction reference.');transitionSites.add(key);
      const previous=transitionProofs.get(transitionId);
      if(previous&&(transitionProofKeys.some(key=>previous.transition_reference_evidence[key]!==edge.transition_reference_evidence[key])||previous.source_import_sha256!==edge.source_import_sha256||previous.source_catalog_key!==edge.source_catalog_key||previous.scene_id!==edge.scene_id))throw new Error('Transition edges disagree about their verified source.');
      transitionProofs.set(transitionId,edge);
    }
    if(Object.hasOwn(edge,'flag_reference_evidence')&&edge.kind!=='script_flag_reference')throw new Error('Flag evidence cannot assert another relationship.');
    if(edge.kind==='script_flag_reference'){
      const e=edge.flag_reference_evidence;
      if(edge.layer!=='decoded'||nodes.get(edge.source_id).kind!=='script'||nodes.get(edge.target_id).kind!=='flag'||edge.pc===undefined||!exactKeys(e,['bank','index','scope','extended_target','grouping_layer','operation','mnemonic'])||!['local','global','context','system','extra'].includes(e.bank)||!Number.isSafeInteger(e.index)||e.index<0||e.index>(e.bank==='system'?65535:31)||!identity(e.scope)||e.grouping_layer!=='retail'||!['set','clear','test'].includes(e.operation)||!identity(e.mnemonic)||e.extended_target!==null&&(!Number.isSafeInteger(e.extended_target)||e.extended_target<0||e.extended_target>255)||edge.target_id!==`${edge.source_id.replace('script://','flag-reference://')}/${e.extended_target===null?'current':`extended-${e.extended_target}`}/${e.bank}/${e.index}`)throw new Error('Invalid source-scoped flag reference evidence.');
    }
    if(edge.kind==='static_material_texture_source'){
      const e=edge.material_evidence;if(edge.layer!=='decoded'||nodes.get(edge.source_id).kind!=='model'||nodes.get(edge.target_id).kind!=='texture'||!e||!Number.isSafeInteger(e.material_index)||e.material_index<0||e.material_index>=32||!Number.isSafeInteger(e.tpage)||e.tpage<0||e.tpage>511||!Number.isSafeInteger(e.clut)||e.clut<0||e.clut>32767||!hash(e.model_source_sha256)||e.evidence!=='static_vram_addresses_not_runtime_residency'||!Array.isArray(e.uv_bounds)||e.uv_bounds.length!==4||e.uv_bounds.some(v=>!Number.isSafeInteger(v)||v<0||v>255)||e.uv_bounds[0]>e.uv_bounds[2]||e.uv_bounds[1]>e.uv_bounds[3])throw new Error('Invalid material address evidence.');
    }
    if(['effective_initial_animation_binding','draft_initial_animation_binding'].includes(edge.kind)){
      const e=edge.effective_animation_evidence;if(edge.layer!==(edge.kind==='draft_initial_animation_binding'?'authored':'effective')||nodes.get(edge.source_id).kind!=='actor'||nodes.get(edge.target_id).kind!=='animation'||!hash(edge.source_catalog_key)||!e||!identity(e.donor_entity_id)||!identity(e.model_id)||!Number.isSafeInteger(e.initial_animation_id)||e.initial_animation_id<1||e.initial_animation_id>255)throw new Error('Invalid effective animation evidence.');
    }
    if(Object.hasOwn(edge,'reference_clip_evidence')&&edge.kind!=='reference_pinned_model_clip')throw new Error('Pinned clip evidence cannot assert an actor binding.');
    if(edge.kind==='reference_pinned_model_clip'&&!validReferenceClip(edge,nodes))throw new Error('Invalid pinned model/clip reference evidence.');
  }
  const coverage=value.coverage;if(!coverage||!Array.isArray(coverage.verified_scene_ids)||coverage.verified_scene_ids.length<1||coverage.verified_scene_ids.length>64||coverage.verified_scene_ids.some(id=>!identity(id))||new Set(coverage.verified_scene_ids).size!==coverage.verified_scene_ids.length||!coverage.verified_scene_ids.includes(coverage.resource_scene_id)||!Number.isSafeInteger(coverage.unresolved_reference_count)||coverage.unresolved_reference_count<0||!Array.isArray(value.limitations)||value.limitations.length>256||value.limitations.some(item=>typeof item!=='string'||item.length>8192))throw new Error('Invalid asset reference coverage.');
  for(const edge of [...value.incoming,...value.outgoing])if(!coverage.verified_scene_ids.includes(edge.scene_id))throw new Error('Unverified reference source scene.');
  for(const node of value.nodes)if(node.available&&!coverage.verified_scene_ids.includes(node.scene_id))throw new Error('Unavailable navigation source scene.');
  if(scope==='project'){
    if(!canonicalScenes(coverage.verified_scene_ids)||!Array.isArray(coverage.scenes)||coverage.scenes.length!==coverage.verified_scene_ids.length||JSON.stringify(coverage.scenes.map(row=>row?.scene_id))!==JSON.stringify(coverage.verified_scene_ids))throw new Error('Invalid project reference scene coverage.');
    const scenes=new Map();for(const row of coverage.scenes){
      if(row.limitations!==undefined&&(!Array.isArray(row.limitations)||row.limitations.length>256||row.limitations.some(item=>typeof item!=='string'||item.length>8192))||!hash(row.source_import_sha256)||!['available','unavailable'].includes(row.status)||row.status==='available'&&(!hash(row.resource_source_key)||row.reason!==null)||row.status==='unavailable'&&(row.resource_source_key!==null||typeof row.reason!=='string'||!row.reason.length||row.reason.length>8192))throw new Error('Invalid project reference resource coverage.');
      scenes.set(row.scene_id,row);
    }
    for(const node of value.nodes)if(!canonicalScenes(node.scene_ids)||!node.scene_ids.includes(node.scene_id)||!canonicalScenes(node.navigable_scene_ids,0)||node.available!==Boolean(node.navigable_scene_ids.length)||node.navigable_scene_ids.some(id=>!node.scene_ids.includes(id)||!scenes.has(id))||node.available&&node.scene_id!==node.navigable_scene_ids[0])throw new Error('Invalid project reference node membership.');
    for(const edge of [...value.incoming,...value.outgoing]){
      const source=scenes.get(edge.scene_id);if(!source||edge.source_import_sha256!==source.source_import_sha256||edge.source_catalog_key!==undefined&&(source.status!=='available'||edge.source_catalog_key!==source.resource_source_key))throw new Error('Project reference provenance differs from verified coverage.');
      if(!nodes.get(edge.source_id).scene_ids.includes(edge.scene_id))throw new Error('Project reference source membership differs from its edge.');
    }
  }
  const diagnostic=value.material_diagnostics;if(diagnostic!=null){if(nodes.get(assetId).kind!=='model'||diagnostic.model_id!==assetId||diagnostic.source_sha256!==undefined&&!hash(diagnostic.source_sha256)||diagnostic.unavailable_reason!==undefined&&(typeof diagnostic.unavailable_reason!=='string'||diagnostic.unavailable_reason.length>8192)||!Array.isArray(diagnostic.materials)||diagnostic.materials.length>256||diagnostic.materials.some(row=>!Number.isSafeInteger(row.material_index)||row.material_index<0||row.material_index>255||!['address_match','missing','ambiguous','unsupported'].includes(row.status)||!Array.isArray(row.source_ids)||row.source_ids.length>1024||row.source_ids.some(id=>!identity(id))))throw new Error('Invalid material diagnostics.');}
  return structuredClone(value);
}
export const assetReferenceNavigationNode=(node,edge,scope='active')=>scope==='project'&&node.navigable_scene_ids.includes(edge.scene_id)?{...node,scene_id:edge.scene_id}:node;
export const assetReferenceRelationLabel=edge=>edge.kind==='reference_pinned_model_clip'?`pinned model/clip association · clip ${edge.reference_clip_evidence.clip_id} · actor playback unknown`:transitionRelations.has(edge.kind)?`${edge.kind==='script_transition_reference'?'source script instruction':'encoded destination source'} · reachability not evaluated`:edge.kind.replaceAll('_',' ');
export function assetReferenceTransitionEvidenceLabel(edge){
  const proof=edge.transition_reference_evidence;if(!proof)return null;
  return `Source instruction: ${proof.transition_id} · record SHA-256 ${proof.source_record_sha256} · ${proof.destination_scene_id===null?'Destination name unresolved':`Encoded destination: ${proof.destination_scene_id}`} · ${proof.extended_target===null?'Current script context':`Extended target ${proof.extended_target} unresolved`}. Trigger position, executed path and gameplay connection are not established.`;
}
export function openAssetReferences({record,getState,busy,onNavigate,onError=()=>{},initialScope='active'}){
  if(busy()||!getState().capabilities?.asset_references)return;
  const key=getState().asset_reference_source_key,dialog=document.createElement('dialog');let controller=null,generation=0;dialog.id='asset-references-dialog';dialog.className='project-dialog';
  const current=()=>dialog.open&&key===getState().asset_reference_source_key&&getState().capabilities?.asset_references===true;
  const title=document.createElement('h2');title.textContent=`Asset references · ${record.label}`;
  const content=document.createElement('div'),status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying recorded references…';
  const scopeLabel=document.createElement('label'),scopeSelect=document.createElement('select');scopeLabel.textContent='Reference scope';scopeSelect.setAttribute('aria-label','Reference scope');for(const [value,label] of [['active','Active scene'],['project','Project']]){const option=document.createElement('option');option.value=value;option.textContent=label;scopeSelect.append(option);}scopeSelect.value=initialScope==='project'?'project':'active';scopeLabel.append(scopeSelect);
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();dialog.addEventListener('close',()=>{generation++;controller?.abort();dialog.remove();});dialog.append(title,scopeLabel,status,content,close);document.body.append(dialog);dialog.showModal();
  const navigate=async node=>{if(busy())return;if(!current()){status.textContent='Project sources changed. Reopen asset references.';return;}try{dialog.close();await onNavigate(node);}catch(error){onError(error);}};
  const load=async()=>{const request=++generation;controller?.abort();const activeController=new AbortController();controller=activeController;const scope=scopeSelect.value;content.replaceChildren();status.textContent='Verifying recorded references…';try{
    const response=await fetch('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(scope==='project'?{asset_id:record.id,scope:'project'}:{asset_id:record.id}),signal:activeController.signal}),value=await response.json();
    if(activeController.signal.aborted||request!==generation||!dialog.open)return;if(!current())throw new Error('Project sources changed. Reopen asset references.');if(!response.ok||value.error)throw new Error(value.error||'Asset reference verification failed.');
    const result=decodeAssetReferences(value,record.id,key,scope),nodes=new Map(result.nodes.map(node=>[node.id,node]));status.textContent=`Recorded references only · ${result.coverage.unresolved_reference_count} unresolved references across the graph · derived resources: ${result.coverage.resource_scene_id}`;
    if(scope==='project'){const available=result.coverage.scenes.filter(row=>row.status==='available').length;status.textContent=`Recorded references only · ${result.coverage.unresolved_reference_count} unresolved references · resource catalogs ${available}/${result.coverage.scenes.length} available`;for(const row of result.coverage.scenes.filter(row=>row.status==='unavailable')){const reason=document.createElement('p');reason.textContent=`${row.scene_id}: ${row.reason}`;content.append(reason);}}
    for(const [heading,rows,target] of [['Dependencies',result.outgoing,'target_id'],['Referenced by',result.incoming,'source_id']]){
      const section=document.createElement('section'),label=document.createElement('h3');label.textContent=heading;section.append(label);
      if(!rows.length){const empty=document.createElement('p');empty.textContent='No recorded relationships in this coverage.';section.append(empty);}
      for(const edge of rows){const node=nodes.get(edge[target]),row=document.createElement('div'),button=document.createElement('button'),description=document.createElement('p');button.textContent=node.label;button.title=node.id;button.dataset.referenceTarget=node.id;button.disabled=!node.available;button.onclick=()=>navigate(assetReferenceNavigationNode(node,edge,scope));description.textContent=`${assetReferenceRelationLabel(edge)} · ${edge.layer}${scope==='project'?` · ${edge.scene_id}`:''}${edge.pc===undefined?'':` · instruction PC ${edge.pc}`}${edge.material_evidence?` · material ${edge.material_evidence.material_index}`:''}${node.available?'':node.kind==='scene'?' · source scene not imported':' · outside navigable resource catalog'}`;
        const evidence=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Recorded provenance';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(edge,null,2);evidence.append(summary,pre);row.append(button,description,evidence);section.append(row);
        if(edge.transition_reference_evidence){const note=document.createElement('p');note.textContent=assetReferenceTransitionEvidenceLabel(edge);row.append(note);}
      }content.append(section);
    }
    if(result.material_diagnostics){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Imported material address results';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(result.material_diagnostics,null,2);details.append(summary,pre);content.append(details);}
    const limitations=document.createElement('ul');for(const text of result.limitations){const li=document.createElement('li');li.textContent=text;limitations.append(li);}content.append(limitations);
  }catch(error){if(error.name!=='AbortError'&&request===generation&&dialog.open&&!activeController.signal.aborted)status.textContent=error.message;}};
  scopeSelect.onchange=()=>{void load();};void load();
  return dialog;
}

import {decodeFlagQualification} from './flag-qualification.js';
import {decodeCurrentWavBinding} from './audio-input-assets.js';
import {validateNpcFlagReference,npcFlagInstructionSite,npcFlagReferenceLabel} from './npc-flag-references.js';
const kinds=new Set(['audio','scene','actor','model','texture','animation','script','dialogue','flag','transition','collision','trigger','region','worldmap']);
const relations=new Set(['current_native_sample_wav_binding','retained_wav_sample_input','scene_actor','scene_model_catalog','draft_donor','initial_model','effective_initial_model','actor_script_record','encoded_scene_change','script_dialogue_segment','initial_animation_binding','recorded_model_clip_binding','field_map_table_source','landmark_destination_source','static_material_texture_source']);
relations.add('effective_initial_animation_binding');relations.add('draft_initial_animation_binding');relations.add('appearance_donor');
relations.add('allocated_initial_animation_binding');relations.add('allocated_model_clip_binding');relations.add('retained_model_capture');
relations.add('reference_pinned_model_clip');
relations.add('script_flag_reference');relations.add('effective_script_flag_reference');
relations.add('script_transition_reference');relations.add('transition_destination_source');
relations.add('field_trigger_script_reference');
relations.add('effective_field_trigger_script_reference');
relations.add('effective_material_texture_source');
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
relations.add('draft_script_donor');
relations.add('npc_script_flag_operand');
const identity=value=>typeof value==='string'&&value.length>0&&value.length<=1024;
const canonicalScenes=(ids,minimum=1)=>Array.isArray(ids)&&ids.length>=minimum&&ids.length<=64&&ids.every(id=>identity(id)&&id.startsWith('scene://')&&id.length>8)&&new Set(ids).size===ids.length&&JSON.stringify(ids)===JSON.stringify([...ids].sort());
const exactKeys=(value,keys)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const boundedInteger=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const referenceModels=Array.from({length:5},(_,slot)=>`asset://legaia/models/global-special/${(0xf0+slot).toString(16).padStart(4,'0')}`);
const transitionRelations=new Set(['script_transition_reference','transition_destination_source']);
const transitionProofKeys=['transition_id','source_record_sha256','destination_scene_id','extended_target','name_sha256','status','reachability'];
const triggerProofKeys=['trigger_source_record_sha256','script_source_record_sha256','table_source','table_kind','trigger_row_index','partition_two_record_index','gate','reachability'];
function validTriggerReference(edge,nodes){
  const proof=edge.trigger_reference_evidence,match=/^trigger:\/\/([A-Za-z0-9_-]+)\/field-map\/(primary|fallback)\/kind-1\/([0-9]{4})$/.exec(edge.source_id);
  if(!match||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','trigger_reference_evidence'])||!exactKeys(proof,triggerProofKeys)||edge.layer!=='decoded'||edge.scene_id!=='scene://'+match[1]||nodes.get(edge.source_id).kind!=='trigger'||nodes.get(edge.target_id).kind!=='script'||nodes.get(edge.source_id).scene_id!==edge.scene_id||nodes.get(edge.target_id).scene_id!==edge.scene_id)return false;
  return hash(proof.trigger_source_record_sha256)&&hash(proof.script_source_record_sha256)&&proof.table_source===match[2]&&proof.table_kind===1&&boundedInteger(proof.trigger_row_index,0,2042)&&proof.trigger_row_index===Number.parseInt(match[3],10)&&boundedInteger(proof.partition_two_record_index,0,255)&&proof.gate===1&&proof.reachability==='not_evaluated'&&edge.target_id===`script://${match[1]}/scripts/man-p2/${String(proof.partition_two_record_index).padStart(4,'0')}`;
}
function validEffectiveTriggerReference(edge,nodes){
  const binding=edge.trigger_binding_evidence;
  if(!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','trigger_reference_evidence','trigger_binding_evidence'])||edge.layer!=='effective'||!hash(edge.source_catalog_key)||!exactKeys(binding,['map_source_sha256','component_sha256','imported_partition_two_record_index','target_byte_offset'])||!hash(binding.map_source_sha256)||!hash(binding.component_sha256)||!boundedInteger(binding.imported_partition_two_record_index,0,255)||!boundedInteger(binding.target_byte_offset,65556,73727)||edge.trigger_reference_evidence?.table_source!=='primary'||binding.imported_partition_two_record_index===edge.trigger_reference_evidence.partition_two_record_index)return false;
  const source={...edge,kind:'field_trigger_script_reference',layer:'decoded'};delete source.trigger_binding_evidence;
  return validTriggerReference(source,nodes);
}
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
  const npcDonors=new Set(),npcFlagSites=new Set(),npcFlagOwners=new Map();
  const nodes=new Map();for(const node of value.nodes){if(!identity(node.id)||nodes.has(node.id)||!kinds.has(node.kind)||!identity(node.scene_id)||!identity(node.label)||typeof node.available!=='boolean')throw new Error('Invalid asset reference node.');nodes.set(node.id,node);}
  if(!nodes.has(assetId))throw new Error('Missing asset reference root.');
  const edges=new Set(),transitionProofs=new Map(),transitionSites=new Set(),triggerSites=new Set(),triggerTargets=new Map(),triggerSources=new Map(),triggerBindings=new Map();for(const [direction,rows] of [['incoming',value.incoming],['outgoing',value.outgoing]])for(const edge of rows){
    if(!hash(edge.id)||edges.has(edge.id)||!nodes.has(edge.source_id)||!nodes.has(edge.target_id)||!relations.has(edge.kind)||!['imported','effective','authored','decoded'].includes(edge.layer)||edge.runtime_binding!=='not_asserted'||!hash(edge.source_import_sha256)||!identity(edge.scene_id)||direction==='incoming'&&edge.target_id!==assetId||direction==='outgoing'&&edge.source_id!==assetId||edge.layer==='decoded'&&!hash(edge.source_catalog_key)||edge.pc!==undefined&&(!Number.isSafeInteger(edge.pc)||edge.pc<0))throw new Error('Invalid asset reference edge.');
    edges.add(edge.id);
    if(Object.hasOwn(edge,'npc_flag_operand_evidence')&&edge.kind!=='npc_script_flag_operand')throw Error('NPC flag evidence cannot assert another relationship.');
    if(edge.kind==='npc_script_flag_operand'){
      const proof=validateNpcFlagReference(edge,nodes),site=edge.scene_id+'|'+edge.source_id+'|flag|'+edge.pc;
      if(npcFlagSites.has(site))throw Error('Duplicate NPC flag instruction ownership.');npcFlagSites.add(site);
      const owner=edge.scene_id+'|'+edge.source_id+'|flag-owner',identity=JSON.stringify(proof.donor);
      if(npcFlagOwners.has(owner)&&npcFlagOwners.get(owner)!==identity)throw Error('Conflicting NPC flag donor or authored draft ownership.');npcFlagOwners.set(owner,identity);
    }
    if(Object.hasOwn(edge,'npc_script_donor_evidence')&&edge.kind!=='draft_script_donor')throw Error('NPC script donor evidence cannot assert another relationship.');
    if(edge.kind==='draft_script_donor'){
      const p=edge.npc_script_donor_evidence,match=/^scene:\/\/([A-Za-z0-9_-]+)\/actors\/man-p1\/([0-9]{4})$/.exec(p?.donor_entity_id??'');
      const donorSite=edge.scene_id+'|'+edge.source_id;if(npcDonors.has(donorSite))throw Error('Duplicate NPC script donor relationship.');npcDonors.add(donorSite);
      if(!match||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','npc_script_donor_evidence'])||!exactKeys(p,['donor_entity_id','source_record_sha256','reference_commit','record_index','byte_offset','byte_length','byte_coordinate_space','authored_draft_sha256','script_status'])||edge.layer!=='authored'||!hash(edge.source_catalog_key)||!hash(p.source_record_sha256)||!hash(p.authored_draft_sha256)||p.reference_commit!=='d6e64c68ede25813d35db20980da82a1a025549b'||edge.target_id!=='script://'+p.donor_entity_id.slice(8)||edge.scene_id!=='scene://'+match[1]||!boundedInteger(p.record_index,0,511)||p.record_index!==Number(match[2])||!boundedInteger(p.byte_offset,0,4*1024*1024-1)||!boundedInteger(p.byte_length,1,4*1024*1024-p.byte_offset)||!['decoded_lzs_descriptor','raw_man_payload'].includes(p.byte_coordinate_space)||!['decoded_supported_paths','partial'].includes(p.script_status)||nodes.get(edge.source_id).kind!=='actor'||nodes.get(edge.target_id).kind!=='script'||!nodes.get(edge.source_id).available||!nodes.get(edge.target_id).available||nodes.get(edge.source_id).scene_id!==edge.scene_id||nodes.get(edge.target_id).scene_id!==edge.scene_id)throw Error('Invalid recorded NPC script donor relationship.');
    }
    if(Object.hasOwn(edge,'current_wav_binding_evidence')&&edge.kind!=='current_native_sample_wav_binding')throw Error('Current WAV evidence cannot assert another relationship.');
    if(edge.kind==='current_native_sample_wav_binding'){
      const p=decodeCurrentWavBinding(edge.current_wav_binding_evidence);
      if(!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','current_wav_binding_evidence'])||edge.layer!=='effective'||edge.source_id!==p.native_asset_id||edge.target_id!==p.wav_asset_id||edge.scene_id!==p.binding_scene_id||nodes.get(edge.source_id).kind!=='audio'||nodes.get(edge.target_id).kind!=='audio')throw Error('Invalid Current authored native WAV reference.');
    }

    if(Object.hasOwn(edge,'wav_input_evidence')&&edge.kind!=='retained_wav_sample_input')throw Error('WAV capture evidence cannot assert another relationship.');
    if(edge.kind==='retained_wav_sample_input'){
      const p=edge.wav_input_evidence;
      if(!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','wav_input_evidence'])||!exactKeys(p,['receipt_key','wav_sha256','sample_index','source_scene_id','bank_sha256','source_sample_sha256','native_asset_id','disc_sha256','entry_sha256','relationship'])||edge.layer!=='authored'||p.relationship!=='historical_capture_target'||p.native_asset_id!==edge.source_id||!/^audio:\/\/legaia\/prot\/[0-9]{4}$/.test(edge.source_id)||edge.target_id!=='audio-input://legaia/wav/'+p.wav_sha256||p.source_scene_id!==edge.scene_id||nodes.get(edge.source_id).kind!=='audio'||nodes.get(edge.target_id).kind!=='audio'||!boundedInteger(p.sample_index,0,254)||!['receipt_key','wav_sha256','bank_sha256','source_sample_sha256','disc_sha256','entry_sha256'].every(k=>hash(p[k])))throw Error('Invalid historical WAV capture relationship.');
    }

    if(Object.hasOwn(edge,'trigger_reference_evidence')&&!['field_trigger_script_reference','effective_field_trigger_script_reference'].includes(edge.kind))throw new Error('Trigger evidence cannot assert another relationship.');
    if(Object.hasOwn(edge,'trigger_binding_evidence')&&edge.kind!=='effective_field_trigger_script_reference')throw new Error('Authored trigger binding evidence cannot assert another relationship.');
    if(['field_trigger_script_reference','effective_field_trigger_script_reference'].includes(edge.kind)){
      if(!(edge.kind==='field_trigger_script_reference'?validTriggerReference(edge,nodes):validEffectiveTriggerReference(edge,nodes)))throw new Error('Invalid source-scoped field trigger script reference evidence.');
      const site=edge.kind+'|'+edge.source_id;if(triggerSites.has(site))throw new Error('Duplicate field trigger script reference.');triggerSites.add(site);
      const oldSource=triggerSources.get(edge.source_id),proof=edge.trigger_reference_evidence;
      if(oldSource&&(oldSource.trigger_reference_evidence.trigger_source_record_sha256!==proof.trigger_source_record_sha256||oldSource.source_import_sha256!==edge.source_import_sha256||oldSource.source_catalog_key!==edge.source_catalog_key||oldSource.scene_id!==edge.scene_id))throw new Error('Retail and effective trigger sources disagree.');
      if(oldSource&&oldSource.kind!==edge.kind){const retail=edge.kind==='field_trigger_script_reference'?edge:oldSource,effective=edge.kind==='effective_field_trigger_script_reference'?edge:oldSource;if(retail.trigger_reference_evidence.partition_two_record_index!==effective.trigger_binding_evidence.imported_partition_two_record_index)throw new Error('Effective trigger evidence differs from its Retail target.');}
      triggerSources.set(edge.source_id,edge);
      if(edge.trigger_binding_evidence){const old=triggerBindings.get(edge.scene_id),binding=edge.trigger_binding_evidence;if(old&&(old.map_source_sha256!==binding.map_source_sha256||old.component_sha256!==binding.component_sha256))throw new Error('Effective trigger bindings disagree about their scene component.');triggerBindings.set(edge.scene_id,binding);}
      const previous=triggerTargets.get(edge.target_id);
      if(previous&&(previous.trigger_reference_evidence.script_source_record_sha256!==edge.trigger_reference_evidence.script_source_record_sha256||previous.source_import_sha256!==edge.source_import_sha256||previous.source_catalog_key!==edge.source_catalog_key||previous.scene_id!==edge.scene_id))throw new Error('Field triggers disagree about their verified P2 source.');
      triggerTargets.set(edge.target_id,edge);
    }
    if(Object.hasOwn(edge,'transition_reference_evidence')&&!transitionRelations.has(edge.kind))throw new Error('Transition evidence cannot assert another relationship.');
    if(transitionRelations.has(edge.kind)){
      if(!validTransitionReference(edge,nodes))throw new Error('Invalid source-scoped transition reference evidence.');
      const transitionId=edge.kind==='script_transition_reference'?edge.target_id:edge.source_id,key=`${transitionId}/${edge.kind}`;
      if(transitionSites.has(key))throw new Error('Duplicate transition instruction reference.');transitionSites.add(key);
      const previous=transitionProofs.get(transitionId);
      if(previous&&(transitionProofKeys.some(key=>previous.transition_reference_evidence[key]!==edge.transition_reference_evidence[key])||previous.source_import_sha256!==edge.source_import_sha256||previous.source_catalog_key!==edge.source_catalog_key||previous.scene_id!==edge.scene_id))throw new Error('Transition edges disagree about their verified source.');
      transitionProofs.set(transitionId,edge);
    }
    if(Object.hasOwn(edge,'flag_reference_evidence')&&!['script_flag_reference','effective_script_flag_reference','npc_script_flag_operand'].includes(edge.kind))throw new Error('Flag evidence cannot assert another relationship.');
    if(Object.hasOwn(edge,'flag_binding_evidence')&&edge.kind!=='effective_script_flag_reference')throw new Error('Authored flag evidence cannot assert another relationship.');
    if(['script_flag_reference','effective_script_flag_reference'].includes(edge.kind)){
      const e=edge.flag_reference_evidence,current=edge.kind==='effective_script_flag_reference';
      if(edge.layer!==(current?'effective':'decoded')||nodes.get(edge.source_id).kind!=='script'||nodes.get(edge.target_id).kind!=='flag'||edge.pc===undefined||!exactKeys(e,['bank','index','scope','extended_target','grouping_layer','operation','mnemonic'])||!['local','global','context','system','extra'].includes(e.bank)||!Number.isSafeInteger(e.index)||e.index<0||e.index>(e.bank==='system'?65535:31)||!identity(e.scope)||e.grouping_layer!=='retail'||!['set','clear','test'].includes(e.operation)||!identity(e.mnemonic)||e.extended_target!==null&&(!Number.isSafeInteger(e.extended_target)||e.extended_target<0||e.extended_target>255)||edge.target_id!==`${edge.source_id.replace('script://','flag-reference://')}/${e.extended_target===null?'current':`extended-${e.extended_target}`}/${e.bank}/${e.index}`)throw new Error('Invalid source-scoped flag reference evidence.');
      if(current){
        const binding=edge.flag_binding_evidence,prefix={local:'LFLAG',global:'GFLAG',context:'CFLAG'}[e.bank],script=/^script:\/\/([a-z0-9_]+)\/(actors\/man-p1|scripts\/man-p2)\/[0-9]{4}$/.exec(edge.source_id);
        if(!script||edge.scene_id!=='scene://'+script[1]||nodes.get(edge.source_id).scene_id!==edge.scene_id||nodes.get(edge.target_id).scene_id!==edge.scene_id||e.scope!=={local:'dispatch_context_local_flags',global:'host_global_flags',context:'dispatch_context_flags'}[e.bank]||!boundedInteger(edge.pc,0,65535)||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','pc','source_import_sha256','source_catalog_key','flag_reference_evidence','flag_binding_evidence'])||!hash(edge.source_catalog_key)||!(exactKeys(binding,['operand_id','retail_index','effective_index','source_record_sha256','component_sha256'])||exactKeys(binding,['operand_id','retail_index','effective_index','source_record_sha256','component_sha256','native_operand_qualification']))||binding.operand_id!==`${edge.source_id}/flag-bit/${edge.pc.toString(16).padStart(4,'0')}`||binding.retail_index!==e.index||!boundedInteger(binding.effective_index,0,31)||!hash(binding.source_record_sha256)||!hash(binding.component_sha256)||!prefix||e.mnemonic!==`${prefix}_${e.operation.toUpperCase()}`||e.bank==='local'&&(e.index>=16||binding.effective_index>=16)||e.mnemonic==='CFLAG_SET'&&(e.index===8||binding.effective_index===8)||e.mnemonic==='CFLAG_CLEAR'&&(e.index===10||binding.effective_index===10))throw new Error('Invalid Current authored flag operand evidence.');
        if(Object.hasOwn(binding,'native_operand_qualification'))decodeFlagQualification(binding.native_operand_qualification,{owner_id:'scene://'+edge.source_id.slice(9),operand_id:binding.operand_id,source_record_sha256:binding.source_record_sha256,pc:edge.pc,mnemonic:e.mnemonic,extended_target:e.extended_target,retail_index:binding.retail_index,authored_index:binding.effective_index});
      }
    }
    if(Object.hasOwn(edge,'material_evidence')&&!['static_material_texture_source','effective_material_texture_source'].includes(edge.kind))throw new Error('Material evidence cannot assert another relationship.');
    if(['static_material_texture_source','effective_material_texture_source'].includes(edge.kind)){
      const e=edge.material_evidence,current=edge.kind==='effective_material_texture_source';if(edge.layer!==(current?'effective':'decoded')||current&&(!hash(edge.source_catalog_key)||!exactKeys(e,['material_index','tpage','clut','uv_bounds','evidence','model_source_sha256','model_current_sha256','authored_materials_sha256'])||!hash(e.model_current_sha256)||!hash(e.authored_materials_sha256))||nodes.get(edge.source_id).kind!=='model'||nodes.get(edge.target_id).kind!=='texture'||!e||!Number.isSafeInteger(e.material_index)||e.material_index<0||e.material_index>=32||!Number.isSafeInteger(e.tpage)||e.tpage<0||e.tpage>511||!Number.isSafeInteger(e.clut)||e.clut<0||e.clut>32767||!hash(e.model_source_sha256)||e.evidence!=='static_vram_addresses_not_runtime_residency'||!Array.isArray(e.uv_bounds)||e.uv_bounds.length!==4||e.uv_bounds.some(v=>!Number.isSafeInteger(v)||v<0||v>255)||e.uv_bounds[0]>e.uv_bounds[2]||e.uv_bounds[1]>e.uv_bounds[3])throw new Error('Invalid material address evidence.');
    }
    if(['effective_initial_animation_binding','draft_initial_animation_binding'].includes(edge.kind)){
      const e=edge.effective_animation_evidence;if(edge.layer!==(edge.kind==='draft_initial_animation_binding'?'authored':'effective')||nodes.get(edge.source_id).kind!=='actor'||nodes.get(edge.target_id).kind!=='animation'||!hash(edge.source_catalog_key)||!e||!identity(e.donor_entity_id)||!identity(e.model_id)||!Number.isSafeInteger(e.initial_animation_id)||e.initial_animation_id<1||e.initial_animation_id>255)throw new Error('Invalid effective animation evidence.');
    }

    if(Object.hasOwn(edge,'retained_capture_evidence')&&edge.kind!=='retained_model_capture')throw new Error('Retained capture evidence cannot assert another relationship.');
    if(edge.kind==='retained_model_capture'){
      const e=edge.retained_capture_evidence,match=/^animation:\/\/([a-z0-9]{1,12})\/authored-record\/([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/.exec(edge.source_id);
      if(!match||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','retained_capture_evidence'])||!exactKeys(e,['source_kind','record_id','record_sha256','ledger_sha256','donor_record_sha256','donor_animation_id','model_id','channel_owner_entity_id','model_source_entity_id','frame_count','object_count','active'])||e.source_kind!=='authored_animation_record'||e.record_id!==match[2]||edge.scene_id!=='scene://'+match[1]||edge.layer!=='authored'||!hash(edge.source_catalog_key)||![e.record_sha256,e.ledger_sha256,e.donor_record_sha256].every(hash)||!new RegExp('^animation://'+match[1]+'/scene-anm/[0-9]{4}$').test(e.donor_animation_id)||e.model_id!==edge.target_id||nodes.get(edge.source_id).kind!=='animation'||nodes.get(edge.target_id).kind!=='model'||![e.channel_owner_entity_id,e.model_source_entity_id].every(id=>typeof id==='string'&&new RegExp('^'+edge.scene_id+'/actors/man-p1/[0-9]{4}$').test(id))||!boundedInteger(e.frame_count,1,512)||!boundedInteger(e.object_count,1,64)||typeof e.active!=='boolean')throw new Error('Invalid retained model capture evidence.');
    }
    if(Object.hasOwn(edge,'allocated_animation_evidence')&&!['allocated_initial_animation_binding','allocated_model_clip_binding'].includes(edge.kind))throw new Error('Retained clip evidence cannot assert another relationship.');
    if(['allocated_initial_animation_binding','allocated_model_clip_binding'].includes(edge.kind)){
      const e=edge.allocated_animation_evidence,assignment=edge.kind==='allocated_initial_animation_binding',base=['record_id','record_sha256','ledger_sha256','bank_sha256','model_id','model_source_entity_id','channel_owner_entity_id','native_record_index','native_animation_id','frame_count','object_count'];
      const clip=assignment?edge.target_id:edge.source_id,match=/^animation:\/\/([a-z0-9]{1,12})\/authored-record\/([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/.exec(clip);
      if(!e||!match||!exactKeys(e,assignment?[...base,'assignment_owner_id','assignment_sha256']:base)||!exactKeys(edge,['id','source_id','target_id','kind','scene_id','layer','runtime_binding','source_import_sha256','source_catalog_key','allocated_animation_evidence'])||edge.layer!==(assignment?'effective':'authored')||edge.scene_id!=='scene://'+match[1]||e.record_id!==match[2]||!hash(edge.source_catalog_key)||['record_sha256','ledger_sha256','bank_sha256'].some(k=>!hash(e[k]))||!boundedInteger(e.native_record_index,0,254)||e.native_animation_id!==e.native_record_index+1||!boundedInteger(e.frame_count,1,512)||!boundedInteger(e.object_count,1,64)||!identity(e.model_id)||nodes.get(e.model_id)?.kind!=='model'||![e.model_source_entity_id,e.channel_owner_entity_id,...(assignment?[e.assignment_owner_id]:[])].every(id=>typeof id==='string'&&new RegExp('^'+edge.scene_id+'/actors/man-p1/[0-9]{4}$').test(id))||nodes.get(clip).kind!=='animation'||assignment&&(nodes.get(edge.source_id).kind!=='actor'||e.assignment_owner_id!==edge.source_id||!hash(e.assignment_sha256))||!assignment&&(nodes.get(edge.target_id).kind!=='model'||e.model_id!==edge.target_id))throw new Error('Invalid retained initial animation source evidence.');
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
  for(const diagnostic of [value.material_diagnostics,value.current_material_diagnostics])if(diagnostic!=null){if(nodes.get(assetId).kind!=='model'||diagnostic.model_id!==assetId||diagnostic.source_sha256!==undefined&&!hash(diagnostic.source_sha256)||diagnostic.unavailable_reason!==undefined&&(typeof diagnostic.unavailable_reason!=='string'||diagnostic.unavailable_reason.length>8192)||!Array.isArray(diagnostic.materials)||diagnostic.materials.length>256||diagnostic.materials.some(row=>!Number.isSafeInteger(row.material_index)||row.material_index<0||row.material_index>255||!['address_match','missing','ambiguous','unsupported'].includes(row.status)||!Array.isArray(row.source_ids)||row.source_ids.length>1024||row.source_ids.some(id=>!identity(id))))throw new Error('Invalid material diagnostics.');}
  const currentDiagnostic=value.current_material_diagnostics;if(currentDiagnostic&&currentDiagnostic.unavailable_reason===undefined){if(!hash(currentDiagnostic.retail_sha256)||!hash(currentDiagnostic.source_sha256)||value.outgoing.some(edge=>edge.kind==='effective_material_texture_source'&&(edge.material_evidence.model_source_sha256!==currentDiagnostic.retail_sha256||edge.material_evidence.model_current_sha256!==currentDiagnostic.source_sha256)))throw new Error('Current diagnostics differ from material link hashes.');}
  return structuredClone(value);
}
export const assetReferenceNavigationNode=(node,edge,scope='active')=>scope==='project'&&node.navigable_scene_ids.includes(edge.scene_id)?{...node,scene_id:edge.scene_id}:node;
export function assetReferenceInstructionSite(edge,nodes,scope='active'){
  if(edge?.kind==='npc_script_flag_operand')return npcFlagInstructionSite(edge,nodes,scope);
  const targets={script_dialogue_segment:'dialogue',script_flag_reference:'flag',effective_script_flag_reference:'flag',script_transition_reference:'transition',encoded_scene_change:'scene'};
  if(!Object.hasOwn(targets,edge?.kind)||edge.layer!==(edge.kind==='effective_script_flag_reference'?'effective':'decoded')||!boundedInteger(edge.pc,0,65535)||
    !hash(edge.source_import_sha256)||!hash(edge.source_catalog_key)||edge.runtime_binding!=='not_asserted')return null;
  const source=nodes.get(edge.source_id),target=nodes.get(edge.target_id),match=/^script:\/\/([A-Za-z0-9_-]+)\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})$/.exec(edge.source_id);
  if(!match||!source?.available||source.kind!=='script'||target?.kind!==targets[edge.kind]||edge.scene_id!=='scene://'+match[1])return null;
  const location=assetReferenceNavigationNode(source,edge,scope);
  if(location.scene_id!==edge.scene_id)return null;
  const recordHash=edge.flag_binding_evidence?.source_record_sha256??edge.flag_reference_evidence?.source_record_sha256??edge.transition_reference_evidence?.source_record_sha256??null;
  if(recordHash!==null&&!hash(recordHash))return null;
  return {script_id:source.id,owner_id:'scene://'+source.id.slice(9),scene_id:edge.scene_id,
    partition:match[2]==='actors/man-p1'?1:2,record_index:Number(match[3]),pc:edge.pc,
    source_catalog_key:edge.source_catalog_key,source_import_sha256:edge.source_import_sha256,source_record_sha256:recordHash};
}
export function qualifyAssetReferenceInstructionSite(site,record,sourceKey){
  const match=/^script:\/\/([A-Za-z0-9_-]+)\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})$/.exec(site?.script_id??'');
  const partition=match?.[2]==='actors/man-p1'?1:2,source=record?.source_record;
  if(!match||site.scene_id!=='scene://'+match[1]||site.owner_id!=='scene://'+site.script_id.slice(9)||site.partition!==partition||site.record_index!==Number(match[3])||
    !boundedInteger(site.pc,0,65535)||!hash(site.source_import_sha256)||!hash(site.source_catalog_key)||sourceKey!==site.source_catalog_key||
    record?.semantic_id!==site.script_id||record.asset_kind!=='script'||record.script_id!==site.script_id||record.owner_semantic_id!==site.owner_id||record.partition!==partition||
    source?.partition!==partition||source.record_index!==site.record_index||!hash(source.sha256)||
    !boundedInteger(source.byte_length,1,65536)||site.pc>=source.byte_length||
    site.source_record_sha256!==null&&(!hash(site.source_record_sha256)||source.sha256!==site.source_record_sha256))throw new Error('Reference instruction source changed or could not be qualified. Refresh asset references.');
  return structuredClone(site);
}
export const assetReferenceRelationLabel=edge=>edge.kind==='npc_script_flag_operand'?npcFlagReferenceLabel(edge):edge.kind==='draft_script_donor'?'NPC retail script donor · authored clone source · generated/live script not asserted':edge.kind==='current_native_sample_wav_binding'?`Current authored native sample ${edge.current_wav_binding_evidence.sample_index+1} / verified output bytes / runtime usage unknown`:edge.kind==='retained_wav_sample_input'?`historical WAV capture target / sample ${edge.wav_input_evidence.sample_index+1} / Current assignment unknown`:['script_flag_reference','effective_script_flag_reference'].includes(edge.kind)?`${edge.kind==='effective_script_flag_reference'?'Current authored':'Retail encoded'} ${edge.flag_reference_evidence.bank} flag operand ${edge.flag_binding_evidence?.effective_index??edge.flag_reference_evidence.index} · source group ${edge.flag_reference_evidence.index} · runtime binding unresolved`:['static_material_texture_source','effective_material_texture_source'].includes(edge.kind)?`${edge.kind==='effective_material_texture_source'?'Current':'Retail'} static material to texture address match`:edge.kind==='reference_pinned_model_clip'?`pinned model/clip association · clip ${edge.reference_clip_evidence.clip_id} · actor playback unknown`:['field_trigger_script_reference','effective_field_trigger_script_reference'].includes(edge.kind)?`${edge.kind==='effective_field_trigger_script_reference'?'Current authored':'Retail encoded'} gate-1 trigger → partition 2 source record ${edge.trigger_reference_evidence.partition_two_record_index} · activation not evaluated`:transitionRelations.has(edge.kind)?`${edge.kind==='script_transition_reference'?'source script instruction':'encoded destination source'} · reachability not evaluated`:edge.kind.replaceAll('_',' ');
export function assetReferenceTriggerEvidenceLabel(edge){
  const proof=edge.trigger_reference_evidence;if(!proof)return null;
  const binding=edge.trigger_binding_evidence;
  return `${proof.table_source} MAP kind-${proof.table_kind} row ${proof.trigger_row_index} · Retail trigger SHA-256 ${proof.trigger_source_record_sha256} · partition 2 record ${proof.partition_two_record_index} SHA-256 ${proof.script_source_record_sha256}.${binding?` Authored TriggerScripts SHA-256 ${binding.component_sha256} · MAP source SHA-256 ${binding.map_source_sha256} · Retail target record ${binding.imported_partition_two_record_index}.`:''} Encoded source reference only; activation, script execution and gameplay reachability are not established.`;
}
export function assetReferenceTransitionEvidenceLabel(edge){
  const proof=edge.transition_reference_evidence;if(!proof)return null;
  return `Source instruction: ${proof.transition_id} · record SHA-256 ${proof.source_record_sha256} · ${proof.destination_scene_id===null?'Destination name unresolved':`Encoded destination: ${proof.destination_scene_id}`} · ${proof.extended_target===null?'Current script context':`Extended target ${proof.extended_target} unresolved`}. Trigger position, executed path and gameplay connection are not established.`;
}
export function filterAssetReferences(value,{layer='all',direction='all',query=''}={}){
  if(!['all','imported','decoded','authored','effective'].includes(layer)||!['all','incoming','outgoing'].includes(direction)||typeof query!=='string'||query.length>512)throw new Error('Reference filters exceed their supported bounds.');
  const terms=query.trim().toLowerCase().split(/\s+/).filter(Boolean);if(terms.length>32)throw new Error('Reference search is limited to 32 terms.');
  const nodes=new Map(value.nodes.map(node=>[node.id,node]));
  const rows=(name,target)=>direction!=='all'&&direction!==name?[]:value[name].filter(edge=>{
    if(layer!=='all'&&edge.layer!==layer)return false;const node=nodes.get(edge[target]);
    const text=[node.id,node.label,node.kind,assetReferenceRelationLabel(edge),JSON.stringify(edge)].join(' ').toLowerCase();return terms.every(term=>text.includes(term));
  });
  return structuredClone({incoming:rows('incoming','source_id'),outgoing:rows('outgoing','target_id')});
}
export function assetReferenceDownload(value,assetId,sourceKey,scope='active'){
  const report=decodeAssetReferences(value,assetId,sourceKey,scope),text=JSON.stringify(report,null,2)+'\n';
  if(new TextEncoder().encode(text).byteLength>32*1024*1024)throw new Error('Reference report download exceeds 32 MiB.');
  const name=assetId.replace(/[^a-z0-9_-]/gi,'_').slice(-100);
  return {filename:`legaia-references-${scope}-${name}-${sourceKey.slice(0,12)}.json`,text};
}
// Navigation history is local UI state; every selected neighborhood is requalified.
export function createReferenceTrail(root){
 const node=value=>{if(!value||typeof value.id!=='string'||!value.id.length||value.id.length>1024||typeof value.label!=='string'||!value.label.length||value.label.length>1024)throw Error('Reference history requires a bounded identity and label.');return {id:value.id,label:value.label};};
 let entries=[node(root)],index=0;
 return {current:()=>({...entries[index]}),entries:()=>entries.map(v=>({...v})),position:()=>index,canBack:()=>index>0,canForward:()=>index+1<entries.length,
 visit:value=>{const next=node(value);if(next.id===entries[index].id)return false;entries=entries.slice(0,index+1);entries.push(next);if(entries.length>32)entries.shift();index=entries.length-1;return true;},
 move:position=>{if(!Number.isSafeInteger(position)||position<0||position>=entries.length)throw Error('Reference history position is unavailable.');index=position;return {...entries[index]};},
 reset:()=>{entries=[{...entries[index]}];index=0;}};
}
export function openAssetReferences({record,getState,busy,onNavigate,onInspectInstruction=null,onError=()=>{},initialScope='active'}){
  if(busy()||!getState().capabilities?.asset_references)return;
  const key=getState().asset_reference_source_key,dialog=document.createElement('dialog');let controller=null,generation=0,accepted=null,acceptedScope=null,loading=false;dialog.id='asset-references-dialog';dialog.className='project-dialog';
  const current=()=>dialog.open&&key===getState().asset_reference_source_key&&getState().capabilities?.asset_references===true;
  const trail=createReferenceTrail(record),title=document.createElement('h2');title.textContent=`Asset references · ${record.label}`;
  const content=document.createElement('div'),status=document.createElement('p');status.setAttribute('role','status');status.textContent='Verifying recorded references…';
  const tools=document.createElement('div');tools.className='reference-filters';
  function choice(title,options){const label=document.createElement('label'),select=document.createElement('select');label.textContent=title;select.setAttribute('aria-label',title);for(const [value,text] of options){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}label.append(select);tools.append(label);return select;}
  const scopeSelect=choice('Reference scope',[['active','Active scene'],['project','Project']]);scopeSelect.value=initialScope==='project'?'project':'active';
  const layer=choice('Recorded reference layer',[['all','All layers'],['imported','Imported'],['decoded','Derived source'],['authored','Authored'],['effective','Effective / Current']]);
  const direction=choice('Reference direction',[['all','Both directions'],['outgoing','Dependencies'],['incoming','Referenced by']]);
  const searchLabel=document.createElement('label'),search=document.createElement('input');search.type='search';search.maxLength=512;search.setAttribute('aria-label','Search recorded references');search.placeholder='Labels, IDs, relationships, scenes or hashes';searchLabel.textContent='Search recorded references';searchLabel.append(search);tools.append(searchLabel);
  const save=document.createElement('button');save.type='button';save.textContent='Save full reference report';save.disabled=true;save.title='Save every verified relationship and coverage limit. Display filters do not trim the report.';
  const history=document.createElement('nav');history.setAttribute('aria-label','Reference exploration history');history.className='dialog-actions';const back=document.createElement('button'),forward=document.createElement('button'),path=document.createElement('span');back.type=forward.type='button';back.textContent='Back in references';forward.textContent='Forward in references';path.setAttribute('style','display:block;overflow-wrap:anywhere;margin-block:8px');path.dataset.referenceTrail='';history.append(back,forward);
  const trace=document.createElement('button');trace.type='button';trace.textContent='Trace project relationships…';trace.disabled=true;
  const counts=document.createElement('p');counts.dataset.referenceFilterCount='';counts.setAttribute('role','status');
  const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();dialog.addEventListener('close',()=>{generation++;controller?.abort();accepted=null;dialog.remove();});const heading=document.createElement('div');heading.className='dialog-heading';heading.append(title,close);dialog.append(heading,history,path,tools,save,trace,status,counts,content);document.body.append(dialog);dialog.showModal();
  const navigate=async (value,action=onNavigate)=>{if(!dialog.open||busy())return;if(!current()){status.textContent='Project sources changed. Reopen asset references.';return;}try{dialog.close();await action(value);}catch(error){onError(error);}};
  trace.onclick=async()=>{if(loading||!accepted||busy()||!current())return;try{const {openReferenceTrace}=await import('/asset-reference-trace.js');if(current())openReferenceTrace({record:trail.current(),getState,busy,onNavigate:navigate,sourceKey:key});}catch(error){status.textContent=error.message;}};
  save.onclick=()=>{
    if(loading||!accepted||busy()||!current())return;
    try{const file=assetReferenceDownload(accepted,trail.current().id,key,acceptedScope),url=URL.createObjectURL(new Blob([file.text],{type:'application/json;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=file.filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
    catch(error){status.textContent=error.message;onError(error);}
  };
  const controls=()=>{const locked=loading||busy()||!current();trace.disabled=locked||!accepted;back.disabled=locked||!trail.canBack();forward.disabled=locked||!trail.canForward();path.textContent=`Recent reference trail ${trail.position()+1}/${trail.entries().length} (up to32): ${trail.entries().map(n=>n.label).join(' → ')} · ${trail.current().id}`;title.textContent=`Asset references · ${trail.current().label}`;save.disabled=loading||!accepted||busy()||!current();for(const input of [layer,direction,search])input.disabled=loading||!accepted||!current();};
  const render=()=>{content.replaceChildren();counts.textContent='';if(!current()){status.textContent='Project sources changed. Reopen asset references.';controls();return;}if(!accepted)return;
    const result=accepted,scope=acceptedScope,nodes=new Map(result.nodes.map(node=>[node.id,node]));let filtered;try{filtered=filterAssetReferences(result,{layer:layer.value,direction:direction.value,query:search.value});search.setAttribute('aria-invalid','false');}catch(error){search.setAttribute('aria-invalid','true');status.textContent=error.message;return;}status.textContent=`Recorded references only · ${result.coverage.unresolved_reference_count} unresolved references across the graph · derived resources: ${result.coverage.resource_scene_id}`;
    if(scope==='project'){const available=result.coverage.scenes.filter(row=>row.status==='available').length;status.textContent=`Recorded references only · ${result.coverage.unresolved_reference_count} unresolved references · resource catalogs ${available}/${result.coverage.scenes.length} available`;for(const row of result.coverage.scenes.filter(row=>row.status==='unavailable')){const reason=document.createElement('p');reason.textContent=`${row.scene_id}: ${row.reason}`;content.append(reason);}}
    for(const [heading,rows,target,name] of [['Dependencies',filtered.outgoing,'target_id','outgoing'],['Referenced by',filtered.incoming,'source_id','incoming']]){
      if(direction.value!=='all'&&direction.value!==name)continue;const section=document.createElement('section'),label=document.createElement('h3');label.textContent=heading+` (${rows.length}/${result[name].length})`;section.dataset.referenceDirection=name;section.append(label);
      if(!rows.length){const empty=document.createElement('p');empty.textContent=result[name].length?'No matches for these filters.':'No recorded relationships in this coverage.';section.append(empty);}
      for(const edge of rows){const node=nodes.get(edge[target]),row=document.createElement('div'),button=document.createElement('button'),description=document.createElement('p');row.dataset.referenceEdgeId=edge.id;button.textContent=node.label;button.title=node.id;button.dataset.referenceTarget=node.id;button.disabled=!node.available;button.onclick=()=>navigate(assetReferenceNavigationNode(node,edge,scope));description.textContent=`${assetReferenceRelationLabel(edge)} · ${edge.layer}${scope==='project'?` · ${edge.scene_id}`:''}${edge.pc===undefined?'':` · instruction PC ${edge.pc}`}${edge.material_evidence?` · material ${edge.material_evidence.material_index}`:''}${node.available?'':node.kind==='scene'?' · source scene not imported':' · outside navigable resource catalog'}`;
        const evidence=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='Recorded provenance';pre.className='diagnostic-detail';pre.textContent=JSON.stringify(edge,null,2);evidence.append(summary,pre);row.append(button,description,evidence);section.append(row);
        const explore=document.createElement('button');explore.type='button';explore.textContent='Explore references';explore.dataset.exploreReferenceTarget=node.id;explore.title=`Explore recorded relationships of ${node.id}`;explore.disabled=!node.available;explore.onclick=()=>{if(loading||busy()||!current()||!node.available)return;if(trail.visit(node)){layer.value=direction.value='all';search.value='';void load();}};row.append(explore);
        const site=assetReferenceInstructionSite(edge,nodes,scope);
        if(site&&typeof onInspectInstruction==='function'){
          const inspect=document.createElement('button');inspect.type='button';inspect.textContent=edge.kind==='npc_script_flag_operand'?'Inspect retail donor instruction':'Inspect reference instruction';inspect.dataset.referenceInstruction=site.script_id;inspect.dataset.referencePc=site.pc;
          inspect.title=`${site.script_id} · PC 0x${site.pc.toString(16).toUpperCase()}`;inspect.onclick=()=>navigate(site,onInspectInstruction);row.append(inspect);
        }
        if(edge.npc_script_donor_evidence){const p=edge.npc_script_donor_evidence,note=document.createElement('p');note.style.overflowWrap='anywhere';note.textContent=`Retail source: ${p.donor_entity_id} · ${p.script_status} · ${p.byte_coordinate_space} byte ${p.byte_offset}, ${p.byte_length} bytes. Source record SHA-256 ${p.source_record_sha256}. Authored NPC SHA-256 ${p.authored_draft_sha256}. Use the NPC's saved Build comparison to inspect its emitted script.`;row.append(note);}
        if(edge.npc_flag_operand_evidence){const p=edge.npc_flag_operand_evidence,note=document.createElement('p');note.style.overflowWrap='anywhere';note.textContent=`NPC script donor ${p.donor.donor_entity_id} · ${p.donor.script_status} catalog · ${p.authored_operand_qualified?'authored operand independently qualified':'inherited source operand'} · Retail index ${p.retail_index} · NPC authored index ${p.authored_index??'none'} · NPC Current index ${p.effective_index}. Source record SHA-256 ${p.donor.source_record_sha256}; NPC draft SHA-256 ${p.donor.authored_draft_sha256}. The donor actor's authored flag edits are separate. Generated bytes and live values require their own inspection.`;row.append(note);}
        if(edge.current_wav_binding_evidence){const p=edge.current_wav_binding_evidence,note=document.createElement('p');note.textContent=`Current entry SHA-256 ${p.current_entry_sha256} / sample SHA-256 ${p.current_sample_sha256} / entry byte ${p.sample_entry_byte_offset} / ${p.sample_size_bytes} bytes / authored binding SHA-256 ${p.binding_sha256}. Native output dependency only; runtime playback is not established.`;row.append(note);}
        if(edge.wav_input_evidence){const note=document.createElement('p');note.textContent=`Historical receipt ${edge.wav_input_evidence.receipt_key} / bank SHA-256 ${edge.wav_input_evidence.bank_sha256} / source sample SHA-256 ${edge.wav_input_evidence.source_sample_sha256}. Current native assignment and runtime usage are not established.`;row.append(note);}
        if(edge.transition_reference_evidence){const note=document.createElement('p');note.textContent=assetReferenceTransitionEvidenceLabel(edge);row.append(note);}
        if(edge.flag_binding_evidence){const note=document.createElement('p'),proof=edge.flag_binding_evidence;note.textContent=`${proof.operand_id} · Retail index ${proof.retail_index} · Current index ${proof.effective_index}. Source record SHA-256 ${proof.source_record_sha256}; authored ScriptFlags SHA-256 ${proof.component_sha256}. ${proof.native_operand_qualification?' Native authoring operand independently qualified; script coverage unchanged.':''} Source groups retain Retail identities; runtime values and execution are unresolved.`;row.append(note);}
        if(edge.trigger_reference_evidence){const note=document.createElement('p');note.textContent=assetReferenceTriggerEvidenceLabel(edge);row.append(note);}
      }content.append(section);
    }
    for(const [label,diagnostic] of [['Retail material address results',result.material_diagnostics],['Current material address results',result.current_material_diagnostics]])if(diagnostic){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent=label;pre.className='diagnostic-detail';pre.textContent=JSON.stringify(diagnostic,null,2);details.append(summary,pre);content.append(details);}
    const limitations=document.createElement('ul');for(const text of result.limitations){const li=document.createElement('li');li.textContent=text;limitations.append(li);}content.append(limitations);
    counts.textContent=`Showing ${filtered.incoming.length+filtered.outgoing.length} of ${result.incoming.length+result.outgoing.length} recorded relationships. Filters affect rows only; source coverage and diagnostics remain unchanged.`;
  };
  const load=async()=>{const request=++generation;controller?.abort();const activeController=new AbortController();controller=activeController;const scope=scopeSelect.value,selected=trail.current();accepted=null;acceptedScope=null;loading=true;content.replaceChildren();counts.textContent='';status.textContent='Verifying recorded references…';controls();try{
    const response=await fetch('/api/asset-references',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(scope==='project'?{asset_id:selected.id,scope:'project'}:{asset_id:selected.id}),signal:activeController.signal}),value=await response.json();
    if(activeController.signal.aborted||request!==generation||!dialog.open)return;if(!current())throw new Error('Project sources changed. Reopen asset references.');if(!response.ok||value.error)throw new Error(value.error||'Asset reference verification failed.');
    accepted=decodeAssetReferences(value,selected.id,key,scope);acceptedScope=scope;render();
  }catch(error){if(error.name!=='AbortError'&&request===generation&&dialog.open&&!activeController.signal.aborted)status.textContent=error.message;}finally{if(request===generation&&dialog.open){loading=false;controls();}}};
  const move=offset=>{if(loading||busy()||!current())return;trail.move(trail.position()+offset);layer.value=direction.value='all';search.value='';void load();};back.onclick=()=>move(-1);forward.onclick=()=>move(1);scopeSelect.onchange=()=>{trail.reset();void load();};for(const input of [layer,direction])input.onchange=render;search.oninput=render;void load();
  return dialog;
}

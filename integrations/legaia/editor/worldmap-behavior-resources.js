import {mountWorldAnimationChannels} from './worldmap-animation-channels.js';
import {mountWorldScriptOperands} from './world-script-animation-operands.js';
import {mountWorldScriptInspection} from './world-script-inspection.js';
import {mountWorldScriptBranches} from './world-script-branches.js';
import {qualifyWorldAnimationAuthoredAsset} from './worldmap-animation-assets.js';
// SDK metadata projections; source byte decoding remains in the importer.
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const exact=(v,keys)=>object(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=message=>{throw Error(message);};
const list=v=>Array.isArray(v)&&v.length<=4096;
const unique=v=>list(v)&&new Set(v).size===v.length;
const sorted=v=>[...new Set(v)].sort();
const kingdoms=['map01','map02','map03'];
const pin='d6e64c68ede25813d35db20980da82a1a025549b';
const entity=(id,scene)=>typeof id==='string'&&new RegExp('^scene://'+scene+'/worldmap/placements/[0-9a-f]{4}$').test(id);
const model=(id,scene)=>typeof id==='string'&&new RegExp('^asset://'+scene+'/worldmap/models/[0-9]{4}$').test(id);
const notes=v=>Array.isArray(v)&&v.length<=256&&v.every(s=>typeof s==='string'&&s.length>0&&s.length<=8192);
function slot(v,index,type){
 return exact(v,['slot_index','descriptor_type','decoded_byte_length','decoded_sha256','compressed_stream_offset','compressed_span_end','compressed_bytes_consumed','compressed_sha256'])&&v.slot_index===index&&v.descriptor_type===type&&integer(v.decoded_byte_length,1,4*1024*1024)&&hash(v.decoded_sha256)&&hash(v.compressed_sha256)&&integer(v.compressed_stream_offset,0,0x7fffffff)&&integer(v.compressed_span_end,v.compressed_stream_offset+1,0x7fffffff)&&v.compressed_bytes_consumed===v.compressed_span_end-v.compressed_stream_offset;
}
export function decodeWorldmapBehaviorResources(value,state){
 if(!exact(value,['schema_version','project_path','source_key','assets','kingdoms','metadata_only','read_only','project_changed','gameplay_verified','limitations'])||!['legaia.worldmap-behavior-resources.v1','legaia.worldmap-behavior-resources.v2'].includes(value.schema_version)||value.project_path!==state.project?.path||!hash(value.source_key)||value.source_key!==state.worldmap_authoring_state_key||value.metadata_only!==true||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!list(value.assets)||!Array.isArray(value.kingdoms)||value.kingdoms.length!==3||!notes(value.limitations))fail('World behavior resources differ from current project sources.');
 if(new TextEncoder().encode(JSON.stringify(value)).length>32*1024*1024)fail('World behavior metadata exceeds its budget.');
 const extended=value.schema_version==='legaia.worldmap-behavior-resources.v2',byId=new Map(),owners=new Set();
 for(const r of value.assets){
  const script=r.kind==='script',common=['semantic_id','asset_kind','kind','name','source_scene','source_record','bindings','source_instance_ids','model_asset_ids','scope','runtime_state','reference_commit','read_only','authoring','id','layer','scene_id','asset_registration'];
  const keys=script?['entry_pc','inspection_status','decoded_instruction_count','dialogue_segment_count','opaque_region_count','stopped_path_count','animation_asset_ids']:['frame_count','channel_count','timing','looping','script_asset_ids',...(extended?['authored_animation_id']:[])];
  if(!exact(r,[...common,...keys])||!['script','animation'].includes(r.kind)||r.asset_kind!==r.kind||r.id!==r.semantic_id||byId.has(r.id)||!kingdoms.includes(r.source_scene)||typeof r.name!=='string'||r.name.length>256||r.scope!=='global-worldmap-behavior-resources'||r.runtime_state!=='not_observed'||r.reference_commit!==pin||r.read_only!==true||!(r.authoring==='unsupported'||extended&&!script&&['shared_rigid_channels','source_metadata_only'].includes(r.authoring)||script&&['fixed_animation_operands','fixed_instruction_operands'].includes(r.authoring))||r.layer!=='derived'||r.scene_id!==null||r.asset_registration!=='verified_world_behavior_catalog')fail('World behavior asset identity or scope is invalid.');
  const s=r.source_record,scene=r.source_scene;
  if(!exact(s,['disc_sha256','iso_file','prot_entry_index','table_offset',...(script?['man_slot','partition','flat_record_index']:['animation_slot']),'record_index','byte_offset','byte_length','sha256'])||!hash(s.disc_sha256)||!hash(s.sha256)||s.iso_file!=='PROT.DAT'||!integer(s.prot_entry_index,0,65535)||!integer(s.table_offset,0,0x7fffffff)||!integer(s.record_index,0,4095)||!integer(s.byte_offset,0,4*1024*1024)||!integer(s.byte_length,1,4*1024*1024)||!slot(script?s.man_slot:s.animation_slot,script?2:4,script?3:5)||s.byte_offset+s.byte_length>(script?s.man_slot:s.animation_slot).decoded_byte_length||r.id!==(script?'script://'+scene+'/worldmap/man-p0/':'animation://'+scene+'/worldmap/scene-anm/')+String(s.record_index).padStart(4,'0'))fail('World behavior source ownership is invalid.');
  if(script){if(s.partition!==0||s.flat_record_index!==s.record_index||!integer(r.entry_pc,2,s.byte_length)||r.entry_pc%2||!['decoded_supported_paths','partial'].includes(r.inspection_status)||['decoded_instruction_count','dialogue_segment_count','opaque_region_count','stopped_path_count'].some(k=>!integer(r[k],0,65536)))fail('World script entry or inspection summary is invalid.');}
  else if(extended&&r.authored_animation_id!==`animation://${scene}/worldmap/anm/${String(s.record_index).padStart(4,'0')}`||!integer(r.frame_count,1,512)||!integer(r.channel_count,1,256)||r.timing!=='unresolved'||r.looping!=='unresolved')fail('World animation summary is invalid.');
  if(!list(r.bindings)||(script||!extended)&&!r.bindings.length||!unique(r.source_instance_ids)||!unique(r.model_asset_ids)||!unique(r[script?'animation_asset_ids':'script_asset_ids']))fail('World behavior relationships are invalid.');
  if(extended&&!script&&r.authoring!==(r.bindings.length?'shared_rigid_channels':'source_metadata_only'))fail('World animation authoring requires a compatible source object.');
  const local=new Set();
  for(const b of r.bindings){
   if(!exact(b,script?['entity_id','model_asset_id','trigger_id','trigger_source_record','anchor','encoded_animation_selector','animation_asset_id','animation_status']:['entity_id','model_asset_id','script_asset_id','encoded_selector'])||!entity(b.entity_id,scene)||!model(b.model_asset_id,scene)||local.has(b.entity_id))fail('World behavior object relationship is invalid.');local.add(b.entity_id);
   if(script){
    if(owners.has(b.entity_id)||!exact(b.anchor,['col','row'])||!integer(b.anchor.col,0,127)||!integer(b.anchor.row,0,127)||!integer(b.encoded_animation_selector,0,255)||!['none_encoded','resolved_source_clip','unsupported_source_clip'].includes(b.animation_status)||typeof b.trigger_id!=='string'||!b.trigger_id.startsWith('trigger://'+scene+'/field-map/')||!object(b.trigger_source_record)||b.trigger_source_record.disc?.sha256!==s.disc_sha256||!hash(b.trigger_source_record.sha256))fail('World script source binding is invalid.');owners.add(b.entity_id);
    if((b.animation_status==='none_encoded')!==(b.encoded_animation_selector===0)||(b.animation_status==='resolved_source_clip')!==(b.animation_asset_id!==null))fail('World script animation association is inconsistent.');
   }else if(!integer(b.encoded_selector,1,255)||b.encoded_selector!==s.record_index+1)fail('World animation selector is inconsistent.');
  }
  if(!same(r.source_instance_ids,sorted(r.bindings.map(b=>b.entity_id)))||!same(r.model_asset_ids,sorted(r.bindings.map(b=>b.model_asset_id)))||!same(r[script?'animation_asset_ids':'script_asset_ids'],sorted(r.bindings.map(b=>b[script?'animation_asset_id':'script_asset_id']).filter(v=>v!==null))))fail('World behavior relationship summaries conflict.');
  byId.set(r.id,r);
 }
 for(const r of value.assets)for(const b of r.bindings){
  const script=r.kind==='script',id=script?b.animation_asset_id:b.script_asset_id;if(id===null)continue;const target=byId.get(id);
  if(!target||target.kind===(script?'script':'animation')||target.source_scene!==r.source_scene||!target.bindings.some(other=>other.entity_id===b.entity_id&&other.model_asset_id===b.model_asset_id&&other[script?'script_asset_id':'animation_asset_id']===r.id))fail('World behavior reciprocal resource relationship is absent.');
 }
 const seen=new Set();
 for(const k of value.kingdoms){
  if(!exact(k,['scene','consumer','unbound','unsupported_animation_bindings','script_asset_count','animation_asset_count',...(extended?['animation_bank','unsupported_animation_records']:[])])||!kingdoms.includes(k.scene)||seen.has(k.scene)||!exact(k.consumer,['executable_sha256','function'])||k.consumer.executable_sha256!=='292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482'||!exact(k.consumer.function,['address','byte_length','sha256'])||k.consumer.function.address!=='0x8003A55C'||k.consumer.function.byte_length!==1144||k.consumer.function.sha256!=='6414981beba670dcf6f86da8edb5f504fafbc6fa31c8a3650535a229263f5aa7'||!list(k.unbound)||!list(k.unsupported_animation_bindings))fail('World behavior kingdom consumer evidence is invalid.');seen.add(k.scene);
  if(extended){
   if(!exact(k.animation_bank,['record_count','source'])||!integer(k.animation_bank.record_count,1,4096)||!slot(k.animation_bank.source,4,5)||!list(k.unsupported_animation_records))fail('World animation bank inventory is invalid.');
   const records=value.assets.filter(r=>r.kind==='animation'&&r.source_scene===k.scene),indices=new Set(),spans=[];
   for(const row of records){const r=row.source_record;if(!same(r.animation_slot,k.animation_bank.source))fail('World animation source bank conflicts.');indices.add(r.record_index);spans.push({index:r.record_index,at:r.byte_offset,length:r.byte_length});}
   for(const r of k.unsupported_animation_records){if(!exact(r,['record_index','byte_offset','byte_length','sha256','reason'])||!integer(r.record_index,0,k.animation_bank.record_count-1)||indices.has(r.record_index)||!integer(r.byte_offset,4+k.animation_bank.record_count*4,k.animation_bank.source.decoded_byte_length-1)||!integer(r.byte_length,1,k.animation_bank.source.decoded_byte_length-r.byte_offset)||!hash(r.sha256)||typeof r.reason!=='string'||!r.reason||r.reason.length>8192)fail('World animation diagnostic span is invalid.');indices.add(r.record_index);spans.push({index:r.record_index,at:r.byte_offset,length:r.byte_length});}
   spans.sort((a,b)=>a.index-b.index);
   if(indices.size!==k.animation_bank.record_count||spans.some((r,i)=>r.index!==i||r.at<4+k.animation_bank.record_count*4||(i?spans[i-1].at+spans[i-1].length!==r.at:false))||spans.at(-1).at+spans.at(-1).length!==k.animation_bank.source.decoded_byte_length)fail('World animation bank coverage is incomplete.');
  }
  for(const kind of ['script','animation'])if(k[kind+'_asset_count']!==value.assets.filter(r=>r.kind===kind&&r.source_scene===k.scene).length)fail('World behavior kingdom counts conflict.');
  for(const b of k.unbound){if(!exact(b,['entity_id','status'])||!entity(b.entity_id,k.scene)||owners.has(b.entity_id)||!['no_source_bind','unsupported_header_partition'].includes(b.status))fail('World unbound object coverage conflicts.');owners.add(b.entity_id);}
  for(const b of k.unsupported_animation_bindings)if(!exact(b,['entity_id','encoded_selector','reason'])||!entity(b.entity_id,k.scene)||!integer(b.encoded_selector,1,255)||typeof b.reason!=='string'||!value.assets.some(r=>r.kind==='script'&&r.bindings.some(x=>x.entity_id===b.entity_id&&x.encoded_animation_selector===b.encoded_selector&&x.animation_status==='unsupported_source_clip')))fail('World unsupported animation coverage conflicts.');
 }
 return structuredClone(value);
}
export function worldmapBehaviorProjectRecords(index,projectSourceKey){return index.assets.map(data=>({id:data.id,type:data.kind,label:data.name,source:'Global World behavior resources Ã‚Â· '+data.source_scene,sceneId:null,data:structuredClone(data),projectWorldBehaviorResource:{sourceKey:index.source_key,projectSourceKey}}));}
export function qualifyWorldmapBehaviorResource(record,index,state){
 if(state.project?.mode!=='edit'||record?.projectWorldBehaviorResource?.projectSourceKey!==state.project_assets_source_key||record.projectWorldBehaviorResource.sourceKey!==state.worldmap_authoring_state_key)fail('World behavior project sources changed. Refresh Project resources.');
 const graph=decodeWorldmapBehaviorResources(index,state),row=graph.assets.find(r=>r.id===record.id);
 if(!row||record.sceneId!==null||record.type!==row.kind||!same(record.data,row))fail('World behavior record differs from the verified project index.');
 return {projectPath:state.project.path,sourceKey:graph.source_key,record:row};
}
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export function showWorldmapBehaviorResource({dialog,record,lookup,getReport,getState,busy,setBusy,api,onApplied,onFocus,onNavigate,onError}){
 const target=qualifyWorldmapBehaviorResource(record,getReport(),getState());let editing=null,inspecting=null,branching=null,channels=null;
 const current=()=>{if(busy()||!dialog.open||!same(lookup().find(r=>r.id===record.id),record))fail('World behavior details are no longer current.');return qualifyWorldmapBehaviorResource(record,getReport(),getState());};
 dialog.replaceChildren();const heading=node('div');heading.className='dialog-heading';const close=node('button','Close');close.setAttribute('aria-label','Close asset details');close.onclick=()=>dialog.close();heading.append(node('h2',record.label),close);dialog.append(heading,node('p','Registered Retail source resource. Bindings describe source objects; Current edits and live activation are separate. Supported fixed instruction arguments use separate project overrides.'));
 if(record.type==='animation')dialog.append(node('p',`${target.record.frame_count} frames · ${target.record.channel_count} rigid object channels · ${target.record.bindings.length} compatible source instances. Timing, looping and runtime use are unknown. ${target.record.bindings.length?'Open a source object to inspect its Retail and Current poses.':'No source object association is recorded for this clip.'}`));
 if(record.authoredRecord?.authored?.WorldAnimationChannels){
  const entry=qualifyWorldAnimationAuthoredAsset(record,getState().worldmap_edit_bindings?.[`worldmap://${target.record.source_scene}/animation-channels`]?.WorldAnimationChannels),saved=node('section');saved.dataset.worldAnimationAuthored='';saved.append(node('h3','Saved Current Channels'),node('p',`${entry.edits.length} saved frame/object channel rows affect this shared native record. Retail bytes remain immutable. ${target.record.bindings.length?'Open a source object to inspect Current poses or edit/reset the saved channels.':'No compatible source object is recorded; this panel shows saved channel metadata without a posed preview.'}`),node('p','Authored alias: '+record.authoredRecord.id));
  for(const edit of entry.edits.slice(0,64)){const axes=['translation','rotation_psx'].flatMap(field=>Object.entries(edit[field]??{}).map(([axis,value])=>`${field==='translation'?'Translation':'Rotation'} ${axis.toUpperCase()} ${value}`));saved.append(node('p',`Frame ${edit.frame_index} · Object ${edit.object_index} · ${axes.join(' · ')}`));}
  if(entry.edits.length>64)saved.append(node('p',`${entry.edits.length-64} additional saved rows; inspect the Current clip for complete frame coverage.`));for(const e of saved.children)Object.assign(e.style,{whiteSpace:'normal',overflowWrap:'anywhere'});dialog.append(saved);
 }
 const links=node('section');links.dataset.worldBehaviorRelationships='';links.append(node('h3','Related Resources'));
 for(const id of [...target.record.model_asset_ids,...(record.type==='script'?target.record.animation_asset_ids:target.record.script_asset_ids)]){
  const related=lookup().find(r=>r.id===id);if(!related)fail('Related World resource is absent from Project resources.');const button=node('button',related.label);button.dataset.worldBehaviorResourceId=id;Object.assign(button.style,{display:'block',whiteSpace:'normal',overflowWrap:'anywhere',maxWidth:'100%'});button.onclick=()=>{try{current();dialog.close();onNavigate(related);}catch(e){onError(e);}};links.append(button);
 }
 dialog.append(links);const bindings=node('section');bindings.dataset.worldBehaviorBindings='';bindings.append(node('h3','Source Object Bindings'));
 for(const b of target.record.bindings){const button=node('button','Inspect source object '+b.entity_id.split('/').at(-1));button.dataset.worldBehaviorEntityId=b.entity_id;Object.assign(button.style,{display:'block',whiteSpace:'normal',maxWidth:'100%'});button.onclick=async()=>{try{const fresh=current();dialog.close();if(!await onFocus({...fresh,scene:fresh.record.source_scene,entityId:b.entity_id,...(record.type==='animation'?{animationRecord:fresh.record}:{})}))fail('World source object could not be opened.');}catch(e){onError(e);}};bindings.append(button);}
 if(record.type==='animation'&&!target.record.bindings.length)bindings.append(node('p','No compatible placed source object is associated with this clip. Native frames and channel provenance remain available; runtime use is unknown.'));dialog.append(bindings);if(record.type==='script'){
  const valid=()=>{try{return dialog.open&&same(lookup().find(r=>r.id===record.id),record)&&!!qualifyWorldmapBehaviorResource(record,getReport(),getState());}catch{return false;}};
  const ownedBusy=value=>{setBusy(value);editing?.update();inspecting?.update();branching?.update();};
  inspecting=mountWorldScriptInspection({host:dialog,record:target.record,key:target.sourceKey,path:target.projectPath,current:valid,busy,setBusy:ownedBusy,onError,onEditBranch:async pc=>{try{if(!await branching.focus(pc))throw Error('World branch editor is no longer current.');return true;}catch(e){onError(e);return false;}},onEdit:async pc=>{try{if(!await editing.focus(pc))throw Error('World instruction editor is no longer current.');return true;}catch(e){onError(e);return false;}}});
  editing=mountWorldScriptOperands({host:dialog,record:target.record,key:target.sourceKey,path:target.projectPath,current:valid,busy,setBusy:ownedBusy,api,onApplied,onError});
  branching=mountWorldScriptBranches({host:dialog,record:target.record,key:target.sourceKey,path:target.projectPath,current:valid,busy,setBusy:ownedBusy,api,onApplied,onError});
  dialog.addEventListener('close',()=>{editing.dispose();inspecting.dispose();branching.dispose();},{once:true});editing.update();inspecting.update();branching.update();
 }else if(record.type==='animation'){
  const valid=()=>{try{return dialog.open&&same(lookup().find(r=>r.id===record.id),record)&&!!qualifyWorldmapBehaviorResource(record,getReport(),getState());}catch{return false;}};
  channels=mountWorldAnimationChannels({host:dialog,record:target.record,key:target.sourceKey,path:target.projectPath,getBinding:()=>getState().worldmap_edit_bindings?.[`worldmap://${target.record.source_scene}/animation-channels`]?.WorldAnimationChannels??null,current:valid,busy,setBusy,onError});
  dialog.addEventListener('close',()=>channels.dispose(),{once:true});
 }const metadata=node('details');metadata.open=record.type==='script';metadata.append(node('summary','SDK Source and Provenance'));const pre=node('pre',JSON.stringify(target.record,null,2));pre.id='asset-source-data';pre.className='diagnostic-detail';Object.assign(pre.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});metadata.append(pre);dialog.append(metadata);dialog.showModal();editing?.update();inspecting?.update();branching?.update();channels?.update();
}

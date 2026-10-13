import {qualifyPlayerArtInspection,composePlayerArtOwners,playerArtNativeChannels,editPlayerArtChannels,qualifyPlayerArtSamplerPose} from './player-art-authoring.js';
import {qualifyPlayerArtInputs} from './player-art-inputs.js';
import {decodeArtArchive,replaceArtEntry} from './player-art-codec.js';
import {samplePlayerActionBytes} from './player-action-playback.js';
import {placementDigest} from './worldmap-placement-replay.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b)),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const fail=()=>{throw Error('PLAYER art GLB input, converted channels or native projection changed.');};
const bytes=(s,max)=>{if(typeof s!=='string'||s.length>Math.ceil(max/3)*4)fail();const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));if(b.length>max)fail();return b;};
const differences=(a,b)=>a.reduce((n,v,k)=>n+Number(v!==b[k]),0);
const numeric=owners=>Object.fromEntries(Object.entries(owners).map(([id,v])=>{const o=structuredClone(v);delete o.glb_import;return [id,o];}));

export async function qualifyPlayerArtGlbReview(value,inspection,arts,models,record,selection,input,options){
  const current=await qualifyPlayerArtInspection(inspection,arts,models,record,selection,inspection.frame_index,inspection.part_index);
  if(!(input instanceof Uint8Array)||input.length<1||input.length>4*1024*1024)fail();
  const i=inspection,s=i.base_playback.stream,a=value?.glb_import,e=value?.retained_input,fps=options?.fps;
  if(value?.schema_version!=='legaia.player-art-glb-review.v1'||!same(value.inspection,i)||value.frame_index!==i.frame_index||value.part_index!==i.part_index||value.motion_layer!=='proposed'||value.geometry_layer!==selection.layer||value.persistence!=='not_applied'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!hash(value.review_key)||typeof fps!=='number'||!Number.isFinite(fps)||fps<1||fps>120)fail();
  const inputHash=await placementDigest(input),parts=i.base_playback.base_inspection.assembly.animation_part_indices;
  if(a?.schema_version!=='legaia.player-art-glb-import.v1'||a.stream_id!==s.semantic_id||a.glb_sha256!==inputHash||a.current_slot_sha256!==i.current_slot_sha256||a.fps!==fps||a.frame_count!==s.frame_count||a.part_count!==s.part_count||!same(a.object_part_indices,parts)||a.attachment_alias_checks!==(parts.length-s.part_count)*s.frame_count||a.rotation_step_psx!==1||a.allocation!==false||a.gameplay_verified!==false||a.timing_evidence!=='caller_selected_rate_not_verified_retail_timing'||!Number.isFinite(a.maximum_translation_error)||a.maximum_translation_error<0||a.maximum_translation_error>.500001||!Number.isFinite(a.maximum_angular_error_degrees)||a.maximum_angular_error_degrees<0||a.maximum_angular_error_degrees>.150001||e?.glb_sha256!==inputHash||e.glb_byte_length!==input.length||e.stream_id!==s.semantic_id||e.archive_id!==s.archive_asset_id||e.baseline_slot_sha256!==i.current_slot_sha256||!same(e.baseline_owners,numeric(i.owners))||!same(e.equipped,selection.equipped)||!same(e.object_part_indices,parts)||e.fps!==fps||!same(e.animation_index,options.animation_index)||!same(e.object_node_indices,options.object_node_indices))fail();
  const original=bytes(i.base_playback.source_slot_base64,0x10800),before=bytes(i.current_slot_base64,0x10800),decoded=editPlayerArtChannels(bytes(i.current_decoded_base64,146882),a.edits),raw=replaceArtEntry(before,s.stream_index,decoded);
  if(await placementDigest(raw)!==a.proposed_slot_sha256||await placementDigest(decoded)!==a.proposed_decoded_sha256)fail();
  const retail=decodeArtArchive(original)[s.stream_index].decoded,rows=[];
  for(let frame=0;frame<s.frame_count;frame++)for(let part=0;part<s.part_count;part++){const after=playerArtNativeChannels(decoded,frame,part);if(!same(after,playerArtNativeChannels(retail,frame,part)))rows.push({frame_index:frame,part_index:part,...after});}
  const after=value.ownership_after,owners=structuredClone(i.owners);
  if(!rows.length){if(after!==null)fail();delete owners[s.semantic_id];}else{if(!after||!same(after.edits,rows)||!same(after.glb_import,e))fail();owners[s.semantic_id]=after;}
  // Validate proposed input metadata even for restoration, where no active
  // retained owner will be published. Sampling remains the native interpreter.
  const registered={semantic_id:`retained-animation://legaia/player-art/${String(s.player_index).padStart(4,'0')}/${s.archive_role}/${String(s.stream_index).padStart(4,'0')}/glb/${inputHash}`,asset_kind:'retained_player_art_glb',name:`PLAYER ${s.player_index} ${s.archive_role[0].toUpperCase()+s.archive_role.slice(1)} Art Stream ${s.stream_index} GLB Input`,model_asset_id:s.model_asset_id,stream_asset_id:s.semantic_id,player_index:s.player_index,archive_role:s.archive_role,stream_index:s.stream_index,layer:'retained_authored_input',source_record:structuredClone(e),retail_source:s.source_record,references:[s.model_asset_id,s.semantic_id],current_body_sha256:value.candidate_body_sha256,current_decoded_sha256:a.proposed_decoded_sha256,relationship:'historical_import_input_not_final_current_art',read_only:true,gameplay_verified:false};
  const proposedArts={...arts,retained_art_inputs:[...(arts.retained_art_inputs??[]).filter(r=>r.stream_asset_id!==s.semantic_id),registered]};qualifyPlayerArtInputs(after?proposedArts:{...arts,retained_art_inputs:[registered]});
  const baseline=await composePlayerArtOwners(original,arts,s.archive_asset_id,e.baseline_owners,false);if(await placementDigest(baseline)!==e.baseline_slot_sha256)fail();
  const candidate=await composePlayerArtOwners(original,proposedArts,s.archive_asset_id,owners),claimed=bytes(value.candidate_slot_base64,0x10800),row=decodeArtArchive(candidate)[s.stream_index];
  if(!same([...candidate],[...claimed])||await placementDigest(candidate)!==value.candidate_slot_sha256||await placementDigest(candidate.slice(row.byte_offset,row.byte_offset+row.byte_length))!==value.candidate_body_sha256||!same([...row.decoded],[...decoded])||!same([...decoded],[...bytes(value.candidate_decoded_base64,146882)])||!same(value.capacity,{original_body_size:row.byte_length,decoded_byte_count:decoded.length,growth:false})||!same(value.projection,{byte_change_count:differences(candidate,before),changed_current_part_frames:a.edits.length,retail_relative_part_frames:rows.length,native_body_policy:'retail_relative_canonical_owner',canonicalized_body_bytes:differences(candidate,raw)}))fail();
  return {current:current.sampler,proposed:samplePlayerActionBytes(decoded,i.base_playback.base_inspection.geometry,parts),review:structuredClone(value)};
}

export async function qualifyPlayerArtGlbPose(value,review,inspection,arts,models,record,selection,input,options){
  const result=await qualifyPlayerArtGlbReview(review,inspection,arts,models,record,selection,input,options);
  if(value?.schema_version!=='legaia.player-art-glb-pose.v1'||!same(value.review,review)||value.review_key!==review.review_key||value.motion_layer!=='proposed'||value.geometry_layer!==selection.layer||value.persistence!=='not_applied'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false)fail();
  qualifyPlayerArtSamplerPose(value.current_pose,result.current,inspection.frame_index);qualifyPlayerArtSamplerPose(value.proposed_pose,result.proposed,inspection.frame_index);return result;
}

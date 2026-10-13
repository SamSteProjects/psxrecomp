import {createPlayerArtSampler} from './player-art-animation.js';
import {decodeArtArchive,replaceArtEntry} from './player-art-codec.js';
import {samplePlayerActionBytes} from './player-action-playback.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyPlayerArtInputs} from './player-art-inputs.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b)),fail=()=>{throw Error('Native PLAYER art channels differ from their source, ownership or Review.');};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const bytes=(s,max=0x10800)=>{if(typeof s!=='string'||s.length>Math.ceil(max/3)*4)fail();const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));if(b.length>max)fail();return b;};
const signed=n=>n&2048?n-4096:n;
function channels(b,frame,part){const at=2+(frame*b[0]+part)*9,v=[];for(let pair=0;pair<3;pair++){const i=at+pair*3;v.push(b[i]|(b[i+2]&15)<<8,b[i+1]|(b[i+2]>>4)<<8);}return {translation:v.slice(0,3).map(signed),rotation_psx:v.slice(3)};}
function typed(c){if(!exact(c,['translation','rotation_psx']))fail();for(const [field,low,high]of [['translation',-2048,2047],['rotation_psx',0,4095]])if(!Array.isArray(c[field])||c[field].length!==3||c[field].some(n=>!Number.isSafeInteger(n)||n<low||n>high))fail();}
function edited(original,edits){if(!Array.isArray(edits)||!edits.length||edits.length>original[0]*original[1])fail();const b=original.slice();let previous=-1;
  for(const e of edits){if(!exact(e,['frame_index','part_index','translation','rotation_psx'])||!Number.isSafeInteger(e.frame_index)||e.frame_index<0||e.frame_index>=b[1]||!Number.isSafeInteger(e.part_index)||e.part_index<0||e.part_index>=b[0])fail();const key=e.frame_index*b[0]+e.part_index;if(key<=previous)fail();previous=key;const c={translation:e.translation,rotation_psx:e.rotation_psx};typed(c);if(same(c,channels(original,e.frame_index,e.part_index)))fail();const values=[...e.translation,...e.rotation_psx],at=2+key*9;for(let pair=0;pair<3;pair++){const [a,z]=values.slice(pair*2,pair*2+2);b[at+pair*3]=a;b[at+pair*3+1]=z;b[at+pair*3+2]=((a>>8)&15)|((z>>4)&240);}}
  return b;
}
const profile={schema_version:'legaia.player-art-consumer-source.v1',executable_sha256:'292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482',functions:[{address:'0x8002A9CC',byte_length:2240,sha256:'4846568647c9d13fdf55938ca4832679c2674dc611898267ccac55fe8da42acd'},{address:'0x8002B28C',byte_length:328,sha256:'708ff5d29efa7afa0ae55a29ee44cda7c07e9842aa881b46e3c13b4ee69130ef'}],evidence:'retail_instruction_witnesses_with_bounded_offline_consumer_oracle',constraints:['Preserve each original ME size word and body offset.','Preserve original decoded parts, frames and byte count.','Every encoded stream must fit its original declared body.','Source and destination spans require complete bounded replay.'],allocation:'not_supported',resident_archive:'not_observed',timing:'not_observed',gameplay_verified:false};

export async function composePlayerArtOwners(original,arts,archiveId,owners,allowImports=true){if(!owners||typeof owners!=='object'||Array.isArray(owners)||Object.keys(owners).length>87)fail();let result=original.slice();const rows=decodeArtArchive(original);
  for(const id of Object.keys(owners).sort()){const owner=owners[id],stream=arts.catalog.streams.find(s=>s.semantic_id===id),source=stream?.source_record;
    const fields=['schema_version','asset_id','source_record','edits','decoded_sha256','current_body_sha256'],hasInput=Object.hasOwn(owner??{},'glb_import');
    if(!stream||stream.archive_asset_id!==archiveId||!exact(owner,hasInput&&allowImports?[...fields,'glb_import']:fields)||owner.schema_version!=='legaia.player-art-override.v1'||owner.asset_id!==id||!same(owner.source_record,source))fail();
    if(hasInput){
      const registered=qualifyPlayerArtInputs(arts).find(r=>r.stream_asset_id===id),e=owner.glb_import;
      if(!registered||!same(registered.source_record,e))fail();
      const baseline=await composePlayerArtOwners(original,arts,archiveId,e.baseline_owners,false);
      if(baseline.length!==e.baseline_slot_byte_length||await placementDigest(baseline)!==e.baseline_slot_sha256)fail();
    }
    const row=rows[stream.stream_index],decoded=edited(row.decoded,owner.edits);if(await placementDigest(decoded)!==owner.decoded_sha256)fail();result=replaceArtEntry(result,stream.stream_index,decoded);if(await placementDigest(result.slice(row.byte_offset,row.byte_offset+row.byte_length))!==owner.current_body_sha256)fail();
  }return result;
}
const compose=composePlayerArtOwners;
export {channels as playerArtNativeChannels,edited as editPlayerArtChannels};

export function qualifyPlayerArtSamplerPose(actual,sampler,frame){
  const expected=sampler.sample(frame);if(!same(actual?.object_transforms,expected.object_transforms)||actual.frame_index!==expected.frame_index||actual.geometry?.vertices?.length!==expected.geometry.vertices.length||actual.geometry.vertices.some((v,i)=>v.length!==3||v.some((n,a)=>!Number.isFinite(n)||Math.abs(n-expected.geometry.vertices[i][a])>1e-7)))fail();const g=structuredClone(actual.geometry);g.vertices=expected.geometry.vertices;g.bounds=expected.geometry.bounds;if(!same(g,expected.geometry))fail();for(const bound of ['min','max'])if(actual.geometry.bounds?.[bound]?.length!==3||actual.geometry.bounds[bound].some((n,a)=>!Number.isFinite(n)||Math.abs(n-expected.geometry.bounds[bound][a])>1e-7))fail();
}

export async function qualifyPlayerArtInspection(value,arts,models,record,selection,frame,part){
  if(value?.schema_version!=='legaia.player-art-frame-inspection.v1'||value.project_path!==arts.project_path||value.project_source_key!==arts.project_source_key||value.frame_index!==frame||value.part_index!==part||value.motion_layer!=='current'||value.geometry_layer!==selection.layer||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!same(value.consumer_profile,profile))fail();
  const retailSampler=await createPlayerArtSampler(value.base_playback,arts,models,record,selection),base=value.base_playback,stream=base.stream;
  if(!Number.isSafeInteger(frame)||frame<0||frame>=stream.frame_count||!Number.isSafeInteger(part)||part<0||part>=stream.part_count)fail();
  const original=bytes(base.source_slot_base64),current=bytes(value.current_slot_base64);if(current.length!==0x10800||!same([...current],[...await compose(original,arts,stream.archive_asset_id,value.owners)])||await placementDigest(current)!==value.current_slot_sha256)fail();
  for(const input of qualifyPlayerArtInputs(arts)){const s=arts.catalog.streams.find(s=>s.semantic_id===input.stream_asset_id);if(s.archive_asset_id!==stream.archive_asset_id)continue;const owner=value.owners[input.stream_asset_id];if(!owner||!same(owner.glb_import,input.source_record)||input.current_body_sha256!==owner.current_body_sha256||input.current_decoded_sha256!==owner.decoded_sha256)fail();}
  const rows=decodeArtArchive(current),row=rows[stream.stream_index];if(await placementDigest(current.slice(row.byte_offset,row.byte_offset+row.byte_length))!==value.current_body_sha256||!same([...row.decoded],[...bytes(value.current_decoded_base64,146882)])||!same(value.channels,channels(row.decoded,frame,part)))fail();
  return {retailSampler,sampler:samplePlayerActionBytes(row.decoded,base.base_inspection.geometry,base.base_inspection.assembly.animation_part_indices),inspection:structuredClone(value)};
}

export async function qualifyPlayerArtReview(value,observed,arts,models,record,selection,desired){
  typed(desired);const i=observed,frame=i.frame_index,part=i.part_index;
  await qualifyPlayerArtInspection(i,arts,models,record,selection,frame,part);
  if(value?.schema_version!=='legaia.player-art-frame-review.v1'||!same(value.inspection,i)||value.frame_index!==frame||value.part_index!==part||value.motion_layer!=='proposed'||value.geometry_layer!==selection.layer||value.persistence!=='not_applied'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!hash(value.review_key)||!same(value.projection?.before,i.channels)||!same(value.projection.after,desired)||same(i.channels,desired))fail();
  const stream=i.base_playback.stream,original=bytes(i.base_playback.source_slot_base64),retail=decodeArtArchive(original)[stream.stream_index].decoded,owners=structuredClone(i.owners),rows=new Map((owners[stream.semantic_id]?.edits??[]).map(e=>[e.frame_index*stream.part_count+e.part_index,e])),key=frame*stream.part_count+part;
  if(same(desired,channels(retail,frame,part)))rows.delete(key);else rows.set(key,{frame_index:frame,part_index:part,...structuredClone(desired)});
  const after=value.ownership_after;
  if(!rows.size){if(after!==null)fail();delete owners[stream.semantic_id];}else{if(!after||!same(after.edits,[...rows.entries()].sort((a,b)=>a[0]-b[0]).map(([,v])=>v))||Object.hasOwn(after,'glb_import')!==Object.hasOwn(owners[stream.semantic_id]??{},'glb_import')||!same(after.glb_import,owners[stream.semantic_id]?.glb_import))fail();owners[stream.semantic_id]=after;}
  const candidate=await compose(original,arts,stream.archive_asset_id,owners),claimed=bytes(value.candidate_slot_base64),current=bytes(i.current_slot_base64),row=decodeArtArchive(candidate)[stream.stream_index];
  if(!same([...candidate],[...claimed])||await placementDigest(candidate)!==value.candidate_slot_sha256||await placementDigest(candidate.slice(row.byte_offset,row.byte_offset+row.byte_length))!==value.candidate_body_sha256||!same([...row.decoded],[...bytes(value.candidate_decoded_base64,146882)])||!same(value.capacity,{original_body_size:row.byte_length,decoded_byte_count:row.decoded.length,growth:false})||value.projection.byte_change_count!==candidate.reduce((n,b,k)=>n+Number(b!==current[k]),0))fail();
  return {sampler:samplePlayerActionBytes(row.decoded,i.base_playback.base_inspection.geometry,i.base_playback.base_inspection.assembly.animation_part_indices),review:structuredClone(value)};
}

export async function qualifyPlayerArtProposedPose(value,review,observed,arts,models,record,selection,desired){
  const current=await qualifyPlayerArtInspection(observed,arts,models,record,selection,observed.frame_index,observed.part_index),proposed=await qualifyPlayerArtReview(review,observed,arts,models,record,selection,desired);
  if(value?.schema_version!=='legaia.player-art-frame-pose.v1'||!same(value.review,review)||value.review_key!==review.review_key||value.motion_layer!=='proposed'||value.geometry_layer!==selection.layer||value.persistence!=='not_applied'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false)fail();
  for(const [key,sampler]of [['current_pose',current.sampler],['proposed_pose',proposed.sampler]])qualifyPlayerArtSamplerPose(value[key],sampler,observed.frame_index);
  return {current:current.sampler,proposed:proposed.sampler};
}

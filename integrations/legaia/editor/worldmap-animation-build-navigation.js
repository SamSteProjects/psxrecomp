import {qualifyWorldAnimationAuthoredAsset} from './worldmap-animation-assets.js';
import {qualifyWorldAnimationAsset} from './worldmap-animation-current.js';
const fail=()=>{throw Error('World animation Build change differs from its saved clip, source span or Current channels.');};
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
export function worldAnimationBuildSource(change,authoredAssets){
  if(change?.scope!=='world-animation-channel-content-only')return null;
  const match=/^animation:\/\/(map01|map02|map03)\/worldmap\/anm\/([0-9]{4})$/.exec(change.owner_id??''),field=/^(translation|rotation_psx)\.([xyz])$/.exec(change.field??'');
  if(!match||!field||change.asset_id!==change.owner_id||change.scene!==match[1]||change.record_index!==Number(match[2])||change.shared_record!==true||change.contributor_scope!=='clip'||JSON.stringify(change.authored_owners)!==JSON.stringify([`worldmap://${match[1]}/animation-channels`])||!Number.isSafeInteger(change.frame_index)||change.frame_index<0||change.frame_index>511||!Number.isSafeInteger(change.object_index)||change.object_index<0||change.object_index>63||!Number.isSafeInteger(change.bank_byte_offset)||change.bank_byte_offset<8||change.bank_byte_offset>4194304||!hash(change.source_record_sha256)||!hash(change.proposed_record_sha256)||change.before===change.after)fail();
  for(const value of [change.before,change.after])if(!Number.isSafeInteger(value)||(field[1]==='translation'?value< -2048||value>2047:value<0||value>4080||value%16))fail();
  const rows=(authoredAssets??[]).filter(r=>r.kind==='animation'&&r.id===change.owner_id),entry=rows[0]?.authored?.WorldAnimationChannels,edit=entry?.edits?.find(e=>e.frame_index===change.frame_index&&e.object_index===change.object_index);
  if(rows.length!==1||rows[0].source_scene!==change.scene||rows[0].scene_id!==null||rows[0].source_record?.record_index!==change.record_index||entry?.source_record_sha256!==change.source_record_sha256||rows[0].source_record.source_record_sha256!==change.source_record_sha256||edit?.[field[1]]?.[field[2]]!==change.after)fail();
  return {id:`animation://${change.scene}/worldmap/scene-anm/${match[2]}`,scene:change.scene,frame:change.frame_index,object:change.object_index,field:change.field};
}
export function worldAnimationBuildTarget(change,records,bindings){
  const source=worldAnimationBuildSource(change,records.flatMap(r=>r.authoredRecord?[r.authoredRecord]:[]));if(!source)return null;
  const record=records.find(r=>r.id===source.id),r=record?.data;
  if(!record||change.bank_byte_offset!==r.source_record.byte_offset+8+(source.frame*r.channel_count+source.object)*8)fail();
  qualifyWorldAnimationAuthoredAsset(record,bindings?.[`worldmap://${source.scene}/animation-channels`]?.WorldAnimationChannels);
  return {...source,record:r,entityId:r.bindings[0]?.entity_id??null};
}

// Held is independently admitted Current inspection, not unverified Build metadata.
export function qualifyWorldAnimationBuildPose(held,record,change){
  qualifyWorldAnimationAsset(held,record);const match=/^(translation|rotation_psx)\.([xyz])$/.exec(change.field??'');if(!match)fail();
  const field=match[1],index=[...'xyz'].indexOf(match[2]),current=held.preview.object_transforms[change.object_index]?.[field]?.[index],retail=held.source.before.preview.object_transforms[change.object_index]?.[field]?.[index];
  if(held.frame_index!==change.frame_index||held.animation_id!==change.owner_id||held.preview.record_sha256!==change.proposed_record_sha256||held.source.before.preview.record_sha256!==change.source_record_sha256||current!==change.after||retail!==change.before)fail();
  return {retail,current};
}

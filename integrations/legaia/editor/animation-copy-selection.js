import {decodeRetainedAnimationAsset,retainedAnimationEditContext} from './retained-animation-assets.js';

export function copiedAnimationAsset(records,review,state){
  const entry=review?.duplicate_entry;
  if(review?.schema_version!=='legaia.animation-record-duplicate-review.v1'||review.project_changed!==false||review.assignments_changed!==false||review.gameplay_verified!==false||review.scene_id!==state.scene?.id||!entry||entry.record_id===review.record_id)throw Error('Copied clip receipt differs from the current scene. Refresh the animation library.');
  return createdAssetFromEntry(records,review.scene_id,entry,state);
}

export function variantAnimationAsset(records,change,state){
  const review=change?.review,request=change?.request,entry=review?.proposed_ledger?.records?.at(-1),source=review?.source_allocated_entry,native=review?.allocation?.allocated_records?.[0];
  if(change?.kind!=='variant'||review?.schema_version!=='legaia.animation-record-allocation-review.v3'||review.project_changed!==false||review.gameplay_verified!==false||review.scene_id!==state.scene?.id||!source||!native||request?.source_record_id!==source.record_id||request?.entity_id!==review.entity_id||request?.expected_source_key!==review.project_source_key||!entry||entry.record_id===source.record_id||entry.entity_id!==request.entity_id||entry.record_sha256!==native.candidate_record_sha256||entry.record_id!==native.record_id||native.frame_count!==entry.source_frame_indices?.length||native.object_count!==entry.object_count||review.allocation.allocated_records.length!==1||review.candidate_bank_sha256!==review.allocation.candidate_bank_sha256||review.animation_id!==`animation://${review.scene_id.slice(8)}/authored-record/${entry.record_id}`||!Array.isArray(review.proposed_ledger.removed_record_ids)||review.proposed_ledger.removed_record_ids.includes(entry.record_id)||['channel_owner_entity_id','model_source_entity_id','donor_animation_id','donor_asset_id','donor_record_sha256','effective_donor_record_sha256','donor_frame_count','object_count'].some(k=>entry[k]!==source[k]))throw Error('Variant receipt differs from the created native clip. Refresh the animation library.');
  return createdAssetFromEntry(records,review.scene_id,entry,state);
}

function createdAssetFromEntry(records,sceneId,entry,state){
  const id=`animation://${sceneId.replace('scene://','')}/authored-record/${entry.record_id}`,matches=records.filter(record=>record.id===id);
  if(matches.length!==1)throw Error('Copied clip is missing or ambiguous in the refreshed asset database.');
  const record=matches[0],data=decodeRetainedAnimationAsset(record),row=data.retained_record;
  retainedAnimationEditContext(record,state);
  if(!row.active||row.assigned_actor_ids.length||row.record_sha256!==entry.record_sha256||row.entity_id!==entry.entity_id||row.channel_owner_entity_id!==entry.channel_owner_entity_id||row.model_source_entity_id!==entry.model_source_entity_id||row.donor_asset_id!==entry.donor_asset_id||row.donor_animation_id!==entry.donor_animation_id||row.object_count!==entry.object_count||row.frame_count!==entry.source_frame_indices?.length||data.source_record.donor_record_sha256!==entry.donor_record_sha256)throw Error('Copied clip source or ownership differs from its reviewed native record.');
  return structuredClone(record);
}

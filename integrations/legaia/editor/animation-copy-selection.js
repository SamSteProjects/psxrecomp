import {decodeRetainedAnimationAsset,retainedAnimationEditContext} from './retained-animation-assets.js';

export function copiedAnimationAsset(records,review,state){
  const entry=review?.duplicate_entry;
  if(review?.schema_version!=='legaia.animation-record-duplicate-review.v1'||review.project_changed!==false||review.assignments_changed!==false||review.gameplay_verified!==false||review.scene_id!==state.scene?.id||!entry||entry.record_id===review.record_id)throw Error('Copied clip receipt differs from the current scene. Refresh the animation library.');
  const id=`animation://${review.scene_id.replace('scene://','')}/authored-record/${entry.record_id}`,matches=records.filter(record=>record.id===id);
  if(matches.length!==1)throw Error('Copied clip is missing or ambiguous in the refreshed asset database.');
  const record=matches[0],data=decodeRetainedAnimationAsset(record),row=data.retained_record;
  retainedAnimationEditContext(record,state);
  if(!row.active||row.assigned_actor_ids.length||row.record_sha256!==entry.record_sha256||row.entity_id!==entry.entity_id||row.channel_owner_entity_id!==entry.channel_owner_entity_id||row.model_source_entity_id!==entry.model_source_entity_id||row.donor_asset_id!==entry.donor_asset_id||row.donor_animation_id!==entry.donor_animation_id||row.object_count!==entry.object_count||row.frame_count!==entry.source_frame_indices?.length||data.source_record.donor_record_sha256!==entry.donor_record_sha256)throw Error('Copied clip source or ownership differs from its reviewed native record.');
  return structuredClone(record);
}

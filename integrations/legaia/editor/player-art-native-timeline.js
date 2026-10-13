import {playerActionChannelTrack} from './player-action-timeline.js';
export function playerArtNativeChannelTrack(inspection,review,part,field,axis){
  if(inspection?.schema_version!=='legaia.player-art-frame-inspection.v1'||review&&review.inspection.current_slot_sha256!==inspection.current_slot_sha256)throw Error('Inspect qualified Current art channels before displaying tracks.');
  const base=inspection.base_playback,stream={...base.stream,action_slot:0};
  return playerActionChannelTrack({current_clip:stream,original_action_base64:base.decoded_stream_base64,current_action_base64:inspection.current_decoded_base64},part,field,axis,review?{current_action_base64:inspection.current_decoded_base64,projection:{action_slot:0},proposed_action_base64:review.candidate_decoded_base64}:null);
}

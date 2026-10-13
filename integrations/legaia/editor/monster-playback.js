import {qualifyMonsterPose} from './monster-motion.js';
import {samplePlayerActionBytes} from './player-action-playback.js';

export async function createMonsterPlaybackSampler(value,report,record,base,layer){
 await qualifyMonsterPose(value,report,record,value.animation_id,value.frame_index,base,layer);
 const bytes=Uint8Array.from(atob(value.source_motion_base64),c=>c.charCodeAt(0));
 if(base.objects.length!==value.clip.part_count)throw Error('Monster playback requires the qualified one-to-one source object mapping.');
 const sampler=samplePlayerActionBytes(bytes,base,base.objects.map((_,i)=>i));sampler.initialFrame=value.frame_index;
 return sampler;
}

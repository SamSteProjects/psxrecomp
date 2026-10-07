// Encoded block markers qualify a decoded PCM loop, not native ADPCM re-decoding.
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
export function validatePcmLoop(loop,frames){
 if(!loop||typeof loop!=='object'||Array.isArray(loop)||Object.keys(loop).length!==2||!Object.hasOwn(loop,'startFrame')||!Object.hasOwn(loop,'endFrame')||!integer(frames,28,114688)||frames%28||!integer(loop.startFrame,0,frames-28)||loop.startFrame%28||loop.endFrame!==frames)throw Error('Decoded PCM loop differs from the qualified block extent.');
 return {startFrame:loop.startFrame,endFrame:loop.endFrame};
}
export function encodedPcmLoop(wave,frames){
 if(!wave||!integer(frames,28,114688)||frames%28||wave.decoded_frames!==frames||wave.decoded_blocks!==frames/28||wave.consumed_bytes!==frames/28*16||!wave.termination||!Array.isArray(wave.markers)||wave.markers.length>wave.decoded_blocks)throw Error('Loop markers differ from the qualified decoded sample.');
 let previous=-1,start=null;
 for(const marker of wave.markers){
  if(!marker||!integer(marker.block_index,previous+1,wave.decoded_blocks-1)||marker.frame_offset!==marker.block_index*28||!integer(marker.flags,0,7)||!integer(marker.encoded_shift,0,15)||marker.effective_shift!==(marker.encoded_shift<=12?marker.encoded_shift:9)||!(marker.flags||marker.encoded_shift>12)||marker.flags&1&&marker.block_index!==wave.decoded_blocks-1)throw Error('Invalid encoded PCM loop marker.');
  previous=marker.block_index;if(marker.flags&4)start=marker.frame_offset;
 }
 const end=wave.markers.at(-1);
 if(wave.termination.reason!=='encoded-end')return null;
 if(wave.termination.byte_offset!==wave.consumed_bytes-16||!(end?.flags&1)||end.block_index!==wave.decoded_blocks-1)throw Error('Encoded loop end differs from sample termination.');
 return (end.flags&2)&&start!==null?validatePcmLoop({startFrame:start,endFrame:frames},frames):null;
}
export function pcmLoopFrame(frame,frames,loop){
 return frame<frames?frame:loop.startFrame+(frame-loop.startFrame)%(loop.endFrame-loop.startFrame);
}

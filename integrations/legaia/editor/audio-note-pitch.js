// Pinned Andrew reference note model; chosen base rate is not Retail driver tuning.
const integer=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
export function referenceNotePitch(note,center,shift,sourceRate){
 if(!integer(note,0,127)||!integer(center,0,255)||!integer(shift,0,255)||![11025,22050,32000,44100,48000].includes(sourceRate))throw Error('Reference note preview requires key0..127, encoded center/shift bytes and an explicit supported base rate.');
 const fineCents=shift<128?shift:shift-256,semitones=note-center-fineCents/100,unclamped=Math.round(4096*sourceRate/44100*2**(semitones/12)),pitchRegister=Math.max(1,Math.min(16384,unclamped));
 return {model:'andrew-pinned-reference-note-v1',note,center,shift,fineCents,sourceRate,semitones,pitchRegister,clamped:unclamped!==pitchRegister,effectiveSourceRate:pitchRegister*44100/4096,renderable:pitchRegister<=16383,runtime_pitch:'not_asserted'};
}

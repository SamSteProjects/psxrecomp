// Exact native-word sampling; display/authoring curve choice does not infer cadence.
export function interpolateNativeFrameAxis(kind,first,last,index,span,curve='linear'){
 const integer=(v,a,b)=>Number.isSafeInteger(v)&&v>=a&&v<=b;
 if(!['linear','ease_in','ease_out','smoothstep'].includes(curve)||!['translation','rotation_psx'].includes(kind)||!integer(span,1,4095)||!integer(index,0,span)||![first,last].every(v=>integer(v,kind==='translation'?-2048:0,kind==='translation'?2047:4080)&&(kind!=='rotation_psx'||v%16===0)))throw Error('Choose qualified native endpoints, a bounded frame range and a supported interpolation curve.');
 if(curve==='ease_in')[index,span]=[index*index,span*span];else if(curve==='ease_out')[index,span]=[2*index*span-index*index,span*span];else if(curve==='smoothstep')[index,span]=[index*index*(3*span-2*index),span*span*span];
 const rounded=n=>Math.floor((2*n+span)/(2*span));if(kind==='translation')return rounded(first*(span-index)+last*index);
 let delta=(last/16-first/16+256)%256;if(delta>128)delta-=256;return ((rounded(first/16*span+delta*index)%256+256)%256)*16;
}

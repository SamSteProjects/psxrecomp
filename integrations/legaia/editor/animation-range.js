// Author existing rigid channels on the retail integer grid; this does not infer playback timing.
function values(value){
  for(const kind of ['translation','rotation_psx']){
    if(!value?.[kind]||Object.keys(value[kind]).sort().join('')!=='xyz')throw new Error('Interpolation requires all six verified channel axes.');
    for(const axis of 'xyz'){const v=value[kind][axis];if(!Number.isInteger(v)||(kind==='translation'?(v< -2048||v>2047):(v<0||v>4080||v%16!==0)))throw new Error('Channel endpoint is outside the retail integer grid.');}
  }
}
const nearest=value=>Math.floor(value+0.5); // Exact half ties choose the larger integer.
export function interpolateNativeAnimationAxis(kind,first,last,t){
  if(!['translation','rotation_psx'].includes(kind)||!Number.isFinite(t)||t<0||t>1||[first,last].some(v=>!Number.isInteger(v)||(kind==='translation'?(v< -2048||v>2047):(v<0||v>4080||v%16))))throw new Error('Interpolation endpoints must use the native channel grid.');
  if(kind==='translation')return nearest(first+t*(last-first));
  let delta=(last-first+4096)%4096;if(delta>2048)delta-=4096;
  return ((nearest((first+t*delta)/16)*16)%4096+4096)%4096;
}
export function interpolateAnimationRange({first,last,start,end,object,frameCount,objectCount,edits}){
  values(first);values(last);
  if(![start,end,object,frameCount,objectCount].every(Number.isInteger)||frameCount<1||objectCount<1||start<0||start>=end||end>=frameCount||object<0||object>=objectCount||end-start+1>4096||!Array.isArray(edits)||edits.length>4096)throw new Error('Choose two distinct target frames and an existing rigid object within the clip.');
  const seen=new Set();for(const edit of edits){const key=JSON.stringify([edit.frame_index,edit.object_index]);if(!Number.isInteger(edit.frame_index)||!Number.isInteger(edit.object_index)||edit.frame_index<0||edit.frame_index>=frameCount||edit.object_index<0||edit.object_index>=objectCount||seen.has(key))throw new Error('Existing channel contributions have invalid or duplicate identities.');seen.add(key);}
  const proposed=[];
  for(let frame=start;frame<=end;frame++){
    const t=(frame-start)/(end-start),row={frame_index:frame,object_index:object,translation:{},rotation_psx:{}};
    for(const axis of 'xyz'){
      row.translation[axis]=interpolateNativeAnimationAxis('translation',first.translation[axis],last.translation[axis],t);
      row.rotation_psx[axis]=interpolateNativeAnimationAxis('rotation_psx',first.rotation_psx[axis],last.rotation_psx[axis],t);
    }
    proposed.push(row);
  }
  const next=structuredClone(edits.filter(edit=>edit.object_index!==object||edit.frame_index<start||edit.frame_index>end));next.push(...structuredClone(proposed));
  if(next.length>4096)throw new Error('Interpolation and existing contributions exceed the 4096-channel limit.');
  next.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
  return {proposed,edits:next};
}

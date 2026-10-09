import {interpolateNativeFrameAxis} from './animation-sample-curves.js';
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
export function interpolateAnimationRange({first,last,start,end,object,frameCount,objectCount,edits,curve='linear'}){
  values(first);values(last);
  if(![start,end,object,frameCount,objectCount].every(Number.isInteger)||frameCount<1||objectCount<1||start<0||start>=end||end>=frameCount||object<0||object>=objectCount||end-start+1>4096||!Array.isArray(edits)||edits.length>4096)throw new Error('Choose two distinct target frames and an existing rigid object within the clip.');
  const seen=new Set();for(const edit of edits){const key=JSON.stringify([edit.frame_index,edit.object_index]);if(!Number.isInteger(edit.frame_index)||!Number.isInteger(edit.object_index)||edit.frame_index<0||edit.frame_index>=frameCount||edit.object_index<0||edit.object_index>=objectCount||seen.has(key))throw new Error('Existing channel contributions have invalid or duplicate identities.');seen.add(key);}
  const proposed=[];
  for(let frame=start;frame<=end;frame++){
    const row={frame_index:frame,object_index:object,translation:{},rotation_psx:{}};
    for(const axis of 'xyz'){
      row.translation[axis]=interpolateNativeFrameAxis('translation',first.translation[axis],last.translation[axis],frame-start,end-start,curve);
      row.rotation_psx[axis]=interpolateNativeFrameAxis('rotation_psx',first.rotation_psx[axis],last.rotation_psx[axis],frame-start,end-start,curve);
    }
    proposed.push(row);
  }
  const next=structuredClone(edits.filter(edit=>edit.object_index!==object||edit.frame_index<start||edit.frame_index>end));next.push(...structuredClone(proposed));
  if(next.length>4096)throw new Error('Interpolation and existing contributions exceed the 4096-channel limit.');
  next.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
  return {proposed,edits:next};
}

export function decodeImportedFrame(value,{entityId,frame,binding,sourceKey}){
  if(!Number.isSafeInteger(binding.bone_count)||binding.bone_count<1||binding.bone_count>64||!Number.isSafeInteger(binding.frame_count)||binding.frame_count<1||binding.frame_count>512||!Number.isSafeInteger(frame)||frame<0||frame>=binding.frame_count)throw Error('Complete frame requires a bounded imported object/frame binding.');
  const keys=['frame_index','object_count','animation_id','source_record_sha256','effective_record_sha256','retail','effective','schema_version','entity_id','project_source_key','project_changed','gameplay_verified'];
  if(!value||Object.keys(value).length!==keys.length||!keys.every(k=>Object.hasOwn(value,k))||value.schema_version!=='legaia.imported-animation-frame.v1'||value.entity_id!==entityId||value.frame_index!==frame||value.object_count!==binding.bone_count||value.animation_id!==binding.semantic_id||value.source_record_sha256!==binding.source_record.record_sha256||value.project_source_key!==sourceKey||typeof value.effective_record_sha256!=='string'||!/^([a-f0-9]{64})$/.test(value.effective_record_sha256)||value.project_changed!==false||value.gameplay_verified!==false)throw Error('Complete frame differs from the current imported clip.');
  for(const layer of ['retail','effective']){
    if(!Array.isArray(value[layer])||value[layer].length!==binding.bone_count)throw Error('Complete frame has missing rigid objects.');
    value[layer].forEach((row,index)=>{if(!row||Object.keys(row).sort().join(',')!=='object_index,rotation_psx,translation'||row.object_index!==index)throw Error('Complete frame has invalid object ownership.');values(row);});
  }
  return structuredClone(value);
}

export function interpolateAnimationFrameRange({first,last,start,end,frameCount,objectCount,edits,curve='linear'}){
  if(!Number.isSafeInteger(objectCount)||objectCount<1||objectCount>64||!Array.isArray(first)||!Array.isArray(last)||first.length!==objectCount||last.length!==objectCount||!Array.isArray(edits)||edits.length>4096||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>=end||(end-start+1)*objectCount>4096)throw Error('Choose complete endpoint frames within the 4096-channel budget.');
  const proposed=[];
  for(let object=0;object<objectCount;object++){
    for(const endpoint of [first,last])if(endpoint[object]?.object_index!==object)throw Error('Complete endpoint frames must retain ordered rigid-object identities.');
    proposed.push(...interpolateAnimationRange({first:first[object],last:last[object],start,end,object,frameCount,objectCount,edits:[],curve}).proposed);
  }
  // Validate every existing contribution before withdrawing only the target frames.
  const seen=new Set();for(const edit of edits){const key=JSON.stringify([edit.frame_index,edit.object_index]);if(!Number.isSafeInteger(edit.frame_index)||!Number.isSafeInteger(edit.object_index)||edit.frame_index<0||edit.frame_index>=frameCount||edit.object_index<0||edit.object_index>=objectCount||seen.has(key))throw Error('Existing contributions have invalid or duplicate identities.');seen.add(key);}
  proposed.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
  const next=structuredClone(edits.filter(edit=>edit.frame_index<start||edit.frame_index>end));next.push(...structuredClone(proposed));
  if(next.length>4096)throw Error('Interpolation and existing contributions exceed the 4096-channel limit.');
  next.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
  return {proposed,edits:next};
}

// Repeat an inspected complete pose without inferring timing or changing object ownership.
export function holdAnimationFrameRange({first,start,end,frameCount,objectCount,edits}){
  if(!Number.isSafeInteger(frameCount)||frameCount<1||frameCount>512||!Number.isSafeInteger(objectCount)||objectCount<1||objectCount>64||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||start>end||end>=frameCount||!Array.isArray(first)||first.length!==objectCount||!Array.isArray(edits)||edits.length>4096||(end-start+1)*objectCount>4096)throw Error('Choose a complete copied pose and a target range within the 4096-channel budget.');
  first.forEach((row,index)=>{if(!row||Object.keys(row).sort().join(',')!=='object_index,rotation_psx,translation'||row.object_index!==index)throw Error('Complete copied pose must retain ordered rigid-object identities.');values(row);});
  const seen=new Set();for(const edit of edits){const key=JSON.stringify([edit.frame_index,edit.object_index]);if(!Number.isSafeInteger(edit.frame_index)||!Number.isSafeInteger(edit.object_index)||edit.frame_index<0||edit.frame_index>=frameCount||edit.object_index<0||edit.object_index>=objectCount||seen.has(key))throw Error('Existing contributions have invalid or duplicate identities.');seen.add(key);}
  const proposed=[];
  for(let frame=start;frame<=end;frame++)for(const row of first)proposed.push({frame_index:frame,object_index:row.object_index,translation:structuredClone(row.translation),rotation_psx:structuredClone(row.rotation_psx)});
  const next=structuredClone(edits.filter(edit=>edit.frame_index<start||edit.frame_index>end));next.push(...structuredClone(proposed));
  if(next.length>4096)throw Error('Copied pose and existing contributions exceed the 4096-channel limit.');
  next.sort((a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index);
  return {proposed,edits:next};
}

export function removeAnimationRange({start,end,frameCount,objectCount,object=null,axes='all',edits}){
  const choices=['all','translation','rotation_psx',...['translation','rotation_psx'].flatMap(k=>[... 'xyz'].map(a=>k+'.'+a))];
  if(!Number.isSafeInteger(frameCount)||frameCount<1||frameCount>512||!Number.isSafeInteger(objectCount)||objectCount<1||objectCount>64||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||start>end||end>=frameCount||(object!==null&&(!Number.isSafeInteger(object)||object<0||object>=objectCount))||!choices.includes(axes)||!Array.isArray(edits)||edits.length>4096)throw Error('Choose a bounded frame range, object scope and supported channel axes.');
  const next=[],removed=[],seen=new Set();
  for(const edit of edits){
    if(!edit||Object.keys(edit).some(k=>!['frame_index','object_index','translation','rotation_psx'].includes(k))||!Number.isSafeInteger(edit.frame_index)||edit.frame_index<0||edit.frame_index>=frameCount||!Number.isSafeInteger(edit.object_index)||edit.object_index<0||edit.object_index>=objectCount||seen.has(edit.frame_index+':'+edit.object_index))throw Error('Stored contributions have invalid or duplicate identities.');
    seen.add(edit.frame_index+':'+edit.object_index);
    const keep={frame_index:edit.frame_index,object_index:edit.object_index},drop={...keep};let count=0;
    for(const kind of ['translation','rotation_psx'])if(Object.hasOwn(edit,kind)){
      const v=edit[kind];if(!v||typeof v!=='object'||Array.isArray(v)||!Object.keys(v).length)throw Error('Stored channel group is invalid.');
      for(const [axis,value] of Object.entries(v)){
        if(!'xyz'.includes(axis)||axis.length!==1||!Number.isSafeInteger(value)||(kind==='translation'?(value< -2048||value>2047):(value<0||value>4080||value%16)))throw Error('Stored channel axis is outside the native grid.');
        count++;const target=edit.frame_index>=start&&edit.frame_index<=end&&(object===null||edit.object_index===object)&&(axes==='all'||axes===kind||axes===kind+'.'+axis)?drop:keep;
        (target[kind]??={})[axis]=value;
      }
    }
    if(!count)throw Error('Stored contribution has no native axes.');
    if(keep.translation||keep.rotation_psx)next.push(keep);
    if(drop.translation||drop.rotation_psx)removed.push(drop);
  }
  const order=(a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index;next.sort(order);removed.sort(order);
  return {proposed:removed,edits:next,removedAxes:removed.reduce((n,r)=>n+Object.keys(r.translation??{}).length+Object.keys(r.rotation_psx??{}).length,0)};
}

export function moveAnimationRange(args){
  const {offset,frameCount}=args;
  if(!Number.isSafeInteger(offset)||!offset||Math.abs(offset)>=frameCount)throw Error('Choose a nonzero integer frame shift within the clip.');
  const selected=removeAnimationRange(args);
  if(!selected.removedAxes)throw Error('This actor has no contributions matching that range, scope and axes.');
  // Remove the complete selection first, so overlapping source/destination ranges move simultaneously.
  const rows=new Map(selected.edits.map(row=>[row.frame_index+':'+row.object_index,structuredClone(row)])),proposed=[];
  for(const source of selected.proposed){
    const frame=source.frame_index+offset;
    if(frame<0||frame>=frameCount)throw Error('Moving this selection would place authored channels outside the existing clip.');
    const moved={...structuredClone(source),frame_index:frame},key=frame+':'+source.object_index;
    const destination=rows.get(key)??{frame_index:frame,object_index:source.object_index};
    for(const kind of ['translation','rotation_psx'])for(const [axis,value] of Object.entries(moved[kind]??{})){
      if(Object.hasOwn(destination[kind]??{},axis))throw Error('Destination frame '+frame+', object '+source.object_index+' already has '+kind+'.'+axis+'. Choose an unoccupied destination or remove that contribution first.');
      (destination[kind]??={})[axis]=value;
    }
    rows.set(key,destination);proposed.push(moved);
  }
  const order=(a,b)=>a.frame_index-b.frame_index||a.object_index-b.object_index;proposed.sort(order);const edits=[...rows.values()].sort(order);
  if(edits.length>4096)throw Error('Moved and retained contributions exceed the 4096-channel limit.');
  return {proposed,edits,movedAxes:selected.removedAxes};
}

export function decodeReversedRange(report,{entityId,binding,sourceKey,start,end,object}){
  const keys=['animation_id','source_record_sha256','before_record_sha256','after_record_sha256','start','end','object_index','proposed','value','changed_axes','schema_version','entity_id','project_source_key','project_changed','gameplay_verified'];
  if(!report||Object.keys(report).length!==keys.length||!keys.every(k=>Object.hasOwn(report,k))||report.schema_version!=='legaia.animation-range-reverse.v1'||report.entity_id!==entityId||report.project_source_key!==sourceKey||report.project_changed!==false||report.gameplay_verified!==false||report.animation_id!==binding.semantic_id||report.source_record_sha256!==binding.source_record.record_sha256||report.start!==start||report.end!==end||report.object_index!==object||!['before_record_sha256','after_record_sha256'].every(k=>/^[a-f0-9]{64}$/.test(report[k]))||!Number.isSafeInteger(report.changed_axes)||report.changed_axes<0||report.changed_axes>24576)throw Error('Reversed pose review differs from the current clip, source or selection.');
  const objects=object===null?Array.from({length:binding.bone_count},(_,i)=>i):[object];
  if(!Array.isArray(report.proposed)||report.proposed.length!==(end-start+1)*objects.length||report.proposed.length>4096||!report.value||Object.keys(report.value).sort().join(',')!=='animation_id,edits,source_record_sha256'||report.value.animation_id!==binding.semantic_id||report.value.source_record_sha256!==binding.source_record.record_sha256)throw Error('Reversed poses are incomplete or have different source ownership.');
  // Validate all retained and proposed contributions, then require every complete reversed pose in the command.
  removeAnimationRange({start,end,frameCount:binding.frame_count,objectCount:binding.bone_count,object,axes:'all',edits:report.value.edits});
  report.proposed.forEach((row,i)=>{if(!row||Object.keys(row).sort().join(',')!=='frame_index,object_index,rotation_psx,translation'||row.frame_index!==start+Math.floor(i/objects.length)||row.object_index!==objects[i%objects.length])throw Error('Reversed poses have invalid frame/object ownership.');values(row);const stored=report.value.edits.find(r=>r.frame_index===row.frame_index&&r.object_index===row.object_index);if(!stored)throw Error('Reversed pose is missing from the reviewed command.');for(const kind of ['translation','rotation_psx'])for(const axis of 'xyz')if(stored[kind]?.[axis]!==row[kind][axis])throw Error('Reversed pose differs from the reviewed command.');});
  return {proposed:structuredClone(report.proposed),edits:structuredClone(report.value.edits),changedAxes:report.changed_axes};
}

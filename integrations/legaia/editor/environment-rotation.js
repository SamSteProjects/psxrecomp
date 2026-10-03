// Pure source-axis scenery yaw previews and ordinary authoring commands.
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const wrap=value=>((value%4096)+4096)%4096;
const integer=(value,low,high,label)=>{if(!Number.isSafeInteger(value)||value<low||value>high)throw new Error(`Invalid scenery ${label}`);return value;};
const yaw=value=>integer(value,0,4095,'yaw');

export function environmentYawMatrix(entity,targetYaw){
  yaw(targetYaw);
  const transform=entity?.effective_transform,position=transform?.position,rotation=transform?.rotation_psx;
  if(!position||!rotation||!['x','y','z'].every(axis=>finite(position[axis])&&Number.isSafeInteger(rotation[axis])))throw new Error('Invalid effective scenery transform');
  const [rx,ry,rz]=[rotation.x&4095,targetYaw,rotation.z&4095].map(value=>value*Math.PI*2/4096);
  const sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz);
  // Rz*Ry*Rx, with the reflection applied to the entire source Y row.
  return [cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx,position.x,
          -sz*cy,-sz*sy*sx-cz*cx,-sz*sy*cx+cz*sx,-position.y,
          -sy,cy*sx,cy*cx,position.z,0,0,0,1];
}

export function yawFromDrag(start,current,pivot,startYaw,snapStep=1){
  yaw(startYaw);integer(snapStep,1,4096,'snap step');
  if(4096%snapStep)throw new Error('Scenery yaw snap step must divide 4096');
  if(![start,current,pivot].every(point=>point&&finite(point.x)&&finite(point.z)))throw new Error('Scenery yaw drag requires finite X/Z points');
  const a={x:start.x-pivot.x,z:start.z-pivot.z},b={x:current.x-pivot.x,z:current.z-pivot.z};
  if(![a.x,a.z,b.x,b.z].every(finite)||Math.hypot(a.x,a.z)<=1e-8||Math.hypot(b.x,b.z)<=1e-8)throw new Error('Scenery yaw drag vector is too close to its pivot');
  const delta=Math.atan2(b.x,b.z)-Math.atan2(a.x,a.z);
  return wrap(Math.round((startYaw+delta*4096/(Math.PI*2))/snapStep)*snapStep);
}

function validateRows(rows,indexKey){
  if(!Array.isArray(rows)||rows.length>512)throw new Error('Invalid scenery authoring rows');
  const seen=new Set();
  for(const row of rows){
    if(!row||typeof row!=='object'||Object.keys(row).some(key=>![indexKey,'offset','rotation_psx'].includes(key)))throw new Error('Invalid scenery authoring row');
    const index=integer(row[indexKey],0,indexKey==='cell_index'?16383:511,'authoring identity');
    if(seen.has(index))throw new Error('Duplicate scenery authoring identity');seen.add(index);
    if(!row.offset&&!row.rotation_psx)throw new Error('Scenery authoring row requires axes');
    for(const field of ['offset','rotation_psx'])if(row[field]!==undefined){
      const axes=row[field];
      if(!axes||typeof axes!=='object'||Array.isArray(axes)||!Object.keys(axes).length||Object.keys(axes).some(axis=>!['x','y','z'].includes(axis)))throw new Error('Invalid scenery authoring axes');
      for(const value of Object.values(axes))integer(value,field==='offset'?-32768:0,field==='offset'?32767:4095,'authoring axis');
    }
  }
}

export function environmentRotationCommand(sceneId,item,authoring,targetYaw,shared=false){
  yaw(targetYaw);if(typeof shared!=='boolean')throw new Error('Invalid scenery shared scope');
  const scene=typeof sceneId==='string'?/^scene:\/\/([^/]+)$/.exec(sceneId):null;
  const match=typeof item?.entity_id==='string'?/^environment:\/\/([^/]+)\/field-map\/(decorations|cells)\/(\d{5})$/.exec(item.entity_id):null;
  const source=item?.source_record,binding=source?.source_record;
  if(!scene||!match||scene[1]!==match[1]||source?.semantic_id!==item.entity_id)throw new Error('Invalid scenery scene or source identity');
  const cell=integer(Number(match[3]),0,16383,'source cell'),record=integer(source.object_record_index,0,511,'source record');
  if(binding?.grid_byte_offset!==0x8000+cell*2||!(/^[0-9a-f]{64}$/.test(binding?.map_sha256??'')))throw new Error('Invalid scenery source grid or hash');
  if(!shared&&(match[2]!=='decorations'||record<4))throw new Error('Individual yaw requires a static decoration');
  const retail=source.imported_transform?.rotation_psx;
  if(!retail||!['x','y','z'].every(axis=>Number.isInteger(retail[axis])&&retail[axis]>=0&&retail[axis]<=65535))throw new Error('Invalid retail scenery rotation');
  if(authoring!=null&&(!authoring||typeof authoring!=='object'||authoring.source_sha256!==binding.map_sha256||Object.keys(authoring).some(key=>!['source_sha256','edits','instances'].includes(key))))throw new Error('Stale or invalid scenery authoring source');
  const edits=structuredClone(authoring?.edits??[]),instances=structuredClone(authoring?.instances??[]);
  validateRows(edits,'record_index');validateRows(instances,'cell_index');
  const sharedEdit=edits.find(row=>row.record_index===record);
  const inherited=shared?retail.y&4095:sharedEdit?.rotation_psx?.y??(retail.y&4095);
  const rows=shared?edits:instances,indexKey=shared?'record_index':'cell_index',index=shared?record:cell;
  let edit=rows.find(row=>row[indexKey]===index);
  if(!edit&&targetYaw!==inherited){edit={[indexKey]:index};rows.push(edit);}
  if(edit){
    if(targetYaw===inherited){if(edit.rotation_psx){delete edit.rotation_psx.y;if(!Object.keys(edit.rotation_psx).length)delete edit.rotation_psx;}}
    else(edit.rotation_psx??={}).y=targetYaw;
    if(!edit.offset&&!edit.rotation_psx)rows.splice(rows.indexOf(edit),1);
  }
  validateRows(edits,'record_index');validateRows(instances,'cell_index');
  return edits.length||instances.length?{type:'set_environment_transforms',entity_id:sceneId,value:{source_sha256:binding.map_sha256,edits,instances}}:{type:'clear_environment_transforms',entity_id:sceneId};
}

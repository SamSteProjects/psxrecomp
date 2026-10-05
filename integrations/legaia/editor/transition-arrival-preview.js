import {decodeTransitionResource} from './transition-resource.js';
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
export function decodeTransitionArrivalPreview(value,assetId,sourceKey,projectKey){
  const keys=['schema_version','read_only','asset_id','source_scene_id','source_key','project_state_key','destination_scene_id','destination_source_key','resource','reference_y','height_known','runtime_verified','limitations'];
  if(!value||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key))||value.schema_version!=='legaia.transition-arrival-preview.v1'||value.read_only!==true||value.asset_id!==assetId||value.source_key!==sourceKey||value.project_state_key!==projectKey||![sourceKey,projectKey,value.destination_source_key].every(hash)||value.reference_y!==0||value.height_known!==false||value.runtime_verified!==false||!Array.isArray(value.limitations)||value.limitations.length>32||value.limitations.some(note=>typeof note!=='string'||note.length>8192))throw new Error('Transition arrival source changed or has invalid evidence.');
  const resource=decodeTransitionResource(value.resource);
  if(resource.semantic_id!==assetId||resource.source!==value.source_scene_id||resource.target!==value.destination_scene_id||resource.reference.target_scene_name===null)throw new Error('Transition arrival destination differs from its source resource.');
  return structuredClone({...value,resource});
}
export function transitionArrivalCurrent(report,state){
  return !!report&&state?.project?.mode==='edit'&&state.scene?.id===report.destination_scene_id&&state.scene_preview_source_key===report.destination_source_key&&state.project_transition_state_key===report.project_state_key;
}
export function transitionArrivalMarkers(report,height=0,proposal=null){
  if(!Number.isFinite(height)||Math.abs(height)>1e7)throw new Error('Arrival reference Y must be finite and within 10000000 units.');
  const markers=['imported','effective'].map((layer,index)=>({layer:layer==='imported'?'Retail':'Current',color:index?'#ffd878':'#84c9ff',...report.resource.arrival_layers[layer],y:height}));
  if(proposal)markers.push({layer:'Proposed',color:'#91efa6',...proposal.proposed_arrival,y:height});return markers;
}
export function decodeTransitionArrivalReview(value,request){
  const keys=['schema_version','read_only','preview','arrival','proposed_encoded','proposed_arrival','source_byte_audit','authored_change','current_change_count','review_key'];
  if(!value||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key))||value.schema_version!=='legaia.transition-arrival-review.v1'||value.read_only!==true||!hash(value.review_key)||typeof value.authored_change!=='boolean'||!Number.isInteger(value.current_change_count)||value.current_change_count<0||value.current_change_count>3||JSON.stringify(value.arrival)!==JSON.stringify(request.arrival)||!Array.isArray(value.source_byte_audit)||value.source_byte_audit.length>3)throw new Error('Arrival Review changed or has invalid evidence.');
  const preview=decodeTransitionArrivalPreview(value.preview,request.asset_id,value.preview?.source_key,request.project_state_key);
  if(preview.destination_source_key!==request.destination_source_key)throw new Error('Arrival Review destination changed.');
  const fields=['entry_x_encoded','entry_z_encoded','direction_encoded'],encoded=value.proposed_encoded;
  if(!encoded||Object.keys(encoded).length!==3||fields.some(key=>!Number.isInteger(encoded[key])||encoded[key]<0||encoded[key]>255))throw new Error('Invalid reviewed arrival operands.');
  const coordinate=byte=>(byte&127)*128+(byte&128?128:64),arrival=value.proposed_arrival;
  if(arrival?.x!==coordinate(encoded.entry_x_encoded)||arrival.z!==coordinate(encoded.entry_z_encoded)||arrival.facing_angle_12bit!==(encoded.direction_encoded&7)*512||arrival.runtime_verified!==false||arrival.evidence!=='retail_static_handler_and_table')throw new Error('Proposed arrival differs from its encoded operands.');
  const current=preview.resource.entry_layers.effective;
  const authored=preview.resource.entry_layers.authored;if(value.authored_change!==(Object.keys(authored).length!==3||fields.some(key=>authored[key]!==encoded[key]))||(encoded.direction_encoded&248)!==(current.direction_encoded&248)||!Object.hasOwn(request.arrival,'x')&&encoded.entry_x_encoded!==current.entry_x_encoded||!Object.hasOwn(request.arrival,'z')&&encoded.entry_z_encoded!==current.entry_z_encoded||!Object.hasOwn(request.arrival,'facing_sector')&&encoded.direction_encoded!==current.direction_encoded)throw new Error('Arrival Review changed preserved or unrequested operands.');
  if(value.current_change_count!==fields.filter(key=>encoded[key]!==current[key]).length||Object.keys(request.arrival).some(key=>!['x','z','facing_sector'].includes(key))||Object.hasOwn(request.arrival,'x')&&request.arrival.x!==arrival.x||Object.hasOwn(request.arrival,'z')&&request.arrival.z!==arrival.z||Object.hasOwn(request.arrival,'facing_sector')&&request.arrival.facing_sector*512!==arrival.facing_angle_12bit)throw new Error('Proposed arrival differs from the requested coordinates.');
  const seen=new Set();for(const row of value.source_byte_audit){if(!fields.includes(row.field)||seen.has(row.field)||row.transition_id!==preview.resource.entry_layers.transition_id||row.owner_id!==preview.resource.owner_id||row.source_record_sha256!==preview.resource.source_record.sha256||!Number.isInteger(row.decoded_byte_offset)||row.decoded_byte_offset<0||row.before_byte!==preview.resource.entry_layers.imported[row.field]||row.after_byte!==encoded[row.field]||row.before_byte===row.after_byte||row.pc!==preview.resource.reference.pc||row.record_relative_byte_offset!==preview.resource.reference.pc+(preview.resource.reference.extended_target===null?1:2)+3+preview.resource.reference.name_byte_length+fields.indexOf(row.field)||row.record_relative_byte_offset>=preview.resource.source_record.byte_length||row.decoded_byte_offset!==preview.resource.source_record.byte_offset+row.record_relative_byte_offset||!hash(row.source_decoded_man_sha256))throw new Error('Invalid arrival source byte audit.');seen.add(row.field);}
  if(fields.some(key=>(encoded[key]!==preview.resource.entry_layers.imported[key])!==seen.has(key)))throw new Error('Arrival byte audit is incomplete.');
  return structuredClone({...value,preview});
}
export function drawTransitionArrival(ctx,report,height,project,displayPosition,bounds,proposal=null){
  const markers=transitionArrivalMarkers(report,height,proposal);ctx.save();ctx.lineWidth=2;ctx.font='12px "Segoe UI",sans-serif';
  for(const [index,marker] of markers.entries()){
    const point=project(displayPosition(marker));if(!point)continue;
    ctx.strokeStyle=marker.color;ctx.fillStyle=marker.color;ctx.beginPath();ctx.arc(point.x,point.y,index?11:7,0,Math.PI*2);ctx.moveTo(point.x-14,point.y);ctx.lineTo(point.x+14,point.y);ctx.moveTo(point.x,point.y-14);ctx.lineTo(point.x,point.y+14);ctx.stroke();
    const label=`${marker.layer} arrival X ${marker.x} Z ${marker.z} · facing ${marker.facing_angle_12bit}/4096`,labelWidth=ctx.measureText(label).width,
      x=Math.max(4,Math.min(point.x+18,bounds.width-labelWidth-8)),y=Math.max(16,Math.min(point.y+(index===0?-18:index===1?24:46),bounds.height-6));
    ctx.fillStyle='#101b20ed';ctx.fillRect(x-4,y-13,labelWidth+8,18);ctx.fillStyle=marker.color;ctx.fillText(label,x,y);
  }ctx.restore();
}

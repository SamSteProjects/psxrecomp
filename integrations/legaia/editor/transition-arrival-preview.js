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
export function transitionArrivalMarkers(report,height=0){
  if(!Number.isFinite(height)||Math.abs(height)>1e7)throw new Error('Arrival reference Y must be finite and within 10000000 units.');
  return ['imported','effective'].map((layer,index)=>({layer:layer==='imported'?'Retail':'Current',color:index?'#ffd878':'#84c9ff',...report.resource.arrival_layers[layer],y:height}));
}
export function drawTransitionArrival(ctx,report,height,project,displayPosition,bounds){
  const markers=transitionArrivalMarkers(report,height);ctx.save();ctx.lineWidth=2;ctx.font='12px "Segoe UI",sans-serif';
  for(const [index,marker] of markers.entries()){
    const point=project(displayPosition(marker));if(!point)continue;
    ctx.strokeStyle=marker.color;ctx.fillStyle=marker.color;ctx.beginPath();ctx.arc(point.x,point.y,index?11:7,0,Math.PI*2);ctx.moveTo(point.x-14,point.y);ctx.lineTo(point.x+14,point.y);ctx.moveTo(point.x,point.y-14);ctx.lineTo(point.x,point.y+14);ctx.stroke();
    const label=`${marker.layer} arrival X ${marker.x} Z ${marker.z} · facing ${marker.facing_angle_12bit}/4096`,labelWidth=ctx.measureText(label).width,
      x=Math.max(4,Math.min(point.x+18,bounds.width-labelWidth-8)),y=Math.max(16,Math.min(point.y+(index?24:-18),bounds.height-6));
    ctx.fillStyle='#101b20ed';ctx.fillRect(x-4,y-13,labelWidth+8,18);ctx.fillStyle=marker.color;ctx.fillText(label,x,y);
  }ctx.restore();
}

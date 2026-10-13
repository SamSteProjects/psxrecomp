import {qualifyMonsterPreview} from './monster-archive.js';
import {qualifyMonsterPose} from './monster-motion.js';
import {modelPreviewFrame} from './model-preview-frame.js';
import {SceneRenderer} from './scene-renderer.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=()=>{throw Error('Monster Proposed pose differs from its reviewed native frame.');};

export async function qualifyMonsterMotionComparison(v,review,report,record){
 if(v?.schema_version!=='legaia.monster-frame-pose.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.review_key!==review.review_key||!same(v.review,review)||v.layer!=='proposed'||v.persistence!=='not_applied'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||v.proposed_pose?.layer!=='proposed_native_frame'||v.proposed_pose.source_motion_base64!==review.candidate_motion_base64||v.current_pose?.source_motion_base64!==review.source_motion_base64||!same(v.current_pose.base_preview,v.proposed_pose.base_preview))fail();
 const base=await qualifyMonsterPreview(v.current_pose.base_preview,report,record,'current'),id=review.clip.semantic_id,index=review.frame_index;
 const current=await qualifyMonsterPose(v.current_pose,report,record,id,index,base,'current'),proposed=await qualifyMonsterPose({...v.proposed_pose,layer:'current_palette_stored_pose'},report,record,id,index,base,'current');
 if(!same(v.proposed_pose.object_transforms[review.part_index],{object_index:review.part_index,...review.projection.after}))fail();
 return {current,proposed};
}

export async function qualifyMonsterGlbComparison(v,review,report,record,index){
 if(v?.schema_version!=='legaia.monster-glb-pose.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.review_key!==review.review_key||!same(v.review,review)||v.frame_index!==index||v.layer!=='proposed'||v.persistence!=='not_applied'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||v.proposed_pose?.layer!=='proposed_native_frame'||v.proposed_pose.source_motion_base64!==review.candidate_motion_base64||v.current_pose?.source_motion_base64!==review.source_motion_base64||!same(v.current_pose.base_preview,v.proposed_pose.base_preview))fail();
 const base=await qualifyMonsterPreview(v.current_pose.base_preview,report,record,'current'),id=review.clip.semantic_id;
 return {current:await qualifyMonsterPose(v.current_pose,report,record,id,index,base,'current'),proposed:await qualifyMonsterPose({...v.proposed_pose,layer:'current_palette_stored_pose'},report,record,id,index,base,'current')};
}

export function mountMonsterMotionComparison(host){
 const section=document.createElement('section'),label=document.createElement('label'),select=document.createElement('select'),canvas=document.createElement('canvas'),status=document.createElement('p');label.textContent='Motion Comparison Layer';select.setAttribute('aria-label','Monster Motion Comparison Layer');for(const [value,text] of [['current','Current Stored Pose'],['proposed','Proposed Unsaved Pose']]){const o=document.createElement('option');o.value=value;o.textContent=text;select.append(o);}label.append(select);Object.assign(canvas.style,{width:'100%',height:'320px',background:'#101a20'});canvas.dataset.monsterMotionComparison='';section.append(label,status,canvas);host.append(section);section.hidden=true;
 let disposed=false,poses=null,renderer=null,drag=null,yaw=.55,pitch=-.18,zoom=1;
 function draw(){if(!poses||disposed)return;const f=modelPreviewFrame(poses.current,poses.proposed,select.value,'comparison'),rect=canvas.getBoundingClientRect(),c=Math.cos(yaw),s=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);renderer.draw({width:rect.width,height:rect.height,positions:new Map(),grid:false,camera:{target:{x:f.center[0],y:-f.center[1],z:f.center[2]},distance:f.radius*4/zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
 function load(){const g=poses[select.value];renderer??=new SceneRenderer(canvas);const errors=renderer.load({assets:[{geometry_key:'motion-comparison',preview:g}],entities:[{entity_id:'motion-comparison',geometry_key:'motion-comparison',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(errors.length)throw Error(errors.join('; '));status.textContent=select.value==='proposed'?'Proposed native pose / not applied':'Current stored pose / unchanged';draw();}
 select.onchange=()=>{if(poses&&!disposed)load();};canvas.onpointerdown=e=>{if(poses){canvas.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY};}};canvas.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.009;pitch+=(e.clientY-drag.y)*.009;drag={x:e.clientX,y:e.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;canvas.onwheel=e=>{if(poses){e.preventDefault();zoom=Math.max(.15,Math.min(8,zoom*Math.exp(-e.deltaY*.001)));draw();}};const resize=new ResizeObserver(draw);resize.observe(canvas);
 return {show:value=>{poses=value;select.value='proposed';section.hidden=false;load();},withdraw:()=>{poses=null;renderer?.clear();section.hidden=true;},setDisabled:value=>select.disabled=value,dispose:()=>{disposed=true;renderer?.dispose();resize.disconnect();section.remove();}};
}

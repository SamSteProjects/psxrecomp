import {placementDigest} from './worldmap-placement-replay.js';
import {qualifyMonsterModelTextures} from './monster-textures.js';
import {qualifyMonsterCurrentPool} from './monster-palette-replay.js';
import {SceneRenderer} from './scene-renderer.js';
import {modelPreviewFrame} from './model-preview-frame.js';

const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),fail=()=>{throw Error('Monster native model source or proposal changed.');};
const decode=(s,max=11200000)=>{if(typeof s!=='string'||s.length>max)fail();return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
const original=(report,record)=>report.catalog.models.find(r=>r.semantic_id===record.id);

export async function qualifyMonsterAuthoringExport(v,report,record){
 const source=original(report,record),binding=v?.binding;
 if(!source||v?.schema_version!=='legaia.monster-model-export.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.catalog_source_key!==report.catalog.source_key||!same(v.record,source)||binding?.schema_version!=='legaia.monster-model-glb-binding.v1'||binding.asset_id!==record.id||!same(binding.source_record,source.source_record)||!hash(binding.current_block_sha256)||binding.profile?.effective_sha256!==source.source_record.sha256||v.layer!=='current_native_authoring'||v.filename!==`monster-${source.monster_id}-native-authoring.glb`||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)fail();
 const bytes=decode(v.glb_base64),view=new DataView(bytes.buffer);
 if(bytes.length<28||bytes.length>8*1024*1024||view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length||bytes.length!==v.glb_byte_length||await placementDigest(bytes)!==v.glb_sha256)fail();
 const texture=report.catalog.textures.find(r=>r.model_asset_id===record.id);
 if(texture){if(!same(v.texture_record,texture))fail();await qualifyMonsterCurrentPool(v,texture);}
 else if(v.texture_record!==null||v.source_pool_base64!==null||v.palette_binding!==null)fail();
 return structuredClone(v);
}

export async function qualifyMonsterAuthoringReview(v,exported,report,record,input){
 const source=original(report,record),p=v?.projection;
 if(v?.schema_version!=='legaia.monster-model-review.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.catalog_source_key!==report.catalog.source_key||!same(v.record,source)||!same(v.binding,exported.binding)||v.input_sha256!==await placementDigest(input)||v.input_byte_length!==input.length||p?.schema_version!=='legaia.monster-model-projection.v1'||p.source_block_sha256!==exported.binding.current_block_sha256||!hash(p.candidate_block_sha256)||p.source_tmd_sha256!==source.source_record.sha256||!hash(p.candidate_tmd_sha256)||!Array.isArray(p.changes)||p.project_changed!==false||p.gameplay_verified!==false||v.layer!=='proposed'||v.persistence!=='not_applied'||v.project_changed!==false||v.read_only!==true||v.gameplay_verified!==false||!hash(v.review_key))fail();
 const before=decode(v.current_tmd_base64),after=decode(v.candidate_tmd_base64),g=v.geometry;
 if(before.length!==source.source_record.byte_length||after.length!==before.length||p.candidate_tmd_byte_length!==after.length||await placementDigest(before)!==source.source_record.sha256||await placementDigest(after)!==p.candidate_tmd_sha256||!same(g?.source_record,source.source_record)||g.semantic_id!==record.id||g.coordinate_system!=='retail_tmd_object_local'||g.posed!==false)fail();
 const view=new DataView(after.buffer);let cursor=0;
 if(view.getUint32(0,true)!==0x80000002||view.getUint32(4,true)!==0||view.getUint32(8,true)!==source.preview_summary.objects||!same([...before.subarray(0,12+28*g.objects.length)],[...after.subarray(0,12+28*g.objects.length)]))fail();
 for(let i=0;i<g.objects.length;i++){
  const at=12+28*i,start=12+view.getUint32(at,true),count=view.getUint32(at+4,true),o=g.objects[i];
  if(o.object_index!==i||o.vertex_start!==cursor||o.vertex_count!==count||start+count*8>after.length)fail();
  for(let n=0;n<count;n++)if(!same(g.vertices[cursor++],[0,2,4].map(axis=>view.getInt16(start+n*8+axis,true))))fail();
 }
 if(cursor!==g.vertices.length||cursor!==source.preview_summary.vertices||g.triangles.length!==source.preview_summary.triangles)fail();
 modelPreviewFrame(g,g,'current','visible');
 if(!same(v.texture_record,exported.texture_record)||v.source_pool_base64!==exported.source_pool_base64||v.retail_pool_base64!==exported.retail_pool_base64||!same(v.palette_binding,exported.palette_binding))fail();
 await qualifyMonsterModelTextures({...v,layer:'current_palette'},report);return structuredClone(v);
}

export function mountMonsterModelAuthoring({host,record,report,current,busy,onPending,onError}){
 const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const section=node('section'),download=node('button','Download Monster Authoring GLB'),file=node('input'),review=node('button','Review Monster Native Model'),status=node('p','Fixed-layout native model edits. Review shows an unsaved proposal; persistent Apply is in progress.'),canvas=node('canvas');
 file.type='file';file.accept='.glb';file.setAttribute('aria-label','Monster Native Model GLB');const label=node('label','Edited Monster Authoring GLB');label.append(file);canvas.dataset.monsterModelProposed='';Object.assign(canvas.style,{width:'100%',height:'320px',display:'none',background:'#101a20'});section.append(node('h3','Native Model Authoring'),download,label,review,status,canvas);host.append(section);
 let pending=null,disposed=false,exported=null,renderer=null,geometry=null,drag=null,yaw=.55,pitch=-.18,zoom=1;
 const valid=()=>!disposed&&current(),context=()=>({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.id,catalog_source_key:report.catalog.source_key});
 function update(){const blocked=!valid()||busy()||!!pending;download.disabled=file.disabled=blocked;review.disabled=blocked||!exported||!file.files?.length;}
 function withdraw(){geometry=null;renderer?.clear();canvas.style.display='none';}
 function draw(){if(!geometry||disposed)return;const f=modelPreviewFrame(geometry,geometry,'current','visible'),r=canvas.getBoundingClientRect(),c=Math.cos(yaw),s=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);renderer.draw({width:r.width,height:r.height,positions:new Map(),grid:false,camera:{target:{x:f.center[0],y:-f.center[1],z:f.center[2]},distance:f.radius*4/zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
 async function run(route,args,accept){if(!valid()||busy()||pending)return;pending=new AbortController();onPending(true);update();try{const r=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(args),signal:pending.signal}),text=await r.text();if(text.length>16*1024*1024)fail();const v=JSON.parse(text);if(!r.ok)throw Error(v.error||'Monster model authoring failed');if(valid())await accept(v);}catch(e){if(valid()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}finally{pending=null;onPending(false);update();}}
 download.onclick=()=>{update();if(download.disabled)return;withdraw();exported=null;run('/api/monster-model-glb-export',context(),async v=>{exported=await qualifyMonsterAuthoringExport(v,report,record);const url=URL.createObjectURL(new Blob([decode(v.glb_base64)],{type:'model/gltf-binary'})),a=node('a');a.href=url;a.download=v.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Current native authoring GLB exported. Preserve source attributes when editing.';});};
 file.onchange=()=>{withdraw();status.textContent='File changed; review again.';update();};
 review.onclick=async()=>{update();if(review.disabled)return;withdraw();const selected=file.files[0],owner=exported;if(selected.size>8*1024*1024){status.textContent='Choose a GLB up to 8 MiB.';return;}try{const bytes=new Uint8Array(await selected.arrayBuffer());if(!valid()||file.files[0]!==selected||exported!==owner)return;let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));await run('/api/monster-model-glb-review',{...context(),binding:owner.binding,glb_base64:btoa(text)},async v=>{const qualified=await qualifyMonsterAuthoringReview(v,owner,report,record,bytes);geometry=qualified.geometry;renderer??=new SceneRenderer(canvas);canvas.style.display='block';const errors=renderer.load({assets:[{geometry_key:'proposed-monster',preview:geometry}],entities:[{entity_id:'proposed-monster',geometry_key:'proposed-monster',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(errors.length)throw Error(errors.join('; '));draw();status.textContent=`Proposed native model / ${qualified.projection.changes.length} typed changes / not applied`;});}catch(e){if(valid()){status.textContent=e.message;onError(e);}}};
 canvas.onpointerdown=e=>{if(geometry){canvas.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY};}};canvas.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.009;pitch+=(e.clientY-drag.y)*.009;drag={x:e.clientX,y:e.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;canvas.onwheel=e=>{if(geometry){e.preventDefault();zoom=Math.max(.15,Math.min(8,zoom*Math.exp(-e.deltaY*.001)));draw();}};
 const resize=new ResizeObserver(draw);resize.observe(canvas);update();return {update,pending:()=>!!pending,dispose:()=>{disposed=true;pending?.abort();renderer?.dispose();resize.disconnect();section.remove();}};
}

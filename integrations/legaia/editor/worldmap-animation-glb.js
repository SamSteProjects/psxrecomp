import {qualifyWorldAnimationEdit} from './worldmap-animation-current.js';
import {placementDigest} from './worldmap-placement-replay.js';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
export async function qualifyWorldAnimationGlb(value,held,current,id,path,request){
  const bytes=Uint8Array.from(atob(request.glb_base64),c=>c.charCodeAt(0)),hash=await placementDigest(bytes),v=value;
  if(!v||v.schema_version!=='legaia.world-animation-glb-review.v1'||v.project_path!==path||v.scene!==current.scene||v.source_key!==current.project_source_key||v.entity_id!==id||v.frame_index!==held.frame_index||!same(v.binding,request.binding)||!same(v.object_nodes,request.object_nodes)||v.animation_index!==request.animation_index||v.glb_sha256!==hash||v.byte_length!==bytes.length||v.shared_record!==true||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||typeof v.review_key!=='string'||!/^[0-9a-f]{64}$/.test(v.review_key)||v.analysis?.glb_sha256!==hash||v.analysis?.candidate_sha256!==v.candidate_record_sha256)throw Error('World GLB Review differs from the uploaded file or Current source.');
  const native=await qualifyWorldAnimationEdit(v.native_review,held,current,id,path,held.frame_index,v.native_review?.edits);
  if(native.proposed_preview.record_sha256!==v.candidate_record_sha256||v.analysis.frame_count!==native.proposed_preview.frame_count)throw Error('World GLB candidate differs from the reviewed native clip.');
  return {native,request:{...structuredClone(request),review_key:v.review_key},analysis:structuredClone(v.analysis)};
}
export async function worldAnimationGlbFiles(file,auditFile,held,context,animationValue,mappingValue){
  if(!file||file.size<28||file.size>32*1024*1024||!auditFile||auditFile.size>128*1024)throw Error('Choose a bounded GLB and its fresh World export audit JSON.');
  const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
  const binding=JSON.parse(await auditFile.text()),animation=animationValue.trim()===''?null:Number(animationValue),mapping=mappingValue.trim()===''?null:mappingValue.split(',').map(v=>v.trim()===''?NaN:Number(v));
  if(animation!==null&&(!Number.isSafeInteger(animation)||animation<0||animation>63)||mapping!==null&&(mapping.length!==held.preview.channel_count||mapping.some(v=>!Number.isSafeInteger(v)||v<0||v>4095)||new Set(mapping).size!==mapping.length))throw Error('Choose a bounded clip index and one distinct node index per rigid object, or leave mapping blank for native object identities.');
  return {...context,frame_index:held.frame_index,glb_base64:btoa(binary),binding,shared_record:true,animation_index:animation,object_nodes:mapping};
}

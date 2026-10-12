import {placementDigest} from './worldmap-placement-replay.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=()=>{throw Error('PLAYER playback differs from the inspected layer and original action stream.');};

export async function createPlayerActionSampler(value,report,record,raw,clip){
 const current=raw.layer==='current',expectedClip=current?raw.action_clips?.[clip.action_slot]:clip,effective=current?raw.effective_file_sha256:record.data.source_record.sha256;
 if(value?.schema_version!=='legaia.player-playback.v1'||value.project_path!==report.project_path||value.project_source_key!==report.project_source_key||value.catalog_source_key!==report.catalog.source_key||!same(value.record,record.data)||!same(value.assembly,raw.assembly)||!same(value.clip,clip)||!same(record.data.actions[clip.action_slot],clip)||value.layer!==raw.layer||value.effective_file_sha256!==effective||(current&&!same(value.current_clip,expectedClip))||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||raw.geometry?.posed!==false||!clip.preview_supported||typeof value.action_base64!=='string'||value.action_base64.length>200000)fail();
 const bytes=Uint8Array.from(atob(value.action_base64),c=>c.charCodeAt(0));
 if(bytes.length!==clip.source_record.byte_length||bytes.length!==2+clip.part_count*clip.frame_count*9||bytes[0]!==clip.part_count||bytes[1]!==clip.frame_count||await placementDigest(bytes)!==expectedClip?.source_record.sha256||raw.assembly.animation_part_indices.length!==raw.geometry.objects.length||raw.assembly.animation_part_indices.some(v=>!Number.isSafeInteger(v)||v<0||v>=clip.part_count))fail();
 return samplePlayerActionBytes(bytes,raw.geometry,raw.assembly.animation_part_indices);
}

// Pure display math for already-qualified source or Proposed bytes. This does
// not register an authored layer; the caller owns source/Review qualification.
export function samplePlayerActionBytes(input,geometry,parts){
 if(!(input instanceof Uint8Array)||!input[0]||!input[1]||input.length!==2+input[0]*input[1]*9||geometry?.posed!==false||!Array.isArray(parts)||parts.length!==geometry.objects?.length||parts.some(p=>!Number.isSafeInteger(p)||p<0||p>=input[0]))fail();
 const bytes=new Uint8Array(input),base=structuredClone(geometry),mapping=[...parts],signed=v=>v&2048?v-4096:v,frameCount=bytes[1],partCount=bytes[0];
 return {frameCount,initialFrame:0,sample(frame){
  if(!Number.isSafeInteger(frame)||frame<0||frame>=frameCount)fail();
  const transforms=mapping.map((part,i)=>{const at=2+(frame*partCount+part)*9,b=bytes.subarray(at,at+9);return {object_index:i,part_index:part,translation:[signed(b[0]|(b[2]&15)<<8),signed(b[1]|(b[2]>>4)<<8),signed(b[3]|(b[5]&15)<<8)],rotation_psx:[b[4]|(b[5]>>4)<<8,b[6]|(b[8]&15)<<8,b[7]|(b[8]>>4)<<8]};});
  const geometry=structuredClone(base);
  for(const [i,o] of geometry.objects.entries()){
   const tr=transforms[i],[rx,ry,rz]=tr.rotation_psx.map(v=>v*Math.PI/2048),sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz);
   for(let j=o.vertex_start;j<o.vertex_start+o.vertex_count;j++){
    let [x,y,z]=base.vertices[j];[y,z]=[y*cx-z*sx,y*sx+z*cx];[x,z]=[x*cy+z*sy,-x*sy+z*cy];[x,y]=[x*cz-y*sz,x*sz+y*cz];geometry.vertices[j]=[x+tr.translation[0],y+tr.translation[1],z+tr.translation[2]];
   }
  }
  geometry.bounds={min:[0,1,2].map(i=>Math.min(...geometry.vertices.map(v=>v[i]))),max:[0,1,2].map(i=>Math.max(...geometry.vertices.map(v=>v[i])))};
  geometry.posed=true;geometry.coordinate_system='retail_psx_actor_local_y_down';delete geometry.triangle_normals;delete geometry.normal_preview;
  return {geometry,object_transforms:transforms,frame_index:frame};
 }};
}

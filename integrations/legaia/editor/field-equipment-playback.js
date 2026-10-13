import {qualifyFieldEquipment} from './field-equipment.js';
import {placementDigest} from './worldmap-placement-replay.js';

const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=()=>{throw Error('Field equipment playback differs from its qualified source record, variant or frame.');};
const bytes=(s,max)=>{if(typeof s!=='string'||s.length>Math.ceil(max/3)*4)fail();const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));if(b.length>max)fail();return b;};

function transformsAt(record,frame){
 const signed=n=>n&2048?n-4096:n;
 return Array.from({length:10},(_,object_index)=>{
  const at=8+(frame*10+object_index)*8,d=record.slice(at,at+8);
  return {object_index,translation:[signed(d[0]+(d[2]&15)*256),signed(d[1]+(d[2]>>4)*256),signed(d[3]+(d[4]&15)*256)],rotation_psx:[d[5]*16,d[6]*16,d[7]*16],opaque_nibble:d[4]>>4};
 });
}

function pose(base,transforms,frame){
 const vertices=new Array(base.vertices.length);
 for(const [i,obj] of base.objects.entries()){
  if(obj.object_index!==i||!Number.isSafeInteger(obj.vertex_start)||!Number.isSafeInteger(obj.vertex_count)||obj.vertex_start<0||obj.vertex_count<0||obj.vertex_start+obj.vertex_count>vertices.length)fail();
  const tr=transforms[i],[rx,ry,rz]=tr.rotation_psx.map(n=>n*Math.PI/2048),sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz);
  for(let j=obj.vertex_start;j<obj.vertex_start+obj.vertex_count;j++){
   if(vertices[j]!==undefined||base.vertices[j]?.length!==3||base.vertices[j].some(n=>!Number.isFinite(n)))fail();
   let [x,y,z]=base.vertices[j];[y,z]=[y*cx-z*sx,y*sx+z*cx];[x,z]=[x*cy+z*sy,-x*sy+z*cy];[x,y]=[x*cz-y*sz,x*sz+y*cz];vertices[j]=[x+tr.translation[0],y+tr.translation[1],z+tr.translation[2]];
  }
 }
 for(let i=0;i<vertices.length;i++)if(vertices[i]===undefined)fail();
 const geometry={...structuredClone(base),vertices,bounds:{min:[0,1,2].map(i=>Math.min(...vertices.map(v=>v[i]))),max:[0,1,2].map(i=>Math.max(...vertices.map(v=>v[i])))},frame_index:frame,object_transforms:transforms,posed:true,coordinate_system:'retail_psx_actor_local_y_down'};
 delete geometry.triangle_normals;delete geometry.normal_preview;delete geometry.frames;
 return geometry;
}

export async function createFieldEquipmentPlaybackSampler(value,context){
 if(!value||!same(Object.keys(value).sort(),['schema_version','preview','source_record','bank_base64','bank_sha256','bank_record_count','record_base64','record_sha256','frame_count','channel_count','active_object_indices','timing','looping','read_only','project_changed','gameplay_verified'].sort()))fail();
 const held=await qualifyFieldEquipment(value?.preview,context),source=value.source_record,slot=held.geometry.equipment_variant.party_slot,index=slot*7+(context.clipId==='idle'?1:0);
 if(value.schema_version!=='legaia.field-equipment-playback.v1'||!['idle','walk'].includes(context.clipId)||!same(source,held.animation.source_record)||value.bank_record_count!==23||value.channel_count!==10||!same(value.active_object_indices,Array.from({length:10},(_,i)=>i))||value.timing!=='caller_selected_display_rate_not_native_cadence'||value.looping!=='one_pass_display_only'||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||source.prot_entry_index!==874||source.container_section!==1||source.record_index!==index||source.byte_coordinate_space!=='decoded_lzs_section'||source.disc?.sha256!==held.source_record.disc.sha256||held.animation.semantic_id!==`animation://legaia/field-locomotion/${String(index).padStart(4,'0')}`||held.animation.bone_count!==10||held.animation.association?.record_index!==index||held.animation.association?.pack_slot!==slot||!same(held.animation.association?.active_object_indices,value.active_object_indices))fail();
 const bank=bytes(value.bank_base64,4*1024*1024);if(bank.length<96||await placementDigest(bank)!==value.bank_sha256||source.containing_size!==bank.length)fail();
 const view=new DataView(bank.buffer);if(view.getUint32(0,true)!==23)fail();
 const offsets=Array.from({length:23},(_,i)=>view.getUint32(4+i*4,true));if(offsets[0]<96||offsets.at(-1)>=bank.length||offsets.some((n,i)=>i&&n<=offsets[i-1]))fail();
 const start=offsets[index],end=offsets[index+1]??bank.length,record=bank.slice(start,end),declared=bytes(value.record_base64,4*1024*1024);if(source.byte_offset!==start||source.byte_length!==end-start||record.length<16||!same(Array.from(record),Array.from(declared))||await placementDigest(record)!==value.record_sha256)fail();
 const r=new DataView(record.buffer),a=r.getUint16(0,true),count=r.getUint16(2,true),flags=r.getUint16(6,true);if((a&255)!==10||a>>8>1||r.getUint16(4,true)!==0x080c||![2,4].includes(flags)||count<1||count>512||record.length!==16+10*count*8||record.slice(-8).some(n=>n)||count!==value.frame_count||count!==held.animation.frame_count||a!==held.animation.header_a||flags!==held.animation.header_flags||!Number.isSafeInteger(context.frameIndex)||context.frameIndex<0||context.frameIndex>=count)fail();
 const native=transformsAt(record,context.frameIndex);if(!same(native,held.geometry.object_transforms))fail();
 const base=structuredClone(held.base_geometry),initial=pose(base,native,context.frameIndex);
 if(initial.vertices.length!==held.geometry.vertices.length||initial.vertices.some((v,i)=>v.some((n,k)=>!Number.isFinite(held.geometry.vertices[i]?.[k])||Math.abs(n-held.geometry.vertices[i][k])>1e-7)))fail();
 return {frameCount:count,initialFrame:context.frameIndex,recordHash:value.record_sha256,sample(frame){if(!Number.isSafeInteger(frame)||frame<0||frame>=count)fail();const transforms=transformsAt(record,frame);return {frame_index:frame,object_transforms:transforms,geometry:pose(base,transforms,frame)};}};
}

import {worldNativeGroups} from './worldmap-model-face-replay.js';
import {worldModelContentAudit} from './worldmap-model-content.js';
const fail=m=>{throw Error(m);},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===k.sort().join(','),identity=(v,kind)=>typeof v==='string'&&new RegExp('^'+kind+'://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$').test(v);
export function worldObjectIdentities(bytes,hash){
 worldModelContentAudit(bytes,bytes);const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 return new Map(Array.from({length:v.getUint32(8,true)},(_,object_index)=>{const object_id=`object://source/${hash}/${object_index}`;return [object_id,{object_id,origin:'source',object_index,source_object_index:object_index}];}));
}
export function allocateWorldObjects(source,faces,objects,requests,reservedGroups=new Set()){
 const native=worldNativeGroups(source),v=new DataView(source.buffer,source.byteOffset,source.byteLength),oldCount=v.getUint32(8,true),objectIds=new Set(objects.keys()),groupIds=new Set(reservedGroups),faceIds=new Set(faces.keys()),donors=[];let faceCount=0,groupCount=0,vectorCount=0,payloadGrowth=0;
 if(!Array.isArray(requests)||!requests.length||requests.length>64||oldCount+requests.length>1024)fail('World object replay requires bounded clone requests.');
 for(const request of requests){
  if(!exact(request,['object_id','donor_object_id','groups'])||!identity(request.object_id,'object')||objectIds.has(request.object_id)||typeof request.donor_object_id!=='string'||!objects.has(request.donor_object_id))fail('World object identity or donor differs.');objectIds.add(request.object_id);
  const owner=objects.get(request.donor_object_id).object_index,groups=native.filter(g=>g.owner===owner);
  if(!Number.isInteger(owner)||owner<0||owner>=oldCount||!Array.isArray(request.groups)||request.groups.length!==groups.length||(groupCount+=groups.length)>64)fail('World object requires complete native donor groups.');
  for(const [ordinal,group] of request.groups.entries()){
   const old=groups[ordinal];if(!old.count||!exact(group,['group_id','faces'])||!identity(group.group_id,'group')||groupIds.has(group.group_id)||!Array.isArray(group.faces)||group.faces.length!==old.count||(faceCount+=group.faces.length)>512)fail('World object group identity or coverage differs.');groupIds.add(group.group_id);
   for(const [index,face] of group.faces.entries()){
    if(!exact(face,['face_id','donor_face_id'])||!identity(face.face_id,'face')||faceIds.has(face.face_id)||typeof face.donor_face_id!=='string')fail('World object face identity differs.');faceIds.add(face.face_id);
    const donor=faces.get(face.donor_face_id);if(!donor||donor.owner!==owner||donor.group!==ordinal||donor.index!==old.first+index)fail('World object face donor order differs.');
   }
  }
  const header=12+owner*28,vert=v.getUint32(header,true),nv=v.getUint32(header+4,true),normal=v.getUint32(header+8,true),nn=v.getUint32(header+12,true),prim=v.getUint32(header+16,true);
  if(!nv)fail('World object donor requires native vertices.');const end=Math.min(vert+12,nn?normal+12:source.length),size=end-prim-12;if(size<4)fail('World object primitive allocation differs.');vectorCount+=nv+nn;payloadGrowth+=size+(nv+nn)*8;donors.push({request,groups,header,vert,nv,normal,nn,prim,end,size});
 }
 const tableEnd=12+oldCount*28,tableGrowth=requests.length*28,padding=(4-source.length%4)%4,length=source.length+tableGrowth+padding+payloadGrowth;
 if(length>4*1024*1024)fail('World object replay exceeds its native byte budget.');const candidate=new Uint8Array(length),output=new DataView(candidate.buffer);candidate.set(source.subarray(0,tableEnd));candidate.set(source.subarray(tableEnd),tableEnd+tableGrowth);output.setUint32(8,oldCount+requests.length,true);
 for(let owner=0;owner<oldCount;owner++){const header=12+owner*28;for(const field of [0,8,16])if(field===16||v.getUint32(header+field+4,true))output.setUint32(header+field,v.getUint32(header+field,true)+tableGrowth,true);}
 let at=source.length+tableGrowth+padding;const updatedFaces=new Map([...faces].map(([id,f])=>[id,{...f}])),updatedObjects=new Map([...objects].map(([id,o])=>[id,{...o}])),groupRecords=[];
 for(const [ordinal,donor] of donors.entries()){
  const {request,groups,header,vert,nv,normal,nn,prim,end}=donor,owner=oldCount+ordinal,primitiveAt=at;candidate.set(source.subarray(prim+12,end),at);at+=donor.size;const vertexAt=at;candidate.set(source.subarray(vert+12,vert+12+nv*8),at);at+=nv*8;const normalAt=at;candidate.set(source.subarray(normal+12,normal+12+nn*8),at);at+=nn*8;
  const newHeader=12+owner*28;candidate.set(source.subarray(header,header+28),newHeader);output.setUint32(newHeader,vertexAt-12,true);output.setUint32(newHeader+8,nn?normalAt-12:normal,true);output.setUint32(newHeader+16,primitiveAt-12,true);
  updatedObjects.set(request.object_id,{object_id:request.object_id,origin:'authored',object_index:owner,donor_object_id:request.donor_object_id});
  for(const [index,group] of request.groups.entries()){
   const old=groups[index];groupRecords.push({group_id:group.group_id,object_index:owner,origin_group_index:index,donor_face_id:group.faces[0].donor_face_id,flags:v.getUint16(old.at+2,true),mode:v.getUint8(old.at+7)});
   for(const [n,face] of group.faces.entries())updatedFaces.set(face.face_id,{owner,group:index,index:old.first+n,donor_id:face.donor_face_id});
  }
 }
 if(at!==length)fail('World object allocation length differs.');worldModelContentAudit(candidate,candidate);return {bytes:candidate,faces:updatedFaces,objects:updatedObjects,groups:groupRecords,vectorCount};
}

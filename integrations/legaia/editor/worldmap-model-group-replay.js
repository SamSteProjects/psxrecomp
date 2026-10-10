import {worldNativeGroups,writeWorldFaceFields} from './worldmap-model-face-replay.js';
import {worldModelContentAudit} from './worldmap-model-content.js';
const fail=m=>{throw Error(m);},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===k.sort().join(','),identity=(v,kind)=>typeof v==='string'&&new RegExp('^'+kind+'://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$').test(v);
export function allocateWorldGroups(source,faces,requests,reserved=new Set()){
 const groups=worldNativeGroups(source),view=new DataView(source.buffer,source.byteOffset,source.byteLength),pending=new Map(),ids=new Set(),faceIds=new Set();let total=0,growth=0;
 if(!Array.isArray(requests)||!requests.length||requests.length>64)fail('World group replay requires bounded requests.');
 for(const request of requests){
  if(!exact(request,['group_id','donor_face_id','faces'])||!identity(request.group_id,'group')||reserved.has(request.group_id)||ids.has(request.group_id)||!Array.isArray(request.faces)||!request.faces.length)fail('World group identity or fields differ.');ids.add(request.group_id);
  const donor=faces.get(request.donor_face_id),group=donor&&groups.find(g=>g.owner===donor.owner&&g.index===donor.group);if(!group)fail('World group donor differs.');
  if((total+=request.faces.length)>512)fail('World group face budget exceeded.');const payload=new Uint8Array(8+(request.faces.length+1)*group.stride);payload.set(source.subarray(group.at,group.at+8));new DataView(payload.buffer).setUint16(0,request.faces.length,true);
  for(const [n,face] of request.faces.entries()){
   if(!exact(face,['face_id','donor_face_id','fields'])||!identity(face.face_id,'face')||faces.has(face.face_id)||faceIds.has(face.face_id))fail('World group face identity differs.');faceIds.add(face.face_id);
   const packet=faces.get(face.donor_face_id);if(!packet||packet.owner!==donor.owner||packet.group!==donor.group||!face.fields||typeof face.fields!=='object'||Array.isArray(face.fields)||!Object.hasOwn(face.fields,'vertices')||Object.keys(face.fields).some(k=>!['vertices','uvs','colors','normal_indices'].includes(k)))fail('World group face donor or fields differ.');
   const at=group.at+8+(packet.index-group.first)*group.stride;payload.set(source.subarray(at,at+group.stride),8+n*group.stride);
  }
  payload.set(source.subarray(group.at+8+group.count*group.stride,group.at+8+(group.count+1)*group.stride),8+request.faces.length*group.stride);
  if(!pending.has(donor.owner))pending.set(donor.owner,[]);pending.get(donor.owner).push({request,group,payload});growth+=payload.length;
 }
 if(source.length+growth>4*1024*1024)fail('World group native byte budget exceeded.');const events=[];
 for(const [owner,rows] of pending){const last=groups.filter(g=>g.owner===owner).at(-1),at=last.at+8+(last.count+1)*last.stride;if(view.getUint32(at,true)!==0)fail('World group terminator differs.');events.push({owner,at,rows,size:rows.reduce((n,r)=>n+r.payload.length,0)});}
 events.sort((a,b)=>a.at-b.at);const candidate=new Uint8Array(source.length+growth);let before=0,position=0;
 for(const event of events){candidate.set(source.subarray(before,event.at),position);position+=event.at-before;for(const row of event.rows){candidate.set(row.payload,position);position+=row.payload.length;}before=event.at;}candidate.set(source.subarray(before),position);
 const output=new DataView(candidate.buffer),relocate=at=>at+events.reduce((n,e)=>n+(e.at<=at?e.size:0),0),updated=new Map([...faces].map(([id,f])=>[id,{...f}])),newRows=[],groupRecords=[];
 for(let owner=0;owner<view.getUint32(8,true);owner++){const header=12+owner*28;for(const field of [0,8,16]){const old=view.getUint32(header+field,true);if(field===16||view.getUint32(header+field+4,true))output.setUint32(header+field,relocate(old+12)-12,true);}let index=view.getUint32(header+20,true),ordinal=groups.filter(g=>g.owner===owner).length;for(const row of pending.get(owner)??[]){groupRecords.push({group_id:row.request.group_id,object_index:owner,origin_group_index:ordinal,donor_face_id:row.request.donor_face_id,flags:view.getUint16(row.group.at+2,true),mode:view.getUint8(row.group.at+7)});for(const face of row.request.faces){const value={owner,group:ordinal,index:index++,donor_id:face.donor_face_id};updated.set(face.face_id,value);newRows.push({...value,fields:face.fields});}ordinal++;}output.setUint32(header+20,index,true);}
 writeWorldFaceFields(candidate,newRows);worldModelContentAudit(candidate,candidate);return {bytes:candidate,faces:updated,groups:groupRecords};
}

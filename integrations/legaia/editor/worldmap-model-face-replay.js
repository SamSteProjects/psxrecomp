import {worldModelContentAudit,worldModelContentFields} from './worldmap-model-content.js';
const fail=m=>{throw Error(m);},exact=(v,k)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===k.sort().join(',');
function groups(bytes){
 worldModelContentAudit(bytes,bytes);const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),rows=[];
 for(let owner=0;owner<v.getUint32(8,true);owner++){const header=12+owner*28;let at=12+v.getUint32(header+16,true),first=0,index=0;
 while(v.getUint16(at,true)||v.getUint16(at+2,true)){const count=v.getUint16(at,true),stride=v.getUint8(at+5)*4;rows.push({owner,index,at,count,stride,first});at+=8+(count+1)*stride;first+=count;index++;}}
 return rows;
}
export function worldFaceIdentities(bytes,hash){
 const faces=new Map();for(const g of groups(bytes))for(let n=0;n<g.count;n++){const id=`face://source/${hash}/${g.owner}/${g.first+n}`;faces.set(id,{owner:g.owner,group:g.index,index:g.first+n});}return faces;
}
export function addWorldFaces(source,faces,requests){
 const rows=groups(source),v=new DataView(source.buffer,source.byteOffset,source.byteLength),additions=new Map(),ids=new Set();
 if(!Array.isArray(requests)||!requests.length||requests.length>512)fail('World face replay requires bounded additions.');
 for(const r of requests){
  if(!exact(r,['face_id','donor_face_id','fields'])||!/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(r.face_id)||ids.has(r.face_id)||faces.has(r.face_id))fail('World face authored identity differs.');
  const donor=faces.get(r.donor_face_id),g=donor&&rows.find(g=>g.owner===donor.owner&&g.index===donor.group);
  if(!g||!r.fields||typeof r.fields!=='object'||Array.isArray(r.fields)||!Object.hasOwn(r.fields,'vertices')||Object.keys(r.fields).some(k=>!['vertices','uvs','colors','normal_indices'].includes(k)))fail('World face donor or typed fields differ.');
  ids.add(r.face_id);const key=g.owner+'/'+g.index;if(!additions.has(key))additions.set(key,[]);additions.get(key).push({request:r,donor});
 }
 const events=[];let growth=0;
 for(const g of rows){const added=additions.get(g.owner+'/'+g.index)??[];if(g.count+added.length>65535)fail('World face native group budget exceeded.');if(added.length){events.push({at:g.at+8+g.count*g.stride,g,added});growth+=added.length*g.stride;}}
 if(source.length+growth>4*1024*1024)fail('World face native byte budget exceeded.');
 const candidate=new Uint8Array(source.length+growth);let before=0,position=0;
 for(const e of events.sort((a,b)=>a.at-b.at)){candidate.set(source.subarray(before,e.at),position);position+=e.at-before;for(const a of e.added){const start=e.g.at+8+(a.donor.index-e.g.first)*e.g.stride;candidate.set(source.subarray(start,start+e.g.stride),position);position+=e.g.stride;}before=e.at;}
 candidate.set(source.subarray(before),position);const output=new DataView(candidate.buffer),relocate=at=>at+events.reduce((sum,e)=>sum+(e.at<=at?e.added.length*e.g.stride:0),0);
 for(let owner=0;owner<v.getUint32(8,true);owner++){const header=12+owner*28;for(const field of [0,8,16]){const old=v.getUint32(header+field,true),count=v.getUint32(header+field+4,true);if(field===16||count)output.setUint32(header+field,relocate(old+12)-12,true);}output.setUint32(header+20,v.getUint32(header+20,true)+events.filter(e=>e.g.owner===owner).reduce((n,e)=>n+e.added.length,0),true);}
 for(const e of events)output.setUint16(relocate(e.g.at),e.g.count+e.added.length,true);
 const updated=new Map(),newRows=[];for(const g of rows){const prefix=events.filter(e=>e.g.owner===g.owner&&e.g.index<g.index).reduce((n,e)=>n+e.added.length,0);for(const [id,face] of faces)if(face.owner===g.owner&&face.group===g.index)updated.set(id,{...face,index:face.index+prefix});for(const [n,a] of (additions.get(g.owner+'/'+g.index)??[]).entries()){const face={owner:g.owner,group:g.index,index:g.first+g.count+prefix+n};updated.set(a.request.face_id,face);newRows.push({...face,fields:a.request.fields});}}
 const fields=worldModelContentFields(candidate);
 for(const row of newRows){const native=fields.filter(f=>f.kind==='primitive'&&f.object_index===row.owner&&f.primitive_index===row.index);
  for(const [name,value] of Object.entries(row.fields)){const kind={vertices:'vertex_index',uvs:'uv',colors:'color',normal_indices:'normal_index'}[name],selected=native.filter(f=>f.field===kind),corners=selected.reduce((n,f)=>Math.max(n,f.corner_index+1),0),width=name==='uvs'?2:name==='colors'?3:1;
   if(!selected.length||!Array.isArray(value)||value.length!==corners||value.some(v=>width===1?!Number.isSafeInteger(v):!Array.isArray(v)||v.length!==width||v.some(n=>!Number.isSafeInteger(n))))fail('World face typed field coverage differs.');
   for(const f of selected){const number=width===1?value[f.corner_index]:value[f.corner_index][(name==='uvs'?'uv':'rgb').indexOf(f.axis)],maximum=f.reference_count===null?255:Math.min(f.reference_count-1,8191);if(number<0||number>maximum)fail('World face field exceeds native bounds.');if(f.width===1)output.setUint8(f.byte_offset,number);else output.setUint16(f.byte_offset,number*8,true);}
  }
 }
 worldModelContentAudit(candidate,candidate);return {bytes:candidate,faces:updated};
}

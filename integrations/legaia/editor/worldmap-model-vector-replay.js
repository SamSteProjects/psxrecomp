import {allocateWorldObjects,worldObjectIdentities} from './worldmap-model-object-replay.js';
import {allocateWorldGroups} from './worldmap-model-group-replay.js';
import {worldFaceIdentities,addWorldFaces} from './worldmap-model-face-replay.js';
import {worldModelContentAudit} from './worldmap-model-content.js';
export const vectorDigest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===keys.sort().join(','),fail=m=>{throw Error(m);};
export function allocateWorldVectors(source,requests){
 worldModelContentAudit(source,source);
 const view=new DataView(source.buffer,source.byteOffset,source.byteLength),objects=view.getUint32(8,true),tables=new Map(),events=new Map();let added=0;
 if(!Array.isArray(requests)||!requests.length||requests.length>2048)fail('World vector replay requires bounded requests.');
 for(const request of requests){
  if(!exact(request,['object_index','kind','vectors'])||!Number.isInteger(request.object_index)||request.object_index<0||request.object_index>=objects||!['vertices','normals'].includes(request.kind)||!Array.isArray(request.vectors)||!request.vectors.length||request.vectors.some(row=>!Array.isArray(row)||row.length!==3||row.some(v=>!Number.isInteger(v)||v<-32768||v>32767)))fail('World vector replay row ownership differs.');
  const id=`${request.object_index}/${request.kind}`,field=request.kind==='vertices'?0:8,header=12+28*request.object_index,count=view.getUint32(header+field+4,true),at=count?12+view.getUint32(header+field,true)+count*8:source.length;
  if(tables.has(id)||(added+=request.vectors.length)>4096||count+request.vectors.length>8192)fail('World vector replay table or row budget differs.');
  const payload=new Uint8Array(request.vectors.length*8),words=new DataView(payload.buffer);request.vectors.forEach((row,n)=>row.forEach((value,a)=>words.setInt16(n*8+a*2,value,true)));
  const table={owner:request.object_index,kind:request.kind,count,at,payload};tables.set(id,table);if(!events.has(at))events.set(at,[]);events.get(at).push(table);
 }
 if(source.length+added*8>4*1024*1024)fail('World vector replay exceeds its byte budget.');
 const candidate=new Uint8Array(source.length+added*8);let before=0,position=0;
 for(const [at,rows] of [...events].sort((a,b)=>a[0]-b[0])){
  candidate.set(source.subarray(before,at),position);position+=at-before;
  rows.sort((a,b)=>Number(!a.count)-Number(!b.count)||a.owner-b.owner||(a.kind<b.kind?-1:a.kind>b.kind?1:0));
  for(const row of rows){row.start=position;candidate.set(row.payload,position);position+=row.payload.length;}before=at;
 }
 candidate.set(source.subarray(before),position);const output=new DataView(candidate.buffer),relocate=offset=>offset+[...events].reduce((sum,[at,rows])=>sum+(at<=offset?rows.reduce((n,row)=>n+row.payload.length,0):0),0);
 for(let owner=0;owner<objects;owner++)for(const field of [0,8,16]){
  const header=12+owner*28,old=view.getUint32(header+field,true),count=view.getUint32(header+field+4,true),table=tables.get(`${owner}/${field===0?'vertices':field===8?'normals':''}`),next=table&&!count?table.start-12:field===16||count?relocate(old+12)-12:old;
  output.setUint32(header+field,next,true);if(table)output.setUint32(header+field+4,count+table.payload.length/8,true);
 }
 worldModelContentAudit(candidate,candidate);return candidate;
}
export async function replayWorldVectors(retail,base,binding,{withFaces=false}={}){
 const fields=['format','source_scene_id','source_sha256','asset_sha256','byte_length','base_binding','ledger'];
 if(!exact(binding,fields)||!['world-tmd-vector-allocation-v1','world-tmd-vector-content-v1','world-tmd-face-addition-v1','world-tmd-group-allocation-v1','world-tmd-object-allocation-v1'].includes(binding.format)||!/^worldmap:\/\/map0[123]\/models$/.test(binding.source_scene_id)||binding.source_sha256!==await vectorDigest(retail)||base.length!==retail.length)fail('World vector retained base ownership differs.');
 const retained=binding.base_binding;
 if(retained===null){if(await vectorDigest(base)!==binding.source_sha256)fail('World vector unedited base differs.');}
 else{
  if(!exact(retained,['format','source_scene_id','source_sha256','asset_sha256','byte_length'])||!['tmd-shape','tmd-content-v1','tmd-content-v2','tmd-content-v3'].includes(retained.format)||retained.source_scene_id!==binding.source_scene_id||retained.source_sha256!==binding.source_sha256||retained.byte_length!==base.length||retained.asset_sha256!==await vectorDigest(base))fail('World vector retained binding differs.');
  const changes=worldModelContentAudit(retail,base,{content:retained.format!=='tmd-shape'});
  if(retained.format==='tmd-content-v1'&&changes.some(r=>r.kind==='primitive_group'||r.kind==='primitive'&&['clut','tpage'].includes(r.field))||retained.format!=='tmd-content-v3'&&changes.some(r=>r.kind==='primitive'&&r.field==='normal_index'))fail('World vector base content exceeds binding scope.');
 }
 const ledger=binding.ledger,objected=binding.format==='world-tmd-object-allocation-v1',grouped=objected||binding.format==='world-tmd-group-allocation-v1',topology=grouped||binding.format==='world-tmd-face-addition-v1',batches=topology&&ledger?.schema_version==='legaia.model-face-addition-ledger.v1',member=batches?'batches':'operations';
 if(!exact(ledger,['schema_version','source_sha256','source_byte_length',member])||!(objected?['legaia.model-face-addition-ledger.v7']:grouped?['legaia.model-face-addition-ledger.v6']:topology?['legaia.model-face-addition-ledger.v1','legaia.model-face-addition-ledger.v2','legaia.model-face-addition-ledger.v5']:['legaia.model-face-addition-ledger.v5']).includes(ledger.schema_version)||ledger.source_sha256!==await vectorDigest(base)||ledger.source_byte_length!==base.length||!Array.isArray(ledger[member])||!ledger[member].length||ledger[member].length>(batches?8:64)||new TextEncoder().encode(JSON.stringify(ledger)).length>2*1024*1024)fail('World native ledger ownership differs.');
 const operations=batches?ledger.batches.map(op=>{if(!exact(op,['input_sha256','proposed_sha256','additions']))fail('World face batch schema differs.');return {...op,kind:'add_faces'};}):ledger.operations;
 let faces=worldFaceIdentities(base,ledger.source_sha256),faceCount=0,faceBatches=0;
 let current=base,total=0,objects=objected?worldObjectIdentities(base,ledger.source_sha256):null,objectCount=0,objectBatches=0;
 let allocations=0,edits=0,groupCount=0;const groupIds=new Set(),groupRecords=[],ranks=new Map([...faces.keys()].map((id,i)=>[id,i]));let groupBatches=0;
 for(const operation of operations){
  if(operation?.input_sha256!==await vectorDigest(current))fail('World ledger operation source differs.');
  if(operation.kind==='allocate_vectors'){
   if(!exact(operation,['kind','input_sha256','proposed_sha256','requests']))fail('World vector operation schema differs.');
   current=allocateWorldVectors(current,operation.requests);total+=operation.requests.reduce((sum,r)=>sum+r.vectors.length,0);allocations++;
  }else if(operation.kind==='add_faces'&&topology){
   if(!exact(operation,['kind','input_sha256','proposed_sha256','additions'])||++faceBatches>8||!Array.isArray(operation.additions)||(faceCount+=operation.additions.length)>512)fail('World face operation schema or budget differs.');
   const added=addWorldFaces(current,faces,operation.additions);current=added.bytes;faces=added.faces;
  }else if(operation.kind==='allocate_groups'&&grouped){
   if(!exact(operation,['kind','input_sha256','proposed_sha256','requests'])||!Array.isArray(operation.requests)||(groupCount+=operation.requests.length)>64||++faceBatches>8||(faceCount+=operation.requests.reduce((n,r)=>n+(Array.isArray(r?.faces)?r.faces.length:513),0))>512)fail('World group operation schema or budget differs.');
   const added=allocateWorldGroups(current,faces,operation.requests,groupIds);current=added.bytes;faces=added.faces;groupBatches++;for(const r of operation.requests){groupIds.add(r.group_id);groupRecords.push(added.groups.find(g=>g.group_id===r.group_id));}
  }else if(operation.kind==='allocate_objects'&&objected){
   if(!exact(operation,['kind','input_sha256','proposed_sha256','requests'])||!Array.isArray(operation.requests)||(objectCount+=operation.requests.length)>64||++faceBatches>8)fail('World object operation schema or budget differs.');
   const added=allocateWorldObjects(current,faces,objects,operation.requests,groupIds);current=added.bytes;faces=added.faces;objects=added.objects;objectBatches++;total+=added.vectorCount;allocations++;
   groupCount+=added.groups.length;faceCount+=operation.requests.reduce((n,r)=>n+r.groups.reduce((m,g)=>m+g.faces.length,0),0);if(groupCount>64||faceCount>512)fail('World cloned group/face budget exceeded.');if(added.groups.length)groupBatches++;for(const g of added.groups){groupIds.add(g.group_id);groupRecords.push(g);}
  }else if(operation.kind==='edit_content'&&['world-tmd-vector-content-v1','world-tmd-face-addition-v1','world-tmd-group-allocation-v1','world-tmd-object-allocation-v1'].includes(binding.format)){
   if(!exact(operation,['kind','input_sha256','proposed_sha256','runs'])||!Array.isArray(operation.runs)||!operation.runs.length||operation.runs.length>600000)fail('World content operation schema differs.');
   const candidate=current.slice();let end=0;
   for(const run of operation.runs){
    if(!exact(run,['offset','before_hex','after_hex'])||!Number.isInteger(run.offset)||run.offset<end||typeof run.before_hex!=='string'||typeof run.after_hex!=='string'||!/^([0-9a-f]{2})+$/.test(run.before_hex)||!/^([0-9a-f]{2})+$/.test(run.after_hex)||run.before_hex.length!==run.after_hex.length||run.offset+run.before_hex.length/2>current.length)fail('World content run ownership differs.');
    for(let n=0;n<run.before_hex.length/2;n++){const before=parseInt(run.before_hex.slice(n*2,n*2+2),16),after=parseInt(run.after_hex.slice(n*2,n*2+2),16);if(current[run.offset+n]!==before||before===after)fail('World content preimage differs.');candidate[run.offset+n]=after;}end=run.offset+run.before_hex.length/2;
   }
   worldModelContentAudit(current,candidate);current=candidate;edits++;
  }else fail('Unsupported World ledger operation.');
  for(const id of operation.kind==='add_faces'?operation.additions.map(r=>r.face_id):operation.kind==='allocate_groups'?operation.requests.flatMap(r=>r.faces.map(f=>f.face_id)):operation.kind==='allocate_objects'?operation.requests.flatMap(r=>r.groups.flatMap(g=>g.faces.map(f=>f.face_id))):[])if(!ranks.has(id))ranks.set(id,ranks.size);
  if(total>4096||operation.proposed_sha256!==await vectorDigest(current))fail('World vector operation output differs.');
 }
 if(objected?!objectCount:grouped?!groupCount:topology?!faceCount:!allocations||binding.format==='world-tmd-vector-content-v1'&&!edits)fail('World content binding lacks its native allocation/edit lineage.');
 if(current.length!==binding.byte_length||await vectorDigest(current)!==binding.asset_sha256)fail('World vector binding output differs.');return withFaces?{bytes:current,faces,groups:groupRecords.map(g=>({...g,current_group_index:g.origin_group_index,face_ids:[...faces].filter(([,f])=>f.owner===g.object_index&&f.group===g.origin_group_index).map(([id])=>id).sort((a,b)=>ranks.get(a)-ranks.get(b))})),groupBatches,...(objected?{objects:[...objects.values()],objectBatches,objectCount,vectorCount:total,vectorBatches:allocations,faceCount,faceBatches}: {})}:current;
}

export function worldContentRuns(before,after){
 worldModelContentAudit(before,after);const runs=[];let at=0;
 const hex=bytes=>Array.from(bytes,n=>n.toString(16).padStart(2,'0')).join('');
 while(at<before.length){if(before[at]===after[at]){at++;continue;}const start=at;while(at<before.length&&before[at]!==after[at])at++;runs.push({offset:start,before_hex:hex(before.subarray(start,at)),after_hex:hex(after.subarray(start,at))});}return runs;
}

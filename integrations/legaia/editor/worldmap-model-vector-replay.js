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
export async function replayWorldVectors(retail,base,binding){
 const fields=['format','source_scene_id','source_sha256','asset_sha256','byte_length','base_binding','ledger'];
 if(!exact(binding,fields)||binding.format!=='world-tmd-vector-allocation-v1'||!/^worldmap:\/\/map0[123]\/models$/.test(binding.source_scene_id)||binding.source_sha256!==await vectorDigest(retail)||base.length!==retail.length)fail('World vector retained base ownership differs.');
 const retained=binding.base_binding;
 if(retained===null){if(await vectorDigest(base)!==binding.source_sha256)fail('World vector unedited base differs.');}
 else{
  if(!exact(retained,['format','source_scene_id','source_sha256','asset_sha256','byte_length'])||!['tmd-shape','tmd-content-v1','tmd-content-v2','tmd-content-v3'].includes(retained.format)||retained.source_scene_id!==binding.source_scene_id||retained.source_sha256!==binding.source_sha256||retained.byte_length!==base.length||retained.asset_sha256!==await vectorDigest(base))fail('World vector retained binding differs.');
  const changes=worldModelContentAudit(retail,base,{content:retained.format!=='tmd-shape'});
  if(retained.format==='tmd-content-v1'&&changes.some(r=>r.kind==='primitive_group'||r.kind==='primitive'&&['clut','tpage'].includes(r.field))||retained.format!=='tmd-content-v3'&&changes.some(r=>r.kind==='primitive'&&r.field==='normal_index'))fail('World vector base content exceeds binding scope.');
 }
 const ledger=binding.ledger;
 if(!exact(ledger,['schema_version','source_sha256','source_byte_length','operations'])||ledger.schema_version!=='legaia.model-face-addition-ledger.v5'||ledger.source_sha256!==await vectorDigest(base)||ledger.source_byte_length!==base.length||!Array.isArray(ledger.operations)||!ledger.operations.length||ledger.operations.length>64||new TextEncoder().encode(JSON.stringify(ledger)).length>2*1024*1024)fail('World vector ledger ownership differs.');
 let current=base,total=0;
 for(const operation of ledger.operations){
  if(!exact(operation,['kind','input_sha256','proposed_sha256','requests'])||operation.kind!=='allocate_vectors'||operation.input_sha256!==await vectorDigest(current))fail('World vector operation source differs.');
  current=allocateWorldVectors(current,operation.requests);total+=operation.requests.reduce((sum,r)=>sum+r.vectors.length,0);
  if(total>4096||operation.proposed_sha256!==await vectorDigest(current))fail('World vector operation output differs.');
 }
 if(current.length!==binding.byte_length||await vectorDigest(current)!==binding.asset_sha256)fail('World vector binding output differs.');return current;
}

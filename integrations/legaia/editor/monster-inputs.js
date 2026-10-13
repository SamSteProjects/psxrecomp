import {placementDigest} from './worldmap-placement-replay.js';

const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const fail=()=>{throw Error('Monster retained input identity or bytes changed.');};

export function qualifyMonsterInputs(report){
 const rows=report.retained_inputs??[],seen=new Set(),owners=new Map();
 if(!Array.isArray(rows)||rows.length>372)fail();
 for(const row of rows){
  const asset=report.catalog.textures.find(r=>r.semantic_id===row.texture_asset_id),receipt=row.source_record;
  if(!asset||!receipt||!['png','stp'].includes(row.kind))fail();
  const keys=['schema_version','asset_id','png_sha256','png_byte_length','stp_sha256','stp_byte_length','baseline_sha256','baseline_byte_length','palette_index','palette_mode','candidate_pool_sha256'];
  if(!same(Object.keys(receipt).sort(),keys.sort())||receipt.schema_version!=='legaia.monster-png-input.v1'||receipt.asset_id!==asset.semantic_id||!hash(receipt.png_sha256)||!hash(receipt.baseline_sha256)||!hash(receipt.candidate_pool_sha256)||!Number.isSafeInteger(receipt.png_byte_length)||receipt.png_byte_length<1||receipt.png_byte_length>8*1024*1024||receipt.baseline_byte_length!==asset.source_record.byte_length||!Number.isSafeInteger(receipt.palette_index)||receipt.palette_index<0||receipt.palette_index>=15||!['existing','rebuild'].includes(receipt.palette_mode))fail();
  if(receipt.stp_sha256===null?receipt.stp_byte_length!==null:!hash(receipt.stp_sha256)||!Number.isSafeInteger(receipt.stp_byte_length)||receipt.stp_byte_length<1||receipt.stp_byte_length>8*1024*1024)fail();
  if(row.semantic_id!==`retained-texture://legaia/monster-archive/${String(asset.monster_id).padStart(4,'0')}/${row.kind}/${receipt[row.kind+'_sha256']}`||seen.has(row.semantic_id)||!hash(row.sha256)||row.sha256!==receipt[row.kind+'_sha256']||row.byte_length!==receipt[row.kind+'_byte_length']||row.asset_kind!=='retained_monster_png'||row.name!==`Monster ${asset.monster_id} Original ${row.kind==='png'?'PNG Input':'STP Mask Input'}`||row.layer!=='historical_authored_input'||!same(row.retail_source,asset.source_record)||!same(row.references,[asset.semantic_id])||!hash(row.current_pool_sha256)||row.relationship!=='historical_import_input_not_final_current_texture'||row.read_only!==true||row.gameplay_verified!==false)fail();
  seen.add(row.semantic_id);const owner=owners.get(asset.semantic_id);
  if(owner&&(!same(owner.receipt,receipt)||owner.current!==row.current_pool_sha256||owner.kinds.has(row.kind)))fail();
  if(owner)owner.kinds.add(row.kind);else owners.set(asset.semantic_id,{receipt,current:row.current_pool_sha256,kinds:new Set([row.kind])});
 }
 for(const {receipt,kinds} of owners.values())if(!kinds.has('png')||kinds.has('stp')!==(receipt.stp_sha256!==null))fail();
}

export function monsterInputRecords(report){return (report.retained_inputs??[]).map(data=>({id:data.semantic_id,type:'texture',label:data.name,source:'Monster Archive / Historical Authored Input',data:structuredClone(data),projectMonsterInput:{projectPath:report.project_path,sourceKey:report.project_source_key,catalogSourceKey:report.catalog.source_key}}));}

export async function qualifyMonsterInputDownload(v,report,record){
 const row=record.data,asset=report.catalog.textures.find(r=>r.semantic_id===row.texture_asset_id);
 if(!asset||v?.schema_version!=='legaia.monster-input-download.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.asset_id!==asset.semantic_id||v.current_pool_sha256!==row.current_pool_sha256||v.kind!==row.kind||!same(v.retained_source,row.source_record)||v.sha256!==row.sha256||v.byte_length!==row.byte_length||v.filename!==`monster-${asset.monster_id}-original-${row.kind}.png`||v.layer!=='historical_authored_input'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||typeof v.png_base64!=='string'||v.png_base64.length>11200000)fail();
 const bytes=Uint8Array.from(atob(v.png_base64),c=>c.charCodeAt(0));
 if(bytes.length!==row.byte_length||await placementDigest(bytes)!==row.sha256)fail();return bytes;
}

export function mountMonsterInput({dialog,record,report,current,busy,onTexture,onError}){
 if(!same(monsterInputRecords(report).find(r=>r.id===record.id),record))fail();
 const node=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;};
 const close=node('button','Close Monster Input'),open=node('button','Open Matching Monster Texture'),download=node('button',record.data.kind==='png'?'Download Original Monster PNG':'Download Original Monster STP Mask'),status=node('p','Original import bytes; later palette edits may differ.'),facts=node('p',`${record.data.byte_length} bytes / SHA256 ${record.data.sha256}`),pre=node('pre',JSON.stringify(record.data,null,2)),details=node('details');
 facts.style.overflowWrap='anywhere';Object.assign(pre.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});details.append(node('summary','Historical Input Provenance'),pre);
 dialog.replaceChildren(node('h2',record.label),facts,status,download,open,details,close);
 let disposed=false,pending=null;const valid=()=>!disposed&&dialog.open&&current();
 function update(){download.disabled=open.disabled=!valid()||busy()||!!pending;}
 download.onclick=async()=>{
  update();if(download.disabled)return;pending=new AbortController();update();
  try{
   const response=await fetch('/api/monster-input-download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.data.texture_asset_id,expected_current_sha256:record.data.current_pool_sha256,kind:record.data.kind}),signal:pending.signal}),text=await response.text();
   if(text.length>12*1024*1024)fail();const v=JSON.parse(text);if(!response.ok)throw Error(v.error||'Monster input download failed');const bytes=await qualifyMonsterInputDownload(v,report,record);if(!valid())return;
   const url=URL.createObjectURL(new Blob([bytes],{type:'image/png'})),a=node('a','');a.href=url;a.download=v.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Exact original import bytes downloaded.';
  }catch(e){if(valid()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}
  finally{pending=null;update();}
 };
 open.onclick=()=>{update();if(!open.disabled)onTexture(record.data.texture_asset_id);};close.onclick=()=>dialog.close();
 dialog.showModal();update();return ()=>{disposed=true;pending?.abort();};
}

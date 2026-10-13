import {placementDigest} from './worldmap-placement-replay.js';
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b)),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),fail=()=>{throw Error('Monster original model input identity or bytes changed.');};

export function qualifyMonsterModelInputs(report){
 const rows=report.retained_model_inputs??[],seen=new Set(),owners=new Map();
 if(!Array.isArray(rows)||rows.length>186*16)fail();
 for(const row of rows){
  const model=report.catalog.models.find(r=>r.semantic_id===row.model_asset_id),receipt=row.source_record,native=receipt?.binding;
  if(!model||!Number.isSafeInteger(row.import_index)||row.import_index<0||row.import_index>=16||!Number.isSafeInteger(row.import_count)||row.import_count<1||row.import_count>16||row.import_index>=row.import_count||!receipt||!same(Object.keys(receipt).sort(),['glb_sha256','glb_byte_length','baseline_sha256','baseline_byte_length','binding','candidate_tmd_sha256','review_key'].sort())||!hash(receipt.glb_sha256)||!Number.isSafeInteger(receipt.glb_byte_length)||receipt.glb_byte_length<28||receipt.glb_byte_length>8*1024*1024||!hash(receipt.baseline_sha256)||receipt.baseline_byte_length!==model.source_record.containing_size||!hash(receipt.candidate_tmd_sha256)||!hash(receipt.review_key)||native?.schema_version!=='legaia.monster-model-glb-binding.v1'||native.asset_id!==model.semantic_id||!same(native.source_record,model.source_record)||native.current_block_sha256!==receipt.baseline_sha256||!hash(native.current_tmd_sha256)||native.profile?.effective_sha256!==native.current_tmd_sha256)fail();
  if(row.semantic_id!==`retained-model://legaia/monster-archive/${String(model.monster_id).padStart(4,'0')}/${String(row.import_index).padStart(2,'0')}/${receipt.glb_sha256}`||seen.has(row.semantic_id)||row.name!==`Monster ${model.monster_id} Original GLB Input ${row.import_index+1}`||row.asset_kind!=='retained_monster_glb'||row.layer!=='historical_authored_input'||row.sha256!==receipt.glb_sha256||row.byte_length!==receipt.glb_byte_length||!hash(row.current_tmd_sha256)||!same(row.retail_source,model.source_record)||!same(row.references,[model.semantic_id])||row.relationship!=='historical_import_input_not_final_current_model'||row.read_only!==true||row.gameplay_verified!==false)fail();
  seen.add(row.semantic_id);let owner=owners.get(model.semantic_id);
  if(!owner){owner={model,count:row.import_count,current:row.current_tmd_sha256,rows:new Map()};owners.set(model.semantic_id,owner);}
  if(owner.count!==row.import_count||owner.current!==row.current_tmd_sha256||owner.rows.has(row.import_index))fail();owner.rows.set(row.import_index,row);
 }
 for(const owner of owners.values()){
  if(owner.rows.size!==owner.count)fail();let previous=owner.model.source_record.sha256;
  for(let i=0;i<owner.count;i++){const row=owner.rows.get(i);if(!row||row.source_record.binding.current_tmd_sha256!==previous)fail();previous=row.source_record.candidate_tmd_sha256;}
  if(previous!==owner.current)fail();
 }
}

export function monsterModelInputRecords(report){return (report.retained_model_inputs??[]).map(data=>({id:data.semantic_id,type:'model',label:data.name,source:'Monster Archive / Historical Authored GLB Input',data:structuredClone(data),projectMonsterModelInput:{projectPath:report.project_path,sourceKey:report.project_source_key,catalogSourceKey:report.catalog.source_key}}));}

export async function qualifyMonsterModelInputDownload(v,report,record){
 const row=record.data,model=report.catalog.models.find(r=>r.semantic_id===row.model_asset_id);
 if(!model||v?.schema_version!=='legaia.monster-model-input-download.v1'||v.project_path!==report.project_path||v.project_source_key!==report.project_source_key||v.asset_id!==row.model_asset_id||v.current_tmd_sha256!==row.current_tmd_sha256||v.import_index!==row.import_index||v.input_count!==row.import_count||!same(v.retained_source,row.source_record)||v.sha256!==row.sha256||v.byte_length!==row.byte_length||v.filename!==`monster-${model.monster_id}-input-${row.import_index+1}.glb`||v.layer!=='historical_authored_input'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false||typeof v.glb_base64!=='string'||v.glb_base64.length>11200000)fail();
 const bytes=Uint8Array.from(atob(v.glb_base64),c=>c.charCodeAt(0));
 if(bytes.length!==row.byte_length||await placementDigest(bytes)!==row.sha256||bytes.length<28)fail();const view=new DataView(bytes.buffer);
 if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length)fail();return bytes;
}

export function mountMonsterModelInput({dialog,record,report,current,busy,onModel,onError}){
 if(!same(monsterModelInputRecords(report).find(r=>r.id===record.id),record))fail();
 const node=(tag,text)=>{const e=document.createElement(tag);e.textContent=text;return e;},close=node('button','Close Monster Model Input'),open=node('button','Open Matching Monster Model'),download=node('button','Download Original Monster GLB'),status=node('p','Original import bytes; later imports may change Current geometry.'),facts=node('p',`Input ${record.data.import_index+1} of ${record.data.import_count} / ${record.data.byte_length} bytes / SHA256 ${record.data.sha256}`),pre=node('pre',JSON.stringify(record.data,null,2)),details=node('details');
 facts.style.overflowWrap='anywhere';Object.assign(pre.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});details.append(node('summary','Historical Model Input Provenance'),pre);dialog.replaceChildren(node('h2',record.label),facts,status,download,open,details,close);
 let disposed=false,pending=null;const valid=()=>!disposed&&dialog.open&&current();function update(){download.disabled=open.disabled=!valid()||busy()||!!pending;}
 download.onclick=async()=>{
  update();if(download.disabled)return;pending=new AbortController();update();
  try{const r=await fetch('/api/monster-model-input-download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.data.model_asset_id,expected_current_tmd_sha256:record.data.current_tmd_sha256,import_index:record.data.import_index,expected_input_sha256:record.data.sha256}),signal:pending.signal}),text=await r.text();if(text.length>12*1024*1024)fail();const v=JSON.parse(text);if(!r.ok)throw Error(v.error||'Monster original GLB download failed');const bytes=await qualifyMonsterModelInputDownload(v,report,record);if(!valid())return;const url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'})),a=node('a','');a.href=url;a.download=v.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Exact original GLB import downloaded.';}catch(e){if(valid()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}finally{pending=null;update();}
 };
 open.onclick=()=>{update();if(!open.disabled)onModel(record.data.model_asset_id);};close.onclick=()=>dialog.close();dialog.showModal();update();return ()=>{disposed=true;pending?.abort();};
}

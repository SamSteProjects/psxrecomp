import {placementDigest} from './worldmap-placement-replay.js';

const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const integer=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const fail=()=>{throw Error('PLAYER art input source or registration changed.');};
const inputKeys=['schema_version','stream_id','archive_id','source_record','glb_sha256','glb_byte_length','baseline_slot_sha256','baseline_slot_byte_length','baseline_owners','model_source_sha256','equipped','object_part_indices','fps','animation_index','object_node_indices','import_digest'];

export function qualifyPlayerArtInputs(report){
  const rows=report.retained_art_inputs??[],c=report.catalog,seen=new Set(),files=new Map();
  if(!Array.isArray(rows)||rows.length>87)fail();
  for(const r of rows){
    const s=c.streams.find(v=>v.semantic_id===r.stream_asset_id),e=r.source_record;
    if(!s||!exact(e,inputKeys)||e.schema_version!=='legaia.player-art-glb-input.v1'||e.stream_id!==s.semantic_id||e.archive_id!==s.archive_asset_id||!same(e.source_record,s.source_record)||!hash(e.glb_sha256)||!hash(e.baseline_slot_sha256)||!hash(e.import_digest)||e.model_source_sha256!==c.player_file_sha256[s.player_index]||!integer(e.glb_byte_length,1,4*1024*1024)||e.baseline_slot_byte_length!==0x10800||typeof e.fps!=='number'||!Number.isFinite(e.fps)||e.fps<1||e.fps>120||!Array.isArray(e.equipped)||e.equipped.length!==5||e.equipped.some(v=>!integer(v,0,255))||!Array.isArray(e.object_part_indices)||!integer(e.object_part_indices.length,1,64)||e.object_part_indices.some(v=>!integer(v,0,s.part_count-1))||new Set(e.object_part_indices).size!==s.part_count||e.animation_index!==null&&!integer(e.animation_index,0,Number.MAX_SAFE_INTEGER)||e.object_node_indices!==null&&(!Array.isArray(e.object_node_indices)||e.object_node_indices.length!==e.object_part_indices.length||new Set(e.object_node_indices).size!==e.object_node_indices.length||e.object_node_indices.some(v=>!integer(v,0,Number.MAX_SAFE_INTEGER))))fail();
    const owners=e.baseline_owners;
    if(!owners||typeof owners!=='object'||Array.isArray(owners)||Object.keys(owners).length>87)fail();
    for(const [id,o] of Object.entries(owners)){
      const stream=c.streams.find(v=>v.semantic_id===id);
      if(!stream||stream.archive_asset_id!==s.archive_asset_id||!exact(o,['schema_version','asset_id','source_record','edits','decoded_sha256','current_body_sha256'])||o.schema_version!=='legaia.player-art-override.v1'||o.asset_id!==id||!same(o.source_record,stream.source_record)||!hash(o.decoded_sha256)||!hash(o.current_body_sha256)||!Array.isArray(o.edits)||!integer(o.edits.length,1,stream.part_count*stream.frame_count))fail();
      let previous=-1;
      for(const row of o.edits){
        if(!exact(row,['frame_index','part_index','translation','rotation_psx'])||!integer(row.frame_index,0,stream.frame_count-1)||!integer(row.part_index,0,stream.part_count-1)||row.frame_index*stream.part_count+row.part_index<=previous)fail();
        previous=row.frame_index*stream.part_count+row.part_index;
        for(const [key,lo,hi] of [['translation',-2048,2047],['rotation_psx',0,4095]])if(!Array.isArray(row[key])||row[key].length!==3||row[key].some(v=>!integer(v,lo,hi)))fail();
      }
    }
    const id=`retained-animation://legaia/player-art/${String(s.player_index).padStart(4,'0')}/${s.archive_role}/${String(s.stream_index).padStart(4,'0')}/glb/${e.glb_sha256}`;
    const role=s.archive_role[0].toUpperCase()+s.archive_role.slice(1);
    if(r.semantic_id!==id||seen.has(id)||r.asset_kind!=='retained_player_art_glb'||r.name!==`PLAYER ${s.player_index} ${role} Art Stream ${s.stream_index} GLB Input`||r.model_asset_id!==s.model_asset_id||r.player_index!==s.player_index||r.archive_role!==s.archive_role||r.stream_index!==s.stream_index||r.layer!=='retained_authored_input'||!same(r.retail_source,s.source_record)||!same(r.references,[s.model_asset_id,s.semantic_id])||!hash(r.current_body_sha256)||!hash(r.current_decoded_sha256)||r.relationship!=='historical_import_input_not_final_current_art'||r.read_only!==true||r.gameplay_verified!==false)fail();
    seen.add(id);
    for(const [key,size] of [['glb:'+e.glb_sha256,e.glb_byte_length],['bin:'+e.baseline_slot_sha256,e.baseline_slot_byte_length]]){if(files.has(key)&&files.get(key)!==size)fail();files.set(key,size);}
  }
  if([...files.values()].reduce((a,b)=>a+b,0)>64*1024*1024)fail();
  return rows;
}

export function playerArtInputRecords(report){
  return qualifyPlayerArtInputs(report).map(data=>({id:data.semantic_id,type:'animation',label:data.name,source:'PLAYER Art / Historical GLB Input',data:structuredClone(data),projectPlayerArtInput:{projectPath:report.project_path,sourceKey:report.project_source_key,artSourceKey:report.catalog.source_key}}));
}

export async function qualifyPlayerArtInputExport(value,report,record){
  if(!same(playerArtInputRecords(report).find(r=>r.id===record.id),record))fail();
  const e=record.data.source_record,r=record.data;
  if(value?.schema_version!=='legaia.player-art-input-export.v1'||value.project_path!==report.project_path||value.project_source_key!==report.project_source_key||!same(value.record,r)||value.filename!==`player-art-input-${r.player_index}-${r.archive_role}-${r.stream_index}-${e.glb_sha256}.glb`||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||typeof value.glb_base64!=='string'||value.glb_base64.length>6*1024*1024)fail();
  const bytes=Uint8Array.from(atob(value.glb_base64),c=>c.charCodeAt(0));
  if(bytes.length!==e.glb_byte_length||await placementDigest(bytes)!==e.glb_sha256)fail();
  return bytes;
}

const mounted=new WeakMap();
export function showPlayerArtInput({dialog,record,getReport,current,busy,onStream,onError}){
  mounted.get(dialog)?.();const report=getReport();
  if(!report||!same(playerArtInputRecords(report).find(r=>r.id===record.id),record)||!current())fail();
  const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
  dialog.replaceChildren();const close=node('button','×');close.setAttribute('aria-label','Close PLAYER Art Input');close.onclick=()=>dialog.close();
  const heading=node('div');heading.className='dialog-heading';heading.append(node('h2',record.label),close);
  const status=node('p','Historical imported GLB. Later numeric edits may change Current motion.'),open=node('button','Open Matching Art Stream'),download=node('button','Download Retained Art GLB');
  const evidence=record.data.source_record,facts=node('p',`Interchange FPS: ${evidence.fps} · GLB: ${evidence.glb_byte_length} bytes · Equipment: ${evidence.equipped.join(', ')}`);
  const details=node('details'),pre=node('pre',JSON.stringify(record.data,null,2));Object.assign(pre.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});details.append(node('summary','Source And Import Provenance'),pre);
  let pending=null,disposed=false,withdrawn=false;
  const valid=()=>!disposed&&!withdrawn&&current();
  // sourceReport clones the complete project catalogue. Use it only at an
  // action boundary, never from the periodic cheap freshness/busy guard.
  const registered=()=>{const next=getReport();return valid()&&next?.project_path===report.project_path&&next.project_source_key===report.project_source_key&&next.catalog?.source_key===report.catalog.source_key&&same(next.retained_art_inputs?.find(r=>r.semantic_id===record.id),record.data);};
  const refresh=()=>{if(!current())withdrawn=true;const stale=!valid(),disabled=stale||busy()||!!pending;if(open.disabled!==disabled)open.disabled=disabled;if(download.disabled!==disabled)download.disabled=disabled;if(stale){pending?.abort();const message='Project or input changed. Refresh Project assets.';if(status.textContent!==message)status.textContent=message;}};
  open.onclick=()=>{if(valid()&&!busy()&&!pending&&registered())onStream(record.data.stream_asset_id);};
  download.onclick=async()=>{if(!valid()||busy()||pending||!registered())return;pending=new AbortController();refresh();try{
    const response=await fetch('/api/player-art-input-export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected_project_path:report.project_path,expected_source_key:report.project_source_key,asset_id:record.id}),signal:pending.signal});
    const text=await response.text();if(text.length>6*1024*1024)fail();const value=JSON.parse(text);if(!response.ok)throw Error(value.error||'Art input download failed');
    const bytes=await qualifyPlayerArtInputExport(value,report,record);if(!valid()||busy()||!registered())return;
    const url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'})),a=node('a');a.href=url;a.download=value.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(error){if(!disposed&&error.name!=='AbortError'){status.textContent=error.message;onError?.(error);}}finally{pending=null;if(!disposed)refresh();}};
  dialog.append(heading,status,facts,open,download,details);
  const timer=setInterval(refresh,200),dispose=()=>{if(disposed)return;disposed=true;pending?.abort();clearInterval(timer);dialog.removeEventListener('close',onClose);if(mounted.get(dialog)===dispose)mounted.delete(dialog);},onClose=()=>{if(!dialog.open)dispose();};
  mounted.set(dialog,dispose);dialog.addEventListener('close',onClose);refresh();dialog.showModal();
}

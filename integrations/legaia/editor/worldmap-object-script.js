import {qualifyWorldObjectBind} from './worldmap-object-bind.js';
import {placementDigest} from './worldmap-placement-replay.js';
import {renderComponentSection} from './component-inspector.js';
const fail=()=>{throw Error('World source script graph differs from its bounded record witness.');};
export async function qualifyWorldObjectScript(v,current,id,path){
  if(!v||Object.keys(v).sort().join(',')!==['schema_version','project_path','scene','source_key','entity_id','binding','consumer','inspection','read_only','project_changed','gameplay_verified'].sort().join(','))fail();
  await qualifyWorldObjectBind(v.binding,current,id,path);
  if(v.schema_version!=='legaia.worldmap-object-script.v1'||v.project_path!==path||v.scene!==current.scene||v.source_key!==current.project_source_key||v.entity_id!==id||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)fail();
  const r=v.binding.bind.man_record,s=v.inspection,g=s.graph,man=Uint8Array.from(atob(v.binding.source_witness.man_base64),c=>c.charCodeAt(0)),data=man.slice(r.byte_offset,r.byte_offset+r.byte_length),entry=2+2*data[0];
  if(!r||r.partition!==0||await placementDigest(data)!==s.record_sha256||s.record_sha256!==r.sha256||s.record_index!==r.record_index||s.flat_record_index!==r.flat_record_index||s.entry_pc!==entry||g.entry_pc!==entry||entry!==r.header.byte_length||s.source_record_id!==`script://${v.scene}/worldmap/man-p0/${String(r.record_index).padStart(4,'0')}`||s.entry_basis!=='retail_object_init_post_p0_header'||s.asset_registration!=='not_registered'||s.runtime_execution!=='not_asserted'||s.representation!=='retail_source_script'||s.read_only!==true||!['partial','decoded_supported_paths'].includes(g.status))fail();
  const c=v.consumer;if(c.executable_sha256!=='292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482'||c.function.address!=='0x8003A55C'||c.function.byte_length!==1144||c.function.sha256!=='6414981beba670dcf6f86da8edb5f504fafbc6fa31c8a3650535a229263f5aa7'||c.script_base_store!=='0x8003A8AC'||c.script_pc_store!=='0x8003A8B4')fail();
  const ownership=new Uint8Array(data.length),hex=data=>Array.from(data,n=>n.toString(16).padStart(2,'0')).join('');
  for(const family of ['instructions','dialogues','opaque_regions']){
    if(!Array.isArray(g[family])||g[family].length>4096)fail();
    for(const row of g[family]){
      if(!Number.isInteger(row.pc)||!Number.isInteger(row.length)||row.pc<entry||row.length<1||row.pc+row.length>data.length||row.byte_offset!==r.byte_offset+row.pc||row.raw_hex!==hex(data.slice(row.pc,row.pc+row.length)))fail();
      for(let p=row.pc;p<row.pc+row.length;p++){if(ownership[p])fail();ownership[p]=1;}
      if(family==='instructions'&&(typeof row.mnemonic!=='string'||row.mnemonic.length>128||row.opcode!== (data[row.pc]&127)))fail();
    }
  }
  if(ownership.slice(entry).some(n=>!n)||!Array.isArray(g.stops)||g.stops.length>4096||(g.opaque_regions.length||g.stops.length)&&g.status!=='partial')fail();
  return structuredClone(v);
}

export function mountWorldObjectScript({host,binding,currentReport,entityId,path,current,busy,setBusy,getSchema,onError,update,onOpenScript}){
  const box=document.createElement('div');box.dataset.worldObjectScript='';host.append(box);
  const button=document.createElement('button');button.type='button';button.textContent='Inspect source interaction script';box.append(button);
  const status=document.createElement('p');status.textContent='Retail script source only; execution, story branches and live PC remain unknown.';box.append(status);
  const output=document.createElement('div');box.append(output);let disposed=false,pending=null;
  const refresh=()=>{button.disabled=disposed||!current()||busy();};
  button.onclick=async()=>{if(button.disabled)return;const controller=new AbortController();pending=controller;setBusy(true);refresh();update();const valid=()=>!disposed&&current()&&pending===controller;
    try{const response=await fetch('/api/worldmap-object-script',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:currentReport.scene,source_key:binding.source_key,entity_id:entityId}),signal:controller.signal}),text=await response.text();if(!valid())return;if(new TextEncoder().encode(text).length>32*1024*1024)fail();const v=JSON.parse(text);if(!response.ok)throw Error(v.error||'Source interaction script inspection failed.');const q=await qualifyWorldObjectScript(v,currentReport,entityId,path);if(!valid())return;
      output.innerHTML=renderComponentSection(getSchema(),'WorldSourceObjectScript',q.inspection);const table=document.createElement('table');table.dataset.worldObjectInstructions='';table.style.width='100%';table.style.tableLayout='fixed';const header=document.createElement('tr');for(const label of ['PC','SDK decoded instruction','Source bytes']){const th=document.createElement('th');th.textContent=label;header.append(th);}table.append(header);
      for(const row of q.inspection.graph.instructions){const tr=document.createElement('tr');for(const text of [row.pc.toString(16).padStart(4,'0'),row.mnemonic,row.raw_hex]){const td=document.createElement('td');td.textContent=text;td.style.overflowWrap='anywhere';tr.append(td);}table.append(tr);}output.append(table);
      if(onOpenScript){const note=document.createElement('p');note.textContent='Open the registered resource to inspect Current and authored changes. This source table remains Retail.';output.append(note);const open=document.createElement('button');open.type='button';open.textContent='Open Registered Script Editor';open.dataset.worldObjectScriptResource=q.inspection.source_record_id;open.onclick=async()=>{if(disposed||!current()||busy()||open.disabled)return;open.disabled=true;try{await onOpenScript({scriptId:q.inspection.source_record_id,sourceKey:q.source_key,projectPath:q.project_path,recordSha256:q.inspection.record_sha256,entryPc:q.inspection.entry_pc},()=>!disposed&&current());}catch(error){onError(error);}finally{open.disabled=disposed||!current();}};output.append(open);}
      status.textContent=`${q.inspection.graph.status} · ${q.inspection.graph.instructions.length} source instructions · ${q.inspection.graph.opaque_regions.length} opaque regions. No script executed or project changed.`;
    }catch(error){if(error.name!=='AbortError'&&valid()){status.textContent=error.message;onError(error);}}
    finally{if(pending===controller){pending=null;setBusy(false);refresh();update();}}
  };refresh();return {update:refresh,dispose(){disposed=true;pending?.abort();if(pending){pending=null;setBusy(false);}box.remove();}};
}

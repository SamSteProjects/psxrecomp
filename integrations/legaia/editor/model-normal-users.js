import { MODEL_FACE_BUDGET } from './model-topology-limits.js';
import {validateObjectOwnership} from './model-object-ownership.js';
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
export function validateReferenceFaceMapping(value){
  const added=value.schema_version.endsWith('.v2')||(value.schema_version.endsWith('.v3')||value.schema_version.endsWith('.v4'));
  if(value.face_mapping===undefined){if(added)throw new Error('Missing reference face mapping.');return;}
  if(!Array.isArray(value.face_mapping)||value.face_mapping.length>65536)throw new Error('Invalid reference face mapping.');
  const owned=new Set();let last=-1;
  for(const [index,row] of value.face_mapping.entries()){
    if(!row||Object.keys(row).sort().join('|')!=='current_index|retail_index'||row.retail_index!==index||row.current_index!==null&&(!integer(row.current_index,65535)||row.current_index<=last||!added&&row.current_index!==owned.size))throw new Error('Reference face identities conflict.');
    if(row.current_index!==null){owned.add(row.current_index);last=row.current_index;}
  }
  if(added){
    if(!integer(value.current_face_count,65536)||!integer(value.retail_model_byte_length,4*1024*1024)||value.retail_model_byte_length<12||!Array.isArray(value.authored_faces)||value.authored_faces.length>MODEL_FACE_BUDGET)throw new Error('Invalid authored reference ownership.');
    const ids=new Set();
    for(const face of value.authored_faces){
      if(!face||Object.keys(face).sort().join('|')!=='current_index|face_id'||typeof face.face_id!=='string'||!/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(face.face_id)||ids.has(face.face_id)||!integer(face.current_index,value.current_face_count-1)||owned.has(face.current_index))throw new Error('Authored reference face identities conflict.');
      ids.add(face.face_id);owned.add(face.current_index);
    }
    if(owned.size!==value.current_face_count||[...owned].some(index=>index>=value.current_face_count))throw new Error('Reference faces do not cover Current topology.');
  }
  for(const row of value.retail_users)if(row.primitive_index>=value.face_mapping.length)throw new Error('Retail reference face is absent.');
  for(const row of value.current_users)if(!owned.has(row.primitive_index))throw new Error('Current reference face is absent.');
}
export function validateReferenceVector(value,noun){
  const allocated=(value.schema_version.endsWith('.v3')||value.schema_version.endsWith('.v4'));
  if(value.schema_version.endsWith('.v4')){validateObjectOwnership(value.object_mappings,value.current_object_count,value.retail_object_count);if(value.object_index>=value.current_object_count||value.object_mappings[value.object_index].retail_index===null&&(value.retail_vector_count!==0||value.face_mapping.length))throw new Error('Authored object acquired a Retail vector or face owner.');}
  if(allocated){
    if(!integer(value.retail_vector_count,524288)||!integer(value.current_vector_count,524288)||value.current_vector_count<value.retail_vector_count||!integer(value[noun+'_index'],value.current_vector_count-1)||value.vector_origin!==(value[noun+'_index']<value.retail_vector_count?'retail':'allocated'))throw new Error('Vector allocation ownership conflicts.');
    if(value.vector_origin==='allocated'&&(value.retail_coordinates!==null||!Array.isArray(value.retail_users)||value.retail_users.length))throw new Error('Allocated vector cannot have a Retail counterpart.');
  }
  for(const field of ['retail_coordinates','current_coordinates']){
    if(allocated&&value.vector_origin==='allocated'&&field==='retail_coordinates')continue;
    if(!Array.isArray(value[field])||value[field].length!==3||value[field].some(v=>!Number.isInteger(v)||v< -32768||v>32767))throw new Error('Invalid stored '+noun+' coordinates.');
  }
}
export function decodeNormalUsers(value,binding){
  if(!value||!['legaia.model-normal-users.v1','legaia.model-normal-users.v2','legaia.model-normal-users.v3','legaia.model-normal-users.v4'].includes(value.schema_version)||value.asset_id!==binding.asset_id||value.project_source_key!==binding.source_key||value.effective_sha256!==binding.expected_sha256||!hash(value.project_source_key)||!hash(value.effective_sha256)||!hash(value.source_sha256)||value.object_index!==binding.object_index||value.normal_index!==binding.normal_index||!integer(value.object_index,65535)||!integer(value.normal_index,65535)||!integer(value.model_byte_length,32*1024*1024)||value.model_byte_length<12||value.read_only!==true||value.gameplay_verified!==false||value.scope!=='qualified_stored_normal_reference_operands_in_selected_object')throw new Error('Normal users differ from the inspected source vector.');
  validateReferenceVector(value,'normal');
  for(const field of ['retail_users','current_users']){
    if(!Array.isArray(value[field])||value[field].length>4096)throw new Error('Normal users exceed the qualified reference budget.');
    const seen=new Set();
    for(const row of value[field]){
      if(!row||row.kind!=='primitive'||row.field!=='normal_index'||row.object_index!==value.object_index||row.normal_index!==value.normal_index||!integer(row.primitive_index,65535)||!integer(row.group_index,65535)||!integer(row.corner_index,3)||!integer(row.byte_offset,(field==='retail_users'&&(value.schema_version.endsWith('.v2')||(value.schema_version.endsWith('.v3')||value.schema_version.endsWith('.v4')))?value.retail_model_byte_length:value.model_byte_length)-2)||row.byte_offset%2||![3,4].includes(row.corner_count)||!['flat_all_corners','gouraud_corner'].includes(row.sharing)||!Array.isArray(row.affected_corners))throw new Error('Invalid normal reference ownership.');
      const corners=row.sharing==='gouraud_corner'?[row.corner_index]:Array.from({length:row.corner_count},(_,i)=>i);
      if(row.corner_index>=row.corner_count||row.sharing==='flat_all_corners'&&row.corner_index!==0||JSON.stringify(corners)!==JSON.stringify(row.affected_corners)||seen.has(row.byte_offset))throw new Error('Normal reference corner coverage conflicts.');seen.add(row.byte_offset);
    }
  }
  validateReferenceFaceMapping(value);
  return structuredClone(value);
}
function element(tag,text){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;}
export function mountNormalUsers(options){return mountStoredReferenceUsers(options,{noun:'normal',decode:decodeNormalUsers});}
export function mountStoredReferenceUsers({host,assetId,expectedSha,sourceKey,getSelection,isCurrent,onSelect},{noun,decode}){
  const title=noun[0].toUpperCase()+noun.slice(1);
  const section=element('section'),button=element('button',`Find faces using this ${noun}`),status=element('p'),content=element('div');button.type='button';button.dataset[noun+'Users']='';status.setAttribute('role','status');section.append(button,status,content);host.append(section);
  let controller=null,generation=0,bound=null,report=null;
  const binding=()=>{const selection=getSelection();return selection?{asset_id:assetId,expected_sha256:expectedSha,source_key:sourceKey,...selection}:null;};
  const current=()=>isCurrent()&&JSON.stringify(binding())===JSON.stringify(bound);
  function close(){generation++;controller?.abort();controller=null;bound=null;report=null;content.replaceChildren();status.textContent='';}
  function refresh(){if(bound&&!current())close();button.disabled=!isCurrent()||!getSelection()||!!controller;}
  button.onclick=async()=>{
    refresh();if(button.disabled)return;close();bound=binding();const requested=bound,token=++generation,request=new AbortController();controller=request;status.textContent=`Qualifying stored ${noun} references…`;refresh();
    try{
      const response=await fetch(`/api/model-${noun}-users`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(requested),signal:request.signal}),value=await response.json();
      if(token!==generation||!current())return;if(!response.ok||value.error)throw new Error(value.error||`${title} references unavailable`);report=decode(value,requested);
      const label=element('label','Reference layer'),layer=element('select');layer.setAttribute('aria-label',`${title} reference layer`);for(const [key,text] of [['current','Current'],['retail','Retail']]){const option=element('option',text);option.value=key;option.disabled=key==='retail'&&report.vector_origin==='allocated';layer.append(option);}label.append(layer);const table=element('div');content.append(label,table);
      function draw(){if(!current()){close();refresh();return;}const users=report[layer.value+'_users'],coordinates=report[layer.value+'_coordinates'];table.replaceChildren();status.textContent=`${users.length} qualified stored reference operand(s) · ${layer.value==='current'?'Current':'Retail'} XYZ ${coordinates===null?'no Retail vector':coordinates.join(', ')}${report.vector_origin==='allocated'?' · allocated row; no Retail counterpart':''} · Showing ${Math.min(128,users.length)}. Runtime use and visibility are unverified.`;
        for(const row of users.slice(0,128)){const mapped=report.face_mapping?.find(face=>layer.value==='retail'?face.retail_index===row.primitive_index:face.current_index===row.primitive_index),currentIndex=mapped?mapped.current_index:row.primitive_index,authored=layer.value==='current'?report.authored_faces?.find(face=>face.current_index===row.primitive_index):null,retailIndex=mapped?mapped.retail_index:authored?'none (authored)':row.primitive_index;const p=element('p'),identity=element('span',`${authored?authored.face_id+' · ':''}Retail face ${retailIndex} · ${currentIndex===null?'removed from Current':`Current face ${currentIndex}`} `);p.append(identity);const link=onSelect&&currentIndex!==null?element('button',`Inspect current face ${currentIndex}`):element('span',currentIndex===null?'No Current face.':'Read-only topology inspection.');if(onSelect&&currentIndex!==null){link.type='button';link.onclick=()=>{if(current())onSelect({...structuredClone(row),primitive_index:currentIndex,...(authored?{face_id:authored.face_id}:{})});else{close();refresh();}};}p.append(element('span',`${title} ${row[noun+'_index']} · stored word at byte ${row.byte_offset} · ${row.sharing==='flat_all_corners'?'all '+row.corner_count+' corners':'corner '+row.corner_index} `),link);table.append(p);}
      }
      layer.onchange=draw;draw();
    }catch(error){if(error.name!=='AbortError'&&token===generation&&current())status.textContent=error.message;}finally{if(controller===request)controller=null;refresh();}
  };
  refresh();return {refresh,close};
}

const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
export function decodeNormalUsers(value,binding){
  if(!value||value.schema_version!=='legaia.model-normal-users.v1'||value.asset_id!==binding.asset_id||value.project_source_key!==binding.source_key||value.effective_sha256!==binding.expected_sha256||!hash(value.project_source_key)||!hash(value.effective_sha256)||!hash(value.source_sha256)||value.object_index!==binding.object_index||value.normal_index!==binding.normal_index||!integer(value.object_index,65535)||!integer(value.normal_index,65535)||!integer(value.model_byte_length,32*1024*1024)||value.model_byte_length<12||value.read_only!==true||value.gameplay_verified!==false||value.scope!=='qualified_stored_normal_reference_operands_in_selected_object')throw new Error('Normal users differ from the inspected source vector.');
  for(const field of ['retail_coordinates','current_coordinates'])if(!Array.isArray(value[field])||value[field].length!==3||value[field].some(v=>!Number.isInteger(v)||v< -32768||v>32767))throw new Error('Invalid stored normal coordinates.');
  for(const field of ['retail_users','current_users']){
    if(!Array.isArray(value[field])||value[field].length>4096)throw new Error('Normal users exceed the qualified reference budget.');
    const seen=new Set();
    for(const row of value[field]){
      if(!row||row.kind!=='primitive'||row.field!=='normal_index'||row.object_index!==value.object_index||row.normal_index!==value.normal_index||!integer(row.primitive_index,65535)||!integer(row.group_index,65535)||!integer(row.corner_index,3)||!integer(row.byte_offset,value.model_byte_length-2)||row.byte_offset%2||![3,4].includes(row.corner_count)||!['flat_all_corners','gouraud_corner'].includes(row.sharing)||!Array.isArray(row.affected_corners))throw new Error('Invalid normal reference ownership.');
      const corners=row.sharing==='gouraud_corner'?[row.corner_index]:Array.from({length:row.corner_count},(_,i)=>i);
      if(row.corner_index>=row.corner_count||row.sharing==='flat_all_corners'&&row.corner_index!==0||JSON.stringify(corners)!==JSON.stringify(row.affected_corners)||seen.has(row.byte_offset))throw new Error('Normal reference corner coverage conflicts.');seen.add(row.byte_offset);
    }
  }
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
      const label=element('label','Reference layer'),layer=element('select');layer.setAttribute('aria-label',`${title} reference layer`);for(const [key,text] of [['current','Current'],['retail','Retail']]){const option=element('option',text);option.value=key;layer.append(option);}label.append(layer);const table=element('div');content.append(label,table);
      function draw(){if(!current()){close();refresh();return;}const users=report[layer.value+'_users'],coordinates=report[layer.value+'_coordinates'];table.replaceChildren();status.textContent=`${users.length} qualified stored reference operand(s) · ${layer.value==='current'?'Current':'Retail'} XYZ ${coordinates.join(', ')} · Showing ${Math.min(128,users.length)}. Runtime use and visibility are unverified.`;
        for(const row of users.slice(0,128)){const p=element('p'),link=element('button',`Inspect current face ${row.primitive_index}`);link.type='button';link.onclick=()=>{if(current())onSelect(structuredClone(row));else{close();refresh();}};p.append(element('span',`${title} ${row[noun+'_index']} · stored word at byte ${row.byte_offset} · ${row.sharing==='flat_all_corners'?'all '+row.corner_count+' corners':'corner '+row.corner_index} `),link);table.append(p);}
      }
      layer.onchange=draw;draw();
    }catch(error){if(error.name!=='AbortError'&&token===generation&&current())status.textContent=error.message;}finally{if(controller===request)controller=null;refresh();}
  };
  refresh();return {refresh,close};
}

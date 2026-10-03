const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max=64*1024*1024)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const fail=()=>{throw new Error('Allocation metadata differs from this source model.');};
function layer(value,expectedHash){
  if(value?.schema_version!=='legaia.model-allocation.v1'||value.source_sha256!==expectedHash||!integer(value.byte_length)||!Array.isArray(value.objects)||value.objects.length>1024)fail();
  const spans=[[0,12+28*value.objects.length]];if(spans[0][1]>value.byte_length)fail();
  for(const [index,obj] of value.objects.entries()){
    const s=obj.primitive_stream;if(obj.object_index!==index||!integer(obj.primitive_count,65535)||!s||!Array.isArray(obj.groups)||obj.groups.length>4096||!Array.isArray(obj.vectors)||obj.vectors.length>2)fail();
    for(const field of ['byte_offset','byte_limit','terminator_offset','encoded_byte_length','uninterpreted_tail_bytes'])if(!integer(s[field],value.byte_length))fail();
    if(s.byte_offset<spans[0][1]||s.byte_limit<s.terminator_offset+4||s.encoded_byte_length!==s.terminator_offset+4-s.byte_offset||s.uninterpreted_tail_bytes!==s.byte_limit-s.terminator_offset-4)fail();
    let at=s.byte_offset,count=0;
    for(const [j,g] of obj.groups.entries()){
      if(g.group_index!==j||g.byte_offset!==at||g.first_primitive_index!==count||!integer(g.primitive_count,65535)||!g.primitive_count||!integer(g.packet_stride,1020)||!g.packet_stride||g.packet_stride%4||g.byte_length!==8+(g.primitive_count+1)*g.packet_stride)fail();
      at+=g.byte_length;count+=g.primitive_count;
    }
    if(at!==s.terminator_offset||count!==obj.primitive_count)fail();
    spans.push([s.byte_offset,s.byte_limit]);const kinds=new Set();
    for(const v of obj.vectors){if(!['vertex','normal'].includes(v.kind)||kinds.has(v.kind)||!integer(v.count,65535)||!v.count||!integer(v.byte_offset,value.byte_length)||v.byte_length!==v.count*8||v.byte_offset+v.byte_length>value.byte_length)fail();kinds.add(v.kind);spans.push([v.byte_offset,v.byte_offset+v.byte_length]);}
    if(s.byte_limit!==Math.min(...obj.vectors.map(v=>v.byte_offset),value.byte_length))fail();
  }
  spans.sort((a,b)=>a[0]-b[0]);if(spans.some(([a,b],i)=>a>b||i&&a<spans[i-1][1]))fail();
}
export function decodeModelAllocation(value,assetId,key){
  if(value?.schema_version!=='legaia.model-allocation-source.v1'||value.asset_id!==assetId||value.project_source_key!==key||!hash(key)||!hash(value.source_sha256)||!hash(value.effective_sha256)||value.project_changed!==false||value.gameplay_verified!==false)fail();
  layer(value.retail,value.source_sha256);layer(value.current,value.effective_sha256);
  if(JSON.stringify(value).length>4*1024*1024)fail();
  return structuredClone(value);
}
export async function openModelAllocation({assetId,getContext,busy,setBusy,onError=()=>{}}){
  const context=structuredClone(getContext()),key=JSON.stringify(context);
  if(busy()||context.mode!=='edit')return null;
  const dialog=document.createElement('dialog');dialog.id='model-allocation-dialog';dialog.className='model-dialog';
  dialog.innerHTML='<div class="dialog-heading"><h2>Native model allocation</h2><button type="button" aria-label="Close allocation inspection">×</button></div><p>Inspect stored packet and vector extents. Uninterpreted trailing bytes are not authorized space for new geometry.</p><label>Allocation layer<select aria-label="Allocation layer"><option value="current">Current</option><option value="retail">Retail</option></select></label><label>Model object<select aria-label="Allocation object"></select></label><p role="status"></p><div data-allocation-content></div>';
  document.body.append(dialog);const layerSelect=dialog.querySelector('[aria-label="Allocation layer"]'),object=dialog.querySelector('[aria-label="Allocation object"]'),status=dialog.querySelector('[role="status"]'),content=dialog.querySelector('[data-allocation-content]');
  let closed=false,ownedBusy=false,report=null,controller=new AbortController();const request=controller;
  const current=()=>!closed&&JSON.stringify(getContext())===key;
  const release=()=>{if(ownedBusy){ownedBusy=false;setBusy(false);}};
  function dispose(){if(closed)return;closed=true;controller?.abort();controller=null;release();dialog.remove();}
  function updateState(){if(!current())dispose();}
  const text=(tag,value)=>{const e=document.createElement(tag);e.textContent=value;return e;};
  function draw(){if(!current()){dispose();return;}const data=report[layerSelect.value],obj=data.objects[Number(object.value)];content.replaceChildren();if(!obj){status.textContent='No model objects.';return;}
    const s=obj.primitive_stream;status.textContent=`${obj.primitive_count} stored primitives · ${obj.groups.length} groups · ${data.byte_length} model bytes`;
    content.append(text('p',`Packet stream: byte ${s.byte_offset} to ${s.byte_limit}. Encoded bytes including terminator: ${s.encoded_byte_length}.`),text('p',`Terminator: byte ${s.terminator_offset}. Uninterpreted trailing bytes: ${s.uninterpreted_tail_bytes}.`));
    const list=document.createElement('ul');for(const v of obj.vectors)list.append(text('li',`${v.kind}: ${v.count} vectors · byte ${v.byte_offset} · ${v.byte_length} bytes`));content.append(list);
    const groups=document.createElement('details');groups.append(text('summary','Stored packet groups'));
    for(const g of obj.groups)groups.append(text('p',`Group ${g.group_index}: ${g.primitive_count} primitives · byte ${g.byte_offset} · ${g.byte_length} bytes · packet stride ${g.packet_stride}.`));content.append(groups);
  }
  function populate(){const selected=object.value;object.replaceChildren();for(const obj of report[layerSelect.value].objects){const option=text('option',`Object ${obj.object_index}`);option.value=String(obj.object_index);object.append(option);}object.value=report[layerSelect.value].objects.some(o=>String(o.object_index)===selected)?selected:'0';draw();}
  dialog.querySelector('button').onclick=()=>dialog.close();dialog.addEventListener('close',dispose);layerSelect.onchange=()=>{if(report)populate();};object.onchange=()=>{if(report)draw();};layerSelect.disabled=object.disabled=true;status.textContent='Qualifying model allocation…';dialog.showModal();ownedBusy=true;setBusy(true);
  try{const response=await fetch('/api/model-allocation-source',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:assetId,source_key:context.sourceKey}),signal:request.signal}),value=await response.json();if(!current()){dispose();return null;}if(!response.ok||value.error)throw new Error(value.error||'Allocation inspection unavailable.');report=decodeModelAllocation(value,assetId,context.sourceKey);
    layerSelect.disabled=object.disabled=false;populate();
  }catch(error){if(error.name!=='AbortError'&&current()){status.textContent=error.message;onError(error);}}finally{controller=null;release();}
  return {dialog,dispose,updateState};
}

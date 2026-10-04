const fail=m=>{throw new Error(m);};
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,a,b)=>Number.isInteger(v)&&v>=a&&v<=b;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const bytes64=encoded=>{
  if(typeof encoded!=='string'||encoded.length>1398104||encoded.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(encoded))fail('Converted TIM is malformed or exceeds one MiB.');
  return Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
};
const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
export async function decodeImageConversion(v,request,input){
  if(!exact(v,['report','asset_id','project_source_key','source_scene_id','content_base64'])||v.asset_id!==request.asset_id||v.project_source_key!==request.source_key||v.source_scene_id!==input.sceneId)fail('Conversion belongs to another source or scene.');
  const r=v.report,q=r?.quantization;
  if(!exact(r,['schema_version','png_sha256','png_byte_length','stp_png_sha256','options','width','height','proposed_sha256','byte_length','palette_count','quantization','native_readback_verified','alpha_stp_classes_verified','project_changed','gameplay_verified','limitations'])||r.schema_version!=='legaia.texture-image-conversion.v1'||r.png_sha256!==input.pngSha256||r.png_byte_length!==input.pngSize||r.stp_png_sha256!==input.stpSha256||JSON.stringify(r.options)!==JSON.stringify(request.options)||!hash(r.proposed_sha256)||!integer(r.byte_length,20,1048576)||!integer(r.width,1,4096)||!integer(r.height,1,512)||r.palette_count!==(r.options.bpp<=8?1:0)||r.native_readback_verified!==true||r.alpha_stp_classes_verified!==true||r.project_changed!==false||r.gameplay_verified!==false||!Array.isArray(r.limitations)||r.limitations.length>32||r.limitations.some(t=>typeof t!=='string'||t.length>2048))fail('Conversion report contradicts its image or native choices.');
  if(!exact(q,['color_max_error','color_rms_error','quantized_pixel_count','visible_pixel_count','transparent_pixel_count','distinct_requested_words','palette_representative_count','used_palette_entries','forced_black_stp_pixels','forced_transparent_stp_pixels'])||!Number.isFinite(q.color_rms_error)||q.color_rms_error<0||q.color_rms_error>255||!integer(q.color_max_error,0,255)||Object.keys(q).filter(k=>!['color_max_error','color_rms_error'].includes(k)).some(k=>!integer(q[k],0,r.width*r.height))||q.visible_pixel_count+q.transparent_pixel_count!==r.width*r.height||q.quantized_pixel_count>q.visible_pixel_count||q.palette_representative_count>(r.options.bpp<=8?1<<r.options.bpp:0)||q.used_palette_entries>q.palette_representative_count)fail('Conversion quantization diagnostics exceed their image bounds.');
  const bytes=bytes64(v.content_base64);
  if(bytes.length!==r.byte_length||await digest(bytes)!==r.proposed_sha256)fail('Converted TIM hash or length differs from the report.');
  const native=new DataView(bytes.buffer),bpp=r.options.bpp,capacity=bpp<=8?1<<bpp:0,at=capacity?20+capacity*2:8;
  if(![4,8,16,24].includes(bpp)||native.getUint32(0,true)!==16||native.getUint32(4,true)!==([4,8,16,24].indexOf(bpp)|(capacity?8:0))||at+12>bytes.length||native.getUint32(at,true)!==12+r.width*r.height*bpp/8||native.getUint16(at+4,true)!==r.options.image_x||native.getUint16(at+6,true)!==r.options.image_y||native.getUint16(at+8,true)*16!==r.width*bpp||native.getUint16(at+10,true)!==r.height||at+native.getUint32(at,true)!==bytes.length||r.options.image_x+r.width*bpp/16>1024||r.options.image_y+r.height>512)fail('Converted TIM image header differs from the native choices.');
  if(capacity&&(native.getUint32(8,true)!==12+capacity*2||native.getUint16(12,true)!==r.options.clut_x||native.getUint16(14,true)!==r.options.clut_y||native.getUint16(16,true)!==capacity||native.getUint16(18,true)!==1))fail('Converted TIM palette header differs from the native choices.');
  return {sha256:r.proposed_sha256,size:r.byte_length,base64:v.content_base64,conversion:structuredClone(r)};
}
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const button=text=>{const n=node('button',text);n.type='button';return n;};
async function readPng(file){
  if(!file||file.size<8||file.size>8388608)fail('Choose a PNG up to eight MiB.');
  const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let at=0;at<bytes.length;at+=8192)binary+=String.fromCharCode(...bytes.subarray(at,at+8192));
  return {base64:btoa(binary),sha256:await digest(bytes),size:bytes.length};
}
export function openImageConversion({assetId,getContext,busy,setBusy,onDraft,onError=()=>{},initialOptions=null}){
  const context=structuredClone(getContext()),key=JSON.stringify(context);
  if(context.mode!=='edit'||!hash(context.sourceKey))fail('PNG conversion requires the current Edit context.');
  const dialog=node('dialog');dialog.id='texture-image-conversion-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(820px,94vw)',maxHeight:'92vh',overflowY:'auto'});
  const close=button('Close conversion'),heading=node('div');heading.className='dialog-heading';heading.append(node('h2','Convert PNG to a TIM draft'),close);
  const help=node('p','Choose the native mode and image/palette coordinates explicitly. Width must encode whole TIM words: multiples of 4 pixels for 4-bit, 2 for 8-bit or RGB24. STP is separate from binary PNG alpha. Conversion does not change the project.');
  const png=node('input');png.type='file';png.accept='.png';png.setAttribute('aria-label','Source PNG');const pngLabel=node('label','Source PNG - up to 8 MiB');pngLabel.append(png);
  const stp=node('input');stp.type='file';stp.accept='.png';stp.setAttribute('aria-label','Optional STP PNG');const stpLabel=node('label','Optional STP plane - opaque black/white PNG with matching dimensions');stpLabel.append(stp);
  const fields={},grid=node('div');Object.assign(grid.style,{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:'12px'});
  for(const [name,title,values] of [['bpp','Native bit depth',[4,8,16,24]],['stp_mode','Default STP policy',['opaque','semi']]]){const select=node('select');select.setAttribute('aria-label',title);for(const value of values){const option=node('option',String(value));option.value=String(value);select.append(option);}if(name==='bpp')select.value='16';const label=node('label',title);label.append(select);fields[name]=select;grid.append(label);}
  for(const [name,title,max,value] of [['image_x','Image X (VRAM words)',1023,640],['image_y','Image Y',511,32],['clut_x','CLUT X (16-word aligned)',1023,0],['clut_y','CLUT Y',511,0]]){const input=node('input');input.type='number';input.min='0';input.max=String(max);input.step='1';input.value=String(value);input.setAttribute('aria-label',title);const label=node('label',title);label.append(input);grid.append(label);fields[name]=input;}
  if(initialOptions)for(const [key,value] of Object.entries(initialOptions))if(fields[key])fields[key].value=String(value);
  const convert=button('Convert PNG'),use=button('Use converted TIM draft'),actions=node('div');actions.className='dialog-actions';actions.append(convert,use);const status=node('p','Choose a PNG. An explicit STP plane overrides the default policy.'),summary=node('section'),error=node('p');error.className='dialog-error';error.setAttribute('role','alert');dialog.append(heading,help,pngLabel,stpLabel,grid,actions,status,summary,error);document.body.append(dialog);
  let result=null,pending=false,owner=null,controller=null,generation=0,closed=false;
  const current=()=>!closed&&JSON.stringify(getContext())===key;
  function controls(){const blocked=!current()||pending||busy();for(const input of [png,stp,...Object.values(fields)])input.disabled=blocked;for(const name of ['clut_x','clut_y'])fields[name].disabled=blocked||Number(fields.bpp.value)>8;convert.disabled=blocked||!png.files?.length;use.disabled=blocked||!result;}
  function release(token){if(token&&owner===token){owner=null;setBusy(false);}}
  function invalidate(){generation++;controller?.abort();controller=null;pending=false;release(owner);result=null;summary.replaceChildren();controls();}
  function dispose(){if(closed)return;closed=true;invalidate();dialog.remove();}
  for(const input of [png,stp,...Object.values(fields)])input.oninput=()=>{invalidate();status.textContent='Source or choices changed. Convert again before using the draft.';};
  convert.onclick=async()=>{
    if(convert.disabled)return;const token={},ticket=++generation;owner=token;pending=true;result=null;controller=new AbortController();const signal=controller.signal;setBusy(true);error.textContent='';controls();
    const valid=()=>current()&&ticket===generation&&!signal.aborted;
    try{
      const source=await readPng(png.files[0]),plane=stp.files?.length?await readPng(stp.files[0]):null;
      if(!valid())return;
      const options={bpp:Number(fields.bpp.value),image_x:Number(fields.image_x.value),image_y:Number(fields.image_y.value),clut_x:Number(fields.bpp.value)<=8?Number(fields.clut_x.value):0,clut_y:Number(fields.bpp.value)<=8?Number(fields.clut_y.value):0,stp_mode:fields.stp_mode.value};
      if(Object.entries(options).some(([k,v])=>k!=='stp_mode'&&(!Number.isInteger(v)||fields[k].value.trim()==='')))fail('Choose integer native coordinates.');
      const request={asset_id:assetId,source_key:context.sourceKey,png_base64:source.base64,stp_png_base64:plane?.base64??null,options};
      const response=await fetch('/api/texture-image-convert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal}),text=await response.text();if(new TextEncoder().encode(text).length>2097152)fail('Conversion response exceeds its draft budget.');const value=JSON.parse(text);if(!response.ok||value.error)fail(value.error||'PNG conversion failed.');
      const draft=await decodeImageConversion(value,request,{sceneId:context.sceneId,pngSha256:source.sha256,pngSize:source.size,stpSha256:plane?.sha256??null});if(!valid())return;result=draft;const r=draft.conversion,q=r.quantization;summary.replaceChildren(node('h3','Converted TIM - not applied'),node('p',`${r.width} x ${r.height} pixels - ${options.bpp} bpp - ${r.byte_length} bytes - ${r.palette_count} palette`),node('p',`${q.quantized_pixel_count} visible pixels changed; maximum RGB error ${q.color_max_error}, RMS ${q.color_rms_error.toFixed(3)}. ${q.forced_black_stp_pixels} opaque black pixels required STP1.`));const details=node('details'),pre=node('pre',JSON.stringify(r,null,2));pre.style.overflowWrap='anywhere';details.append(node('summary','Conversion evidence'),pre);summary.append(details);status.textContent='Use this draft to review native pack placement and inspect Proposed pixels before Apply.';
    }catch(e){if(valid()&&e.name!=='AbortError'){error.textContent=e.message;onError(e);}}finally{release(token);if(ticket===generation){pending=false;controller=null;controls();}}
  };
  use.onclick=()=>{if(use.disabled||!current())return;onDraft(result,png.files[0].name);dispose();};close.onclick=dispose;dialog.oncancel=e=>{e.preventDefault();dispose();};dialog.onclose=dispose;dialog.showModal();controls();return {dialog,dispose,update:controls};
}

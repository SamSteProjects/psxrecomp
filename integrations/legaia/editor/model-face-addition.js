import {SceneRenderer} from './scene-renderer.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const authored=v=>typeof v==='string'&&/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(v);
const fail=message=>{throw new Error(message);};
export function decodeFaceAdditionSource(value,asset,key){
  if(value?.schema_version!=='legaia.model-face-addition-source.v1'||value.asset_id!==asset||value.project_source_key!==key||!hash(key)||!hash(value.source_sha256)||!hash(value.effective_sha256)||value.project_changed!==false||value.gameplay_verified!==false)fail('Face source differs from this model.');
  const audit=value.topology,objects=value.objects;
  if(!audit||!hash(audit.source_sha256)||audit.proposed_sha256!==value.effective_sha256||!integer(audit.authored_face_count,128)||!integer(audit.batch_count,8)||!Array.isArray(audit.faces)||!Array.isArray(objects)||!objects.length||objects.length>1024)fail('Missing stable face ownership.');
  let count=0;for(const [i,obj] of objects.entries()){
    if(obj.object_index!==i||!integer(obj.vertex_count,65535)||!integer(obj.normal_count,65535)||!Array.isArray(obj.primitives)||obj.primitives.length>65535)fail('Invalid face object.');
    for(const [j,row] of obj.primitives.entries()){
      if(row.primitive_index!==j||!integer(row.group_index,65535)||!integer(row.flags,0x27)||row.flags<0x10||row.corner_count!==(row.flags&2?4:3)||!Array.isArray(row.vertices)||row.vertices.length!==row.corner_count||row.vertices.some(v=>!integer(v,obj.vertex_count-1)))fail('Invalid donor vectors.');
      for(const [field,width,max] of [['uvs',2,255],['colors',3,255],['normal_indices',1,obj.normal_count-1]]){
        const values=row[field];if(values===null)continue;
        if(!Array.isArray(values)||![1,row.corner_count].includes(values.length)||field==='uvs'&&values.length!==row.corner_count||values.some(v=>width===1?!integer(v,max):!Array.isArray(v)||v.length!==width||v.some(n=>!integer(n,max))))fail('Invalid typed donor fields.');
      }
      count++;
    }
  }
  const ids=new Set(),owners=new Set();let added=0;
  if(audit.faces.length!==count)fail('Incomplete face identity table.');
  for(const row of audit.faces){
    const primitive=objects[row.object_index]?.primitives[row.current_primitive_index],owner=`${row.object_index}:${row.current_primitive_index}`;
    if(!primitive||row.group_index!==primitive.group_index||ids.has(row.face_id)||owners.has(owner))fail('Duplicate or missing donor owner.');
    if(row.origin==='source'){if(!integer(row.source_primitive_index,65535)||row.face_id!==`face://source/${audit.source_sha256}/${row.object_index}/${row.source_primitive_index}`)fail('Invalid source face identity.');}
    else if(row.origin==='authored'&&authored(row.face_id)){added++;}else fail('Invalid authored face identity.');
    ids.add(row.face_id);owners.add(owner);
  }
  if(added!==audit.authored_face_count)fail('Authored face count differs.');
  for(const row of audit.faces)if(row.origin==='authored'&&!audit.faces.some(d=>d.face_id===row.donor_face_id&&d.object_index===row.object_index&&d.group_index===row.group_index))fail('Authored donor provenance is missing.');
  if(!value.preview||!Array.isArray(value.preview.vertices)||!Array.isArray(value.preview.objects)||value.preview.objects.length!==objects.length)fail('Missing Current geometry.');
  return structuredClone(value);
}
export function faceAdditionRequest(source,donorId,texts,faceId){
  const donor=source.topology.faces.find(row=>row.face_id===donorId);
  if(!donor||!authored(faceId)||source.topology.faces.some(row=>row.face_id===faceId))fail('Choose an existing donor and a new face identity.');
  const obj=source.objects[donor.object_index],row=obj.primitives[donor.current_primitive_index],fields={};
  for(const [field,width,max] of [['vertices',1,obj.vertex_count-1],['uvs',2,255],['colors',3,255],['normal_indices',1,obj.normal_count-1]]){
    if(row[field]===null)continue;
    const input=texts[field];if(typeof input!=='string'||input.length>4096)fail('Enter typed face values.');
    const parts=width===1?input.split(','):input.split(';');
    const expected=row[field].length;
    if(parts.length!==expected)fail(`${field}: expected ${expected} values.`);
    const parse=part=>{const words=part.trim().split(',').map(v=>v.trim());if(words.length!==width||words.some(v=>!/^\d+$/.test(v)||!integer(Number(v),max)))fail(`${field}: values are outside this donor's domain.`);return words.map(Number);};
    fields[field]=width===1?parts.map(v=>parse(v)[0]):parts.map(parse);
  }
  return {face_id:faceId,donor_face_id:donorId,fields};
}
export function decodeFaceAdditionReview(value,source,request){
  if(!same(value?.requests,[request]))fail('Review differs from the requested typed fields.');
  if(value?.schema_version!=='legaia.model-face-addition-review.v1'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.proposed_sha256===source.effective_sha256||value.project_changed!==false||value.gameplay_verified!==false||!same(value.current_preview,source.preview))fail('Review differs from the inspected model.');
  const donor=source.topology.faces.find(f=>f.face_id===request.donor_face_id),primitive=source.objects[donor?.object_index]?.primitives[donor?.current_primitive_index],audit=value.topology;
  if(!primitive||audit?.source_sha256!==source.topology.source_sha256||audit.proposed_sha256!==value.proposed_sha256||audit.batch_count!==source.topology.batch_count+1||audit.authored_face_count!==source.topology.authored_face_count+1||audit.faces?.length!==source.topology.faces.length+1||!same(value.preview?.vertices,source.preview.vertices)||value.preview?.objects?.length!==source.objects.length)fail('Review changed vector or identity ownership.');
  const inserted=Math.max(...source.objects[donor.object_index].primitives.filter(r=>r.group_index===donor.group_index).map(r=>r.primitive_index))+1;
  const rows=new Map(audit.faces.map(f=>[f.face_id,f]));if(rows.size!==audit.faces.length)fail('Duplicate reviewed identity.');
  for(const old of source.topology.faces){const expected={...old,current_primitive_index:old.current_primitive_index+(old.object_index===donor.object_index&&old.current_primitive_index>=inserted?1:0)};if(!same(rows.get(old.face_id),expected))fail('Review remapped another face incorrectly.');}
  const added=rows.get(request.face_id);if(!added||added.origin!=='authored'||added.donor_face_id!==request.donor_face_id||added.object_index!==donor.object_index||added.group_index!==donor.group_index||added.current_primitive_index!==inserted)fail('Review differs from the requested donor.');
  for(const [i,old] of source.preview.objects.entries()){const next=value.preview.objects[i];if(next.object_index!==old.object_index||next.vertex_start!==old.vertex_start||next.vertex_count!==old.vertex_count||next.triangle_count-old.triangle_count!==(i===donor.object_index?(primitive.corner_count===4?2:1):0))fail('Review face counts differ.');}
  return structuredClone(value);
}

export async function openModelFaceAddition({assetId,getContext,busy,setBusy,onApplied,onError=()=>{}}){
  const context=structuredClone(getContext()),contextKey=JSON.stringify(context);
  if(busy()||context.mode!=='edit')return null;
  const dialog=document.createElement('dialog');dialog.id='model-face-addition-dialog';dialog.className='model-dialog';
  dialog.innerHTML='<div class="dialog-heading"><h2>Add model face</h2><button type="button" aria-label="Close face addition">×</button></div><p>Add one triangle or quad using existing points. The donor preserves its material settings. Review the complete model before applying. Build support for additions is still being connected.</p><label>Donor face<select aria-label="Face addition donor"></select></label><label>Vertex indices<input aria-label="New face vertices"></label><label data-uvs>UV pairs<input aria-label="New face UVs"></label><label data-colors>RGB colors<input aria-label="New face colors"></label><label data-normal_indices>Normal indices<input aria-label="New face normals"></label><button type="button" data-review>Review new face</button><button type="button" data-apply disabled>Apply reviewed new face</button><p role="status"></p><section data-comparison hidden><label>Preview layer<select aria-label="Face addition preview layer"><option value="proposed">Proposed</option><option value="current">Current</option></select></label><canvas style="width:100%;height:280px"></canvas></section>';
  document.body.append(dialog);const donor=dialog.querySelector('[aria-label="Face addition donor"]'),status=dialog.querySelector('[role="status"]'),reviewButton=dialog.querySelector('[data-review]'),applyButton=dialog.querySelector('[data-apply]'),close=dialog.querySelector('button'),comparison=dialog.querySelector('[data-comparison]'),layer=comparison.querySelector('select'),canvas=comparison.querySelector('canvas');
  const inputs=Object.fromEntries([['vertices','vertices'],['uvs','UVs'],['colors','colors'],['normal_indices','normals']].map(([field,label])=>[field,dialog.querySelector(`[aria-label="New face ${label}"]`)]));
  const faceId=`face://authored/${crypto.randomUUID()}`;
  let source=null,review=null,reviewedRequest=null,pending=false,applying=false,closed=false,ownedBusy=false,controller=null,generation=0,renderer=null,drag=null;
  const view={yaw:.6,pitch:.4,zoom:1};canvas.tabIndex=0;canvas.style.touchAction='none';canvas.setAttribute('aria-label','Face addition comparison; drag or arrow keys to orbit, scroll or plus and minus to zoom');
  const current=()=>!closed&&dialog.open&&JSON.stringify(getContext())===contextKey;
  const release=()=>{if(ownedBusy){ownedBusy=false;setBusy(false);}};
  function dispose(){if(closed)return;closed=true;controller?.abort();release();renderer?.dispose();globalThis.removeEventListener?.('resize',draw);if(dialog.open)dialog.close();dialog.remove();}
  const requested=()=>faceAdditionRequest(source,donor.value,Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])),faceId);
  function refresh(){if(!current()){dispose();return;}let valid=false;try{valid=!!source&&!!requested();}catch{}donor.disabled=pending;for(const [field,input] of Object.entries(inputs))input.disabled=pending||!source||field!=='vertices'&&source.objects[source.topology.faces.find(f=>f.face_id===donor.value)?.object_index]?.primitives[source.topology.faces.find(f=>f.face_id===donor.value)?.current_primitive_index]?.[field]===null;reviewButton.disabled=pending||busy()||!valid;applyButton.disabled=reviewButton.disabled||!review;close.disabled=applying;}
  function invalidate(){generation++;review=null;reviewedRequest=null;comparison.hidden=true;refresh();}
  async function request(route,body){controller=new AbortController();const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)fail(value.error||'Face addition request failed.');return value;}
  function begin(){pending=true;ownedBusy=true;setBusy(true);refresh();}
  function end(){pending=false;controller=null;release();refresh();}
  function draw(){if(!review||!renderer||comparison.hidden||!current())return;const rect=canvas.getBoundingClientRect(),bounds=review.preview.bounds,center=bounds.min.map((v,i)=>(v+bounds.max[i])/2),radius=Math.max(1,Math.hypot(...bounds.max.map((v,i)=>v-bounds.min[i]))/2),c=Math.cos(view.yaw),s=Math.sin(view.yaw),cp=Math.cos(view.pitch),sp=Math.sin(view.pitch);renderer.draw({width:rect.width,height:rect.height,positions:new Map(),wireframe:true,grid:false,camera:{target:{x:center[0],y:-center[1],z:center[2]},distance:radius*3/view.zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
  canvas.onpointerdown=e=>{if(e.button!==0||!review)return;drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);};
  canvas.onpointermove=e=>{if(!drag)return;view.yaw+=(e.clientX-drag.x)*.012;view.pitch=Math.max(-1.4,Math.min(1.4,view.pitch+(e.clientY-drag.y)*.012));drag={x:e.clientX,y:e.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
  const zoom=factor=>{view.zoom=Math.max(.15,Math.min(8,view.zoom*factor));draw();};
  canvas.addEventListener('wheel',e=>{if(review){e.preventDefault();zoom(Math.exp(-e.deltaY*.001));}},{passive:false});
  canvas.onkeydown=e=>{if(!review)return;if(e.key==='+'||e.key==='=')zoom(1.2);else if(e.key==='-')zoom(1/1.2);else if(e.key==='ArrowLeft')view.yaw-=.12;else if(e.key==='ArrowRight')view.yaw+=.12;else if(e.key==='ArrowUp')view.pitch=Math.max(-1.4,view.pitch-.12);else if(e.key==='ArrowDown')view.pitch=Math.min(1.4,view.pitch+.12);else return;e.preventDefault();draw();};
  function load(){renderer??=new SceneRenderer(canvas);const preview=layer.value==='current'?review.current_preview:review.preview;const failures=renderer.load({assets:[{geometry_key:'addition',preview}],entities:[{entity_id:'addition',geometry_key:'addition',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(failures.length)fail(failures.join('; '));draw();}
  function populate(){const identity=source.topology.faces.find(f=>f.face_id===donor.value),row=source.objects[identity.object_index].primitives[identity.current_primitive_index];for(const [field,input] of Object.entries(inputs)){input.value=row[field]===null?'':row[field].map(v=>Array.isArray(v)?v.join(','):v).join(Array.isArray(row[field]?.[0])?';':',');if(field!=='vertices')dialog.querySelector(`[data-${field}]`).hidden=row[field]===null;}invalidate();status.textContent=`Object ${identity.object_index}, face ${identity.current_primitive_index} · ${row.corner_count} corners. Separate pairs/colors with semicolons.`;}
  donor.onchange=populate;for(const input of Object.values(inputs))input.oninput=invalidate;layer.onchange=()=>{try{load();}catch(e){status.textContent=e.message;}};
  reviewButton.onclick=async()=>{refresh();if(reviewButton.disabled)return;const asked=requested();invalidate();const token=generation;begin();try{const value=await request('/api/model-face-addition-preview',{asset_id:assetId,source_key:context.sourceKey,expected_sha256:source.effective_sha256,requests:[asked]});if(!current()||token!==generation)return;review=decodeFaceAdditionReview(value,source,asked);reviewedRequest=structuredClone(asked);comparison.hidden=false;layer.value='proposed';load();status.textContent='One new face reviewed. Nothing applied.';}catch(e){if(current()&&e.name!=='AbortError'){invalidate();status.textContent=e.message;onError(e);}}finally{end();}};
  applyButton.onclick=async()=>{refresh();if(applyButton.disabled)return;if(!same(requested(),reviewedRequest)){invalidate();return;}const accepted=review,asked=structuredClone(reviewedRequest);applying=true;begin();try{const value=await request('/api/model-face-addition',{asset_id:assetId,source_key:context.sourceKey,expected_sha256:source.effective_sha256,requests:[asked],proposed_sha256:accepted.proposed_sha256});if(!current())return;applying=false;dispose();await onApplied(value);}catch(e){if(current()){invalidate();status.textContent=e.message;onError(e);}}finally{applying=false;end();}};
  close.onclick=()=>{if(!applying)dispose();};dialog.oncancel=event=>{if(applying)event.preventDefault();};dialog.onclose=dispose;globalThis.addEventListener?.('resize',draw);dialog.showModal();begin();
  try{const value=await request('/api/model-face-addition-source',{asset_id:assetId,source_key:context.sourceKey});if(!current()){dispose();return null;}source=decodeFaceAdditionSource(value,assetId,context.sourceKey);for(const face of source.topology.faces){const option=document.createElement('option');option.value=face.face_id;option.textContent=`Object ${face.object_index} · face ${face.current_primitive_index}${face.origin==='authored'?' · authored':''}`;donor.append(option);}if(source.topology.faces.length)populate();else status.textContent='No existing donor faces.';}catch(e){if(current()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}finally{end();}
  return {dialog,dispose,updateState:refresh};
}

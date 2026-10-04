import {SceneRenderer} from './scene-renderer.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const fail=message=>{throw new Error(message);};
const vector=row=>Array.isArray(row)&&row.length===3&&row.every(v=>Number.isSafeInteger(v)&&v>=-32768&&v<=32767);
export function decodeVectorAllocationSource(value,asset,key){
  if(value?.schema_version!=='legaia.model-vector-allocation-source.v1'||value.asset_id!==asset||value.project_source_key!==key||!hash(key)||!hash(value.source_sha256)||!hash(value.effective_sha256)||value.project_changed!==false||value.gameplay_verified!==false||value.new_vector_limit!==4096||value.addressable_table_limit!==8192||!integer(value.allocated_vector_count,4096)||value.remaining_vector_budget!==4096-value.allocated_vector_count)fail('Vector allocation source differs from this model.');
  const objects=value.objects,audit=value.topology,preview=value.preview;
  if(!Array.isArray(objects)||!objects.length||objects.length>1024||objects.some((obj,i)=>obj.object_index!==i||!integer(obj.vertex_count,524288)||!integer(obj.normal_count,524288)||!integer(obj.primitive_count,65535))||!audit||audit.proposed_sha256!==value.effective_sha256||!hash(audit.source_sha256)||!integer(audit.proposed_byte_length,4194304)||!Array.isArray(audit.faces)||!preview||!Array.isArray(preview.objects)||preview.objects.length!==objects.length||!Array.isArray(preview.vertices))fail('Missing vector table ownership.');
  if((audit.allocated_vector_count??0)!==value.allocated_vector_count)fail('Allocated vector budget conflicts.');
  const ids=new Set(),owners=objects.map(()=>new Set());
  for(const face of audit.faces){
    const obj=objects[face?.object_index];if(!integer(face?.object_index,objects.length-1)||!obj||!integer(face.group_index,65535)||!integer(face.current_primitive_index,obj.primitive_count-1)||ids.has(face.face_id)||owners[face.object_index].has(face.current_primitive_index))fail('Conflicting stable face ownership.');
    if(face.origin==='source'){if(!integer(face.source_primitive_index,65535)||face.face_id!==`face://source/${audit.source_sha256}/${face.object_index}/${face.source_primitive_index}`)fail('Invalid retained face identity.');}
    else if(face.origin!=='authored'||typeof face.face_id!=='string'||!/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(face.face_id)||typeof face.donor_face_id!=='string')fail('Invalid authored face identity.');
    ids.add(face.face_id);owners[face.object_index].add(face.current_primitive_index);
  }
  if(owners.some((rows,i)=>rows.size!==objects[i].primitive_count))fail('Incomplete stable face coverage.');
  let count=0;
  for(const [i,obj] of preview.objects.entries()){
    if(obj.object_index!==i||obj.vertex_start!==count||obj.vertex_count!==objects[i].vertex_count)fail('Preview vector ranges contradict native tables.');
    count+=obj.vertex_count;
  }
  if(count!==preview.vertices.length||preview.vertices.some(row=>!vector(row)))fail('Invalid Current XYZ geometry.');
  if(!Array.isArray(preview.triangles)||!preview.triangles.length||preview.triangles.length>200000)fail('Invalid Current face geometry.');
  let triangles=0;for(const [i,obj] of preview.objects.entries()){
    if(obj.triangle_start!==triangles||!integer(obj.triangle_count,objects[i].primitive_count*2)||obj.triangle_count<objects[i].primitive_count)fail('Current face ranges contradict primitive counts.');
    for(const row of preview.triangles.slice(triangles,triangles+obj.triangle_count))if(!Array.isArray(row)||row.length!==3||row.some(index=>!integer(index,count-1)||index<obj.vertex_start||index>=obj.vertex_start+obj.vertex_count))fail('Current faces escape their vector owner.');
    triangles+=obj.triangle_count;
  }
  if(triangles!==preview.triangles.length)fail('Incomplete Current face ranges.');
  if(audit.proposed_byte_length<12+objects.length*28+objects.reduce((n,obj)=>n+(obj.vertex_count+obj.normal_count)*8,0))fail('Current vector tables exceed their model allocation.');
  return structuredClone(value);
}
function qualifyRequests(source,requests){
  if(!Array.isArray(requests)||!requests.length||requests.length>2048)fail('Choose at least one vector table.');
  const seen=new Set();let count=0;
  for(const row of requests){
    if(!row||Object.keys(row).length!==3||!integer(row.object_index,source.objects.length-1)||!['vertices','normals'].includes(row.kind)||!Array.isArray(row.vectors)||!row.vectors.length||row.vectors.some(v=>!vector(v)))fail('New rows require an object, table and signed integer XYZ.');
    const id=`${row.object_index}:${row.kind}`,before=source.objects[row.object_index][row.kind==='vertices'?'vertex_count':'normal_count'];
    if(seen.has(id)||before+row.vectors.length>source.addressable_table_limit)fail('Duplicate table or native vector addressing limit exceeded.');
    seen.add(id);count+=row.vectors.length;
  }
  if(count>source.new_vector_limit||count>source.remaining_vector_budget)fail('New rows exceed the remaining allocation budget.');
  return count;
}
export function vectorAllocationRequests(source,owner,kind,text){
  if(typeof text!=='string'||text.length>131072)fail('Enter bounded XYZ rows.');
  const rows=text.trim()?text.trim().split(/\r?\n/).filter(row=>row.trim()).map(row=>{
    const words=row.split(',').map(word=>word.trim());if(words.length!==3||words.some(word=>!/^[-+]?\d+$/.test(word)))fail('Use one comma-separated XYZ triple per line.');return words.map(Number);
  }):[];
  const requests=[{object_index:owner,kind,vectors:rows}];qualifyRequests(source,requests);return requests;
}
export function decodeVectorAllocationReview(value,source,requests){
  decodeVectorAllocationSource(source,source.asset_id,source.project_source_key);const count=qualifyRequests(source,requests),allocation=value?.allocation,audit=value?.topology;
  if(value?.schema_version!=='legaia.model-vector-allocation-review.v1'||value.asset_id!==source.asset_id||value.project_source_key!==source.project_source_key||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||!hash(value.proposed_sha256)||value.proposed_sha256===source.effective_sha256||value.project_changed!==false||value.gameplay_verified!==false||!same(value.requests,requests)||!allocation||allocation.source_sha256!==source.effective_sha256||allocation.proposed_sha256!==value.proposed_sha256||allocation.source_byte_length!==source.topology.proposed_byte_length||allocation.growth_bytes!==count*8||allocation.proposed_byte_length!==allocation.source_byte_length+count*8||allocation.proposed_byte_length>4194304||!audit||audit.proposed_sha256!==value.proposed_sha256||audit.source_sha256!==source.topology.source_sha256||audit.allocated_vector_count!==source.allocated_vector_count+count||audit.vector_allocation_count!==(source.topology.vector_allocation_count??0)+1||!same(audit.faces,source.topology.faces)||!same(audit.removed_face_ids??[],source.topology.removed_face_ids??[]))fail('Vector allocation review differs from inspected requests or ownership.');
  if(!Array.isArray(allocation.new_vectors)||allocation.new_vectors.length!==requests.length)fail('Incomplete new row allocation.');
  const seen=new Set();
  for(const row of allocation.new_vectors){const req=requests.find(req=>req.object_index===row.object_index&&req.kind===row.kind),id=`${row.object_index}:${row.kind}`;
    if(!req||seen.has(id)||row.first_index!==source.objects[row.object_index][row.kind==='vertices'?'vertex_count':'normal_count']||row.added_count!==req.vectors.length||!integer(row.byte_offset,allocation.proposed_byte_length-row.added_count*8)||row.byte_offset<12+source.objects.length*28)fail('New vector range contradicts its table owner.');seen.add(id);
  }
  if(!Array.isArray(allocation.pointer_relocations)||allocation.pointer_relocations.length!==source.objects.length*3)fail('Incomplete table pointer relocations.');
  const pointers=new Set();for(const row of allocation.pointer_relocations){const id=`${row.object_index}:${row.table_field_offset}`;if(Object.keys(row).length!==4||!integer(row.object_index,source.objects.length-1)||![0,8,16].includes(row.table_field_offset)||!integer(row.source_offset,allocation.source_byte_length-12)||!integer(row.current_offset,allocation.proposed_byte_length-12)||pointers.has(id))fail('Invalid or duplicate table pointer relocation.');pointers.add(id);}
  const spans=allocation.new_vectors.map(row=>{const field=row.kind==='vertices'?0:8,pointer=allocation.pointer_relocations.find(pointer=>pointer.object_index===row.object_index&&pointer.table_field_offset===field);if(row.byte_offset!==12+pointer.current_offset+row.first_index*8)fail('New rows do not follow their rebased vector table.');return [row.byte_offset,row.byte_offset+row.added_count*8];}).sort((a,b)=>a[0]-b[0]);
  if(spans.some((row,i)=>i&&row[0]<spans[i-1][1]))fail('New vector row spans overlap.');
  const before=value.current_preview,after=value.preview;
  if(!same(before,source.preview)||!after||!Array.isArray(after.objects)||after.objects.length!==source.objects.length||!Array.isArray(after.vertices))fail('Current preview or Proposed object ownership differs.');
  const remap=new Map();let total=0;
  for(const [i,obj] of before.objects.entries()){
    const next=after.objects[i],extra=requests.find(req=>req.object_index===i&&req.kind==='vertices')?.vectors??[];
    if(next.object_index!==i||next.vertex_start!==total||next.vertex_count!==obj.vertex_count+extra.length||next.triangle_start!==obj.triangle_start||next.triangle_count!==obj.triangle_count)fail('Proposed vector counts or face ranges differ.');
    if(!same(after.vertices.slice(total,total+obj.vertex_count),before.vertices.slice(obj.vertex_start,obj.vertex_start+obj.vertex_count))||!same(after.vertices.slice(total+obj.vertex_count,total+next.vertex_count),extra))fail('Allocation changed existing vertices or proposed XYZ.');
    for(let j=0;j<obj.vertex_count;j++)remap.set(obj.vertex_start+j,total+j);total+=next.vertex_count;
  }
  if(after.vertices.length!==total||!same(after.triangles,before.triangles.map(triangle=>triangle.map(index=>remap.get(index)))))fail('Allocation changed retained face references.');
  for(const field of ['materials','triangle_colors','triangle_uvs','triangle_materials','triangle_normals'])if(!same(before[field],after[field]))fail('Allocation changed retained face content.');
  return structuredClone(value);
}

export async function openModelVectorAllocation({assetId,getContext,busy,setBusy,onApplied,onError}){
  const context=structuredClone(getContext()),key=JSON.stringify(context),dialog=document.createElement('dialog');dialog.id='model-vector-allocation-dialog';dialog.className='model-dialog';
  dialog.innerHTML='<div class="dialog-heading"><h2>Add model vectors</h2><button type="button" aria-label="Close vector allocation">×</button></div><p>Add object-local vertices or stored normals. Existing indices stay unchanged. New rows become available to face editing; this operation does not add faces or recompute normals.</p><label>Object<select aria-label="Vector allocation object"></select></label><label>Table<select aria-label="Vector allocation table"><option value="vertices">Vertices</option><option value="normals">Normals</option></select></label><p data-count></p><label>XYZ rows<textarea aria-label="New vector XYZ rows" placeholder="100, 200, 300&#10;400, 500, 600"></textarea></label><p>One comma-separated XYZ triple per line. Coordinates are signed integers from -32768 to 32767.</p><button type="button" data-review>Preview vector allocation</button><button type="button" data-apply disabled>Apply reviewed vector allocation</button><p role="status"></p><section data-comparison hidden><label>Preview layer<select aria-label="Vector allocation preview layer"><option value="proposed">Proposed</option><option value="current">Current</option></select></label><canvas aria-label="Vector allocation model comparison" style="display:block;width:100%;height:320px"></canvas><p>Drag to orbit · Scroll to zoom. Unreferenced vectors do not create visible faces.</p></section>';
  document.body.append(dialog);
  const object=dialog.querySelector('[aria-label="Vector allocation object"]'),table=dialog.querySelector('[aria-label="Vector allocation table"]'),input=dialog.querySelector('textarea'),status=dialog.querySelector('[role=status]'),reviewButton=dialog.querySelector('[data-review]'),applyButton=dialog.querySelector('[data-apply]'),comparison=dialog.querySelector('[data-comparison]'),layer=comparison.querySelector('select'),canvas=comparison.querySelector('canvas');
  let source=null,review=null,pending=false,closed=false,generation=0,renderer=null,view=null,drag=null,controller=null;
  const current=()=>!closed&&JSON.stringify(getContext())===key&&context.mode==='edit';
  const requests=()=>vectorAllocationRequests(source,Number(object.value),table.value,input.value);
  function refresh(){if(!current()){review=null;comparison.hidden=true;}let valid=false;try{valid=!!source&&!!requests().length;}catch{}reviewButton.disabled=!current()||pending||busy()||!valid;applyButton.disabled=reviewButton.disabled||!review;object.disabled=table.disabled=input.disabled=pending||!current();}
  function invalidate(){generation++;review=null;comparison.hidden=true;refresh();}
  async function request(route,body){controller=new AbortController();const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)fail(value.error||'Vector allocation failed');return value;}
  function draw(){if(!renderer||!view||comparison.hidden||!current())return;const rect=canvas.getBoundingClientRect(),c=Math.cos(view.yaw),s=Math.sin(view.yaw),cp=Math.cos(view.pitch),sp=Math.sin(view.pitch);renderer.draw({width:rect.width,height:rect.height,positions:new Map(),wireframe:true,grid:false,camera:{target:{x:view.center[0],y:-view.center[1],z:view.center[2]},distance:view.radius*4/view.zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
  function load(){renderer??=new SceneRenderer(canvas,message=>{if(message&&!closed)status.textContent=message;});const preview=layer.value==='current'?review.current_preview:review.preview,failures=renderer.load({assets:[{geometry_key:'vector-allocation',preview}],entities:[{entity_id:'vector-allocation',geometry_key:'vector-allocation',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(failures.length)fail(failures.join('; '));draw();}
  function changed(){invalidate();if(source){const count=source.objects[Number(object.value)][table.value==='vertices'?'vertex_count':'normal_count'];dialog.querySelector('[data-count]').textContent=`${count} Current rows · new indices start at ${count} · ${source.remaining_vector_budget} rows remaining · table limit ${source.addressable_table_limit}`;}}
  object.onchange=table.onchange=changed;input.oninput=invalidate;
  reviewButton.onclick=async()=>{refresh();if(reviewButton.disabled)return;const proposed=requests();invalidate();const token=generation;pending=true;setBusy(true);refresh();try{const value=await request('/api/model-vector-allocation-preview',{asset_id:assetId,requests:proposed,expected_sha256:source.effective_sha256,source_key:context.sourceKey});if(!current()||generation!==token)return;review=decodeVectorAllocationReview(value,source,proposed);const points=review.current_preview.triangles.flatMap(triangle=>triangle.map(index=>review.current_preview.vertices[index])),min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(const point of points)for(let i=0;i<3;i++){min[i]=Math.min(min[i],point[i]);max[i]=Math.max(max[i],point[i]);}view={center:min.map((v,i)=>(v+max[i])/2),radius:Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2),yaw:.6,pitch:.4,zoom:1};comparison.hidden=false;layer.value='proposed';status.textContent=review.allocation.new_vectors.map(row=>`Object ${row.object_index} ${row.kind}: indices ${row.first_index}–${row.first_index+row.added_count-1}`).join(' · ')+' · not applied';load();}catch(error){if(current()){invalidate();status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}};
  applyButton.onclick=async()=>{refresh();if(applyButton.disabled)return;const proposed=requests(),accepted=review;pending=true;setBusy(true);refresh();try{const value=await request('/api/model-vector-allocation',{asset_id:assetId,requests:proposed,expected_sha256:source.effective_sha256,source_key:context.sourceKey,proposed_sha256:accepted.proposed_sha256});if(!current())return;pending=false;dispose();await onApplied(value);}catch(error){if(current()){status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}};
  layer.onchange=()=>{if(review&&current())try{load();}catch(error){status.textContent=error.message;onError(error);}};
  canvas.onpointerdown=event=>{canvas.setPointerCapture(event.pointerId);drag={x:event.clientX,y:event.clientY};};canvas.onpointermove=event=>{if(!drag||!view)return;view.yaw+=(event.clientX-drag.x)*.009;view.pitch+=(event.clientY-drag.y)*.009;drag={x:event.clientX,y:event.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;canvas.onwheel=event=>{event.preventDefault();if(view){view.zoom=Math.max(.15,Math.min(2.5,view.zoom*Math.exp(-event.deltaY*.001)));draw();}};
  function dispose(){if(closed)return;closed=true;controller?.abort();renderer?.dispose?.();if(dialog.open)dialog.close();dialog.remove();}
  dialog.querySelector('[aria-label="Close vector allocation"]').onclick=()=>{if(!pending)dispose();};dialog.oncancel=event=>{if(pending)event.preventDefault();};dialog.onclose=dispose;dialog.showModal();pending=true;setBusy(true);refresh();
  try{const value=await request('/api/model-vector-allocation-source',{asset_id:assetId,source_key:context.sourceKey});if(!current())return;source=decodeVectorAllocationSource(value,assetId,context.sourceKey);for(const obj of source.objects){const option=document.createElement('option');option.value=String(obj.object_index);option.textContent=`Object ${obj.object_index}`;object.append(option);}changed();}catch(error){if(current()){status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}
  return {dialog,dispose,updateState:refresh};
}

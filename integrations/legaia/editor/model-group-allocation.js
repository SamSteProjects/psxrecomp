import {SceneRenderer} from './scene-renderer.js';
import {decodeFaceAdditionSource,faceAdditionRequest} from './model-face-addition.js';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const integer=(v,max)=>Number.isSafeInteger(v)&&v>=0&&v<=max;
const fail=message=>{throw new Error(message);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&same(Object.keys(v).sort(),keys.sort());
const uuid=(v,kind)=>typeof v==='string'&&new RegExp(`^${kind}://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`).test(v);
const vector=v=>Array.isArray(v)&&v.length===3&&v.every(n=>Number.isSafeInteger(n)&&n>=-32768&&n<=32767);
function faceSource(source){return decodeFaceAdditionSource({...source,schema_version:'legaia.model-face-addition-source.v1'},source.asset_id,source.project_source_key);}
export function renderPackets(objects,vertices,normalVectors){
  const result={triangles:[],triangle_colors:[],triangle_uvs:[],triangle_normals:[],triangle_materials:[],materials:[],objects:[]};
  let vertexStart=0;
  for(const [owner,obj] of objects.entries()){
    const triangleStart=result.triangles.length;
    for(const row of obj.primitives){
      const material={textured:row.uvs!==null,clut:row.material.clut,tpage:row.material.tpage,semi_transparent:row.material.semi_transparent};
      let materialIndex=result.materials.findIndex(old=>same(old,material));if(materialIndex<0){materialIndex=result.materials.length;result.materials.push(material);}
      const corners=row.corner_count,colors=row.colors===null?Array(corners).fill([128,128,128]):row.gouraud?row.colors:Array(corners).fill(row.colors[0]);
      const normals=row.normal_indices===null?null:(row.gouraud?row.normal_indices:Array(corners).fill(row.normal_indices[0])).map(index=>normalVectors[owner][index]);
      for(const use of corners===4?[[0,1,2],[1,3,2]]:[[0,1,2]]){
        result.triangles.push(use.map(i=>vertexStart+row.vertices[i]));result.triangle_colors.push(use.map(i=>colors[i]));
        result.triangle_uvs.push(row.uvs===null?null:use.map(i=>row.uvs[i]));result.triangle_normals.push(normals===null?null:use.map(i=>normals[i]));
        result.triangle_materials.push(materialIndex);
      }
    }
    result.objects.push({object_index:owner,vertex_start:vertexStart,vertex_count:obj.vertex_count,triangle_start:triangleStart,triangle_count:result.triangles.length-triangleStart});
    vertexStart+=obj.vertex_count;
  }
  if(vertexStart!==vertices.length)fail('Group geometry has incomplete vector ranges.');
  return result;
}
export function qualifyRender(preview,expected,vertices){
  if(!preview||preview.coordinate_system!=='retail_tmd_object_local'||!same(preview.vertices,vertices))fail('Group geometry changed Current vector coordinates.');
  for(const key of ['triangles','triangle_colors','triangle_uvs','triangle_normals','triangle_materials','materials'])if(!same(preview[key],expected[key]))fail(`Group geometry differs from typed packet ${key}.`);
  if(!Array.isArray(preview.objects)||preview.objects.length!==expected.objects.length||preview.objects.some((obj,i)=>Object.entries(expected.objects[i]).some(([key,value])=>obj[key]!==value)))fail('Group geometry changed native object ranges.');
}
export function decodeGroupAllocationSource(value,asset,key){
  if(value?.schema_version!=='legaia.model-group-allocation-source.v1'||value.group_limit!==64||value.face_limit!==128)fail('Invalid group allocation source.');
  const source=faceSource(value),audit=source.topology;
  if(value.asset_id!==asset||value.project_source_key!==key||!integer(value.allocated_group_count,64)||value.allocated_group_count!==(audit.allocated_group_count??0)||value.remaining_group_budget!==64-value.allocated_group_count||value.remaining_face_budget!==128-audit.authored_face_count||value.remaining_batch_budget!==8-audit.batch_count||!integer(audit.operation_count,64)||value.remaining_operation_budget!==64-audit.operation_count||!Array.isArray(value.normal_vectors)||value.normal_vectors.length!==source.objects.length||value.normal_vectors.some((rows,i)=>!Array.isArray(rows)||rows.length!==source.objects[i].normal_count||rows.some(row=>!vector(row))))fail('Group allocation budgets or stored normal ownership differ.');
  if(!Array.isArray(value.packet_groups)||value.packet_groups.length!==source.objects.length)fail('Missing native packet-group allocation evidence.');
  for(const [owner,records] of value.packet_groups.entries()){
    if(!Array.isArray(records))fail('Invalid native packet-group evidence.');let first=0;
    for(const [index,record] of records.entries()){
      if(!exact(record,['group_index','byte_offset','primitive_count','first_primitive_index','stride','flags','mode','descriptor_sha256','footer_sha256'])||record.group_index!==index||record.first_primitive_index!==first||!integer(record.primitive_count,65535)||!integer(record.byte_offset,audit.proposed_byte_length-8)||record.byte_offset<12+source.objects.length*28||!integer(record.stride,1020)||record.stride<12||record.stride%4||record.byte_offset+8+(record.primitive_count+1)*record.stride>audit.proposed_byte_length||!integer(record.flags,0x27)||record.flags<0x10||!integer(record.mode,255)||!hash(record.descriptor_sha256)||!hash(record.footer_sha256))fail('Invalid native group descriptor, stride or footer owner.');
      for(let j=0;j<record.primitive_count;j++){const row=source.objects[owner].primitives[first+j];if(!row||row.group_index!==index||row.byte_offset!==record.byte_offset+8+j*record.stride||row.flags!==record.flags||row.material.semi_transparent!==!!(record.mode&2))fail('Current packet rows differ from their native group descriptor.');}
      first+=record.primitive_count;
    }
    if(first!==source.objects[owner].primitives.length)fail('Incomplete native packet-group evidence.');
  }
  if(!Array.isArray(value.table_offsets)||value.table_offsets.length!==source.objects.length||value.table_offsets.some((rows,i)=>!Array.isArray(rows)||rows.length!==3||rows.some((v,j)=>!integer(v,(j===0?source.objects[i].vertex_count:j===1?source.objects[i].normal_count:1)?audit.proposed_byte_length-12:0xffffffff))||value.packet_groups[i].length&&rows[2]!==value.packet_groups[i][0].byte_offset-12))fail('Invalid Current table pointer ownership.');
  if(!Array.isArray(value.limitations)||!value.limitations.length||value.limitations.some(line=>typeof line!=='string'||line.length>4096))fail('Missing group allocation scope.');
  qualifyRender(value.preview,renderPackets(value.objects,value.preview.vertices,value.normal_vectors),value.preview.vertices);
  return structuredClone(value);
}
function qualifyRequests(source,requests){
  if(!Array.isArray(requests)||!requests.length||requests.length>source.remaining_group_budget||source.remaining_batch_budget<1||source.remaining_operation_budget<1)fail('Group allocation exceeds the remaining authoring budget.');
  const ids=new Set(source.topology.faces.map(row=>row.face_id).concat(source.topology.removed_face_ids??[])),groupIds=new Set((source.topology.allocated_groups??[]).map(row=>row.group_id));let faces=0;
  for(const group of requests){
    const donor=source.topology.faces.find(row=>row.face_id===group?.donor_face_id);
    if(!exact(group,['group_id','donor_face_id','faces'])||!uuid(group.group_id,'group')||groupIds.has(group.group_id)||!donor||!Array.isArray(group.faces)||!group.faces.length)fail('Choose a Current group donor and new stable identities.');
    groupIds.add(group.group_id);
    for(const face of group.faces){
      const owner=source.topology.faces.find(row=>row.face_id===face?.donor_face_id),packet=source.objects[owner?.object_index]?.primitives[owner?.current_primitive_index];
      if(!exact(face,['face_id','donor_face_id','fields'])||!uuid(face.face_id,'face')||ids.has(face.face_id)||!owner||owner.object_index!==donor.object_index||owner.group_index!==donor.group_index||!face.fields||!Object.hasOwn(face.fields,'vertices')||Object.keys(face.fields).some(key=>!['vertices','uvs','colors','normal_indices'].includes(key)))fail('New group faces must have typed fields and donors in the selected Current group.');
      ids.add(face.face_id);faces++;
      for(const [key,values] of Object.entries(face.fields)){
        const template=packet[key],width=key==='uvs'?2:key==='colors'?3:1,max=key==='vertices'?Math.min(8191,source.objects[owner.object_index].vertex_count-1):key==='normal_indices'?Math.min(8191,source.objects[owner.object_index].normal_count-1):255;
        if(template===null||!Array.isArray(values)||values.length!==template.length||values.some(row=>width===1?!integer(row,max):!Array.isArray(row)||row.length!==width||row.some(v=>!integer(v,max))))fail('Typed group face fields exceed their native packet domain.');
      }
    }
  }
  if(faces>source.remaining_face_budget)fail('Group faces exceed the remaining authored face budget.');
  return faces;
}
export function groupAllocationRequest(source,donor,texts,groupId,faceId){
  const face=faceAdditionRequest(faceSource(source),donor,texts,faceId),request={group_id:groupId,donor_face_id:donor,faces:[face]};
  qualifyRequests(source,[request]);return request;
}
export function decodeGroupAllocationReview(value,source,requests){
  source=decodeGroupAllocationSource(source,source.asset_id,source.project_source_key);const count=qualifyRequests(source,requests),allocation=value?.allocation,audit=value?.topology;
  if(value?.schema_version!=='legaia.model-group-allocation-review.v1'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.proposed_sha256===source.effective_sha256||!hash(value.review_key)||value.project_changed!==false||value.gameplay_verified!==false||!same(value.requests,requests)||!same(value.current_preview,source.preview)||!allocation||allocation.source_sha256!==source.effective_sha256||allocation.proposed_sha256!==value.proposed_sha256||allocation.source_byte_length!==source.topology.proposed_byte_length||!integer(allocation.proposed_byte_length,4194304)||allocation.proposed_byte_length!==allocation.source_byte_length+allocation.growth_bytes||!same(value.limitations,source.limitations)||!audit||audit.proposed_byte_length!==allocation.proposed_byte_length||audit.proposed_sha256!==value.proposed_sha256||audit.source_sha256!==source.topology.source_sha256||audit.authored_face_count!==source.topology.authored_face_count+count||audit.batch_count!==source.topology.batch_count+1||audit.operation_count!==source.topology.operation_count+1||audit.allocated_group_count!==source.allocated_group_count+requests.length||audit.group_allocation_count!==(source.topology.group_allocation_count??0)+1||!same(audit.removed_face_ids??[],source.topology.removed_face_ids??[])||(audit.allocated_vector_count??0)!==(source.topology.allocated_vector_count??0)||(audit.vector_allocation_count??0)!==(source.topology.vector_allocation_count??0))fail('Group review differs from inspected requests and ownership.');
  if(!Array.isArray(allocation.new_groups)||allocation.new_groups.length!==requests.length||!Array.isArray(allocation.new_faces)||allocation.new_faces.length!==count||!Array.isArray(allocation.retained_faces)||allocation.retained_faces.length!==source.topology.faces.length||!Array.isArray(audit.faces)||audit.faces.length!==source.topology.faces.length+count)fail('Incomplete group allocation audit.');
  const proposed=structuredClone(source.objects),byId=new Map(audit.faces.map(row=>[row.face_id,row])),groupRecords=source.topology.allocated_groups??[];
  if(byId.size!==audit.faces.length||!Array.isArray(audit.allocated_groups)||!same(audit.allocated_groups.slice(0,groupRecords.length),groupRecords))fail('Group review changed existing stable group records.');
  for(const face of source.topology.faces){if(!same(byId.get(face.face_id),face))fail('Group allocation remapped a retained face.');const mapping=allocation.retained_faces.find(row=>row.object_index===face.object_index&&row.source_primitive_index===face.current_primitive_index);if(!same(mapping,{object_index:face.object_index,source_primitive_index:face.current_primitive_index,current_primitive_index:face.current_primitive_index}))fail('Group allocation changed retained native indices.');}
  const insertions=new Map();for(const group of requests){const donor=source.topology.faces.find(row=>row.face_id===group.donor_face_id),owner=donor.object_index,last=source.packet_groups[owner].at(-1),stride=source.packet_groups[owner][donor.group_index].stride,old=insertions.get(owner);insertions.set(owner,{at:last.byte_offset+8+(last.primitive_count+1)*last.stride,growth:(old?.growth??0)+8+(group.faces.length+1)*stride});}
  let growth=0;const spans=[],ownerGrowth=new Map(),groupCounts=source.packet_groups.map(rows=>rows.length);
  for(const group of requests){
    const donor=source.topology.faces.find(row=>row.face_id===group.donor_face_id),owner=donor.object_index,obj=proposed[owner],groupIndex=groupCounts[owner]++,rows=source.objects[owner].primitives.filter(row=>row.group_index===donor.group_index),donorGroup=source.packet_groups[owner][donor.group_index];
    const native=allocation.new_groups.find(row=>row.group_id===group.group_id),record=audit.allocated_groups.find(row=>row.group_id===group.group_id),expectedFaces=[];
    if(!native||native.object_index!==owner||native.group_index!==groupIndex||native.donor_group_index!==donor.group_index||!hash(native.descriptor_sha256)||native.footer_sha256!==donorGroup.footer_sha256||!integer(native.byte_offset,allocation.proposed_byte_length-1)||!integer(native.byte_length,4194304)||native.byte_length<16||(native.byte_length-8)%(group.faces.length+1))fail('New group descriptor/footer ownership differs.');
    const packetStride=(native.byte_length-8)/(group.faces.length+1);
    if(packetStride!==donorGroup.stride)fail('New group packet stride differs from its donor.');
    const insertion=insertions.get(owner),expectedOffset=insertion.at+[...insertions.values()].filter(row=>row.at<insertion.at).reduce((sum,row)=>sum+row.growth,0)+(ownerGrowth.get(owner)??0);
    if(native.byte_offset!==expectedOffset)fail('New group is not at the qualified owner terminator.');ownerGrowth.set(owner,(ownerGrowth.get(owner)??0)+native.byte_length);
    spans.push([native.byte_offset,native.byte_offset+native.byte_length]);growth+=native.byte_length;
    for(const [index,face] of group.faces.entries()){
      const template=source.topology.faces.find(row=>row.face_id===face.donor_face_id),packet=structuredClone(source.objects[owner].primitives[template.current_primitive_index]),primitiveIndex=obj.primitives.length;
      packet.primitive_index=primitiveIndex;packet.group_index=groupIndex;Object.assign(packet,structuredClone(face.fields));obj.primitives.push(packet);
      const expected={face_id:face.face_id,origin:'authored',object_index:owner,group_index:groupIndex,current_primitive_index:primitiveIndex,donor_face_id:face.donor_face_id};
      if(!same(byId.get(face.face_id),expected))fail('New group face identity or ordering differs.');
      const allocated=allocation.new_faces.find(row=>row.face_id===face.face_id);
      if(!allocated||allocated.group_id!==group.group_id||allocated.object_index!==owner||allocated.group_index!==groupIndex||allocated.current_primitive_index!==primitiveIndex||allocated.donor_primitive_index!==template.current_primitive_index||allocated.byte_offset!==native.byte_offset+8+index*packetStride||!hash(allocated.packet_sha256))fail('New group packet range differs from its donor.');
      expectedFaces.push(face.face_id);
    }
    if(!record||record.object_index!==owner||record.current_group_index!==groupIndex||record.donor_face_id!==group.donor_face_id||record.flags!==rows[0].flags||!integer(record.origin_group_index,65535)||record.mode!==donorGroup.mode||!same(record.face_ids,expectedFaces))fail('New stable group metadata differs from its native allocation.');
  }
  spans.sort((a,b)=>a[0]-b[0]);if(growth!==allocation.growth_bytes||spans.some((row,i)=>row[1]>allocation.proposed_byte_length||i&&row[0]<spans[i-1][1]))fail('Allocated group spans overlap or growth differs.');
  if(!Array.isArray(allocation.pointer_relocations)||allocation.pointer_relocations.length!==source.objects.length*3)fail('Missing group pointer relocation audit.');
  const pointers=new Set();for(const row of allocation.pointer_relocations){const key=`${row.object_index}:${row.table_field_offset}`;if(!exact(row,['object_index','table_field_offset','source_offset','current_offset'])||!integer(row.object_index,source.objects.length-1)||![0,8,16].includes(row.table_field_offset)||!integer(row.source_offset,0xffffffff)||!integer(row.current_offset,0xffffffff)||pointers.has(key))fail('Invalid group table pointer relocation.');const field=[0,8,16].indexOf(row.table_field_offset),used=field===2||(field===0?source.objects[row.object_index].vertex_count:source.objects[row.object_index].normal_count)>0,expected=source.table_offsets[row.object_index][field],rebased=expected+(used?[...insertions.values()].filter(part=>part.at<=expected+12).reduce((sum,part)=>sum+part.growth,0):0);if(row.source_offset!==expected||row.current_offset!==rebased)fail('Group table pointer differs from qualified relocation.');pointers.add(key);}
  qualifyRender(value.preview,renderPackets(proposed,source.preview.vertices,source.normal_vectors),source.preview.vertices);
  return structuredClone(value);
}

export async function openModelGroupAllocation({assetId,getContext,busy,setBusy,onApplied,onError=()=>{}}){
  const context=structuredClone(getContext()),contextKey=JSON.stringify(context);
  if(busy()||context.mode!=='edit')return null;
  const dialog=document.createElement('dialog');dialog.id='model-group-allocation-dialog';dialog.className='model-dialog';
  dialog.innerHTML='<div class="dialog-heading"><h2>Create packet group</h2><button type="button" aria-label="Close group allocation">×</button></div><p>Create a separate native packet group with an initial triangle or quad using existing points. The donor supplies its packet layout and material settings. Review the complete model before applying. Further faces can be added to the new group with Add model face.</p><label>Donor face<select aria-label="Packet group donor"></select></label><label>Vertex indices<input aria-label="New face vertices"></label><label data-uvs>UV pairs<input aria-label="New face UVs"></label><label data-colors>RGB colors<input aria-label="New face colors"></label><label data-normal_indices>Normal indices<input aria-label="New face normals"></label><button type="button" data-review>Review new group</button><button type="button" data-apply disabled>Apply reviewed group</button><p role="status"></p><section data-comparison hidden><label>Preview layer<select aria-label="Packet group preview layer"><option value="proposed">Proposed</option><option value="current">Current</option></select></label><canvas style="width:100%;height:280px"></canvas></section>';
  document.body.append(dialog);const donor=dialog.querySelector('[aria-label="Packet group donor"]'),status=dialog.querySelector('[role="status"]'),reviewButton=dialog.querySelector('[data-review]'),applyButton=dialog.querySelector('[data-apply]'),close=dialog.querySelector('button'),comparison=dialog.querySelector('[data-comparison]'),layer=comparison.querySelector('select'),canvas=comparison.querySelector('canvas');
  const inputs=Object.fromEntries([['vertices','vertices'],['uvs','UVs'],['colors','colors'],['normal_indices','normals']].map(([field,label])=>[field,dialog.querySelector(`[aria-label="New face ${label}"]`)]));
  const faceId=`face://authored/${crypto.randomUUID()}`,groupId=`group://authored/${crypto.randomUUID()}`;
  let source=null,review=null,reviewedRequest=null,pending=false,applying=false,closed=false,ownedBusy=false,controller=null,generation=0,renderer=null,drag=null;
  const view={yaw:.6,pitch:.4,zoom:1};canvas.tabIndex=0;canvas.style.touchAction='none';canvas.setAttribute('aria-label','Packet group comparison; drag or arrow keys to orbit, scroll or plus and minus to zoom');
  const current=()=>!closed&&dialog.open&&JSON.stringify(getContext())===contextKey;
  const release=()=>{if(ownedBusy){ownedBusy=false;setBusy(false);}};
  function dispose(){if(closed)return;closed=true;controller?.abort();release();renderer?.dispose();globalThis.removeEventListener?.('resize',draw);if(dialog.open)dialog.close();dialog.remove();}
  const requested=()=>groupAllocationRequest(source,donor.value,Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value])),groupId,faceId);
  function refresh(){if(!current()){dispose();return;}let valid=false;try{valid=!!source&&!!requested();}catch{}donor.disabled=pending;for(const [field,input] of Object.entries(inputs))input.disabled=pending||!source||field!=='vertices'&&source.objects[source.topology.faces.find(f=>f.face_id===donor.value)?.object_index]?.primitives[source.topology.faces.find(f=>f.face_id===donor.value)?.current_primitive_index]?.[field]===null;reviewButton.disabled=pending||busy()||!valid;applyButton.disabled=reviewButton.disabled||!review;close.disabled=applying;}
  function invalidate(){generation++;review=null;reviewedRequest=null;comparison.hidden=true;refresh();}
  async function request(route,body){controller=new AbortController();const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)fail(value.error||'Group allocation request failed.');return value;}
  function begin(){pending=true;ownedBusy=true;setBusy(true);refresh();}
  function end(){pending=false;controller=null;release();refresh();}
  function draw(){if(!review||!renderer||comparison.hidden||!current())return;const rect=canvas.getBoundingClientRect(),bounds=review.preview.bounds,center=bounds.min.map((v,i)=>(v+bounds.max[i])/2),radius=Math.max(1,Math.hypot(...bounds.max.map((v,i)=>v-bounds.min[i]))/2),c=Math.cos(view.yaw),s=Math.sin(view.yaw),cp=Math.cos(view.pitch),sp=Math.sin(view.pitch);renderer.draw({width:rect.width,height:rect.height,positions:new Map(),wireframe:true,grid:false,camera:{target:{x:center[0],y:-center[1],z:center[2]},distance:radius*3/view.zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
  canvas.onpointerdown=e=>{if(e.button!==0||!review)return;drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);};
  canvas.onpointermove=e=>{if(!drag)return;view.yaw+=(e.clientX-drag.x)*.012;view.pitch=Math.max(-1.4,Math.min(1.4,view.pitch+(e.clientY-drag.y)*.012));drag={x:e.clientX,y:e.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
  const zoom=factor=>{view.zoom=Math.max(.15,Math.min(8,view.zoom*factor));draw();};
  canvas.addEventListener('wheel',e=>{if(review){e.preventDefault();zoom(Math.exp(-e.deltaY*.001));}},{passive:false});
  canvas.onkeydown=e=>{if(!review)return;if(e.key==='+'||e.key==='=')zoom(1.2);else if(e.key==='-')zoom(1/1.2);else if(e.key==='ArrowLeft')view.yaw-=.12;else if(e.key==='ArrowRight')view.yaw+=.12;else if(e.key==='ArrowUp')view.pitch=Math.max(-1.4,view.pitch-.12);else if(e.key==='ArrowDown')view.pitch=Math.min(1.4,view.pitch+.12);else return;e.preventDefault();draw();};
  function load(){renderer??=new SceneRenderer(canvas);const preview=layer.value==='current'?review.current_preview:review.preview;const failures=renderer.load({assets:[{geometry_key:'addition',preview}],entities:[{entity_id:'addition',geometry_key:'addition',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(failures.length)fail(failures.join('; '));draw();}
  function populate(){const identity=source.topology.faces.find(f=>f.face_id===donor.value),row=source.objects[identity.object_index].primitives[identity.current_primitive_index];for(const [field,input] of Object.entries(inputs)){input.value=row[field]===null?'':row[field].map(v=>Array.isArray(v)?v.join(','):v).join(Array.isArray(row[field]?.[0])?';':',');if(field!=='vertices')dialog.querySelector(`[data-${field}]`).hidden=row[field]===null;}invalidate();status.textContent=`Object ${identity.object_index}, face ${identity.current_primitive_index} · ${row.corner_count} corners. Separate pairs/colors with semicolons. The initial face can use any Current points in this object.`;}
  donor.onchange=populate;for(const input of Object.values(inputs))input.oninput=invalidate;layer.onchange=()=>{try{load();}catch(e){status.textContent=e.message;}};
  reviewButton.onclick=async()=>{refresh();if(reviewButton.disabled)return;const asked=requested();invalidate();const token=generation;begin();try{const value=await request('/api/model-group-allocation-preview',{asset_id:assetId,source_key:context.sourceKey,expected_sha256:source.effective_sha256,requests:[asked]});if(!current()||token!==generation)return;review=decodeGroupAllocationReview(value,source,[asked]);reviewedRequest=structuredClone(asked);comparison.hidden=false;layer.value='proposed';load();status.textContent=`One new group with one face reviewed · ${review.allocation.growth_bytes} native bytes. Apply is one Undo step. Nothing applied.`;}catch(e){if(current()&&e.name!=='AbortError'){invalidate();status.textContent=e.message;onError(e);}}finally{end();}};
  applyButton.onclick=async()=>{refresh();if(applyButton.disabled)return;if(!same(requested(),reviewedRequest)){invalidate();return;}const accepted=review,asked=structuredClone(reviewedRequest);applying=true;begin();try{const value=await request('/api/model-group-allocation',{asset_id:assetId,source_key:context.sourceKey,expected_sha256:source.effective_sha256,requests:[asked],review_key:accepted.review_key});if(!current())return;applying=false;dispose();await onApplied(value);}catch(e){if(current()){invalidate();status.textContent=e.message;onError(e);}}finally{applying=false;end();}};
  close.onclick=()=>{if(!applying)dispose();};dialog.oncancel=event=>{if(applying)event.preventDefault();};dialog.onclose=dispose;globalThis.addEventListener?.('resize',draw);dialog.showModal();begin();
  try{const value=await request('/api/model-group-allocation-source',{asset_id:assetId,source_key:context.sourceKey});if(!current()){dispose();return null;}source=decodeGroupAllocationSource(value,assetId,context.sourceKey);for(const face of source.topology.faces){const option=document.createElement('option');option.value=face.face_id;option.textContent=`Object ${face.object_index} · group ${face.group_index} / face ${face.current_primitive_index}${face.origin==='authored'?' · authored':''}`;donor.append(option);}if(source.topology.faces.length)populate();else status.textContent='No existing donor faces.';}catch(e){if(current()&&e.name!=='AbortError'){status.textContent=e.message;onError(e);}}finally{end();}
  return {dialog,dispose,updateState:refresh};
}

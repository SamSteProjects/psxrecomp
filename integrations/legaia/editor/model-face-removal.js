import { MODEL_FACE_BUDGET } from './model-topology-limits.js';
import {SceneRenderer} from './scene-renderer.js';
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const integer=(value,max)=>Number.isSafeInteger(value)&&value>=0&&value<=max;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=message=>{throw new Error(message);};
function removedIdentities(rows,objectCount){
  if(!Array.isArray(rows)||rows.length>4096)fail('Invalid Retail removal identities.');
  const seen=new Set();for(const row of rows){if(!row||Object.keys(row).length!==2||!integer(row.object_index,objectCount-1)||!integer(row.primitive_index,65535))fail('Invalid Retail removal owner.');const id=`${row.object_index}:${row.primitive_index}`;if(seen.has(id))fail('Duplicate Retail removal owner.');seen.add(id);}
}
function stableFaceId(value){return typeof value==='string'&&(/^face:\/\/source\/[0-9a-f]{64}\/\d+\/\d+$/.test(value)||/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value));}
function deletedIds(rows){if(!Array.isArray(rows)||rows.length>65536||rows.some(id=>!stableFaceId(id))||new Set(rows).size!==rows.length)fail('Invalid deleted stable face identities.');}
function stableTopology(rows,objects,deleted=[]){
  deletedIds(deleted);if(!Array.isArray(rows)||rows.length>100000)fail('Invalid stable face topology.');const ids=new Set(deleted),owned=objects.map(()=>new Set());let authoredCount=0;
  for(const row of rows){
    const source=row?.origin==='source',keys=['face_id','origin','object_index','group_index','current_primitive_index',source?'source_primitive_index':'donor_face_id'];
    if(!row||!['source','authored'].includes(row.origin)||Object.keys(row).length!==keys.length||keys.some(key=>!Object.hasOwn(row,key))||!stableFaceId(row.face_id)||ids.has(row.face_id)||!integer(row.object_index,objects.length-1)||!integer(row.group_index,65535)||!integer(row.current_primitive_index,objects[row.object_index].primitives.length-1)||owned[row.object_index].has(row.current_primitive_index))fail('Stable face ownership conflicts.');
    if(source){const hashPart=row.face_id.split('/')[3];if(!integer(row.source_primitive_index,65535)||row.face_id!==`face://source/${hashPart}/${row.object_index}/${row.source_primitive_index}`)fail('Source face identity contradicts its owner.');}
    else if(++authoredCount>MODEL_FACE_BUDGET||!row.face_id.startsWith('face://authored/')||!stableFaceId(row.donor_face_id))fail('Invalid authored face or retained donor identity.');
    ids.add(row.face_id);owned[row.object_index].add(row.current_primitive_index);
  }
  if(owned.some((indices,i)=>indices.size!==objects[i].primitives.length))fail('Stable faces do not cover Current topology.');
}
function sameFaces(a,b){const canonical=rows=>rows.map(row=>Object.fromEntries(Object.entries(row).sort(([a],[b])=>a.localeCompare(b)))).sort((a,b)=>a.face_id.localeCompare(b.face_id));return same(canonical(a),canonical(b));}
function restorationLayout(rows,source){
  const owners=new Map([...source.restoration_owners,...source.restorable_faces.map(row=>({...row,face_id:row.face.face_id}))].map(row=>[row.face_id,row]));
  const result=structuredClone(rows);
  for(let owner=0;owner<source.objects.length;owner++){
    const faces=result.filter(row=>row.object_index===owner).sort((a,b)=>owners.get(a.face_id).origin_group_index-owners.get(b.face_id).origin_group_index||owners.get(a.face_id).stable_order-owners.get(b.face_id).stable_order);
    const groups=[...new Set(faces.map(row=>owners.get(row.face_id).origin_group_index))];
    faces.forEach((row,index)=>{row.current_primitive_index=index;row.group_index=groups.indexOf(owners.get(row.face_id).origin_group_index);});
  }
  return result;
}
function restorationSource(value){
  if(value.restoration_available!==true||value.removed_faces.length||!Array.isArray(value.restorable_faces)||value.restorable_faces.length!==value.removed_face_ids.length||!Array.isArray(value.restoration_owners)||value.restoration_owners.length!==value.face_topology.length)fail('Missing stable restoration ownership.');
  const ids=new Set(),ranks=new Set();
  for(const row of [...value.restoration_owners,...value.restorable_faces]){
    const deleted=Object.hasOwn(row,'face'),keys=deleted?['face','origin_group_index','stable_order','corner_count']:['face_id','origin_group_index','stable_order'];
    const id=deleted?row.face?.face_id:row.face_id;
    if(Object.keys(row).length!==keys.length||keys.some(key=>!Object.hasOwn(row,key))||!stableFaceId(id)||ids.has(id)||!integer(row.origin_group_index,65535)||!integer(row.stable_order,100000)||ranks.has(row.stable_order)||(deleted?![3,4].includes(row.corner_count):!value.face_topology.some(face=>face.face_id===id)))fail('Conflicting stable restoration owner or order.');
    ids.add(id);ranks.add(row.stable_order);
  }
  if(!same(value.restorable_faces.map(row=>row.face.face_id),value.removed_face_ids))fail('Restorable identities differ from deleted identities.');
  const combined=[...value.face_topology,...value.restorable_faces.map(row=>row.face)];
  if(combined.some(row=>!integer(row?.current_primitive_index,65535)||!integer(row?.group_index,65535)))fail('Invalid recorded deleted face metadata.');
  const objects=value.objects.map((obj,index)=>({...obj,primitives:combined.filter(row=>row.object_index===index).map((_,i)=>({primitive_index:i}))}));
  const next=objects.map(()=>0);stableTopology(combined.map(row=>({...row,current_primitive_index:next[row.object_index]++})),objects);
  if(!sameFaces(restorationLayout(value.face_topology,value),value.face_topology))fail('Current faces contradict restoration order or groups.');
}
export function decodeFaceRemovalSource(value,assetId,key){
  if(!value||!['legaia.model-face-removal-source.v1','legaia.model-face-removal-source.v2','legaia.model-face-removal-source.v3','legaia.model-face-removal-source.v4'].includes(value.schema_version)||value.asset_id!==assetId||value.project_source_key!==key||!hash(key)||!hash(value.source_sha256)||!hash(value.effective_sha256)||!Array.isArray(value.objects)||value.objects.length>1024||!Array.isArray(value.removed_faces)||value.removed_faces.length>4096)fail('Face removal source differs from this model.');
  for(const [i,obj] of value.objects.entries())if(obj.object_index!==i||!integer(obj.vertex_count,65535)||!Array.isArray(obj.primitives)||obj.primitives.length>65535||obj.primitives.some((row,j)=>row.primitive_index!==j||![3,4].includes(row.corner_count)))fail('Invalid source face ownership.');
  removedIdentities(value.removed_faces,value.objects.length);
  if(value.schema_version==='legaia.model-face-removal-source.v2'){if(!Array.isArray(value.retail_objects)||value.retail_objects.length!==value.objects.length)fail('Missing Retail face capacity.');for(const [i,obj] of value.retail_objects.entries()){if(obj.object_index!==i||obj.vertex_count!==value.objects[i].vertex_count||!Array.isArray(obj.primitives)||obj.primitives.length>65535||obj.primitives.some((row,j)=>row.primitive_index!==j||![3,4].includes(row.corner_count)))fail('Invalid Retail restoration ownership.');if(obj.primitives.length-value.removed_faces.filter(row=>row.object_index===i).length!==value.objects[i].primitives.length)fail('Retail removal count conflicts with Current.');}for(const row of value.removed_faces)if(!value.retail_objects[row.object_index].primitives[row.primitive_index])fail('Removed Retail face is absent.');}
  if(value.schema_version==='legaia.model-face-removal-source.v3'){if(value.restoration_available!==false||value.removed_faces.length)fail('Ledger restoration is not qualified.');stableTopology(value.face_topology,value.objects,value.removed_face_ids);}
  if(value.schema_version==='legaia.model-face-removal-source.v4'){stableTopology(value.face_topology,value.objects,value.removed_face_ids);restorationSource(value);}
  return structuredClone(value);
}
export function faceRemovalSelections(source,objectIndex,text){
  if(!integer(objectIndex,source.objects.length-1)||typeof text!=='string'||text.length>32768)fail('Choose a source object and Current face indices.');
  const values=text.trim()?text.split(',').map(value=>value.trim()):[];
  if(values.length>4096||values.some(value=>!/^\d+$/.test(value)))fail('Enter up to4096 comma-separated Current face indices.');
  const indices=values.map(Number);
  if(new Set(indices).size!==indices.length||indices.some(value=>!integer(value,source.objects[objectIndex].primitives.length-1)))fail('Face indices must be distinct existing Current faces.');
  return indices.sort((a,b)=>a-b).map(primitive_index=>({object_index:objectIndex,primitive_index}));
}
export function faceRestorationSelections(source,objectIndex,text){
  if(source.schema_version==='legaia.model-face-removal-source.v4'){
    decodeFaceRemovalSource(source,source.asset_id,source.project_source_key);
    const deleted=source.restorable_faces.filter(row=>row.face.object_index===objectIndex);
    const objects=source.objects.map((obj,index)=>({...obj,primitives:index===objectIndex?deleted:obj.primitives}));
    return faceRemovalSelections({...source,objects},objectIndex,text).map(row=>({face_id:deleted[row.primitive_index].face.face_id}));
  }
  if(source.restoration_available===false)fail('Stable ledger restoration is not available yet.');
  if(!source.retail_objects)fail('Export a fresh source to restore faces.');
  const rows=faceRemovalSelections({...source,objects:source.retail_objects},objectIndex,text);
  if(rows.some(row=>!source.removed_faces.some(old=>same(row,old))))fail('Only removed Retail faces can be restored.');
  return rows;
}
export function decodeFaceRestorationReview(value,source,selections){
  if(source.schema_version==='legaia.model-face-removal-source.v4')return decodeLedgerRestorationReview(value,source,selections);
  const requested=faceRestorationSelections(source,selections[0]?.object_index??0,selections.map(row=>row.primitive_index).join(','));
  if(!same(requested,selections))fail('Invalid restoration selection.');
  const remaining=source.removed_faces.filter(row=>!selections.some(selected=>same(row,selected)));
  if(!value||value.schema_version!=='legaia.model-face-restoration.v1'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!same(value.selections,selections)||!same(value.previous_removed_faces,source.removed_faces)||!same(value.removed_faces,remaining))fail('Restoration review differs from removed Retail owners.');
  const before=value.current_preview,after=value.preview;
  if(!before||!after||!same(before.vertices,after.vertices)||!Array.isArray(before.objects)||!Array.isArray(after.objects)||before.objects.length!==source.objects.length||after.objects.length!==source.objects.length)fail('Restoration changed vector ownership.');
  for(const [i,obj] of before.objects.entries()){const next=after.objects[i],count=selections.filter(row=>row.object_index===i).reduce((n,row)=>n+(source.retail_objects[i].primitives[row.primitive_index].corner_count===4?2:1),0);if(obj.object_index!==i||next.object_index!==i||obj.vertex_start!==next.vertex_start||obj.vertex_count!==next.vertex_count||next.triangle_count-obj.triangle_count!==count)fail('Restored triangle counts differ from Retail selections.');}
  if(Boolean(selections.length)!==(value.proposed_sha256!==source.effective_sha256))fail('Restoration hash conflicts with its selection.');
  return structuredClone(value);
}
export function decodeFaceRemovalReview(value,source,selections){
  if(['legaia.model-face-removal-source.v3','legaia.model-face-removal-source.v4'].includes(source.schema_version))return decodeLedgerRemovalReview(value,source,selections);

  if(!value||value.schema_version!=='legaia.model-face-removal.v1'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!same(value.selections,selections)||!same(value.previous_removed_faces,source.removed_faces)||!Array.isArray(value.removed_faces)||value.removed_faces.length!==source.removed_faces.length+selections.length)fail('Face removal review differs from its inspected selection.');
  const before=value.current_preview,after=value.preview;
  removedIdentities(value.removed_faces,source.objects.length);
  if(!before||!after||!same(before.vertices,after.vertices)||!Array.isArray(before.objects)||!Array.isArray(after.objects)||before.objects.length!==source.objects.length||after.objects.length!==source.objects.length)fail('Face removal changed object or vertex ownership.');
  for(const [i,obj] of before.objects.entries()){
    const candidate=after.objects[i],count=selections.filter(row=>row.object_index===i).reduce((n,row)=>n+(source.objects[i].primitives[row.primitive_index].corner_count===4?2:1),0);
    if(obj.object_index!==i||candidate.object_index!==i||obj.vertex_count!==candidate.vertex_count||obj.vertex_start!==candidate.vertex_start||obj.triangle_count-candidate.triangle_count!==count)fail('Face removal count differs from its reviewed primitives.');
  }
  if(Boolean(selections.length)!==(value.proposed_sha256!==source.effective_sha256))fail('Face removal hash differs from its reviewed count.');
  return structuredClone(value);
}

function decodeLedgerRemovalReview(value,source,selections){
  decodeFaceRemovalSource(source,source.asset_id,source.project_source_key);
  removedIdentities(selections,source.objects.length);
  const faceIds=selections.map(row=>{const face=source.face_topology.find(face=>face.object_index===row.object_index&&face.current_primitive_index===row.primitive_index);if(!face)fail('Selected stable face is absent.');return face.face_id;});
  if(!value||value.schema_version!=='legaia.model-face-removal.v2'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!same(value.selections,selections)||!same(value.removed_face_ids,faceIds)||!same(value.previous_removed_face_ids,source.removed_face_ids)||!value.topology||value.topology.proposed_sha256!==value.proposed_sha256)fail('Ledger removal review differs from stable source identities.');
  const before=value.current_preview,after=value.preview;
  if(!before||!after||!same(before.vertices,after.vertices)||!Array.isArray(before.objects)||!Array.isArray(after.objects)||before.objects.length!==source.objects.length||after.objects.length!==source.objects.length)fail('Ledger removal changed object or vector ownership.');
  for(const [i,obj] of before.objects.entries()){const next=after.objects[i],count=selections.filter(row=>row.object_index===i).reduce((n,row)=>n+(source.objects[i].primitives[row.primitive_index].corner_count===4?2:1),0);if(obj.object_index!==i||next.object_index!==i||obj.vertex_count!==next.vertex_count||obj.vertex_start!==next.vertex_start||obj.triangle_count-next.triangle_count!==count)fail('Ledger removal triangle counts differ.');}
  const expected=source.face_topology.filter(row=>!faceIds.includes(row.face_id)).map(row=>({...row}));
  for(let owner=0;owner<source.objects.length;owner++){const rows=expected.filter(row=>row.object_index===owner).sort((a,b)=>a.current_primitive_index-b.current_primitive_index),groups=[...new Set(rows.map(row=>row.group_index))].sort((a,b)=>a-b);rows.forEach((row,index)=>{row.current_primitive_index=index;row.group_index=groups.indexOf(row.group_index);});}
  if(!Array.isArray(value.topology.faces)||!sameFaces(expected,value.topology.faces)||!same(value.topology.removed_face_ids??[],[...source.removed_face_ids,...faceIds])||Boolean(selections.length)!==(value.proposed_sha256!==source.effective_sha256))fail('Ledger removal changed surviving stable identities or count/hash ownership.');
  return structuredClone(value);
}
function decodeLedgerRestorationReview(value,source,selections){
  decodeFaceRemovalSource(source,source.asset_id,source.project_source_key);
  if(!Array.isArray(selections)||selections.length>4096||selections.some(row=>!row||Object.keys(row).length!==1||!Object.hasOwn(row,'face_id')||!source.removed_face_ids.includes(row.face_id))||new Set(selections.map(row=>row.face_id)).size!==selections.length)fail('Invalid stable restoration selection.');
  const ids=selections.map(row=>row.face_id),remaining=source.removed_face_ids.filter(id=>!ids.includes(id));
  if(!value||value.schema_version!=='legaia.model-face-restoration.v2'||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||!hash(value.proposed_sha256)||value.project_changed!==false||value.gameplay_verified!==false||!same(value.selections,selections)||!same(value.restored_face_ids,ids)||!same(value.previous_removed_face_ids,source.removed_face_ids)||value.topology?.proposed_sha256!==value.proposed_sha256||!same(value.topology.removed_face_ids,remaining))fail('Stable restoration review differs from its source.');
  const before=value.current_preview,after=value.preview;
  if(!before||!after||!same(before.vertices,after.vertices)||!Array.isArray(before.objects)||!Array.isArray(after.objects)||before.objects.length!==source.objects.length||after.objects.length!==source.objects.length)fail('Stable restoration changed vector ownership.');
  for(const [i,obj] of before.objects.entries()){
    const next=after.objects[i],count=source.restorable_faces.filter(row=>row.face.object_index===i&&ids.includes(row.face.face_id)).reduce((total,row)=>total+(row.corner_count===4?2:1),0);
    if(obj.object_index!==i||next.object_index!==i||obj.vertex_start!==next.vertex_start||obj.vertex_count!==next.vertex_count||next.triangle_count-obj.triangle_count!==count)fail('Stable restored triangle counts differ.');
  }
  const expected=restorationLayout([...source.face_topology,...source.restorable_faces.filter(row=>ids.includes(row.face.face_id)).map(row=>row.face)],source);
  if(!Array.isArray(value.topology.faces)||!sameFaces(expected,value.topology.faces)||Boolean(ids.length)!==(value.proposed_sha256!==source.effective_sha256))fail('Restoration changed stable identities, groups or count/hash ownership.');
  return structuredClone(value);
}
export async function openModelFaceRemoval({assetId,getContext,busy,setBusy,onApplied,onError}){
  const context=structuredClone(getContext()),key=JSON.stringify(context),dialog=document.createElement('dialog');dialog.id='model-face-removal-dialog';dialog.className='model-dialog';
  dialog.innerHTML='<div class="dialog-heading"><h2>Remove or restore model faces</h2><button type="button" aria-label="Close face removal">×</button></div><p>Remove or restore selected whole source faces. Objects, vertex/normal tables and source allocation stay fixed. Retained groups keep their current settings. A model can be shared by several actors. Runtime appearance is unverified.</p><label>Operation<select aria-label="Face topology operation"><option value="remove">Remove Current faces</option><option value="restore">Restore removed Retail faces</option></select></label><label>Object<select aria-label="Face removal object"></select></label><p data-count></p><label data-selection-label>Current face indices<textarea aria-label="Current faces to remove" placeholder="0, 2, 3"></textarea></label><p data-topology-help>Removal uses Current indices; restoration uses the listed removed Retail indices, starting at0. Restored packets use Retail face fields and current vector tables. Retained groups keep current settings; absent groups recover Retail settings. A quad represents two preview triangles. Review shows the complete model; no changes are applied until Apply.</p><button type="button" data-review>Preview face removal</button><button type="button" data-apply disabled>Apply reviewed face removal</button><p role="status"></p><section data-comparison hidden><label>Preview layer<select aria-label="Face removal preview layer"><option value="proposed">Proposed</option><option value="current">Current</option></select></label><canvas aria-label="Face removal model comparison" style="display:block;width:100%;height:320px"></canvas><p>Drag to orbit · Scroll to zoom · Both layers use the same camera. Stored normals are not recomputed.</p></section>';
  document.body.append(dialog);
  const object=dialog.querySelector('[aria-label="Face removal object"]'),input=dialog.querySelector('textarea'),status=dialog.querySelector('[role="status"]'),reviewButton=dialog.querySelector('[data-review]'),applyButton=dialog.querySelector('[data-apply]'),comparison=dialog.querySelector('[data-comparison]'),layer=comparison.querySelector('select'),canvas=comparison.querySelector('canvas');
  const operation=dialog.querySelector('[aria-label="Face topology operation"]');
  let source=null,review=null,pending=false,closed=false,generation=0,renderer=null,view=null,drag=null,controller=null;
  const current=()=>!closed&&JSON.stringify(getContext())===key&&context.mode==='edit';
  const selections=()=>(operation.value==='restore'?faceRestorationSelections:faceRemovalSelections)(source,Number(object.value),input.value);
  const route=()=>operation.value==='restore'?'model-face-restoration':'model-face-removal';
  function invalidate(){generation++;review=null;comparison.hidden=true;refresh();}
  function refresh(){if(!current()){review=null;comparison.hidden=true;}let valid=false;try{valid=!!source&&selections().length>0;}catch{}reviewButton.disabled=!current()||pending||busy()||!valid;applyButton.disabled=reviewButton.disabled||!review;operation.disabled=object.disabled=input.disabled=pending||!current();if(source?.restoration_available===false)operation.disabled=true;}
  async function request(route,body){controller=new AbortController();const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal}),value=await response.json();if(!response.ok||value.error)fail(value.error||'Model face removal failed');return value;}
  function draw(){if(!view||comparison.hidden||!current()||!renderer)return;const rect=canvas.getBoundingClientRect(),c=Math.cos(view.yaw),s=Math.sin(view.yaw),cp=Math.cos(view.pitch),sp=Math.sin(view.pitch);renderer.draw({width:rect.width,height:rect.height,positions:new Map(),wireframe:true,grid:false,camera:{target:{x:view.center[0],y:-view.center[1],z:view.center[2]},distance:view.radius*4/view.zoom},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
  function load(){if(!review||!current())return;renderer??=new SceneRenderer(canvas,message=>{if(message&&!closed)status.textContent=message;});const preview=layer.value==='current'?review.current_preview:review.preview;const failures=renderer.load({assets:[{geometry_key:'face-removal',preview}],entities:[{entity_id:'face-removal',geometry_key:'face-removal',renderable:true,model_to_scene:[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1]}]});if(failures.length)fail(failures.join('; '));draw();}
  reviewButton.onclick=async()=>{refresh();if(reviewButton.disabled)return;const requested=selections();invalidate();const token=generation;pending=true;setBusy(true);refresh();try{const value=await request('/api/'+route()+'-preview',{asset_id:assetId,selections:requested,expected_sha256:source.effective_sha256,source_key:context.sourceKey});if(!current()||generation!==token)return;review=(operation.value==='restore'?decodeFaceRestorationReview:decodeFaceRemovalReview)(value,source,requested);const vertices=review.current_preview.vertices,min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(const point of vertices)for(let i=0;i<3;i++){min[i]=Math.min(min[i],point[i]);max[i]=Math.max(max[i],point[i]);}view={center:min.map((v,i)=>(v+max[i])/2),radius:Math.max(1,Math.hypot(...max.map((v,i)=>v-min[i]))/2),yaw:.6,pitch:.4,zoom:1};comparison.hidden=false;layer.value='proposed';status.textContent=`${requested.length} ${operation.value==='restore'?(source.restorable_faces?'stable faces restored':'Retail faces restored'):'Current faces removed'} · ${review.topology?.removed_face_ids?.length??review.removed_faces?.length??0} total ${review.topology?'stable face deletions':'removals from Retail'} · not applied`;load();}catch(error){if(current()){invalidate();status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}};
  applyButton.onclick=async()=>{refresh();if(applyButton.disabled)return;const accepted=review,requested=selections();pending=true;setBusy(true);refresh();try{const value=await request('/api/'+route(),{asset_id:assetId,selections:requested,expected_sha256:source.effective_sha256,source_key:context.sourceKey,proposed_sha256:accepted.proposed_sha256});if(!current())return;pending=false;dispose();await onApplied(value);}catch(error){if(current()){status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}};
  object.onchange=()=>{input.value='';const restored=operation.value==='restore',ledger=!!source.restorable_faces,deleted=source.restorable_faces?.filter(row=>row.face.object_index===Number(object.value))??[],removed=source.removed_faces.filter(row=>row.object_index===Number(object.value));dialog.querySelector('[data-count]').textContent=`${source.objects[Number(object.value)].primitives.length} Current faces · ${ledger?`deleted stable face indices: ${deleted.map((row,index)=>`${index} (${row.face.origin})`).join(', ')||'none'}`:source.restoration_available===false?`stable deleted faces: ${source.removed_face_ids.length} (restoration pending)`:`removed Retail faces: ${removed.map(row=>row.primitive_index).join(', ')||'none'}`}`;input.setAttribute('aria-label',restored?(ledger?'Deleted stable faces to restore':'Retail faces to restore'):'Current faces to remove');dialog.querySelector('[data-selection-label]').firstChild.textContent=restored?(ledger?'Deleted stable face indices':'Removed Retail face indices'):'Current face indices';reviewButton.textContent=restored?'Preview face restoration':'Preview face removal';applyButton.textContent=restored?'Apply reviewed face restoration':'Apply reviewed face removal';invalidate();};operation.onchange=object.onchange;input.oninput=invalidate;layer.onchange=()=>{try{load();}catch(error){status.textContent=error.message;}};
  canvas.onpointerdown=event=>{canvas.setPointerCapture(event.pointerId);drag={x:event.clientX,y:event.clientY};};canvas.onpointermove=event=>{if(!drag||!view)return;view.yaw+=(event.clientX-drag.x)*.009;view.pitch+=(event.clientY-drag.y)*.009;drag={x:event.clientX,y:event.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>drag=null;canvas.onwheel=event=>{event.preventDefault();if(view){view.zoom=Math.max(.15,Math.min(2.5,view.zoom*Math.exp(-event.deltaY*.001)));draw();}};
  function dispose(){if(closed)return;closed=true;controller?.abort();renderer?.dispose?.();if(dialog.open)dialog.close();dialog.remove();}
  dialog.querySelector('[aria-label="Close face removal"]').onclick=()=>{if(!pending)dispose();};dialog.oncancel=event=>{if(pending)event.preventDefault();};dialog.onclose=dispose;dialog.showModal();pending=true;setBusy(true);refresh();
  try{const value=await request('/api/model-face-removal-source',{asset_id:assetId,source_key:context.sourceKey});if(!current())return;source=decodeFaceRemovalSource(value,assetId,context.sourceKey);if(source.restoration_available===false){dialog.querySelector('h2').textContent='Remove model faces';dialog.querySelector('[data-topology-help]').textContent='Removal uses Current face indices and preserves stable surviving identities and the model ledger. Retained packet groups keep their settings. A quad represents two preview triangles. Review both layers before Apply. Restoring ledger faces is not available yet.';}if(source.restorable_faces){operation.querySelector('[value=restore]').textContent='Restore deleted stable faces';dialog.querySelector('.dialog-heading').nextElementSibling.textContent='Restore recorded source or authored faces while preserving surviving edits and vector tables. Primitive streams may grow. A model can be shared by several actors. Runtime appearance is unverified.';dialog.querySelector('[data-topology-help]').textContent='Removal uses Current face indices. Restoration uses the listed deleted stable face indices for this object, starting at 0. Restored packets recover their exact deletion preimages; surviving groups keep current settings and absent groups recover recorded settings. A quad represents two preview triangles. Review both complete-model layers before Apply.';}for(const obj of source.objects){const option=document.createElement('option');option.value=String(obj.object_index);option.textContent=`Object ${obj.object_index}`;object.append(option);}object.onchange();}catch(error){if(current()){status.textContent=error.message;onError(error);}}finally{pending=false;setBusy(false);refresh();}
  return {dialog,dispose,updateState:refresh};
}

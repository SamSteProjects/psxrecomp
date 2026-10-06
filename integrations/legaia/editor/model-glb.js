import { MODEL_FACE_BUDGET } from './model-topology-limits.js';
// Fixed-layout model interchange. Review and model inspection never author a project.
const MAX_GLB=32*1024*1024,MAX_BINDING=128*1024,MAX_REPORT=32*1024*1024,MAX_CHANGES=65536;
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const clone=value=>structuredClone(value);
const canonical=value=>Array.isArray(value)?value.map(canonical):object(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const fail=message=>{throw new Error(message);};
const asset=value=>typeof value==='string'&&/^asset:\/\/[A-Za-z0-9_./-]{1,512}$/.test(value);
const metadataBytes=value=>new TextEncoder().encode(JSON.stringify(value)).byteLength;

export function modelGlbContext(value){
  if(!exact(value,['projectPath','sceneId','mode','sourceKey'])||!text(value.projectPath,32768)||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value.sceneId)||value.mode!=='edit'||!hash(value.sourceKey))fail('Model GLB editing requires the current editable scene and source key.');
  return clone(value);
}

function metadata(value,budget){
  let count=0;
  function visit(item,depth){
    if(++count>2000000||depth>24)fail('Model GLB metadata exceeds its bounded structure.');
    if(item===null||typeof item==='boolean'||typeof item==='number'&&Number.isFinite(item)||typeof item==='string'&&item.length<=32768)return;
    if(Array.isArray(item)){if(item.length>MAX_CHANGES)fail('Model GLB metadata array exceeds its budget.');for(const child of item)visit(child,depth+1);return;}
    if(object(item)){for(const [key,child] of Object.entries(item)){if(!text(key,512))fail('Model GLB metadata key is invalid.');visit(child,depth+1);}return;}
    fail('Model GLB metadata must contain bounded JSON values.');
  }
  visit(value,0);if(metadataBytes(value)>budget)fail('Model GLB metadata exceeds its byte budget.');
}

function removedFaces(value){
  if(!Array.isArray(value)||!value.length||value.length>4096)fail('Invalid removed GLB source faces.');
  let last=-1;
  for(const row of value){if(!exact(row,['object_index','primitive_index'])||!integer(row.object_index,0,1023)||!integer(row.primitive_index,0,99999))fail('Invalid removed GLB face identity.');const identity=row.object_index*100000+row.primitive_index;if(identity<=last)fail('Removed GLB face identities conflict.');last=identity;}
}
export function decodeModelGlbBinding(value,assetId,context){
  context=modelGlbContext(context);metadata(value,MAX_BINDING);
  if(!asset(assetId)||!exact(value,['schema_version','asset_id','scene_id','source_sha256','effective_sha256','project_source_key','profile',...(value.schema_version==='legaia.model-glb-binding.v2'?['removed_faces']:value.schema_version==='legaia.model-glb-binding.v3'?['topology_sha256','authored_face_count']:[])])||!['legaia.model-glb-binding.v1','legaia.model-glb-binding.v2','legaia.model-glb-binding.v3'].includes(value.schema_version)||value.asset_id!==assetId||value.scene_id!==context.sceneId||!hash(value.source_sha256)||!hash(value.effective_sha256)||value.project_source_key!==context.sourceKey||!object(value.profile))fail('The binding does not match this model or current source. Export a fresh binding.');
  if(value.profile.schema_version!=='legaia.model-glb-profile.v6')fail('Export the current model and binding again to use source-qualified corners, raw RGB, stored normal and material attributes.');
  if(value.schema_version==='legaia.model-glb-binding.v2')removedFaces(value.removed_faces);
  if(value.schema_version==='legaia.model-glb-binding.v3'&&(!hash(value.topology_sha256)||!integer(value.authored_face_count,0,MODEL_FACE_BUDGET)))fail('Invalid authored GLB topology binding.');
  return clone(value);
}

function validateAudit(rows,removed=[]){
  if(!Array.isArray(rows)||rows.length>MAX_CHANGES)fail('Model GLB review contains too many source fields.');
  const offsets=new Set(),omitted=new Set(removed.map(row=>`${row.object_index}:${row.primitive_index}`));
  for(const row of rows){
    if(row?.kind==='primitive_removal'){const key=`${row.object_index}:${row.primitive_index}`;if(!exact(row,['kind','object_index','primitive_index'])||!omitted.delete(key))fail('GLB removal audit differs from the source binding.');continue;}
    if(!object(row)||!integer(row.object_index,0,1023)||!integer(row.byte_offset,0,MAX_GLB-1)||offsets.has(row.byte_offset)||row.before_value===row.after_value)fail('Model GLB review has invalid or duplicate source locations.');
    if(row.kind==='vertex'||row.kind==='normal'){
      if(!exact(row,['object_index','kind','vector_index','axis','byte_offset','before_value','after_value'])||!integer(row.vector_index,0,99999)||!['x','y','z'].includes(row.axis)||!integer(row.before_value,-32768,32767)||!integer(row.after_value,-32768,32767))fail('Model GLB vector audit differs from its source fields.');
    }else if(row.kind==='primitive_group'){
      if(!exact(row,['kind','object_index','group_index','field','byte_offset','before_value','after_value','primitive_indices'])||row.field!=='gpu_mode'||!integer(row.group_index,0,65535)||!integer(row.before_value,0,255)||!integer(row.after_value,0,255)||(row.before_value^row.after_value)!==2||!Array.isArray(row.primitive_indices)||!row.primitive_indices.length||row.primitive_indices.some(i=>!integer(i,0,99999))||new Set(row.primitive_indices).size!==row.primitive_indices.length)fail('Model GLB shared group audit differs from its qualified ABE field.');
    }else if(row.kind==='primitive'&&['clut','tpage'].includes(row.field)){
      if(!exact(row,['kind','object_index','primitive_index','group_index','field','byte_offset','before_value','after_value'])||!integer(row.primitive_index,0,99999)||!integer(row.group_index,0,65535)||!integer(row.before_value,0,65535)||!integer(row.after_value,0,65535)||((row.before_value^row.after_value)&~(row.field==='clut'?0x7fff:0x019f)))fail('Model GLB retained material audit differs from its qualified source mask.');
    }else if(row.kind==='primitive'){
      const axisField=row.field==='uv'||row.field==='color',keys=['kind','object_index','primitive_index','group_index','field','corner_index','byte_offset','before_value','after_value',...(axisField?['axis']:[])],max=['vertex_index','normal_index'].includes(row.field)?8191:255;
      if(!exact(row,keys)||!integer(row.primitive_index,0,99999)||!integer(row.group_index,0,65535)||!['vertex_index','normal_index','uv','color'].includes(row.field)||!integer(row.corner_index,0,3)||axisField&&!(row.field==='uv'?['u','v']:['r','g','b']).includes(row.axis)||!integer(row.before_value,0,max)||!integer(row.after_value,0,max))fail('Model GLB primitive audit differs from its supported source fields.');
    }else fail('Model GLB review contains an unsupported source field.');
    offsets.add(row.byte_offset);
  }
  if(omitted.size)fail('GLB review omitted a removed Retail face.');
}

export function decodeModelGlbReview(value,binding,assetId,context,glbHash){
  binding=decodeModelGlbBinding(binding,assetId,context);metadata(value,MAX_REPORT);
  const keys=['schema_version','asset_id','scene_id','source_sha256','effective_sha256','proposed_sha256','glb_sha256','project_source_key','changes','pending_changes','quantization','limitations','review_key'];
  if(!object(value)||!keys.every(key=>Object.hasOwn(value,key))||value.schema_version!==(binding.schema_version==='legaia.model-glb-binding.v2'?'legaia.model-glb-review.v2':binding.schema_version==='legaia.model-glb-binding.v3'?'legaia.model-glb-review.v3':'legaia.model-glb-review.v1')||value.asset_id!==assetId||value.scene_id!==context.sceneId||value.source_sha256!==binding.source_sha256||value.effective_sha256!==binding.effective_sha256||value.project_source_key!==context.sourceKey||!hash(value.proposed_sha256)||!hash(value.review_key)||!hash(value.glb_sha256)||value.glb_sha256!==glbHash||!Array.isArray(value.limitations)||value.limitations.length>256||value.limitations.some(line=>!text(line)))fail('Model review differs from the selected files or current source. Review them again.');
  const q=value.quantization;
  if(!exact(q,['vertex_max_error','uv_max_error','color_max_error','normal_max_error','quantized_component_count'])||['vertex_max_error','uv_max_error','color_max_error','normal_max_error'].some(key=>typeof q[key]!=='number'||!Number.isFinite(q[key])||q[key]<0)||!integer(q.quantized_component_count,0,Number.MAX_SAFE_INTEGER))fail('Model GLB quantization metadata is invalid.');
  if(binding.schema_version==='legaia.model-glb-binding.v2'&&!same(value.removed_faces,binding.removed_faces))fail('GLB review changed removed source identities.');
  if(binding.schema_version!=='legaia.model-glb-binding.v2'&&Object.hasOwn(value,'removed_faces'))fail('Unexpected GLB removal metadata.');
  const added=binding.schema_version==='legaia.model-glb-binding.v3';if(added&&(value.comparison!=='current_addition_topology'||value.topology_sha256!==binding.topology_sha256||value.authored_face_count!==binding.authored_face_count||!same(value.changes,value.pending_changes)))fail('GLB review differs from the bound Current addition topology.');
  validateAudit(value.changes,binding.removed_faces??[]);validateAudit(value.pending_changes);
  if(value.pending_changes.some(row=>!['vertex','normal'].includes(row.kind)&&!(row.kind==='primitive'&&['uv','color','vertex_index','normal_index','clut','tpage'].includes(row.field))&&!(row.kind==='primitive_group'&&row.field==='gpu_mode')))fail('GLB imports support existing vectors, references, UV/RGB and qualified material masks only.');
  if((value.pending_changes.length===0)!==(value.proposed_sha256===value.effective_sha256)||(value.changes.length===0)!==(value.proposed_sha256===(added?value.effective_sha256:value.source_sha256)))fail('Model review changes contradict its source and current hashes.');
  for(const [key,expected] of [['project_changed',false],['gameplay_verified',false]])if(Object.hasOwn(value,key)&&value[key]!==expected)fail('Model file review cannot claim project or gameplay changes.');
  return clone(value);
}

export function decodeModelGlbPosePreview(value,review,binding,assetId,context,glbHash){
  if(!exact(value,['preview','report'])||!object(value.preview)||value.preview.schema_version!=='legaia.model-preview.v1'||value.preview.semantic_id!==assetId)fail('Model preview belongs to a different source asset.');
  const report=decodeModelGlbReview(value.report,binding,assetId,context,glbHash);if(!same(report,review))fail('Model preview differs from the reviewed proposal. Review the files again.');return clone(value.preview);
}

function validateGlb(bytes){
  if(!(bytes instanceof Uint8Array)||!integer(bytes.length,20,MAX_GLB))fail('Choose a GLB from 20 bytes to 32 MiB.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length)fail('Choose a complete glTF 2 binary (.glb) file.');
}
function encode(bytes){let raw='';for(let start=0;start<bytes.length;start+=32768)raw+=String.fromCharCode(...bytes.subarray(start,start+32768));return btoa(raw);}
function decodeGlb(value){
  if(!text(value,Math.ceil(MAX_GLB/3)*4)||value.length%4!==0||!/^[A-Za-z0-9+/]*={0,2}$/.test(value))fail('Model export returned invalid GLB bytes or exceeded 32 MiB.');
  const raw=atob(value),bytes=Uint8Array.from(raw,char=>char.charCodeAt(0));validateGlb(bytes);if(encode(bytes)!==value)fail('Model export returned noncanonical GLB bytes.');return bytes;
}
async function byteHash(bytes){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),value=>value.toString(16).padStart(2,'0')).join('');}
function element(tag,label){const node=document.createElement(tag);if(label!==undefined)node.textContent=label;return node;}
function button(label,action){const node=element('button',label);node.type='button';node.dataset.action=action;return node;}
function safeFilename(value,fallback){return typeof value==='string'&&value.length>0&&value.length<=160&&!/[\\/\x00-\x1f]/.test(value)?value:fallback;}
function download(data,type,filename){let url,link;try{url=URL.createObjectURL(new Blob([data],{type}));link=element('a');link.href=url;link.download=filename;document.body.append(link);link.click();}finally{link?.remove();if(url)URL.revokeObjectURL(url);}}

/** Export, select both files, review, inspect the proposal, then explicitly Apply. */
export async function openModelGlbEditor({assetId,getContext,busy,setBusy,onError=()=>{},onApplied,onPreview=null}){
  if([getContext,busy,setBusy,onError,onApplied].some(callback=>typeof callback!=='function')||onPreview!==null&&typeof onPreview!=='function')fail('Model GLB editor requires source, state and error callbacks.');
  const context=modelGlbContext(getContext());if(!asset(assetId))fail('Choose an imported source model.');
  const dialog=element('dialog');dialog.id='model-glb-dialog';dialog.className='project-dialog';dialog.dataset.modelGlb='';Object.assign(dialog.style,{width:'min(540px,94vw)',maxHeight:'92vh',overflowY:'auto',boxSizing:'border-box'});
  const heading=element('div');heading.className='dialog-heading';const close=button('×','close');close.setAttribute('aria-label','Close model GLB');heading.append(element('h2','Edit model through GLB'),close);
  const note=element('p','Edit existing vertex positions, packet references through _LEGAIA_SOURCE_VERTEX, supported UVs and _LEGAIA_SOURCE_RGB custom attributes. References may select existing vertices in the same object only; keep corner identities and adjust POSITION aliases to agree with the selected vertex. Vertex, packet and object counts cannot change. RGB uses raw 0..255 byte values per stored flat or Gouraud slot; retain -1 sentinels for packets without stored RGB. Display COLOR_0, vertex paint and shader colors are ignored. Preserved source-object tags allow renamed or reordered nodes; keep object-N names if those tags are removed. Conflicting or duplicate identities reject. Static rigid node transforms and parent groups bake into positions and raw stored normals. Positive uniform scale also bakes positions, preserving normal magnitudes. Nonuniform scale, reflection, shear and animation remain unsupported. Keep the source layout, custom attributes and repeated bindings. In Blender, use merge_vertices=False on import and export_attributes=True on export. Positions round to signed 16-bit source coordinates; UVs and raw RGB round to bytes and are reviewed before Apply. Edit stored normal XYZ through _LEGAIA_SOURCE_NORMAL using signed 16-bit source words, preserving shared aliases. Unlit corners retain [32768,32768,32768]. Display NORMAL is ignored; the viewport does not reproduce retail normal-based lighting. Rewire existing lit normal references through _LEGAIA_SOURCE_NORMAL_INDEX, keeping flat/shared reference aliases and raw XYZ for each selected source normal in agreement. Unlit reference IDs retain -1. Edit exact source material words through _LEGAIA_SOURCE_MATERIAL [CLUT word, TPage word, group ABE 0/1]. Each primitive and shared group must agree across all aliases. Keep reserved bits and source ABR unchanged; untextured CLUT/TPage retain -1. Shader/material assignments, texture images, packet insertion and vector allocation are not imported.');note.className='field-note';
  const exported=element('section');exported.append(element('h3','Export current model'));
  const exportActions=element('div');exportActions.className='dialog-actions';exportActions.style.flexWrap='wrap';const prepare=button('Prepare GLB export','export'),getGlb=button('Download GLB','download-glb'),getBinding=button('Download binding JSON','download-binding');exportActions.append(prepare,getGlb,getBinding);exported.append(exportActions);
  const imported=element('section');imported.append(element('h3','Review edited files'));
  const glb=element('input');glb.type='file';glb.accept='.glb,model/gltf-binary';glb.setAttribute('aria-label','Edited model GLB');const manifest=element('input');manifest.type='file';manifest.accept='.json,application/json';manifest.setAttribute('aria-label','Source binding JSON');
  for(const [label,field] of [['Edited GLB · maximum 32 MiB',glb],['Binding JSON from the export · maximum 128 KiB',manifest]]){const row=element('label',label);Object.assign(field.style,{width:'100%',minWidth:'0'});row.append(field);imported.append(row);}
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const inspect=button('Review selected files','review'),preview=button('Inspect proposed model','preview'),apply=button('Apply reviewed model','apply');preview.hidden=onPreview===null;actions.append(inspect,preview,apply);imported.append(actions);
  const status=element('p','Choose both edited files to review.');status.setAttribute('role','status');const error=element('p');error.className='dialog-error';error.setAttribute('role','alert');const summary=element('section');summary.hidden=true;dialog.append(heading,note,exported,imported,status,error,summary);document.body.append(dialog);
  let closed=false,stale=false,pending=null,generation=0,revision=0,controller=null,busyOwner=null,review=null,candidate=null,exportData=null,retainedClose=false;
  const contextCurrent=()=>{try{return !closed&&!stale&&same(context,modelGlbContext(getContext()));}catch{return false;}};
  const filesCurrent=value=>value!==null&&value.revision===revision&&glb.files?.[0]===value.editedFile&&manifest.files?.[0]===value.bindingFile;
  const acceptedCurrent=value=>contextCurrent()&&value===review&&value!==null&&candidate===value.candidate&&filesCurrent(value.candidate);
  const release=token=>{if(busyOwner===token){busyOwner=null;setBusy(false);}};
  function abort(){generation++;controller?.abort();controller=null;pending=null;if(busyOwner)release(busyOwner);}
  function invalidate(){abort();review=null;summary.hidden=true;summary.replaceChildren();}
  function showError(value){error.textContent=value?.message??String(value);onError(value instanceof Error?value:new Error(String(value)));}
  function updateState(){
    if(!closed&&!stale&&!contextCurrent()){invalidate();stale=true;candidate=exportData=null;status.textContent='Project, scene, mode or model source changed. Reopen model GLB editing.';}
    if(candidate&&!filesCurrent(candidate)){invalidate();candidate=null;status.textContent='Selected files changed. Choose both files and review them again.';}
    const current=contextCurrent(),blocked=!current||pending!==null||busy()!==false;
    prepare.disabled=blocked;getGlb.disabled=getBinding.disabled=blocked||!exportData;glb.disabled=manifest.disabled=!current||pending==='apply'||busy()!==false&&pending===null;
    inspect.disabled=blocked||!filesCurrent(candidate);preview.disabled=blocked||!acceptedCurrent(review);apply.disabled=blocked||!acceptedCurrent(review)||review?.report.pending_changes.length===0;close.disabled=pending==='apply';
  }
  function dispose(){if(closed)return;closed=true;invalidate();candidate=exportData=null;if(dialog.open)dialog.close();dialog.remove();}
  async function run(kind,work){
    if(!contextCurrent()||pending!==null||busy()!==false)return false;
    const token={},ticket=++generation;controller=new AbortController();const signal=controller.signal;pending=kind;busyOwner=token;setBusy(true);error.textContent='';updateState();const valid=()=>contextCurrent()&&generation===ticket&&!signal.aborted;
    try{return await work(signal,valid);}catch(value){if(valid()&&value?.name!=='AbortError')showError(value);return false;}
    finally{release(token);if(generation===ticket){controller=null;pending=null;updateState();}}
  }
  async function post(route,body,signal){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});const value=await response.json();if(!response.ok||value?.error)fail(value?.error??'Model GLB request failed.');return value;}
  function appendReview(report){
    summary.replaceChildren();summary.hidden=false;summary.append(element('h3','Reviewed · not applied'),element('p',`${report.pending_changes.length} changed fields from Current · ${report.changes.length} changes from ${report.comparison==='current_addition_topology'?'Current addition topology':'retail source'}`));
    for(const [label,key] of [['Retail source','source_sha256'],['Current model','effective_sha256'],['Proposed model','proposed_sha256']]){const row=element('p',`${label} SHA-256 · ${report[key]}`);row.style.overflowWrap='anywhere';summary.append(row);}
    const table=element('table');table.className='operand-review-table';const header=element('tr');for(const label of ['Source field','Current','Proposed'])header.append(element('th',label));table.append(header);
    for(const row of report.pending_changes.slice(0,100)){const label=row.kind==='primitive'?`Object ${row.object_index} · primitive ${row.primitive_index} · ${row.field}${row.corner_index!==undefined?' '+row.corner_index:''}${row.axis?'.'+row.axis:''}`:row.kind==='primitive_group'?`Object ${row.object_index} · group ${row.group_index} · ABE (shared by ${row.primitive_indices.length} primitives)`:`Object ${row.object_index} · ${row.kind} ${row.vector_index}.${row.axis}`;const tr=element('tr');for(const value of [label,String(row.before_value),String(row.after_value)])tr.append(element('td',value));table.append(tr);}
    const scroll=element('div');scroll.style.overflowX='auto';scroll.append(table);summary.append(scroll);if(report.pending_changes.length>100)summary.append(element('p',`Showing 100 of ${report.pending_changes.length} current-to-proposed fields.`));
    const q=report.quantization;summary.append(element('p',`Maximum rounding error · position ${Number(q.vertex_max_error.toPrecision(6))} source units · UV ${Number(q.uv_max_error.toPrecision(6))} byte units · RGB ${Number(q.color_max_error.toPrecision(6))} byte units · stored normal ${Number(q.normal_max_error.toPrecision(6))} source units · ${q.quantized_component_count} quantized components`));
    const quantization=element('details');quantization.append(element('summary','Source quantization'));const quantized=element('pre',JSON.stringify(q,null,2));quantized.className='diagnostic-detail';Object.assign(quantized.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});quantization.append(quantized);summary.append(quantization);
    for(const line of report.limitations){const row=element('p',line);row.className='field-note';summary.append(row);}const details=element('details');details.append(element('summary','Complete source and current audit'));const audit=element('pre',JSON.stringify({changes:report.changes,pending_changes:report.pending_changes},null,2));audit.className='diagnostic-detail';Object.assign(audit.style,{maxHeight:'240px',overflow:'auto'});details.append(audit);summary.append(details);
  }
  async function readFiles(){
    if(!contextCurrent()||pending==='apply'||busy()!==false&&busyOwner===null)return false;
    revision++;invalidate();candidate=null;error.textContent='';status.textContent='Choose both edited files to review.';updateState();const editedFile=glb.files?.[0],bindingFile=manifest.files?.[0],fileRevision=revision;if(!editedFile||!bindingFile)return false;
    return run('files',async(_signal,valid)=>{
      if(!integer(editedFile.size,20,MAX_GLB)||!editedFile.name?.toLowerCase().endsWith('.glb'))fail('Choose an edited .glb file up to 32 MiB.');
      if(!integer(bindingFile.size,1,MAX_BINDING)||!bindingFile.name?.toLowerCase().endsWith('.json'))fail('Choose its binding .json file up to 128 KiB.');
      const [buffer,content]=await Promise.all([editedFile.arrayBuffer(),bindingFile.text()]);if(!valid()||revision!==fileRevision||glb.files?.[0]!==editedFile||manifest.files?.[0]!==bindingFile)return false;
      const bytes=new Uint8Array(buffer);validateGlb(bytes);if(bytes.length!==editedFile.size||typeof content!=='string'||new TextEncoder().encode(content).byteLength!==bindingFile.size)fail('Selected file contents differ from their bounded sizes.');
      const binding=decodeModelGlbBinding(JSON.parse(content),assetId,context),glbHash=await byteHash(bytes);if(!valid()||revision!==fileRevision||glb.files?.[0]!==editedFile||manifest.files?.[0]!==bindingFile)return false;
      candidate={content_base64:encode(bytes),binding,glbHash,revision:fileRevision,editedFile,bindingFile};status.textContent=`Ready to review ${editedFile.name} with ${bindingFile.name}.`;return true;
    });
  }
  glb.onchange=manifest.onchange=readFiles;
  prepare.onclick=()=>run('export',async(signal,valid)=>{
    exportData=null;status.textContent='Preparing source-bound model export…';const value=await post('/api/model-glb-export',{asset_id:assetId},signal);if(!valid())return false;
    const binding=decodeModelGlbBinding(value?.binding,assetId,context),bytes=decodeGlb(value.content_base64);exportData={bytes,binding,filename:safeFilename(value.filename,'model.glb'),bindingFilename:safeFilename(value.binding_filename,'model.binding.json')};status.textContent='Export ready. Download both files and retain the binding JSON for review.';return true;
  });
  for(const [control,key] of [[getGlb,'glb'],[getBinding,'binding']])control.onclick=()=>{if(control.disabled||!contextCurrent()||!exportData||busy()!==false)return false;try{if(key==='glb')download(exportData.bytes,'model/gltf-binary',exportData.filename);else{const pretty=JSON.stringify(exportData.binding,null,2)+'\n',content=new TextEncoder().encode(pretty).byteLength<=MAX_BINDING?pretty:JSON.stringify(exportData.binding);download(content,'application/json',exportData.bindingFilename);}error.textContent='';return true;}catch(value){showError(value);return false;}};
  const body=value=>({asset_id:assetId,content_base64:value.content_base64,binding:clone(value.binding)});
  inspect.onclick=()=>{
    updateState();if(inspect.disabled||!filesCurrent(candidate))return false;review=null;summary.hidden=true;const accepted=candidate;
    return run('review',async(signal,valid)=>{status.textContent='Reviewing source-bound model fields…';const value=await post('/api/model-glb-preview',body(accepted),signal);if(!valid()||candidate!==accepted||!filesCurrent(accepted))return false;const report=decodeModelGlbReview(value,accepted.binding,assetId,context,accepted.glbHash);review={report,candidate:accepted};appendReview(report);status.textContent=report.pending_changes.length?'Review complete. Explicit Apply is required.':'The files produce no change from the current model.';return true;});
  };
  preview.onclick=()=>{
    updateState();if(preview.disabled||!acceptedCurrent(review)||onPreview===null)return false;const accepted=review;
    return run('preview',async(signal,valid)=>{
      status.textContent='Preparing reviewed model preview…';const value=await post('/api/model-glb-pose-preview',body(accepted.candidate),signal);if(!valid()||!acceptedCurrent(accepted))return false;const data=decodeModelGlbPosePreview(value,accepted.report,accepted.candidate.binding,assetId,context,accepted.candidate.glbHash);
      const returnToEditor=()=>{if(!acceptedCurrent(accepted)){dispose();return false;}if(!dialog.open)dialog.showModal();status.textContent='Review retained. Explicit Apply is required.';updateState();return true;};
      const result=await onPreview(data,{returnToEditor});if(!valid()||!acceptedCurrent(accepted)||result===false)return false;retainedClose=true;dialog.close();return true;
    });
  };
  apply.onclick=()=>{
    updateState();if(apply.disabled||!acceptedCurrent(review)||!review.report.pending_changes.length)return false;const accepted=review;
    return run('apply',async(signal,valid)=>{
      status.textContent='Applying reviewed model…';let state;
      try{state=await post('/api/model-glb-import',{...body(accepted.candidate),review_key:accepted.report.review_key},signal);if(!object(state)||!object(state.project)||state.project.mode!=='edit')fail('Model import returned invalid project state.');}
      catch(value){if(valid()){review=null;summary.hidden=true;status.textContent='Apply failed. Review the selected files again.';}throw value;}
      if(!valid()||!acceptedCurrent(accepted))return false;review=null;candidate=null;summary.hidden=true;await onApplied(state);if(!closed)dispose();return true;
    });
  };
  close.onclick=()=>{if(pending==='apply')return false;dispose();return true;};dialog.oncancel=event=>{if(pending==='apply'){event.preventDefault();status.textContent='Apply is in progress; wait for its result.';}};dialog.onclose=()=>{if(retainedClose){retainedClose=false;return;}dispose();};dialog.showModal();updateState();return {dialog,ready:Promise.resolve(true),updateState,dispose};
}

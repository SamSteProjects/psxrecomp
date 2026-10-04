import assert from 'node:assert/strict';
import {decodeModelPrimitives,decodeModelPrimitivePreview,modelPrimitiveContext,modelPrimitiveDraft,modelPrimitiveReviewMatches,openModelPrimitiveEditor} from '../editor/model-primitives.js';

const assetId='asset://fixture/models/0000',retailHash='a'.repeat(64),currentHash='b'.repeat(64),candidateHash='c'.repeat(64),key='d'.repeat(64);
const context={projectPath:'C:/private/project',sceneId:'scene://fixture',mode:'edit',sourceKey:key};
function source(){
  const row={primitive_index:0,group_index:0,flags:0x20,byte_offset:100,corner_count:3,vertices:[0,1,2],uvs:[[0,1],[20,30],[255,254]],colors:[[128,80,40]],gouraud:false,baked_colors:true,material:{clut:16,tpage:32,semi_transparent:false}};
  const objects=[{object_index:0,vertex_count:3,primitives:[row]}];
  return {schema_version:'legaia.model-primitives.v1',asset_id:assetId,source_sha256:retailHash,effective_sha256:currentHash,project_source_key:key,objects,retail_objects:structuredClone(objects)};
}
function additionSource(){
const addition=source();addition.schema_version='legaia.model-primitives.v4';
for(const objects of [addition.objects,addition.retail_objects]){objects[0].normal_count=4;objects[0].primitives[0].normal_indices=null;}
const authored=structuredClone(addition.objects[0].primitives[0]);authored.primitive_index=1;authored.byte_offset=128;addition.objects[0].primitives.push(authored);
addition.face_mappings=[[{retail_index:0,current_index:0}]];
addition.authored_faces=[[{face_id:'face://authored/00000000-0000-4000-8000-000000000001',current_index:1}]];
return addition;
}
function geometry(){return {schema_version:'legaia.model-preview.v1',semantic_id:assetId,coordinate_system:'retail_tmd_object_local',vertices:[[0,0,0],[100,0,0],[0,-100,0]],triangles:[[0,1,2]],triangle_colors:[[[128,80,40],[128,80,40],[128,80,40]]],triangle_uvs:[[[0,1],[20,30],[255,254]]],triangle_materials:[0],materials:[{blend:{mode:0,enabled:false}}],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1}],textures:[]};}
function draft(report=source()){const row=report.objects[0].primitives[0];return modelPrimitiveDraft(report,0,0,{vertices:[1,1,2],uvs:row.uvs,colors:row.colors});}
function preview(report=source(),edit=draft(report)){
  const before=report.objects[0].primitives[0],changes=[];
  for(const [field,name,axes] of [['vertex_index','vertices',null],['uv','uvs',['u','v']],['color','colors',['r','g','b']]])for(let corner=0;corner<(edit[name]?.length??0);corner++)for(let axis=0;axis<(axes?.length??1);axis++){
    const old=axes?before[name][corner][axis]:before[name][corner],value=axes?edit[name][corner][axis]:edit[name][corner];
    if(old!==value)changes.push({kind:'primitive',object_index:0,primitive_index:0,group_index:0,field,corner_index:corner,...(axes?{axis:axes[axis]}:{}),byte_offset:100+corner*4+axis,before_value:old,after_value:value});
  }
  const next=geometry();next.triangles=[edit.vertices.slice()];if(edit.uvs)next.triangle_uvs=[edit.uvs];if(edit.colors)next.triangle_colors=[Array.from({length:3},(_,i)=>edit.colors[before.gouraud?i:0])];
  return {asset_id:assetId,source_sha256:report.source_sha256,effective_sha256:report.effective_sha256,project_source_key:report.project_source_key,proposed_sha256:changes.length?candidateHash:report.effective_sha256,coordinate_changes:structuredClone(changes),changes_from_current:changes,project_changed:false,preview:next,current_preview:geometry()};
}

const original=source(),qualified=decodeModelPrimitives(original,assetId,context);qualified.objects[0].primitives[0].vertices[0]=2;assert.deepEqual(original,source());
assert.deepEqual(modelPrimitiveContext(context),context);
for(const mutation of [v=>v.mode='observe',v=>v.sourceKey='bad',v=>v.sceneId='other',v=>v.projectPath='',v=>v.extra=true]){const value=structuredClone(context);mutation(value);assert.throws(()=>modelPrimitiveContext(value));}
for(const mutation of [v=>v.asset_id='asset://wrong',v=>v.schema_version='old',v=>v.project_source_key='e'.repeat(64),v=>v.effective_sha256='A'.repeat(64),v=>v.objects[0].object_index=1,v=>v.objects[0].primitives[0].primitive_index=1,v=>v.objects[0].primitives[0].vertices[0]=3,v=>v.objects[0].primitives[0].vertices[0]=true,v=>v.objects[0].primitives[0].uvs.pop(),v=>v.objects[0].primitives[0].colors.push([1,2,3]),v=>v.objects[0].primitives[0].material.clut=-1,v=>v.objects[0].primitives[0].material.semi_transparent='yes',v=>v.objects[0].primitives[0].flags=0x28,v=>v.objects[0].primitives[0].baked_colors=false,v=>v.retail_objects[0].primitives[0].flags=0x10,v=>v.objects[0].vertex_count=100001,v=>v.objects[0].primitives.push({...v.objects[0].primitives[0],primitive_index:1})]){const value=source();mutation(value);assert.throws(()=>decodeModelPrimitives(value,assetId,context));}
const lit=source();for(const layer of ['objects','retail_objects'])Object.assign(lit[layer][0].primitives[0],{flags:0x10,colors:null,baked_colors:false});decodeModelPrimitives(lit,assetId,context);assert.deepEqual(modelPrimitiveDraft(lit,0,0,{vertices:[0,1,2],uvs:lit.objects[0].primitives[0].uvs}),{object_index:0,primitive_index:0,vertices:[0,1,2],uvs:lit.objects[0].primitives[0].uvs});assert.throws(()=>modelPrimitiveDraft(lit,0,0,{vertices:[0,1,2],uvs:lit.objects[0].primitives[0].uvs,colors:[[1,2,3]]}));
const untextured=source();for(const layer of ['objects','retail_objects'])Object.assign(untextured[layer][0].primitives[0],{flags:0x18,uvs:null,material:{clut:null,tpage:null,semi_transparent:true}});decodeModelPrimitives(untextured,assetId,context);assert.deepEqual(modelPrimitiveDraft(untextured,0,0,{vertices:[0,1,2],colors:[[128,80,40]]}).colors,[[128,80,40]]);
const gouraud=source();for(const layer of ['objects','retail_objects']){const row=gouraud[layer][0].primitives[0];row.flags=0x26;row.corner_count=4;row.vertices=[0,1,2,3];row.uvs.push([255,0]);row.gouraud=true;row.colors=[[0,1,2],[100,101,102],[253,254,255],[128,128,128]];gouraud[layer][0].vertex_count=4;}decodeModelPrimitives(gouraud,assetId,context);
for(const mutate of [row=>row.flags=0x16,row=>row.gouraud=true,row=>row.corner_count=4,row=>row.uvs=null]){const bad=source();for(const layer of ['objects','retail_objects'])mutate(bad[layer][0].primitives[0]);assert.throws(()=>decodeModelPrimitives(bad,assetId,context));}
for(let flags=0x10;flags<=0x27;flags++){
  const valid=source(),layout=Math.floor((flags-0x10)/4),corners=(flags&2)?4:3,textured=[0,1,4,5].includes(layout),isGouraud=[1,3,5].includes(layout),baked=layout>=2;
  for(const layer of ['objects','retail_objects']){const row=valid[layer][0].primitives[0];valid[layer][0].vertex_count=4;Object.assign(row,{flags,corner_count:corners,vertices:Array.from({length:corners},(_,i)=>i),gouraud:isGouraud,baked_colors:baked,uvs:textured?Array.from({length:corners},()=>[0,255]):null,colors:baked?Array.from({length:isGouraud?corners:1},()=>[0,128,255]):null,material:{clut:textured?0:null,tpage:textured?65535:null,semi_transparent:false}});}
  decodeModelPrimitives(valid,assetId,context);
}
const oversizedLocal=source();for(const layer of ['objects','retail_objects']){oversizedLocal[layer][0].vertex_count=9000;oversizedLocal[layer][0].primitives[0].vertices[2]=8191;}decodeModelPrimitives(oversizedLocal,assetId,context);assert.throws(()=>modelPrimitiveDraft(oversizedLocal,0,0,{vertices:[0,1,8192],uvs:source().objects[0].primitives[0].uvs,colors:[[128,80,40]]}));
const edit=draft(),validReport=preview(),accepted=decodeModelPrimitivePreview(validReport,source(),context,[edit]);accepted.preview.vertices[0][0]=99;assert.equal(validReport.preview.vertices[0][0],0);
for(const mutation of [v=>v.source_sha256='0'.repeat(64),v=>v.project_source_key='f'.repeat(64),v=>v.proposed_sha256=currentHash,v=>v.project_changed=true,v=>v.changes_from_current[0].before_value=2,v=>v.changes_from_current[0].after_value=2,v=>v.changes_from_current[0].group_index=1,v=>v.changes_from_current[0].byte_offset=99,v=>v.changes_from_current[0].axis='x',v=>v.changes_from_current.push(v.changes_from_current[0]),v=>v.changes_from_current=[],v=>v.preview.semantic_id='wrong',v=>v.preview.vertices[0][0]=NaN,v=>v.preview.triangles[0][0]=3,v=>v.current_preview.objects[0].vertex_count=2,v=>v.current_preview.coordinate_system='scene_world',v=>v.coordinate_changes[0].byte_offset=-1]){const value=preview();mutation(value);assert.throws(()=>decodeModelPrimitivePreview(value,source(),context,[edit]));}
assert.throws(()=>decodeModelPrimitivePreview(preview(),source(),context,[edit,edit]));assert.throws(()=>decodeModelPrimitivePreview(preview(),source(),context,Array(257).fill(edit)));
const unchanged=modelPrimitiveDraft(source(),0,0,{vertices:[0,1,2],uvs:source().objects[0].primitives[0].uvs,colors:[[128,80,40]]});assert.equal(decodeModelPrimitivePreview(preview(source(),unchanged),source(),context,[unchanged]).proposed_sha256,currentHash);
const review={context:structuredClone(context),effective_sha256:currentHash,source_sha256:retailHash,project_source_key:key,edits:[edit],proposed_sha256:candidateHash};assert.equal(modelPrimitiveReviewMatches(review,source(),context,[edit]),true);assert.equal(modelPrimitiveReviewMatches(review,source(),{...context,sourceKey:'e'.repeat(64)},[edit]),false);assert.equal(modelPrimitiveReviewMatches(review,source(),context,[{...edit,vertices:[2,1,2]}]),false);

class Node {
  constructor(tag){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this.value='';this.textContent='';this.open=false;this.disabled=false;this.hidden=false;}
  append(...nodes){for(const node of nodes){this.children.push(node);node.parent=this;}}
  prepend(...nodes){for(const node of [...nodes].reverse()){this.children.unshift(node);node.parent=this;}}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  setAttribute(key,value){this.attributes[key]=String(value);}
  addEventListener(){}
  showModal(){this.open=true;}
  close(){this.open=false;this.onclose?.();}
  remove(){this.removed=true;if(this.parent)this.parent.children=this.parent.children.filter(node=>node!==this);}
  getContext(){return null;}
  getBoundingClientRect(){return {width:400,height:330};}
  setPointerCapture(){}
}
const tree=node=>[node,...node.children.flatMap(tree)],action=(control,key)=>tree(control.dialog).find(node=>node.dataset.action===key),input=(control,label)=>tree(control.dialog).find(node=>node.attributes['aria-label']===label),deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const globals={document:globalThis.document,fetch:globalThis.fetch,ResizeObserver:globalThis.ResizeObserver};
globalThis.document={body:new Node('body'),createElement:tag=>new Node(tag)};delete globalThis.ResizeObserver;
try{
  let ctx=structuredClone(context),isBusy=false,errors=[],applied=[],calls=[],queue=[];
  globalThis.fetch=async(path,options)=>{calls.push({path,body:JSON.parse(options.body),signal:options.signal});const next=queue.shift();const value=next instanceof Promise?await next:next;return {ok:!value?.error,json:async()=>value};};
  const settings={assetId,getContext:()=>ctx,busy:()=>isBusy,setBusy:value=>isBusy=value,onApplied:async state=>applied.push(state),onError:error=>errors.push(error)};
  queue=[source()];let control=openModelPrimitiveEditor(settings);assert.equal(await control.ready,true);assert.equal(action(control,'apply').disabled,true);assert.equal(input(control,'Flat R').value,'128');assert.equal(input(control,'Flat R').style.width,'72px');assert.equal(input(control,'Flat R').parent.style.flexDirection,'row');assert.ok(tree(control.dialog).filter(node=>node.type==='checkbox').every(node=>node.style.width==='auto'&&node.parent.style.display==='inline-flex'));assert.ok(tree(control.dialog).some(node=>node.textContent.includes('normal references')));assert.equal(calls[0].path,'/api/model-primitive-source');
  input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();queue=[preview()];assert.equal(await action(control,'preview').onclick(),true);assert.equal(action(control,'apply').disabled,false);assert.equal(calls.at(-1).body.expected_sha256,currentHash);assert.deepEqual(calls.at(-1).body.edits,[edit]);
  input(control,'Corner 0 U').value='256';input(control,'Corner 0 U').oninput();assert.equal(action(control,'apply').disabled,true);assert.equal(action(control,'preview').disabled,true);assert.equal(await action(control,'apply').onclick(),false);action(control,'discard').onclick();assert.equal(input(control,'Corner 0 U').value,'0');
  input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();const pending=deferred();queue=[pending.promise];const reviewing=action(control,'preview').onclick();assert.equal(isBusy,true);input(control,'Corner 0 local vertex').value='2';input(control,'Corner 0 local vertex').oninput();pending.resolve(preview());assert.equal(await reviewing,false);assert.equal(isBusy,false);assert.equal(action(control,'apply').disabled,true);
  action(control,'discard').onclick();input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();queue=[preview()];await action(control,'preview').onclick();ctx={...ctx,sourceKey:'e'.repeat(64)};control.updateState();assert.equal(action(control,'apply').disabled,true);assert.equal(await action(control,'apply').onclick(),false);control.dispose();control.dispose();assert.equal(control.dialog.removed,true);

  ctx=structuredClone(context);isBusy=false;const reload=source();reload.effective_sha256=candidateHash;reload.project_source_key='f'.repeat(64);reload.objects[0].primitives[0].vertices[0]=1;
  queue=[source()];control=openModelPrimitiveEditor({...settings,onApplied:async state=>{applied.push(state);ctx={...ctx,sourceKey:reload.project_source_key};control.updateState();}});await control.ready;input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();queue=[preview()];await action(control,'preview').onclick();const applying=deferred();queue=[applying.promise,reload];const operation=action(control,'apply').onclick();assert.equal(await action(control,'apply').onclick(),false);let prevented=false;control.dialog.oncancel({preventDefault(){prevented=true;}});assert.equal(prevented,true);action(control,'close').onclick();assert.equal(control.dialog.removed,undefined);applying.resolve({project:{mode:'edit'}});assert.equal(await operation,true);assert.equal(applied.length,1);assert.equal(input(control,'Corner 0 local vertex').value,'1');assert.equal(action(control,'apply').disabled,true);assert.equal(isBusy,false);assert.equal(calls.filter(row=>row.path==='/api/model-primitives').length,1);control.dispose();

  ctx=structuredClone(context);const closing=deferred();queue=[closing.promise];control=openModelPrimitiveEditor(settings);control.dispose();closing.resolve(source());assert.equal(await control.ready,false);assert.equal(isBusy,false);
  queue=[source()];control=openModelPrimitiveEditor({...settings,initial:{object_index:0,primitive_index:99}});assert.equal(await control.ready,false);assert.match(errors.at(-1).message,/existing object and primitive/);control.dispose();
  let returns=0,restores=0;queue=[source()];control=openModelPrimitiveEditor({...settings,initial:{object_index:0,primitive_index:0},onScenePreview:async(report,edits,binding,actions)=>{assert.equal(report.proposed_sha256,candidateHash);assert.deepEqual(edits,[edit]);assert.equal(binding.effective_sha256,currentHash);returns=actions.returnToEditor;return {restore:()=>restores++};}});await control.ready;input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();queue=[preview()];await action(control,'preview').onclick();assert.equal(await action(control,'scene').onclick(),true);assert.equal(control.dialog.open,false);assert.equal(control.dialog.removed,undefined);assert.equal(returns(),true);assert.equal(restores,1);assert.equal(control.dialog.open,true);assert.equal(action(control,'apply').disabled,false);await action(control,'scene').onclick();ctx={...ctx,sourceKey:'e'.repeat(64)};control.updateState();assert.equal(restores,2);assert.equal(returns(),false);assert.equal(control.dialog.removed,true);
  ctx=structuredClone(context);queue=[source()];control=openModelPrimitiveEditor(settings);await control.ready;const effectiveRow=input(control,'Flat R');effectiveRow.value='0';effectiveRow.oninput();action(control,'retail').onclick();assert.equal(effectiveRow.value,'128');assert.equal(await action(control,'apply').onclick(),false);control.dispose();
  const large=source();for(const layer of ['objects','retail_objects'])large[layer][0].primitives=Array.from({length:300},(_,i)=>({...structuredClone(source().objects[0].primitives[0]),primitive_index:i,byte_offset:100+i*40}));queue=[large];control=openModelPrimitiveEditor({...settings,initial:{object_index:0,primitive_index:299}});assert.equal(await control.ready,true);assert.equal(input(control,'Model primitive').children.length,44);assert.equal(input(control,'Model primitive').value,'299');assert.equal(action(control,'next-page').disabled,true);assert.equal(action(control,'previous-page').onclick(),true);assert.equal(input(control,'Model primitive').children.length,256);input(control,'Corner 0 local vertex').value='1';input(control,'Corner 0 local vertex').oninput();assert.equal(action(control,'next-page').onclick(),false);control.dispose();
  ctx=structuredClone(context);isBusy=false;
  for(const gouraud of [false,true]){
    const normalCatalog=source();normalCatalog.schema_version='legaia.model-primitives.v2';
    for(const layer of ['objects','retail_objects']){normalCatalog[layer][0].normal_count=4;Object.assign(normalCatalog[layer][0].primitives[0],{flags:gouraud?0x14:0x10,colors:null,baked_colors:false,gouraud,normal_indices:gouraud?[0,1,2]:[1]});}
    const selected=[];queue=[normalCatalog];control=openModelPrimitiveEditor({...settings,onInspectNormal:async(target,binding)=>{selected.push({target,binding});binding.objects[0].normal_count=99;return true;}});await control.ready;
    const link=action(control,gouraud?'inspect-normal-2':'inspect-normal-0');assert.equal(link.disabled,false);
    input(control,'Corner 0 U').value='77';input(control,'Corner 0 U').oninput();assert.equal(link.disabled,true);assert.equal(await link.onclick(),false);assert.equal(selected.length,0);
    action(control,'discard').onclick();assert.equal(link.disabled,false);assert.equal(await link.onclick(),true);assert.deepEqual(selected[0].target,{kind:'normal',object_index:0,vector_index:gouraud?2:1});assert.equal(normalCatalog.objects[0].normal_count,4);
    isBusy=true;control.updateState();assert.equal(link.disabled,true);assert.equal(await link.onclick(),false);isBusy=false;
    ctx={...ctx,sourceKey:'e'.repeat(64)};control.updateState();assert.equal(await link.onclick(),false);control.dispose();ctx=structuredClone(context);
  }
  ctx=structuredClone(context);isBusy=false;queue=[additionSource()];control=openModelPrimitiveEditor({...settings,initial:{object_index:0,primitive_index:1}});assert.equal(await control.ready,true);assert.equal(action(control,'retail').disabled,true);assert.equal(action(control,'discard').disabled,false);assert.equal(input(control,'Flat R').value,'128');input(control,'Flat R').value='77';input(control,'Flat R').oninput();assert.equal(action(control,'preview').disabled,false);action(control,'discard').onclick();assert.equal(input(control,'Flat R').value,'128');control.dispose();
}finally{for(const [key,value] of Object.entries(globals)){if(value===undefined)delete globalThis[key];else globalThis[key]=value;}}
console.log('Model primitive source/layout/draft/audit validation and detached data; review hashes, reset, bounded fields, busy/stale/close/Apply and scene Return/Restore lifecycle passed.');

const normalSource=source();normalSource.schema_version='legaia.model-primitives.v2';
for(const layer of ['objects','retail_objects']){normalSource[layer][0].normal_count=4;Object.assign(normalSource[layer][0].primitives[0],{flags:0x10,colors:null,baked_colors:false,normal_indices:[1]});}
decodeModelPrimitives(normalSource,assetId,context);
const normalValues={vertices:[0,1,2],uvs:normalSource.objects[0].primitives[0].uvs,normal_indices:[3]};
const normalDraft=modelPrimitiveDraft(normalSource,0,0,normalValues);
for(const indices of [[4],[true],[1,2],[-1]])assert.throws(()=>modelPrimitiveDraft(normalSource,0,0,{...normalValues,normal_indices:indices}));
const normalReport=preview(normalSource,{...normalDraft,normal_indices:undefined});normalReport.proposed_sha256=candidateHash;normalReport.changes_from_current=[{kind:'primitive',object_index:0,primitive_index:0,group_index:0,field:'normal_index',corner_index:0,byte_offset:112,before_value:1,after_value:3}];normalReport.coordinate_changes=structuredClone(normalReport.changes_from_current);
decodeModelPrimitivePreview(normalReport,normalSource,context,[normalDraft]);
const wrongNormalWord=structuredClone(normalReport);wrongNormalWord.changes_from_current[0].byte_offset=114;assert.throws(()=>decodeModelPrimitivePreview(wrongNormalWord,normalSource,context,[normalDraft]));
for(const mutate of [v=>v.objects[0].normal_count=1,v=>v.objects[0].primitives[0].normal_indices=[1,2],v=>v.retail_objects[0].normal_count=5]){const bad=structuredClone(normalSource);mutate(bad);assert.throws(()=>decodeModelPrimitives(bad,assetId,context));}
console.log('V2 flat normal-reference domain, unchanged topology and exact word audits passed.');

const compact=source();compact.schema_version='legaia.model-primitives.v3';
for(const layer of ['objects','retail_objects']){compact[layer][0].normal_count=0;compact[layer][0].primitives[0].normal_indices=null;}
compact.retail_objects[0].primitives.push({...structuredClone(compact.retail_objects[0].primitives[0]),primitive_index:1,byte_offset:140});
compact.face_mappings=[[{retail_index:0,current_index:null},{retail_index:1,current_index:0}]];
assert.equal(decodeModelPrimitives(compact,assetId,context).face_mappings[0][1].current_index,0);
for(const map of [[{retail_index:0,current_index:0},{retail_index:1,current_index:0}],[{retail_index:0,current_index:null}],[]])assert.throws(()=>decodeModelPrimitives({...compact,face_mappings:[map]},assetId,context));
const compactReview=preview(compact,draft(compact));compactReview.coordinate_changes.push({kind:'primitive_removal',object_index:0,primitive_index:0});
decodeModelPrimitivePreview(compactReview,compact,context,[draft(compact)]);
compactReview.coordinate_changes.at(-1).primitive_index=1;assert.throws(()=>decodeModelPrimitivePreview(compactReview,compact,context,[draft(compact)]));
console.log('V3 compacted face identity and removed Retail audit guards passed.');

const addition=additionSource(),authored=addition.objects[0].primitives[1];
const checkedAddition=decodeModelPrimitives(addition,assetId,context);
assert.equal(checkedAddition.objects[0].primitives.length,2);
assert.deepEqual(modelPrimitiveDraft(checkedAddition,0,1,{vertices:[1,0,2],uvs:authored.uvs,colors:authored.colors}).vertices,[1,0,2]);
for(const mutation of [v=>v.authored_faces[0][0].current_index=0,v=>v.authored_faces[0]=[],v=>v.authored_faces[0][0].face_id='bad',v=>v.face_mappings[0][0].current_index=1,v=>v.authored_faces[0].push({...v.authored_faces[0][0]})]){const bad=structuredClone(addition);mutation(bad);assert.throws(()=>decodeModelPrimitives(bad,assetId,context));}
console.log('V4 source/authored ownership and Current primitive drafts passed.');

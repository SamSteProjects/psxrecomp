import {openGlbMaterialSelection,primitiveGlbSelectionSource} from './model-glb-material-selection.js';
import {uvRectangleDrafts,uvSelectionDrafts} from './uv-rectangle.js';
import {validateObjectOwnership} from './model-object-ownership.js';
import {SceneRenderer} from './scene-renderer.js';

// Existing source packets only. No material, normal-vector, lighting or allocation edits.
const HASH=/^[0-9a-f]{64}$/;
const SOURCE_KEYS=['schema_version','asset_id','source_sha256','effective_sha256','project_source_key','objects','retail_objects'];
const ROW_KEYS=['primitive_index','group_index','flags','byte_offset','corner_count','vertices','uvs','colors','gouraud','baked_colors','material'];
const IDENTITY=[1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1];
const MAX_ROWS=100000,MAX_BYTES=4*1024*1024,MAX_EDITS=256;
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const int=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&HASH.test(value);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=message=>{throw new Error(message);};
const clone=value=>structuredClone(value);

export function modelPrimitiveContext(value){
  if(!exact(value,['projectPath','sceneId','mode','sourceKey'])||typeof value.projectPath!=='string'||!value.projectPath.trim()||value.projectPath.length>32768||value.sceneId!==null&&(typeof value.sceneId!=='string'||!/^scene:\/\/[A-Za-z0-9_-]{1,128}$/.test(value.sceneId))||value.mode!=='edit'||!hash(value.sourceKey))fail('Model face editing requires the current editable project and source key.');
  return clone(value);
}

function vectors(value,count,size,max,label){
  if(!Array.isArray(value)||value.length!==count||value.some(row=>!Array.isArray(row)||row.length!==size||row.some(n=>!int(n,0,max))))fail(`Invalid primitive ${label}.`);
}

function objects(value,normalReferences=false){
  if(!Array.isArray(value)||!value.length||value.length>1024)fail('Model primitive object count exceeds bounds.');
  let vertices=0,rows=0;const offsets=new Set();
  for(const [index,entry] of value.entries()){
    if(!exact(entry,['object_index','vertex_count','primitives',...(normalReferences?['normal_count']:[])])||entry.object_index!==index||!int(entry.vertex_count,0,MAX_ROWS)||!Array.isArray(entry.primitives)||entry.primitives.length>MAX_ROWS)fail('Invalid primitive object identity or vertex count.');
    if(normalReferences&&!int(entry.normal_count,0,MAX_ROWS))fail('Invalid source normal count.');vertices+=entry.vertex_count;rows+=entry.primitives.length;
    if(vertices>MAX_ROWS||rows>MAX_ROWS)fail('Model primitive catalog exceeds its vertex or packet budget.');
    let lastOffset=-1,lastGroup=-1;
    for(const [primitiveIndex,row] of entry.primitives.entries()){
      if(!exact(row,[...ROW_KEYS,...(normalReferences?['normal_indices']:[])])||row.primitive_index!==primitiveIndex||!int(row.group_index,0,65535)||row.group_index<lastGroup||!int(row.flags,0x10,0x27)||!int(row.byte_offset,0,MAX_BYTES-1)||row.byte_offset<=lastOffset||offsets.has(row.byte_offset)||![3,4].includes(row.corner_count)||typeof row.gouraud!=='boolean'||typeof row.baked_colors!=='boolean')fail('Invalid or duplicate primitive source layout.');
      const layout=Math.floor((row.flags-0x10)/4),textured=[0,1,4,5].includes(layout);
      if(row.corner_count!==((row.flags&2)?4:3)||row.gouraud!==[1,3,5].includes(layout)||row.baked_colors!==(layout>=2)||(row.uvs!==null)!==textured)fail('Primitive attributes contradict the supported source flags.');
      if(!Array.isArray(row.vertices)||row.vertices.length!==row.corner_count||row.vertices.some(n=>!int(n,0,Math.min(8191,entry.vertex_count-1))))fail('Primitive vertex connections must use existing local indices.');
      if(row.uvs!==null)vectors(row.uvs,row.corner_count,2,255,'UV byte pairs');
      if(row.baked_colors){vectors(row.colors,row.gouraud?row.corner_count:1,3,255,'baked RGB bytes');}else if(row.colors!==null)fail('Lit primitive colors are not editable baked RGB.');
      if(normalReferences){if(row.baked_colors){if(row.normal_indices!==null)fail('Unlit packets have no normal references.');}else if(!Array.isArray(row.normal_indices)||row.normal_indices.length!==(row.gouraud?row.corner_count:1)||row.normal_indices.some(n=>!int(n,0,Math.min(8191,entry.normal_count-1))))fail('Invalid existing normal reference indices.');}
      const material=row.material;
      if(!exact(material,['clut','tpage','semi_transparent'])||typeof material.semi_transparent!=='boolean'||(row.uvs===null?(material.clut!==null||material.tpage!==null):(!int(material.clut,0,65535)||!int(material.tpage,0,65535))))fail('Invalid immutable primitive material binding.');
      lastOffset=row.byte_offset;lastGroup=row.group_index;offsets.add(row.byte_offset);
    }
  }
  return value;
}

export function decodeModelPrimitives(value,assetId,context){
  context=modelPrimitiveContext(context);
  if(typeof assetId!=='string'||!/^asset:\/\/[A-Za-z0-9_./-]{1,512}$/.test(assetId)||!exact(value,[...SOURCE_KEYS,...(['legaia.model-primitives.v3','legaia.model-primitives.v4','legaia.model-primitives.v5','legaia.model-primitives.v6'].includes(value.schema_version)?['face_mappings']:[]),...(['legaia.model-primitives.v4','legaia.model-primitives.v5','legaia.model-primitives.v6'].includes(value.schema_version)?['authored_faces']:[]),...(['legaia.model-primitives.v5','legaia.model-primitives.v6'].includes(value.schema_version)?['vector_growth']:[]),...(value.schema_version==='legaia.model-primitives.v6'?['object_mappings']:[])])||!['legaia.model-primitives.v1','legaia.model-primitives.v2','legaia.model-primitives.v3','legaia.model-primitives.v4','legaia.model-primitives.v5','legaia.model-primitives.v6'].includes(value.schema_version)||value.asset_id!==assetId||!hash(value.source_sha256)||!hash(value.effective_sha256)||value.project_source_key!==context.sourceKey)fail('Model primitive source is invalid or stale.');
  const cloned=value.schema_version==='legaia.model-primitives.v6',allocated=cloned||value.schema_version==='legaia.model-primitives.v5',additions=allocated||value.schema_version==='legaia.model-primitives.v4',topology=additions||value.schema_version==='legaia.model-primitives.v3',normalReferences=value.schema_version!=='legaia.model-primitives.v1';
  if(topology&&(!Array.isArray(value.face_mappings)||value.face_mappings.length!==value.objects.length))fail('Missing source face mappings.');objects(value.objects,normalReferences);objects(value.retail_objects,normalReferences);
  if(value.source_sha256===value.effective_sha256&&!equal(value.objects,value.retail_objects))fail('Equal source hashes require identical primitive values.');
  if(cloned)validateObjectOwnership(value.object_mappings,value.objects.length,value.retail_objects.length);
  if(!cloned&&value.objects.length!==value.retail_objects.length)fail('Current model differs from the retail object layout.');
  if(allocated&&(!Array.isArray(value.vector_growth)||value.vector_growth.length!==value.objects.length))fail('Missing allocated vector ownership.');
  let allocatedCount=0;const authoredIds=new Set();
  for(const [index,entry] of value.objects.entries()){
    const retail=value.retail_objects[index]??{vertex_count:0,normal_count:0,primitives:[]};
    const growth=allocated?value.vector_growth[index]:{vertices:0,normals:0};
    if(allocated&&(!exact(growth,['object_index','vertices','normals'])||growth.object_index!==index||!int(growth.vertices,0,4096)||!int(growth.normals,0,4096)))fail('Invalid allocated vector ownership.');
    allocatedCount+=growth.vertices+growth.normals;
    if(allocatedCount>4096||allocated&&(entry.vertex_count>8192||entry.normal_count>8192)||normalReferences&&entry.normal_count!==retail.normal_count+growth.normals||entry.vertex_count!==retail.vertex_count+growth.vertices||!topology&&entry.primitives.length!==retail.primitives.length)fail('Current model differs from qualified vector/primitive counts.');
    if(topology){let next=0,previous=-1;const owned=new Set(),map=value.face_mappings[index];if(!Array.isArray(map)||map.length!==retail.primitives.length)fail('Invalid Retail face mapping.');for(const [i,row] of map.entries()){if(!exact(row,['retail_index','current_index'])||row.retail_index!==i||row.current_index!==null&&(!int(row.current_index,0,entry.primitives.length-1)||row.current_index<=previous||!additions&&row.current_index!==next))fail('Invalid retained face identity.');if(row.current_index!==null){previous=row.current_index;owned.add(row.current_index);next++;}}
      if(additions){if(!Array.isArray(value.authored_faces)||value.authored_faces.length!==value.objects.length||!Array.isArray(value.authored_faces[index]))fail('Missing authored face identities.');const ids=authoredIds;for(const row of value.authored_faces[index]){if(!exact(row,['face_id','current_index'])||typeof row.face_id!=='string'||!/^face:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(row.face_id)||ids.has(row.face_id)||!int(row.current_index,0,entry.primitives.length-1)||owned.has(row.current_index))fail('Invalid authored face identity.');ids.add(row.face_id);if(ids.size>128)fail('Authored face budget exceeded.');owned.add(row.current_index);}if(owned.size!==entry.primitives.length)fail('Unowned Current face.');}
      else if(next!==entry.primitives.length)fail('Current face mapping count differs.');}
    const retained=topology?value.face_mappings[index].filter(face=>face.current_index!==null):null;
    for(const [i,row] of entry.primitives.entries()){
      const identity=topology?retained.find(face=>face.current_index===i):null,old=retail.primitives[topology?identity?.retail_index:i];if(!old&&additions)continue;
      for(const field of ROW_KEYS.filter(key=>!['vertices','uvs','colors','material',...(topology?['primitive_index','group_index','byte_offset']:[])].includes(key)))if(!equal(row[field],old[field]))fail('Current model changed immutable primitive metadata.');
      for(const field of ['uvs','colors',...(normalReferences?['normal_indices']:[])])if((row[field]===null)!==(old[field]===null))fail('Current primitive changed the source attribute layout.');
      if(row.uvs!==null&&(((row.material.clut^old.material.clut)&~0x7fff)||((row.material.tpage^old.material.tpage)&~0x019f)))fail('Current material changed reserved source bits.');
    }
  }
  return clone(value);
}

function selectedRow(source,objectIndex,primitiveIndex,retail=false){
  if(!int(objectIndex,0,source.objects.length-1)||!int(primitiveIndex,0,source.objects[objectIndex].primitives.length-1))fail('Select an existing object and primitive.');
  const entries=retail?source.retail_objects:source.objects;
  const index=retail&&source.face_mappings?source.face_mappings[objectIndex].find(face=>face.current_index===primitiveIndex)?.retail_index:primitiveIndex;
  if(index===undefined||!int(index,0,(entries[objectIndex]?.primitives.length??0)-1))fail('Current face has no retained Retail owner.');
  return entries[objectIndex].primitives[index];
}

export function modelPrimitiveDraft(source,objectIndex,primitiveIndex,values){
  const row=selectedRow(source,objectIndex,primitiveIndex),entry=source.objects[objectIndex];
  const keys=['vertices',...(row.uvs===null?[]:['uvs']),...(row.colors===null?[]:['colors']),...(row.normal_indices==null?[]:['normal_indices'])];
  if(!exact(values,keys)||!Array.isArray(values.vertices)||values.vertices.length!==row.corner_count||values.vertices.some(n=>!int(n,0,Math.min(8191,entry.vertex_count-1))))fail('Enter every existing local vertex index within this object.');
  if(row.uvs!==null)vectors(values.uvs,row.corner_count,2,255,'UV byte pairs');
  if(row.colors!==null)vectors(values.colors,row.gouraud?row.corner_count:1,3,255,'baked RGB bytes');
  if(row.normal_indices!=null&&(!Array.isArray(values.normal_indices)||values.normal_indices.length!==row.normal_indices.length||values.normal_indices.some(n=>!int(n,0,Math.min(8191,entry.normal_count-1)))))fail('Choose existing object normal indices with the stored flat or Gouraud ownership.');
  return clone({object_index:objectIndex,primitive_index:primitiveIndex,...values});
}

function expectedChanges(source,edits){
  const changes=new Map();
  for(const edit of edits){
    const row=selectedRow(source,edit.object_index,edit.primitive_index);
    for(const [field,sourceField,axes] of [['vertex_index','vertices',null],['normal_index','normal_indices',null],['uv','uvs',['u','v']],['color','colors',['r','g','b']]]){
      if(!Object.hasOwn(edit,sourceField))continue;
      for(let corner=0;corner<row[sourceField].length;corner++)for(let axis=0;axis<(axes?.length??1);axis++){
        const before=axes?row[sourceField][corner][axis]:row[sourceField][corner],after=axes?edit[sourceField][corner][axis]:edit[sourceField][corner];
        if(before!==after)changes.set(JSON.stringify([edit.object_index,edit.primitive_index,field,corner,axes?.[axis]??null]),{before,after});
      }
    }
  }
  return changes;
}

function previewGeometry(value,assetId){
  if(!object(value)||value.schema_version!=='legaia.model-preview.v1'||value.semantic_id!==assetId||value.coordinate_system!=='retail_tmd_object_local'||value.posed===true||!Array.isArray(value.vertices)||!value.vertices.length||value.vertices.length>MAX_ROWS||value.vertices.some(v=>!Array.isArray(v)||v.length!==3||v.some(n=>typeof n!=='number'||!Number.isFinite(n)||Math.abs(n)>1e9))||!Array.isArray(value.triangles)||!value.triangles.length||value.triangles.length>MAX_ROWS)fail('Invalid unposed model comparison geometry.');
  const count=value.triangles.length;
  if(value.triangles.some(t=>!Array.isArray(t)||t.length!==3||t.some(n=>!int(n,0,value.vertices.length-1)))||!Array.isArray(value.materials)||!value.materials.length||value.materials.length>256||!Array.isArray(value.objects)||!value.objects.length||value.objects.length>1024)fail('Invalid model comparison triangle or object bindings.');
  for(const field of ['triangle_colors','triangle_uvs','triangle_materials'])if(!Array.isArray(value[field])||value[field].length!==count)fail('Model comparison triangle arrays do not agree.');
  for(let i=0;i<count;i++){
    vectors(value.triangle_colors[i],3,3,255,'preview RGB');
    if(value.triangle_uvs[i]!==null)vectors(value.triangle_uvs[i],3,2,255,'preview UV');
    if(!int(value.triangle_materials[i],0,value.materials.length-1))fail('Invalid model comparison material index.');
  }
  const seen=new Set();
  for(const row of value.objects){if(!object(row)||!int(row.object_index,0,1023)||seen.has(row.object_index)||!int(row.vertex_start,0,value.vertices.length)||!int(row.vertex_count,0,value.vertices.length-row.vertex_start)||!int(row.triangle_start,0,count)||!int(row.triangle_count,0,count-row.triangle_start))fail('Invalid comparison object ranges.');seen.add(row.object_index);}
  if(value.textures!==undefined&&(!Array.isArray(value.textures)||value.textures.length>256))fail('Invalid comparison texture catalog.');
}

export function decodeModelPrimitivePreview(value,source,context,edits){
  context=modelPrimitiveContext(context);
  if(!Array.isArray(edits)||!edits.length||edits.length>MAX_EDITS)fail('Model primitive review exceeds the UI edit budget.');
  const seen=new Set();
  for(const edit of edits){
    if(!object(edit)||!Object.hasOwn(edit,'object_index')||!Object.hasOwn(edit,'primitive_index'))fail('Invalid model primitive review draft.');
    const key=JSON.stringify([edit.object_index,edit.primitive_index]);if(seen.has(key))fail('Duplicate model primitive review draft.');seen.add(key);
    modelPrimitiveDraft(source,edit.object_index,edit.primitive_index,Object.fromEntries(Object.entries(edit).filter(([key])=>!['object_index','primitive_index'].includes(key))));
  }
  const keys=['asset_id','source_sha256','effective_sha256','project_source_key','proposed_sha256','coordinate_changes','changes_from_current','project_changed','preview','current_preview'];
  if(!exact(value,keys)||value.asset_id!==source.asset_id||value.source_sha256!==source.source_sha256||value.effective_sha256!==source.effective_sha256||value.project_source_key!==source.project_source_key||value.project_source_key!==context.sourceKey||!hash(value.proposed_sha256)||value.project_changed!==false||!Array.isArray(value.coordinate_changes)||value.coordinate_changes.length>600000||!Array.isArray(value.changes_from_current)||value.changes_from_current.length>MAX_EDITS*24)fail('Model primitive review is invalid or stale.');
  const expected=expectedChanges(source,edits);
  for(const row of value.changes_from_current){
    const fields=['kind','object_index','primitive_index','group_index','field','corner_index','byte_offset','before_value','after_value',...(['vertex_index','normal_index'].includes(row?.field)?[]:['axis'])];
    if(!exact(row,fields)||row.kind!=='primitive'||!['vertex_index','normal_index','uv','color'].includes(row.field))fail('Invalid primitive change audit.');
    const primitive=selectedRow(source,row.object_index,row.primitive_index),key=JSON.stringify([row.object_index,row.primitive_index,row.field,row.corner_index,row.axis??null]),change=expected.get(key);
    if(row.group_index!==primitive.group_index||!int(row.byte_offset,primitive.byte_offset,Math.min(MAX_BYTES-1,primitive.byte_offset+63))||!change||row.before_value!==change.before||row.after_value!==change.after)fail('Primitive change audit differs from the reviewed draft.');
    if(row.field==='normal_index'){const relative=primitive.gouraud?(primitive.corner_count===3?18:20):(primitive.corner_count===3?12:20);if(row.byte_offset!==primitive.byte_offset+relative+row.corner_index*2)fail('Normal reference audit changed source ownership.');}
    expected.delete(key);
  }
  if(expected.size||Boolean(value.changes_from_current.length)!==(value.proposed_sha256!==value.effective_sha256))fail('Primitive review hash or changed values are inconsistent.');
  for(const row of value.coordinate_changes){if(row?.kind==='primitive_removal'){if(!exact(row,['kind','object_index','primitive_index'])||!int(row.object_index,0,source.objects.length-1)||source.face_mappings?.[row.object_index]?.[row.primitive_index]?.current_index!==null)fail('Invalid removed Retail face audit.');continue;}if(!object(row)||!['primitive','primitive_group','vertex','normal'].includes(row.kind)||!int(row.object_index,0,source.objects.length-1)||!int(row.byte_offset,0,MAX_BYTES-1)||!Number.isSafeInteger(row.before_value)||!Number.isSafeInteger(row.after_value))fail('Invalid retail model change audit.');}
  previewGeometry(value.preview,source.asset_id);previewGeometry(value.current_preview,source.asset_id);
  for(const preview of [value.preview,value.current_preview])if(preview.objects.length!==source.objects.length||preview.objects.some(row=>source.objects[row.object_index]?.vertex_count!==row.vertex_count))fail('Comparison geometry differs from the source model layout.');
  return clone(value);
}

export function modelPrimitiveReviewMatches(review,source,context,edits){
  try{return Boolean(review)&&equal(review.context,modelPrimitiveContext(context))&&review.effective_sha256===source.effective_sha256&&review.source_sha256===source.source_sha256&&review.project_source_key===source.project_source_key&&equal(review.edits,edits)&&hash(review.proposed_sha256);}catch{return false;}
}

const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);return node;};
const button=(text,key)=>{const node=element('button',text);node.type='button';node.dataset.action=key;return node;};

/** Context: {projectPath,sceneId,mode:'edit',sourceKey}. The parent owns state updates.
 * onScenePreview(report,edits,source,{returnToEditor}) may return false or {restore}.
 * Returns {dialog,ready,updateState,dispose}; no polling or background game work.
 */
export function openModelPrimitiveEditor({assetId,getContext,busy,setBusy,onApplied,onError=()=>{},onScenePreview=null,onInspectNormal=null,initial=null}){
  let context;
  try{if([getContext,busy,setBusy,onApplied,onError].some(f=>typeof f!=='function')||onScenePreview!==null&&typeof onScenePreview!=='function')fail('Model primitive editor requires current source and state callbacks.');if(onInspectNormal!==null&&typeof onInspectNormal!=='function')fail('Normal inspection requires a navigation callback.');if(busy()!==false)return null;context=modelPrimitiveContext(getContext());}catch(error){onError(error);return null;}
  const dialog=element('dialog');dialog.id='model-primitives-dialog';dialog.className='project-dialog';Object.assign(dialog.style,{width:'min(1160px,94vw)',maxHeight:'92vh',overflowY:'auto'});
  const heading=element('div');heading.className='dialog-heading';const close=button('×','close');close.setAttribute('aria-label','Close model faces');heading.append(element('h2','Model faces, UVs, color and normal references'),close);
  const status=element('p','Loading verified model packets…');status.setAttribute('role','status');
  const note=element('p','Edit a selected primitive or remap UVs across its textured packet group or qualified GLB material faces. Vertex connections use local indices in each object. UV and RGB values are source bytes. Lit normal references select existing normals in this object. Flat faces share one reference across all corners. Inspect current normal opens its stored coordinates; apply or discard any face draft first. Materials, normal vectors, lighting and packet counts remain fixed.');note.className='field-note';
  const selectors=element('div'),objectSelect=element('select'),primitiveSelect=element('select'),previous=button('Previous 256','previous-page'),next=button('Next 256','next-page'),pageNote=element('span');objectSelect.setAttribute('aria-label','Model object');primitiveSelect.setAttribute('aria-label','Model primitive');selectors.append(element('span','Object '),objectSelect,element('span',' Primitive '),primitiveSelect,previous,pageNote,next);
  const metadata=element('p'),form=element('form'),fields=element('div');fields.className='model-primitive-fields';form.append(fields);
  const uvTool=element('details'),uvFields=new Map();uvTool.append(element('summary','Retarget a UV rectangle'),element('p','Copy Current UVs from an explicit source rectangle into a target rectangle. Endpoints are inclusive native bytes (0–255); reversed target endpoints mirror an axis. Every selected corner must fit the source rectangle. Selected vertex, color and normal drafts are retained; texture bindings remain unchanged.'));
  for(const kind of ['Source','Target']){const line=element('div');Object.assign(line.style,{display:'flex',gap:'12px',flexWrap:'wrap',margin:'12px 0'});for(const [i,name] of ['U start','V start','U end','V end'].entries()){const label=element('label',`${kind} ${name}`),input=element('input');input.type='number';input.min='0';input.max='255';input.step='1';input.value=i<2?'0':'255';input.setAttribute('aria-label',`${kind} ${name}`);Object.assign(input.style,{width:'90px'});label.append(input);line.append(label);uvFields.set(`${kind}${i}`,input);}uvTool.append(line);}
  const uvScope=element('select');uvScope.setAttribute('aria-label','UV remap scope');for(const [value,label] of [['primitive','Selected primitive'],['group','All textured primitives in selected packet group'],['glb','Qualified GLB material faces']]){const option=element('option',label);option.value=value;uvScope.append(option);}uvScope.value='primitive';const uvCopy=button('Copy remapped UVs into draft','uv-remap'),uvInfo=element('p');const glbSelect=button('Select UV faces from GLB image','uv-glb-faces'),glbInfo=element('p');uvTool.append(glbSelect,glbInfo,uvScope,uvCopy,uvInfo);let glbSelector=null,glbSelection=null;
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';const reset=button('Reset draft to Retail','retail'),discard=button('Discard draft','discard'),preview=button('Preview faces','preview'),apply=button('Apply reviewed faces','apply'),scene=button('Inspect proposed faces in scene','scene');scene.hidden=onScenePreview===null;actions.append(reset,discard,preview,apply,scene);
  const comparison=element('section');comparison.hidden=true;const controls=element('div'),textures=element('input'),wireframe=element('input'),normalDirections=element('input');normalDirections.type='checkbox';normalDirections.setAttribute('aria-label','Source normal directions');const normalLabel=element('label',' Source normal directions ');normalLabel.prepend(normalDirections);Object.assign(controls.style,{display:'flex',alignItems:'center',flexWrap:'wrap',gap:'14px',margin:'12px 0'});textures.type=wireframe.type='checkbox';textures.checked=true;const textureLabel=element('label',' Textures '),wireLabel=element('label',' Wireframe ');for(const label of [textureLabel,wireLabel,normalLabel])Object.assign(label.style,{display:'inline-flex',flexDirection:'row',alignItems:'center',gap:'5px',margin:'0',width:'auto'});for(const checkbox of [textures,wireframe,normalDirections])Object.assign(checkbox.style,{width:'auto',margin:'0'});textureLabel.prepend(textures);wireLabel.prepend(wireframe);controls.append(textureLabel,wireLabel,normalLabel,element('span',' Drag either view to orbit both; scroll to zoom.'));
  const columns=element('div');Object.assign(columns.style,{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:'12px'});const canvases=[];
  for(const label of ['Current','Proposed']){const panel=element('div'),canvas=element('canvas');canvas.setAttribute('aria-label',`${label} model faces`);Object.assign(canvas.style,{width:'100%',height:'330px',display:'block',touchAction:'none',background:'#10171c'});panel.append(element('h3',label),canvas);columns.append(panel);canvases.push(canvas);}
  const limits=element('p','Static texture-address preview; texture windows, animated palettes, live lighting and retail ordering are not reconstructed. Wireframe shows hidden edges.');limits.className='field-note';const audit=element('pre');audit.className='diagnostic-detail';comparison.append(controls,columns,limits,audit);
  const diagnostics=element('details');diagnostics.append(element('summary','Source hashes and packet binding'));const hashes=element('pre');diagnostics.append(hashes);dialog.append(heading,note,selectors,metadata,form,uvTool,actions,status,comparison,diagnostics);document.body.append(dialog);
  let groupDrafts=[],source=null,objectIndex=0,primitiveIndex=0,page=0,inputs=[],normalLinks=[],generation=0,controller=null,pending=null,ownBusy=false,closed=false,retainedClose=false,review=null,renderers=[],rendererError='',sceneRestore=null,initialSelection=initial;
  const view={center:[0,0,0],radius:1,yaw:.65,pitch:.3,zoom:1};
  const current=()=>{try{return !closed&&equal(context,modelPrimitiveContext(getContext()));}catch{return false;}};
  const releaseBusy=()=>{if(ownBusy){ownBusy=false;setBusy(false);}};
  const restoreScene=()=>{if(sceneRestore){const restore=sceneRestore;sceneRestore=null;try{restore();}catch(error){onError(error);}}};
  function invalidate(){generation++;review=null;comparison.hidden=true;restoreScene();if(controller){controller.abort();controller=null;pending=null;releaseBusy();}audit.textContent='';for(const renderer of renderers)renderer?.clear();}
  function dispose(){if(closed)return;closed=true;glbSelector?.dispose();glbSelector=null;glbSelection=null;dialog.dataset.sceneInspection='false';invalidate();observer?.disconnect();for(const renderer of renderers){if(!renderer)continue;renderer.clear();const gl=renderer.gl;gl.deleteBuffer(renderer.gridBuffer);gl.deleteTexture(renderer.whiteTexture);gl.deleteProgram(renderer.program);}renderers=[];if(dialog.open)dialog.close();dialog.remove();}
  function values(){
    const row=selectedRow(source,objectIndex,primitiveIndex),result={vertices:[]};if(row.uvs!==null)result.uvs=Array.from({length:row.corner_count},()=>[]);if(row.colors!==null)result.colors=Array.from({length:row.gouraud?row.corner_count:1},()=>[]);
    if(row.normal_indices!=null)result.normal_indices=[];
    for(const input of inputs){if(!input.value.trim())fail('Enter every visible primitive byte or local index.');const number=Number(input.value),{field,corner,axis}=input._primitive;if(['vertices','normal_indices'].includes(field))result[field][corner]=number;else result[field][corner][axis]=number;}
    return modelPrimitiveDraft(source,objectIndex,primitiveIndex,result);
  }
  function allEdits(){return [...groupDrafts.filter(row=>row.object_index!==objectIndex||row.primitive_index!==primitiveIndex),values()].sort((a,b)=>a.object_index-b.object_index||a.primitive_index-b.primitive_index);}
  function dirty(){try{return groupDrafts.length>0||!equal(values(),rowValues());}catch{return true;}}
  function rowValues(retail=false){const row=selectedRow(source,objectIndex,primitiveIndex,retail);return modelPrimitiveDraft(source,objectIndex,primitiveIndex,{vertices:row.vertices,...(row.uvs===null?{}:{uvs:row.uvs}),...(row.colors===null?{}:{colors:row.colors}),...(row.normal_indices==null?{}:{normal_indices:row.normal_indices})});}
  function refresh(){
    const available=current(),blocked=!available||pending!==null||busy()!==false,hasRow=source&&source.objects[objectIndex]?.primitives.length>0;let edits=null;try{if(hasRow)edits=allEdits();}catch{}
    for(const input of uvFields.values())input.disabled=blocked;uvScope.disabled=blocked;glbSelect.disabled=blocked||!source;glbSelector?.update();uvCopy.disabled=blocked||!hasRow||(uvScope.value==='glb'?!glbSelection?.can_stage:source.objects[objectIndex].primitives[primitiveIndex].uvs===null);
    uvInfo.textContent=groupDrafts.length?`${groupDrafts.length} neighboring textured face drafts retained for one reviewed Apply. Discard draft clears the whole UV batch.`:hasRow?`Selected group ${source.objects[objectIndex].primitives[primitiveIndex].group_index}: ${source.objects[objectIndex].primitives.filter(row=>row.group_index===source.objects[objectIndex].primitives[primitiveIndex].group_index&&row.uvs!==null).length} textured primitives. Copy changes drafts only; Preview faces is required.`:'No source selection.';
    for(const link of normalLinks)link.disabled=blocked||dirty();
    for(const input of inputs)input.disabled=blocked;objectSelect.disabled=primitiveSelect.disabled=blocked||!source;previous.disabled=blocked||page===0;next.disabled=blocked||!source||(page+1)*256>=source.objects[objectIndex].primitives.length;
    const reviewed=available&&modelPrimitiveReviewMatches(review,source,getContext(),edits);
    discard.disabled=blocked||!hasRow;reset.disabled=blocked||!hasRow||!!source?.authored_faces?.[objectIndex]?.some(face=>face.current_index===primitiveIndex);preview.disabled=blocked||!edits;apply.disabled=blocked||!reviewed||review?.proposed_sha256===source?.effective_sha256;scene.disabled=blocked||!reviewed;close.disabled=pending==='apply';
    if(!available){glbSelector?.dispose();glbSelector=null;glbSelection=null;glbInfo.textContent='GLB UV face selection withdrawn.';invalidate();status.textContent='Project, scene or model source changed. Reopen the face editor.';}
  }
  function selectRows(){
    primitiveSelect.replaceChildren();const rows=source.objects[objectIndex].primitives,start=page*256,end=Math.min(rows.length,start+256);for(let i=start;i<end;i++){const option=element('option',`Primitive ${i} · ${rows[i].corner_count} corners`);option.value=String(i);primitiveSelect.append(option);}primitiveSelect.value=String(primitiveIndex);pageNote.textContent=rows.length?` ${start}–${end-1} of ${rows.length} `:' No primitives ';displayRow();
  }
  function displayRow(){
    invalidate();groupDrafts=[];fields.replaceChildren();inputs=[];normalLinks=[];const entry=source.objects[objectIndex],row=entry.primitives[primitiveIndex];
    if(!row){metadata.textContent='This source object has no editable primitives.';refresh();return;}
    metadata.textContent=`Object ${objectIndex} · Current primitive ${primitiveIndex} · Retail face ${source.face_mappings?(source.face_mappings[objectIndex].find(face=>face.current_index===primitiveIndex)?.retail_index??'none (authored)'):primitiveIndex} · group ${row.group_index} · flags 0x${row.flags.toString(16)} · payload offset ${row.byte_offset} · ${row.gouraud?'Gouraud':'Flat'} · CLUT ${row.material.clut??'none'} · texture page ${row.material.tpage??'none'} · semitransparency ${row.material.semi_transparent?'enabled':'disabled'} (read-only).`;
    hashes.textContent=JSON.stringify({asset_id:source.asset_id,retail_sha256:source.source_sha256,current_sha256:source.effective_sha256,project_source_key:source.project_source_key},null,2);
    const table=element('table'),head=element('tr');Object.assign(table.style,{width:'100%',borderCollapse:'collapse',fontSize:'12px',margin:'10px 0'});fields.style.overflowX='auto';for(const title of ['Corner','Local vertex','UV bytes','Baked RGB / normal reference']){const cell=element('th',title);Object.assign(cell.style,{padding:'4px 6px',textAlign:'left',borderBottom:'1px solid #344b4d'});head.append(cell);}table.append(head);
    const numberInput=(field,corner,axis,value,max,label)=>{const input=element('input');Object.assign(input.style,{width:'72px',maxWidth:'100%',minWidth:'0',padding:'5px 6px'});input.type='number';input.min='0';input.max=String(max);input.step='1';input.required=true;input.value=String(value);input.setAttribute('aria-label',label);input._primitive={field,corner,axis};input.oninput=()=>{invalidate();status.textContent='Draft changed. Preview again before Apply.';refresh();};inputs.push(input);return input;};
    const axisInput=(name,input)=>{const label=element('label',name);Object.assign(label.style,{display:'inline-flex',flexDirection:'row',alignItems:'center',gap:'4px',margin:'0',width:'auto',whiteSpace:'nowrap'});label.append(input);return label;};
    const axisGroup=()=>{const group=element('div');Object.assign(group.style,{display:'flex',alignItems:'center',gap:'6px',flexWrap:'wrap'});return group;};
    for(let corner=0;corner<row.corner_count;corner++){
      const tr=element('tr'),vertex=element('td'),uv=element('td'),rgb=element('td');vertex.append(numberInput('vertices',corner,0,row.vertices[corner],Math.min(8191,entry.vertex_count-1),`Corner ${corner} local vertex`));
      if(row.uvs===null)uv.textContent='Untextured';else{const group=axisGroup();for(const [axis,name] of ['U','V'].entries())group.append(axisInput(name,numberInput('uvs',corner,axis,row.uvs[corner][axis],255,`Corner ${corner} ${name}`)));uv.append(group);}
      if(row.colors===null){if(row.normal_indices==null)rgb.textContent='Lit color · normal references unavailable';else if(!row.gouraud&&corner>0)rgb.textContent='Uses flat normal from corner 0';else{const slot=row.gouraud?corner:0;rgb.append(numberInput('normal_indices',slot,null,row.normal_indices[slot],Math.min(8191,entry.normal_count-1),`${row.gouraud?'Corner '+corner:'Flat'} normal index`));if(onInspectNormal){const link=button(row.gouraud?`Inspect current corner ${corner} normal`:'Inspect current flat normal',`inspect-normal-${slot}`);link.style.marginTop='6px';link.onclick=async()=>{if(!current()||pending!==null||busy()!==false||dirty())return false;try{return await onInspectNormal({kind:'normal',object_index:objectIndex,vector_index:row.normal_indices[slot]},clone(source));}catch(error){onError(error);return false;}};normalLinks.push(link);rgb.append(link);}}}else if(!row.gouraud&&corner>0)rgb.textContent='Uses stored flat RGB';else{const group=axisGroup();for(const [axis,name] of ['R','G','B'].entries())group.append(axisInput(name,numberInput('colors',row.gouraud?corner:0,axis,row.colors[row.gouraud?corner:0][axis],255,`${row.gouraud?'Corner '+corner:'Flat'} ${name}`)));rgb.append(group);}
      const cornerCell=element('th',corner);for(const cell of [cornerCell,vertex,uv,rgb])Object.assign(cell.style,{padding:'4px 6px',textAlign:'left',verticalAlign:'top',borderBottom:'1px solid #344b4d'});tr.append(cornerCell,vertex,uv,rgb);table.append(tr);
    }
    fields.append(table);status.textContent='Current source values loaded. Preview a draft before Apply.';refresh();
  }
  function setDraft(retail){invalidate();groupDrafts=[];const row=rowValues(retail);for(const input of inputs){const {field,corner,axis}=input._primitive;input.value=String(['vertices','normal_indices'].includes(field)?row[field][corner]:row[field][corner][axis]);}status.textContent=retail?'Retail values copied into this primitive draft. Other current primitives remain unchanged. Preview before Apply.':'Draft discarded; Current values restored.';refresh();}
  for(const input of uvFields.values())input.oninput=()=>{invalidate();status.textContent='UV rectangle choices changed. Copy into draft, then Preview faces.';refresh();};uvScope.onchange=()=>{invalidate();refresh();};
  glbSelect.onclick=()=>{refresh();if(glbSelect.disabled)return;glbSelector?.dispose();glbSelector=openGlbMaterialSelection({assetId,source:primitiveGlbSelectionSource(source,context),purpose:'uv',getContext,busy,setBusy,onError,onSelected:selection=>{if(!current()||selection.effective_sha256!==source.effective_sha256)fail('Model changed before UV face selection returned.');invalidate();glbSelection=clone(selection);uvScope.value='glb';glbInfo.textContent=`${selection.face_count} complete native faces selected from GLB material ${selection.material_index}, image ${selection.image_index}. Set explicit Source/Target byte rectangles, then copy into draft.`;refresh();}});};
  uvCopy.onclick=()=>{if(!current()||pending||busy()!==false||uvCopy.disabled)return false;try{const from=Array.from({length:4},(_,i)=>{const value=uvFields.get(`Source${i}`).value;return value.trim()===''?NaN:Number(value);}),to=Array.from({length:4},(_,i)=>{const value=uvFields.get(`Target${i}`).value;return value.trim()===''?NaN:Number(value);}),next=uvScope.value==='glb'?uvSelectionDrafts(source,glbSelection,from,to,allEdits()):uvRectangleDrafts(source,values(),from,to,uvScope.value);for(const row of next)modelPrimitiveDraft(source,row.object_index,row.primitive_index,Object.fromEntries(Object.entries(row).filter(([key])=>!['object_index','primitive_index'].includes(key))));const selected=next.find(row=>row.object_index===objectIndex&&row.primitive_index===primitiveIndex);invalidate();groupDrafts=next.filter(row=>row.object_index!==objectIndex||row.primitive_index!==primitiveIndex);for(const input of inputs)if(selected&&input._primitive.field==='uvs')input.value=String(selected.uvs[input._primitive.corner][input._primitive.axis]);status.textContent=`Current UVs remapped into ${next.length} textured face drafts. Preview faces before one Apply; all model consumers share this edit.`;refresh();return true;}catch(error){status.textContent=error.message;onError(error);return false;}};
  async function request(path,payload,phase){
    const active=new AbortController();controller=active;pending=phase;ownBusy=true;setBusy(true);refresh();
    try{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:active.signal}),value=await response.json();if(active.signal.aborted)fail('Request cancelled.');if(!response.ok||value?.error)fail(typeof value?.error==='string'?value.error:'Model primitive request failed.');return value;}
    finally{if(controller===active){controller=null;pending=null;releaseBusy();refresh();}}
  }
  async function load(){
    const token=++generation;
    try{const value=await request('/api/model-primitive-source',{asset_id:assetId},'source');if(!current()||token!==generation)return false;source=decodeModelPrimitives(value,assetId,context);glbSelection=null;glbInfo.textContent='Qualify a fresh Current GLB/binding to select UV faces.';if(initialSelection!==null){if(!exact(initialSelection,['object_index','primitive_index']))fail('Invalid initial primitive selection.');selectedRow(source,initialSelection.object_index,initialSelection.primitive_index);objectIndex=initialSelection.object_index;primitiveIndex=initialSelection.primitive_index;initialSelection=null;}objectSelect.replaceChildren();for(const entry of source.objects){const option=element('option',`Object ${entry.object_index} · ${entry.vertex_count} vertices`);option.value=String(entry.object_index);objectSelect.append(option);}if(!source.objects[objectIndex]?.primitives.length)objectIndex=Math.max(0,source.objects.findIndex(entry=>entry.primitives.length));primitiveIndex=Math.min(primitiveIndex,Math.max(0,source.objects[objectIndex].primitives.length-1));page=Math.floor(primitiveIndex/256);objectSelect.value=String(objectIndex);selectRows();return true;}catch(error){if(!closed&&error.name!=='AbortError'&&token===generation){status.textContent=error.message;onError(error);}return false;}
  }
  normalDirections.onchange=()=>draw();
  function draw(){
    if(closed||comparison.hidden||!dialog.open||!review)return;
    const c=Math.cos(view.yaw),s=Math.sin(view.yaw),cp=Math.cos(view.pitch),sp=Math.sin(view.pitch);
    for(const [index,canvas] of canvases.entries()){const bounds=canvas.getBoundingClientRect();renderers[index]?.draw({width:bounds.width,height:bounds.height,positions:new Map(),grid:false,normalDiagnostic:normalDirections.checked,wireframe:wireframe.checked,camera:{target:{x:view.center[0],y:-view.center[1],z:view.center[2]},distance:view.radius*4/view.zoom*.9/1.3},basis:{right:{x:c,y:0,z:s},up:{x:sp*s,y:cp,z:-sp*c},forward:{x:-cp*s,y:sp,z:cp*c}}});}
  }
  function render(fit=false){
    if(!review)return;const previews=[review.report.current_preview,review.report.preview];rendererError='';
    if(fit){const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];for(const data of previews){const selected=data.objects.find(row=>row.object_index===objectIndex);for(let i=selected.vertex_start;i<selected.vertex_start+selected.vertex_count;i++)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],data.vertices[i][axis]);max[axis]=Math.max(max[axis],data.vertices[i][axis]);}}view.center=min.map((n,i)=>(n+max[i])/2);view.radius=Math.max(1,Math.hypot(...max.map((n,i)=>n-min[i]))/2);view.zoom=1;}
    for(const [index,data] of previews.entries())try{
      if(!renderers[index])renderers[index]=new SceneRenderer(canvases[index],message=>{if(!closed&&message)status.textContent=message;});
      const selected=data.objects.find(row=>row.object_index===objectIndex),start=selected.triangle_start,end=start+selected.triangle_count,geometry={...data,triangles:data.triangles.slice(start,end),triangle_colors:data.triangle_colors.slice(start,end),triangle_uvs:data.triangle_uvs.slice(start,end),triangle_materials:data.triangle_materials.slice(start,end),...(data.triangle_normals?{triangle_normals:data.triangle_normals.slice(start,end)}:{}),textures:textures.checked?data.textures:[]};
      const failures=renderers[index].load({assets:[{geometry_key:'primitive-view',preview:geometry}],entities:[{entity_id:'primitive-view',geometry_key:'primitive-view',renderable:true,model_to_scene:IDENTITY}]});if(failures.length)fail(failures.join('; '));
    }catch(error){rendererError=error.message;}
    comparison.hidden=false;draw();if(rendererError)status.textContent+=' Graphics preview: '+rendererError;
  }
  preview.onclick=async()=>{
    if(!current()||pending||busy()!==false)return false;let edits;try{edits=allEdits();}catch(error){status.textContent=error.message;return false;}invalidate();const token=++generation,fingerprint=JSON.stringify(edits);status.textContent='Reviewing current and proposed primitive values…';
    try{const value=await request('/api/model-primitive-preview',{asset_id:assetId,expected_sha256:source.effective_sha256,source_key:context.sourceKey,edits},'preview');if(!current()||token!==generation||JSON.stringify(allEdits())!==fingerprint)return false;const report=decodeModelPrimitivePreview(value,source,context,edits);review={context:clone(context),effective_sha256:source.effective_sha256,source_sha256:source.source_sha256,project_source_key:source.project_source_key,edits:clone(edits),proposed_sha256:report.proposed_sha256,report};status.textContent=`${report.changes_from_current.length} values change from Current; ${report.coordinate_changes.length} total coordinate/primitive changes from Retail. Project unchanged. ${report.changes_from_current.length?'Ready for one undoable Apply.':'No model change.'}`;audit.textContent=report.changes_from_current.slice(0,256).map(row=>`Object ${row.object_index} · primitive ${row.primitive_index} · corner ${row.corner_index} · ${row.field}${row.axis?'.'+row.axis:''}: ${row.before_value} → ${row.after_value}`).join('\n')+(report.changes_from_current.length>256?`\nFirst 256 of ${report.changes_from_current.length} changes shown.`:'');render(true);refresh();return true;}catch(error){if(!closed&&token===generation&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}return false;}
  };
  apply.onclick=async()=>{
    if(!current()||pending||busy()!==false)return false;let edits;try{edits=allEdits();}catch{return false;}if(!modelPrimitiveReviewMatches(review,source,getContext(),edits)||review.proposed_sha256===source.effective_sha256)return false;const accepted=review,token=generation;status.textContent='Applying reviewed model faces…';
    try{const value=await request('/api/model-primitives',{asset_id:assetId,expected_sha256:source.effective_sha256,source_key:context.sourceKey,proposed_sha256:accepted.proposed_sha256,edits},'apply');if(!current()||closed||generation!==token||!modelPrimitiveReviewMatches(accepted,source,getContext(),allEdits()))return false;if(!object(value)||!object(value.project))fail('Invalid SDK state after model primitive Apply.');pending='apply';releaseBusy();refresh();await onApplied(value);if(closed)return true;const nextContext=modelPrimitiveContext(getContext());if(nextContext.projectPath!==context.projectPath||nextContext.sceneId!==context.sceneId)return false;context=nextContext;pending=null;invalidate();status.textContent='Applied. Save the project to persist these faces.';await load();return true;}catch(error){if(!closed&&error.name!=='AbortError'){status.textContent=error.message;onError(error);}return false;}finally{if(pending==='apply'){pending=null;refresh();}}
  };
  scene.onclick=async()=>{
    if(!onScenePreview||!current()||pending||busy()!==false)return false;let edits;try{edits=allEdits();}catch{return false;}if(!modelPrimitiveReviewMatches(review,source,getContext(),edits))return false;const accepted=review;
    const returnToEditor=()=>{let matches=false;try{matches=current()&&review===accepted&&modelPrimitiveReviewMatches(accepted,source,getContext(),allEdits());}catch{}if(!matches){dispose();return false;}restoreScene();dialog.dataset.sceneInspection='false';if(!dialog.open)dialog.showModal();draw();refresh();return true;};
    pending='scene';refresh();
    try{const result=await onScenePreview(clone(accepted.report),clone(edits),clone(source),{returnToEditor});if(result===false||!current()||review!==accepted){result?.restore?.();return false;}if(typeof result?.restore==='function')sceneRestore=result.restore;retainedClose=true;dialog.dataset.sceneInspection='true';dialog.close();return true;}catch(error){if(!closed){status.textContent=error.message;onError(error);}return false;}finally{if(pending==='scene'){pending=null;refresh();}}
  };
  objectSelect.onchange=()=>{const chosen=Number(objectSelect.value);if(source.objects[objectIndex].primitives.length&&dirty()){objectSelect.value=String(objectIndex);status.textContent='Apply or discard this primitive draft before changing objects.';return;}objectIndex=chosen;primitiveIndex=0;page=0;selectRows();};
  primitiveSelect.onchange=()=>{const chosen=Number(primitiveSelect.value);if(dirty()){primitiveSelect.value=String(primitiveIndex);status.textContent='Apply or discard this primitive draft before changing primitives.';return;}primitiveIndex=chosen;displayRow();};
  const turnPage=direction=>{if(!current()||pending||busy()!==false||dirty())return false;const nextPage=page+direction;if(nextPage<0||nextPage*256>=source.objects[objectIndex].primitives.length)return false;page=nextPage;primitiveIndex=page*256;selectRows();return true;};previous.onclick=()=>turnPage(-1);next.onclick=()=>turnPage(1);reset.onclick=()=>{if(current()&&!pending&&busy()===false)setDraft(true);};discard.onclick=()=>{if(current()&&!pending&&busy()===false)setDraft(false);};form.onsubmit=event=>{event.preventDefault();return preview.onclick();};
  textures.onchange=()=>render(false);wireframe.onchange=draw;
  for(const canvas of canvases){let drag=null;canvas.onpointerdown=event=>{canvas.setPointerCapture(event.pointerId);drag={x:event.clientX,y:event.clientY};};canvas.onpointermove=event=>{if(!drag)return;view.yaw+=(event.clientX-drag.x)*.009;view.pitch=Math.max(-1.5,Math.min(1.5,view.pitch+(event.clientY-drag.y)*.009));drag={x:event.clientX,y:event.clientY};draw();};canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};canvas.addEventListener('wheel',event=>{event.preventDefault();view.zoom=Math.max(.15,Math.min(4,view.zoom*Math.exp(-event.deltaY*.001)));draw();},{passive:false});}
  const observer=typeof ResizeObserver==='function'?new ResizeObserver(draw):null;for(const canvas of canvases)observer?.observe(canvas);
  close.onclick=()=>{if(pending!=='apply')dispose();};dialog.oncancel=event=>{if(pending==='apply'){event.preventDefault();status.textContent='Apply is in progress; wait for its result.';}};dialog.onclose=()=>{if(retainedClose){retainedClose=false;return;}dispose();};dialog.showModal();const ready=load();return {dialog,ready,updateState:refresh,dispose};
}

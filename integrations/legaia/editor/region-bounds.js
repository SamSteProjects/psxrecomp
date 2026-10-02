import {decodeFieldSpatial} from './field-spatial.js';

// Region X/Z coordinates use the source lookup's 64-unit bias. Height is unknown.
const CORNERS=['x0','z0','x1','z1'],BOUNDS=['x_min','x_max','z_min','z_max'];
const REPORT_KEYS=['schema_version','read_only','project_source_key','scene_id','region_id','review_key','source','region_type','values_layers','tile_bounds_layers','world_bounds_layers','requested_values','action','effective_change_count','project_change','value','scope','height_status','activation','gameplay_verified'];
const SOURCE_KEYS=['disc','iso_file','prot_entry_index','prot_entry_name','prot_start_lba','byte_offset','byte_length','byte_coordinate_space','sha256','containing_span_sha256','table_source','table_kind','record_index','containing_span_byte_offset','containing_span_byte_length'];
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const same=(a,b,keys=Object.keys(a))=>object(a)&&object(b)&&keys.every(key=>a[key]===b[key]);
const fail=message=>{throw new Error(message);};
function identity(value){
  const match=typeof value==='string'&&/^region:\/\/([A-Za-z0-9_-]{1,128})\/field-map\/primary\/([0-9]{4})$/.exec(value);
  if(!match||Number(match[2])>1020)fail('Region bounds require an existing primary MAP identity.');
  return {scene:'scene://'+match[1],name:match[1],index:Number(match[2])};
}
function corners(value){
  if(!exact(value,CORNERS)||CORNERS.some(key=>!integer(value[key],0,255)))fail('Region bounds require four integer corner bytes in 0..255.');
  return Object.fromEntries(CORNERS.map(key=>[key,value[key]]));
}
function tileBounds(values){
  values=corners(values);
  const result={x_min:Math.min(values.x0,values.x1),x_max:Math.max(values.x0,values.x1),z_min:Math.min(values.z0,values.z1),z_max:Math.max(values.z0,values.z1)};
  if(result.x_min===result.x_max)result.x_max+=2;
  if(result.z_min===result.z_max)result.z_min-=2;
  return result;
}
function worldBounds(tiles){return Object.fromEntries(BOUNDS.map(key=>[key,tiles[key]*128+64]));}
function validateBounds(tiles,world,values){
  const expected=tileBounds(values);
  if(!exact(tiles,BOUNDS)||!same(tiles,expected,BOUNDS)||!exact(world,BOUNDS)||!same(world,worldBounds(expected),BOUNDS))fail('Region bounds differ from the source rectangle normalization or world quantization.');
}
function recordContext(record,state){
  const id=identity(record?.id),data=record?.data,source=data?.source_record;
  if(record.type!=='region'||record.sceneId!==id.scene||state?.scene?.id!==id.scene||state.project?.mode!=='edit'||!hash(state.project_copy_source_key)||data?.semantic_id!==record.id||data.asset_kind!=='region'||data.table_source!=='primary'||data.table_kind!==3||data.record_index!==id.index||!exact(data.encoded,[...CORNERS,'type'])||!integer(data.encoded.type,0,255))fail('Region catalog selection differs from the active editable scene.');
  if(!exact(source,SOURCE_KEYS)||!exact(source.disc,['sha256','serial'])||!hash(source.disc.sha256)||source.disc.serial!=='SCUS-94254'||source.iso_file!=='PROT.DAT'||source.prot_entry_name!==id.name||!integer(source.prot_entry_index,0,0xffffffff)||!integer(source.prot_start_lba,0,0xffffffff)||!hash(source.sha256)||!hash(source.containing_span_sha256)||source.byte_coordinate_space!=='prot_entry'||source.byte_length!==8||source.table_source!=='primary'||source.table_kind!==3||source.record_index!==id.index||source.containing_span_byte_offset!==65536||source.containing_span_byte_length!==8192||!integer(source.byte_offset,65554,73720)||source.byte_offset-id.index*8<65554)fail('Region catalog source provenance is invalid.');
  const imported=corners(Object.fromEntries(CORNERS.map(key=>[key,data.encoded[key]])));
  if(!exact(data.tile_bounds,BOUNDS)||!same(data.tile_bounds,tileBounds(imported),BOUNDS))fail('Region catalog bounds differ from its encoded source corners.');
  return {id,source,imported,region_type:data.encoded.type};
}

export function decodeRegionBoundsReview(value,record,state){
  const context=recordContext(record,state);
  if(!exact(value,REPORT_KEYS)||value.schema_version!=='legaia.region-bounds-review.v1'||value.read_only!==true||value.project_source_key!==state.project_copy_source_key||value.scene_id!==context.id.scene||value.region_id!==record.id||!hash(value.review_key)||value.scope!=='source-MAP-region-bounds-only'||value.height_status!=='unknown'||value.activation!=='not_evaluated'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||value.region_type!==context.region_type)fail('Region bounds review is invalid or stale.');
  const source=value.source;
  if(!exact(source,['map_sha256','row_sha256','record_index','byte_offset','byte_length'])||!hash(source.map_sha256)||source.row_sha256!==context.source.sha256||source.record_index!==context.source.record_index||source.byte_offset!==context.source.byte_offset||source.byte_length!==8||state.scene_selection_map_sha256!=null&&source.map_sha256!==state.scene_selection_map_sha256)fail('Region bounds review differs from its source row or MAP identity.');
  if(!exact(value.values_layers,['imported','authored','current','proposed'])||!exact(value.tile_bounds_layers,['imported','current','proposed'])||!exact(value.world_bounds_layers,['imported','current','proposed']))fail('Region bounds review layers are incomplete.');
  const layers=value.values_layers,imported=corners(layers.imported),current=corners(layers.current),proposed=corners(layers.proposed);
  if(!same(imported,context.imported,CORNERS)||!object(layers.authored)||![0,4].includes(Object.keys(layers.authored).length))fail('Region bounds imported or authored corners are invalid.');
  const authored=Object.keys(layers.authored).length?corners(layers.authored):{};
  if(!same(current,Object.keys(authored).length?authored:imported,CORNERS))fail('Region Current bounds differ from their authored layer.');
  for(const layer of ['imported','current','proposed'])validateBounds(value.tile_bounds_layers[layer],value.world_bounds_layers[layer],layers[layer]);
  if(!['set','clear'].includes(value.action)||value.requested_values!==null&&!exact(value.requested_values,CORNERS)||value.action==='clear'&&value.requested_values!==null)fail('Region bounds review has an invalid requested action.');
  const requested=value.requested_values===null?null:corners(value.requested_values),expected=value.action==='clear'?imported:requested??current;
  if(!same(proposed,expected,CORNERS)||!integer(value.effective_change_count,0,4)||value.effective_change_count!==CORNERS.filter(key=>current[key]!==proposed[key]).length||value.effective_change_count>0&&!value.project_change||value.action==='set'&&requested===null&&value.project_change)fail('Region bounds proposal or change count is inconsistent.');
  const binding=value.value;
  if(!exact(binding,['source_sha256','edits'])||binding.source_sha256!==source.map_sha256||!Array.isArray(binding.edits)||binding.edits.length>1021)fail('Region bounds proposal lacks a qualified MAP binding.');
  const seen=new Set();let selected=null,previous='';
  for(const edit of binding.edits){
    if(!exact(edit,['region_id',...CORNERS]))fail('Region proposal edit fields are invalid.');
    const editId=identity(edit.region_id);corners(Object.fromEntries(CORNERS.map(key=>[key,edit[key]])));
    if(editId.scene!==context.id.scene||seen.has(edit.region_id)||edit.region_id<previous)fail('Region proposal identities are duplicated, unordered or cross-scene.');
    seen.add(edit.region_id);previous=edit.region_id;if(edit.region_id===record.id)selected=edit;
  }
  if(selected?!same(selected,proposed,CORNERS)||value.action==='clear':!same(proposed,imported,CORNERS))fail('Region proposal binding differs from its selected reviewed corners.');
  return structuredClone(value);
}

export function regionBoundsGeometry(report,layer='proposed'){
  if(!['imported','current','proposed'].includes(layer))fail('Invalid region comparison layer.');
  identity(report?.region_id);
  if(report.height_status!=='unknown'||report.activation!=='not_evaluated'||report.gameplay_verified!==false)fail('Region geometry requires an unverified source reference plane.');
  const tiles=report.tile_bounds_layers?.[layer],bounds=report.world_bounds_layers?.[layer];
  validateBounds(tiles,bounds,report.values_layers?.[layer]);
  return {id:report.region_id,kind:'region',world_bounds:{...bounds},world_center:{x:(bounds.x_min+bounds.x_max)/2,y:0,z:(bounds.z_min+bounds.z_max)/2}};
}

export function decodeRegionBoundsAnnotations(list,sourceSpatial){
  const spatial=decodeFieldSpatial(sourceSpatial,sourceSpatial?.scene_id);
  if(!Array.isArray(list)||list.length>1021)fail('Region annotations exceed the supported primary table.');
  const rows=new Map(spatial.records.filter(row=>row.kind==='region'&&row.table_source==='primary').map(row=>[row.id,row])),seen=new Set();
  for(const annotation of list){
    if(!exact(annotation,['region_id','row_sha256','values_layers','tile_bounds_layers','world_bounds_layers']))fail('Region annotation fields are invalid.');
    const id=identity(annotation.region_id),source=rows.get(annotation.region_id);
    if(id.scene!==spatial.scene_id||!source||seen.has(annotation.region_id)||annotation.row_sha256!==source.source_record.sha256)fail('Region annotation differs from its immutable source row.');
    seen.add(annotation.region_id);
    if(!exact(annotation.values_layers,['imported','authored','effective'])||!exact(annotation.tile_bounds_layers,['imported','effective'])||!exact(annotation.world_bounds_layers,['imported','effective']))fail('Region annotation layers are incomplete.');
    const imported=corners(annotation.values_layers.imported),authored=corners(annotation.values_layers.authored),effective=corners(annotation.values_layers.effective);
    if(!same(authored,effective,CORNERS)||!same(tileBounds(imported),source.source_tile_bounds,BOUNDS))fail('Region annotations differ from imported bounds or authored corners.');
    for(const layer of ['imported','effective'])validateBounds(annotation.tile_bounds_layers[layer],annotation.world_bounds_layers[layer],annotation.values_layers[layer]);
  }
  return structuredClone(list);
}

function element(tag,text){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;}
function layerTable(report){
  const table=element('table'),heading=element('tr');for(const title of ['Corner byte','Retail','Authored','Current','Proposed'])heading.append(element('th',title));table.append(heading);
  for(const field of CORNERS){const row=element('tr');row.append(element('th',field));for(const layer of ['imported','authored','current','proposed'])row.append(element('td',Object.hasOwn(report.values_layers[layer],field)?String(report.values_layers[layer][field]):'None · inherit'));table.append(row);}
  return table;
}
function outlines(report){
  const section=element('section'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),layers=['imported','current','proposed'],colors=['#83aaff','#f7bf4f','#70e9af'];
  const bounds=layers.map(layer=>report.tile_bounds_layers[layer]),x=Math.min(...bounds.map(row=>row.x_min))-2,z=Math.min(...bounds.map(row=>row.z_min))-2,width=Math.max(...bounds.map(row=>row.x_max))-x+2,height=Math.max(...bounds.map(row=>row.z_max))-z+2;
  svg.setAttribute('viewBox',`${x} ${z} ${width} ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Retail, Current and Proposed region outlines; X increases right, Z increases down');svg.style.width='100%';svg.style.height='240px';svg.style.background='#171e29';
  for(const [index,layer] of layers.entries()){const row=report.tile_bounds_layers[layer],rect=document.createElementNS(svg.namespaceURI,'rect');for(const [key,value] of Object.entries({x:row.x_min,y:row.z_min,width:row.x_max-row.x_min,height:row.z_max-row.z_min,fill:'none',stroke:colors[index],'stroke-width':2,'vector-effect':'non-scaling-stroke','stroke-dasharray':index===0?'7 4':index===1?'3 3':'none'}))rect.setAttribute(key,value);const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=`${['Retail','Current','Proposed'][index]} · half-open tile X [${row.x_min}, ${row.x_max}), Z [${row.z_min}, ${row.z_max})`;rect.append(title);svg.append(rect);}
  section.append(svg,element('p','Blue dashed: Retail · gold dotted: Current · green: Proposed. Region lookup uses tile = (world - 64) >> 7. Y=0 is a reference plane; floor height and activation remain unknown.'));
  const table=element('table'),heading=element('tr');for(const title of ['Layer','World X [min, max)','World Z [min, max)'])heading.append(element('th',title));table.append(heading);for(const [index,layer] of layers.entries()){const row=element('tr'),world=report.world_bounds_layers[layer];row.append(element('th',['Retail','Current','Proposed'][index]),element('td',`[${world.x_min}, ${world.x_max})`),element('td',`[${world.z_min}, ${world.z_max})`));table.append(row);}section.append(table);return section;
}

export function openRegionBounds({record,getState,busy,setBusy,api,current,onInspection=()=>{},onFrame=()=>{},onError=()=>{}}){
  let binding;
  try{if([getState,busy,setBusy,api,current,onInspection,onFrame,onError].some(callback=>typeof callback!=='function'))fail('Region editing requires current editor guards.');if(busy()!==false||current()!==true)return null;recordContext(record,getState());binding={key:getState().project_copy_source_key,scene:getState().scene.id};}catch(error){onError(error);return null;}
  const dialog=element('dialog');dialog.id='region-bounds-dialog';dialog.className='project-dialog';dialog.style.width='min(850px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
  const heading=element('div'),close=element('button','×');heading.className='dialog-heading';close.type='button';close.setAttribute('aria-label','Close region bounds');heading.append(element('h2','Source region bounds'),close);dialog.append(heading,element('p',`Primary region ${record.data.record_index} · type ${record.data.encoded.type} (read-only). Only the four corner bytes change. Reversed and equal corners preserve the source rectangle convention.`));
  const form=element('form'),inputs=new Map();form.style.display='grid';form.style.gridTemplateColumns='repeat(2,minmax(0,1fr))';form.style.gap='10px';
  for(const field of CORNERS){const label=element('label',field),input=element('input');input.name=field;input.type='number';input.min='0';input.max='255';input.step='1';input.required=true;input.value=String(record.data.encoded[field]);input.setAttribute('aria-label','Region '+field);label.append(input);form.append(label);inputs.set(field,input);}
  const reviewButton=element('button','Review bounds');reviewButton.type='submit';reviewButton.dataset.review='';form.append(reviewButton);dialog.append(form);
  const status=element('p');status.setAttribute('role','status');const output=element('div');output.dataset.regionResult='';dialog.append(status,output);
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';
  const clear=element('button','Review retail reset');clear.type='button';clear.dataset.clear='';actions.append(clear);
  const inspectionButtons=[];
  for(const [layer,text] of [['imported','Inspect retail bounds'],['current','Inspect current bounds'],['proposed','Inspect proposed bounds']]){const button=element('button',text);button.type='button';button.dataset.inspect=layer;actions.append(button);inspectionButtons.push(button);}
  const frame=element('button','Frame region bounds'),apply=element('button','Apply region bounds'),cancel=element('button','Close');for(const button of [frame,apply,cancel])button.type='button';frame.dataset.frame='';apply.dataset.apply='';actions.append(frame,apply,cancel);dialog.append(actions);
  const strip=element('div');strip.id='region-bounds-preview';strip.hidden=true;strip.className='project-dialog';Object.assign(strip.style,{position:'fixed',bottom:'18px',right:'18px',zIndex:'100',maxWidth:'440px',padding:'12px'});const note=element('p'),returnButton=element('button','Return to region review'),restoreButton=element('button','Restore source cells');returnButton.type=restoreButton.type='button';strip.append(note,returnButton,restoreButton);
  let controller=null,generation=0,pending=false,closed=false,retainedClose=false,reviewed=null,inspectionLayer=null;
  const isCurrent=()=>!closed&&current()===true&&getState().project?.mode==='edit'&&getState().scene?.id===binding.scene&&getState().project_copy_source_key===binding.key;
  const fingerprint=()=>JSON.stringify(CORNERS.map(field=>inputs.get(field).value));
  const values=()=>corners(Object.fromEntries(CORNERS.map(field=>{const value=inputs.get(field).value;if(typeof value!=='string'||!value.trim())fail('Enter all four region corner bytes.');return [field,Number(value)];})));
  const restoreInspection=()=>{if(inspectionLayer!==null){inspectionLayer=null;onInspection(null);}strip.hidden=true;};
  function withdraw(){generation++;if(controller){controller.abort();controller=null;setBusy(false);}reviewed=null;restoreInspection();output.replaceChildren();}
  function dispose(){if(closed)return;closed=true;withdraw();if(dialog.open)dialog.close();dialog.remove();strip.remove();}
  function refresh(){
    if(!isCurrent()){status.textContent='Project, scene or source changed. Reopen region bounds.';for(const button of [reviewButton,clear,frame,apply,...inspectionButtons])button.disabled=true;for(const input of inputs.values())input.disabled=true;returnButton.disabled=true;restoreInspection();return;}
    const blocked=pending||busy()!==false;for(const input of inputs.values())input.disabled=blocked;let valid=true;try{values();}catch{valid=false;}
    reviewButton.disabled=blocked||!valid;clear.disabled=blocked;frame.disabled=blocked||!reviewed;apply.disabled=blocked||!reviewed?.project_change;for(const button of inspectionButtons)button.disabled=blocked||!reviewed;returnButton.disabled=blocked;restoreButton.disabled=pending&&controller===null;
  }
  async function load(requested=null,action='set',initial=false){
    if(pending||busy()!==false||!isCurrent())return false;
    withdraw();const token=++generation,requestedFingerprint=fingerprint(),activeController=new AbortController();controller=activeController;pending=true;setBusy(true);status.textContent='Qualifying source region bounds…';refresh();
    try{
      const response=await fetch('/api/region-bounds-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({region_id:record.id,values:requested,action}),signal:activeController.signal}),value=await response.json();
      if(activeController.signal.aborted||closed||!dialog.open||generation!==token||!isCurrent()||fingerprint()!==requestedFingerprint)return false;
      if(!response.ok||value.error)fail(typeof value.error==='string'?value.error:'Region bounds review failed.');
      const report=decodeRegionBoundsReview(value,record,getState());
      if(report.action!==action||(requested===null?report.requested_values!==null:!same(report.requested_values,requested,CORNERS)))fail('Region review differs from the requested bounds.');
      reviewed=report;if(initial)for(const field of CORNERS)inputs.get(field).value=String(report.values_layers.current[field]);
      status.textContent=`${report.effective_change_count} changed corner bytes · ${report.project_change?'Ready for one undoable Apply':'No project change'}. Region type, padding and other source bytes are preserved.`;output.append(layerTable(report),outlines(report));return true;
    }catch(error){if(error.name!=='AbortError'&&!closed&&generation===token){status.textContent=error.message;onError(error);}return false;}
    finally{if(controller===activeController){controller=null;pending=false;setBusy(false);}refresh();}
  }
  form.oninput=()=>{if(closed)return;withdraw();pending=false;status.textContent='Inputs changed; review bounds again.';refresh();};
  form.onsubmit=async event=>{event.preventDefault();if(pending||busy()!==false||!isCurrent()||!form.reportValidity())return false;try{return await load(values(),'set');}catch(error){status.textContent=error.message;onError(error);return false;}};
  clear.onclick=()=>load(null,'clear');
  for(const button of inspectionButtons)button.onclick=()=>{
    if(pending||busy()!==false||!reviewed||!isCurrent()||!dialog.open)return false;
    inspectionLayer=button.dataset.inspect;note.textContent=`${inspectionLayer==='imported'?'Retail':inspectionLayer==='current'?'Current':'Proposed'} region bounds · Y=0 reference plane · inspection only`;strip.hidden=false;retainedClose=true;dialog.close();onInspection(reviewed,inspectionLayer);onFrame(reviewed,inspectionLayer);refresh();return true;
  };
  frame.onclick=()=>{if(pending||busy()!==false||!reviewed||!isCurrent())return false;onFrame(reviewed,inspectionLayer??'proposed');return true;};
  apply.onclick=async()=>{
    if(pending||busy()!==false||!reviewed?.project_change||!isCurrent()||!dialog.open)return false;
    const report=reviewed,token=++generation;pending=true;refresh();
    try{const result=await api('/api/region-bounds-apply',{type:'apply_region_bounds',region_id:report.region_id,values:report.requested_values,action:report.action,review_key:report.review_key});if(result===true){dispose();return true;}if(closed||generation!==token)return false;withdraw();status.textContent='Region bounds were rejected. Review current source bounds again.';return false;}
    catch(error){if(!closed&&generation===token){withdraw();status.textContent=error.message;onError(error);}return false;}
    finally{if(!closed){pending=false;refresh();}}
  };
  returnButton.onclick=()=>{if(pending||busy()!==false||!reviewed||!isCurrent())return false;restoreInspection();dialog.showModal();refresh();return true;};restoreButton.onclick=dispose;close.onclick=cancel.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{if(retainedClose){retainedClose=false;return;}dispose();});dialog.dispose=dispose;dialog.restore=dispose;dialog.refresh=refresh;
  document.body.append(dialog,strip);dialog.showModal();refresh();void load(null,'set',true);return dialog;
}

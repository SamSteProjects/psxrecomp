import {decodeFieldSpatial} from './field-spatial.js';

// Trigger lookup uses world >> 7, without the region query's 64-unit bias.
const CELLS=['tile_x','tile_z'],BOUNDS=['x_min','x_max','z_min','z_max'];
const REPORT_KEYS=['schema_version','read_only','project_source_key','scene_id','trigger_id','review_key','source','trigger_kind','values_layers','tile_bounds_layers','world_bounds_layers','requested_values','action','effective_change_count','project_change','value','scope','height_status','activation','gameplay_verified'];
const SOURCE_KEYS=['disc','iso_file','prot_entry_index','prot_entry_name','prot_start_lba','byte_offset','byte_length','byte_coordinate_space','sha256','containing_span_sha256','table_source','table_kind','record_index','containing_span_byte_offset','containing_span_byte_length'];
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const same=(a,b,keys)=>object(a)&&object(b)&&keys.every(key=>a[key]===b[key]);
const fail=message=>{throw new Error(message);};

function identity(value){
  const match=typeof value==='string'&&/^trigger:\/\/([A-Za-z0-9_-]{1,128})\/field-map\/primary\/kind-([01])\/([0-9]{4})$/.exec(value);
  if(!match||Number(match[3])>2042)fail('Trigger cells require an existing primary kind-0 or kind-1 MAP identity.');
  return {scene:'scene://'+match[1],name:match[1],kind:Number(match[2]),index:Number(match[3])};
}
function cells(value){
  if(!exact(value,CELLS)||CELLS.some(key=>!integer(value[key],0,255)))fail('Trigger cells require two integer tile coordinates in 0..255.');
  return Object.fromEntries(CELLS.map(key=>[key,value[key]]));
}
function tileBounds(value){const {tile_x:x,tile_z:z}=cells(value);return {x_min:x,x_max:x+1,z_min:z,z_max:z+1};}
function worldBounds(tiles){return Object.fromEntries(BOUNDS.map(key=>[key,tiles[key]*128]));}
function validateBounds(tiles,world,value){const expected=tileBounds(value);if(!exact(tiles,BOUNDS)||!same(tiles,expected,BOUNDS)||!exact(world,BOUNDS)||!same(world,worldBounds(expected),BOUNDS))fail('Trigger bounds differ from their half-open source cell or raw world quantization.');}

export function triggerCellSource(record,state){return structuredClone(recordContext(record,state));}
function recordContext(record,state){
  const id=identity(record?.id),data=record?.data,source=data?.source_record;
  if(record.type!=='trigger'||record.sceneId!==id.scene||state?.scene?.id!==id.scene||state.project?.mode!=='edit'||!hash(state.project_copy_source_key)||!hash(state.scene_trigger_state_key)||data?.semantic_id!==record.id||data.asset_kind!=='trigger'||data.table_source!=='primary'||data.table_kind!==id.kind||data.record_index!==id.index)fail('Trigger catalog selection differs from the active editable scene.');
  if(!exact(source,SOURCE_KEYS)||!exact(source.disc,['sha256','serial'])||!hash(source.disc.sha256)||source.disc.serial!=='SCUS-94254'||source.iso_file!=='PROT.DAT'||source.prot_entry_name!==id.name||!integer(source.prot_entry_index,0,0xffffffff)||!integer(source.prot_start_lba,0,0xffffffff)||!hash(source.sha256)||!hash(source.containing_span_sha256)||source.byte_coordinate_space!=='prot_entry'||source.byte_length!==4||source.table_source!=='primary'||source.table_kind!==id.kind||source.record_index!==id.index||source.containing_span_byte_offset!==65536||source.containing_span_byte_length!==8192||!integer(source.byte_offset,65554,73724)||source.byte_offset-id.index*4<65554)fail('Trigger catalog source provenance is invalid.');
  const payload=id.kind===0?['dest_x','dest_z']:['record_index','gate'];
  if(!exact(data.encoded,[...CELLS,...payload])||payload.some(key=>!integer(data.encoded[key],0,255)))fail('Trigger payload must remain a source-qualified read-only byte pair.');
  const imported=cells(Object.fromEntries(CELLS.map(key=>[key,data.encoded[key]]))),expectedType=id.kind===0?'intra_scene_teleport':({0:'object_bind',1:'partition_2_trigger'}[data.encoded.gate]??'unknown_gate');
  if(data.trigger_type!==expectedType)fail('Trigger type differs from its immutable payload.');
  if(id.kind===0&&Object.hasOwn(data,'destination_world')&&(!exact(data.destination_world,['x','z'])||data.destination_world.x!==data.encoded.dest_x*64+64||data.destination_world.z!==(data.encoded.dest_z+1)*64))fail('Teleport destination differs from its preserved source bytes.');
  return {id,source,imported,payload:Object.fromEntries(payload.map(key=>[key,data.encoded[key]])),trigger_type:expectedType};
}

export function decodeTriggerCellsReview(value,record,state){
  const context=recordContext(record,state);
  if(!exact(value,REPORT_KEYS)||value.schema_version!=='legaia.trigger-cells-review.v1'||value.read_only!==true||value.project_source_key!==state.project_copy_source_key||value.scene_id!==context.id.scene||value.trigger_id!==record.id||!hash(value.review_key)||value.scope!=='source-MAP-trigger-cell-only'||value.height_status!=='unknown'||value.activation!=='not_evaluated'||value.gameplay_verified!==false||typeof value.project_change!=='boolean'||value.trigger_kind!==context.id.kind)fail('Trigger cells review is invalid or stale.');
  const source=value.source;
  if(!exact(source,['map_sha256','row_sha256','table_kind','record_index','byte_offset','byte_length'])||!hash(source.map_sha256)||source.row_sha256!==context.source.sha256||source.table_kind!==context.id.kind||source.record_index!==context.source.record_index||source.byte_offset!==context.source.byte_offset||source.byte_length!==4||state.scene_selection_map_sha256!=null&&source.map_sha256!==state.scene_selection_map_sha256)fail('Trigger cells review differs from its source row or MAP identity.');
  if(!exact(value.values_layers,['imported','authored','current','proposed'])||!exact(value.tile_bounds_layers,['imported','current','proposed'])||!exact(value.world_bounds_layers,['imported','current','proposed']))fail('Trigger cells review layers are incomplete.');
  const layers=value.values_layers,imported=cells(layers.imported),current=cells(layers.current),proposed=cells(layers.proposed);
  if(!same(imported,context.imported,CELLS)||!object(layers.authored)||![0,2].includes(Object.keys(layers.authored).length))fail('Trigger imported or authored cell is invalid.');
  const authored=Object.keys(layers.authored).length?cells(layers.authored):{};
  if(!same(current,Object.keys(authored).length?authored:imported,CELLS))fail('Trigger Current cell differs from its authored layer.');
  for(const layer of ['imported','current','proposed'])validateBounds(value.tile_bounds_layers[layer],value.world_bounds_layers[layer],layers[layer]);
  if(!['set','clear'].includes(value.action)||value.requested_values!==null&&!exact(value.requested_values,CELLS)||value.action==='clear'&&value.requested_values!==null)fail('Trigger cells review has an invalid requested action.');
  const requested=value.requested_values===null?null:cells(value.requested_values),expected=value.action==='clear'?imported:requested??current;
  if(!same(proposed,expected,CELLS)||!integer(value.effective_change_count,0,2)||value.effective_change_count!==CELLS.filter(key=>current[key]!==proposed[key]).length||value.effective_change_count>0&&!value.project_change||value.action==='set'&&requested===null&&value.project_change)fail('Trigger cell proposal or change count is inconsistent.');
  const binding=value.value;
  if(!exact(binding,['source_sha256','edits'])||binding.source_sha256!==source.map_sha256||!Array.isArray(binding.edits)||binding.edits.length>2043)fail('Trigger cell proposal lacks a qualified MAP binding.');
  const seen=new Set();let selected=null,previous='';
  for(const edit of binding.edits){
    if(!exact(edit,['trigger_id',...CELLS]))fail('Trigger proposal edit fields are invalid.');
    const editId=identity(edit.trigger_id);cells(Object.fromEntries(CELLS.map(key=>[key,edit[key]])));
    if(editId.scene!==context.id.scene||seen.has(edit.trigger_id)||edit.trigger_id<previous)fail('Trigger proposal identities are duplicated, unordered or cross-scene.');
    seen.add(edit.trigger_id);previous=edit.trigger_id;if(edit.trigger_id===record.id)selected=edit;
  }
  if(selected?!same(selected,proposed,CELLS)||value.action==='clear':!same(proposed,imported,CELLS))fail('Trigger proposal binding differs from its selected reviewed cell.');
  return structuredClone(value);
}

export function triggerCellsGeometry(report,layer='proposed'){
  if(!['imported','current','proposed'].includes(layer))fail('Invalid trigger comparison layer.');
  identity(report?.trigger_id);
  if(report.height_status!=='unknown'||report.activation!=='not_evaluated'||report.gameplay_verified!==false)fail('Trigger geometry requires an unverified source reference plane.');
  const tiles=report.tile_bounds_layers?.[layer],bounds=report.world_bounds_layers?.[layer];validateBounds(tiles,bounds,report.values_layers?.[layer]);
  return {id:report.trigger_id,kind:'trigger',world_bounds:{...bounds},world_center:{x:(bounds.x_min+bounds.x_max)/2,y:0,z:(bounds.z_min+bounds.z_max)/2}};
}

export function decodeTriggerCellsAnnotations(list,sourceSpatial){
  const spatial=decodeFieldSpatial(sourceSpatial,sourceSpatial?.scene_id);
  if(!Array.isArray(list)||list.length>2043)fail('Trigger annotations exceed the supported primary tables.');
  const rows=new Map(spatial.records.filter(row=>row.kind==='trigger'&&row.table_source==='primary').map(row=>[row.id,row])),seen=new Set();
  for(const annotation of list){
    if(!exact(annotation,['trigger_id','row_sha256','values_layers','tile_bounds_layers','world_bounds_layers']))fail('Trigger annotation fields are invalid.');
    const id=identity(annotation.trigger_id),source=rows.get(annotation.trigger_id);
    if(id.scene!==spatial.scene_id||!source||seen.has(annotation.trigger_id)||annotation.row_sha256!==source.source_record.sha256)fail('Trigger annotation differs from its immutable source row.');
    seen.add(annotation.trigger_id);
    if(!exact(annotation.values_layers,['imported','authored','effective'])||!exact(annotation.tile_bounds_layers,['imported','effective'])||!exact(annotation.world_bounds_layers,['imported','effective']))fail('Trigger annotation layers are incomplete.');
    const imported=cells(annotation.values_layers.imported),effective=cells(annotation.values_layers.effective),authored=exact(annotation.values_layers.authored,[])?{}:cells(annotation.values_layers.authored);
    if(!same(Object.keys(authored).length?authored:imported,effective,CELLS)||!same(tileBounds(imported),source.source_tile_bounds,BOUNDS))fail('Trigger annotations differ from imported cells or authored coordinates.');
    for(const layer of ['imported','effective'])validateBounds(annotation.tile_bounds_layers[layer],annotation.world_bounds_layers[layer],annotation.values_layers[layer]);
  }
  return structuredClone(list);
}

function element(tag,text){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;}
function layerTable(report){
  const table=element('table'),heading=element('tr');for(const title of ['Tile coordinate','Retail','Authored','Current','Proposed'])heading.append(element('th',title));table.append(heading);
  for(const field of CELLS){const row=element('tr');row.append(element('th',field==='tile_x'?'X':'Z'));for(const layer of ['imported','authored','current','proposed'])row.append(element('td',Object.hasOwn(report.values_layers[layer],field)?String(report.values_layers[layer][field]):'None · inherit'));table.append(row);}
  return table;
}
function outlines(report){
  const section=element('section'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),layers=['imported','current','proposed'],colors=['#83aaff','#f7bf4f','#70e9af'];
  const bounds=layers.map(layer=>report.tile_bounds_layers[layer]),x=Math.min(...bounds.map(row=>row.x_min))-1,z=Math.min(...bounds.map(row=>row.z_min))-1,width=Math.max(...bounds.map(row=>row.x_max))-x+1,height=Math.max(...bounds.map(row=>row.z_max))-z+1;
  svg.setAttribute('viewBox',`${x} ${z} ${width} ${height}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Retail, Current and Proposed source trigger cells; X increases right, Z increases down');svg.style.width='100%';svg.style.height='240px';svg.style.background='#171e29';
  for(const [index,layer] of layers.entries()){const row=report.tile_bounds_layers[layer],rect=document.createElementNS(svg.namespaceURI,'rect');for(const [key,value] of Object.entries({x:row.x_min,y:row.z_min,width:1,height:1,fill:'none',stroke:colors[index],'stroke-width':2,'vector-effect':'non-scaling-stroke','stroke-dasharray':index===0?'7 4':index===1?'3 3':'none'}))rect.setAttribute(key,value);const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=`${['Retail','Current','Proposed'][index]} · half-open tile X [${row.x_min}, ${row.x_max}), Z [${row.z_min}, ${row.z_max})`;rect.append(title);svg.append(rect);}
  section.append(svg,element('p','Blue dashed: Retail · gold dotted: Current · green: Proposed. Source lookup uses tile = world >> 7. Y=0 is a reference plane; floor height, collision and activation remain unknown.'));
  const table=element('table'),heading=element('tr');for(const title of ['Layer','World X [min, max)','World Z [min, max)'])heading.append(element('th',title));table.append(heading);for(const [index,layer] of layers.entries()){const row=element('tr'),world=report.world_bounds_layers[layer];row.append(element('th',['Retail','Current','Proposed'][index]),element('td',`[${world.x_min}, ${world.x_max})`),element('td',`[${world.z_min}, ${world.z_max})`));table.append(row);}section.append(table);return section;
}

export function openTriggerCells({record,getState,busy,setBusy,api,current,onInspection=()=>{},onFrame=()=>{},onError=()=>{}}){
  let binding,context;
  try{if([getState,busy,setBusy,api,current,onInspection,onFrame,onError].some(callback=>typeof callback!=='function'))fail('Trigger editing requires current editor guards.');if(busy()!==false||current()!==true)return null;context=recordContext(record,getState());binding={key:getState().project_copy_source_key,triggerKey:getState().scene_trigger_state_key,scene:getState().scene.id};}catch(error){onError(error);return null;}
  const dialog=element('dialog');dialog.id='trigger-cells-dialog';dialog.className='project-dialog';dialog.style.width='min(850px,90vw)';dialog.style.maxHeight='90vh';dialog.style.overflowY='auto';
  const heading=element('div'),close=element('button','×');heading.className='dialog-heading';close.type='button';close.setAttribute('aria-label','Close trigger cells');heading.append(element('h2','Source trigger cells'),close);dialog.append(heading,element('p',`Primary kind-${context.id.kind} record ${context.id.index} · ${context.trigger_type.replaceAll('_',' ')}. Only the two lookup-cell coordinates change. Moving a cell may change first-match shadowing or contact behavior; gameplay activation remains unverified.`));
  const payload=element('p');payload.className='field-note';payload.textContent=context.id.kind===0?`Read-only teleport bytes: destination X ${context.payload.dest_x}, Z ${context.payload.dest_z}.`:`Read-only binding bytes: record index ${context.payload.record_index}, gate ${context.payload.gate}${context.trigger_type==='unknown_gate'?' · gate meaning unknown':''}.`;dialog.append(payload,element('p','The source dispatcher covers tiles 0..127. Encoded values 0..255 remain representable; cells outside the dispatcher range have no activation guarantee. This tool changes lookup coordinates only, without painting collision/object flags.'));
  const form=element('form'),inputs=new Map();form.style.display='grid';form.style.gridTemplateColumns='repeat(2,minmax(0,1fr))';form.style.gap='10px';
  for(const field of CELLS){const label=element('label',field==='tile_x'?'Tile X':'Tile Z'),input=element('input');input.name=field;input.type='number';input.min='0';input.max='255';input.step='1';input.required=true;input.value=String(context.imported[field]);input.setAttribute('aria-label','Trigger '+(field==='tile_x'?'tile X':'tile Z'));label.append(input);form.append(label);inputs.set(field,input);}
  const reviewButton=element('button','Review cells');reviewButton.type='submit';reviewButton.dataset.review='';form.append(reviewButton);dialog.append(form);
  const status=element('p');status.setAttribute('role','status');const output=element('div');output.dataset.triggerResult='';dialog.append(status,output);
  const actions=element('div');actions.className='dialog-actions';actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';
  const clear=element('button','Review retail reset');clear.type='button';clear.dataset.clear='';actions.append(clear);
  const inspectionButtons=[];
  for(const [layer,text] of [['imported','Inspect retail cell'],['current','Inspect current cell'],['proposed','Inspect proposed cell']]){const button=element('button',text);button.type='button';button.dataset.inspect=layer;actions.append(button);inspectionButtons.push(button);}
  const frame=element('button','Frame trigger cell'),apply=element('button','Apply trigger cells'),cancel=element('button','Close');for(const button of [frame,apply,cancel])button.type='button';frame.dataset.frame='';apply.dataset.apply='';actions.append(frame,apply,cancel);dialog.append(actions);
  const strip=element('div');strip.id='trigger-cells-preview';strip.hidden=true;strip.className='project-dialog';Object.assign(strip.style,{position:'fixed',bottom:'18px',right:'18px',zIndex:'100',maxWidth:'440px',padding:'12px'});const note=element('p'),returnButton=element('button','Return to trigger review'),restoreButton=element('button','Restore source cells');returnButton.type=restoreButton.type='button';strip.append(note,returnButton,restoreButton);
  let controller=null,generation=0,pending=false,closed=false,retainedClose=false,reviewed=null,inspectionLayer=null;
  const isCurrent=()=>!closed&&current()===true&&getState().project?.mode==='edit'&&getState().scene?.id===binding.scene&&getState().project_copy_source_key===binding.key&&getState().scene_trigger_state_key===binding.triggerKey;
  const fingerprint=()=>JSON.stringify(CELLS.map(field=>inputs.get(field).value));
  const values=()=>cells(Object.fromEntries(CELLS.map(field=>{const value=inputs.get(field).value;if(typeof value!=='string'||!value.trim())fail('Enter both trigger tile coordinates.');return [field,Number(value)];})));
  const restoreInspection=()=>{if(inspectionLayer!==null){inspectionLayer=null;onInspection(null);}strip.hidden=true;};
  function withdraw(){generation++;if(controller){controller.abort();controller=null;setBusy(false);}reviewed=null;restoreInspection();output.replaceChildren();}
  function dispose(){if(closed)return;closed=true;withdraw();if(dialog.open)dialog.close();dialog.remove();strip.remove();}
  function refresh(){
    if(!isCurrent()){status.textContent='Project, scene or trigger source changed. Reopen trigger cells.';for(const button of [reviewButton,clear,frame,apply,...inspectionButtons])button.disabled=true;for(const input of inputs.values())input.disabled=true;returnButton.disabled=true;restoreInspection();return;}
    const blocked=pending||busy()!==false;for(const input of inputs.values())input.disabled=blocked;let valid=true;try{values();}catch{valid=false;}
    reviewButton.disabled=blocked||!valid;clear.disabled=blocked;frame.disabled=blocked||!reviewed;apply.disabled=blocked||!reviewed?.project_change;for(const button of inspectionButtons)button.disabled=blocked||!reviewed;returnButton.disabled=blocked;restoreButton.disabled=pending&&controller===null;
  }
  async function load(requested=null,action='set',initial=false){
    if(pending||busy()!==false||!isCurrent())return false;
    withdraw();const token=++generation,requestedFingerprint=fingerprint(),activeController=new AbortController();controller=activeController;pending=true;setBusy(true);status.textContent='Qualifying source trigger cells…';refresh();
    try{
      const response=await fetch('/api/trigger-cells-review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trigger_id:record.id,values:requested,action}),signal:activeController.signal}),value=await response.json();
      if(activeController.signal.aborted||closed||!dialog.open||generation!==token||!isCurrent()||fingerprint()!==requestedFingerprint)return false;
      if(!response.ok||value.error)fail(typeof value.error==='string'?value.error:'Trigger cells review failed.');
      const report=decodeTriggerCellsReview(value,record,getState());
      if(report.action!==action||(requested===null?report.requested_values!==null:!same(report.requested_values,requested,CELLS)))fail('Trigger review differs from the requested cell.');
      reviewed=report;if(initial)for(const field of CELLS)inputs.get(field).value=String(report.values_layers.current[field]);
      status.textContent=`${report.effective_change_count} changed coordinate bytes · ${report.project_change?'Ready for one undoable Apply':'No project change'}. Trigger payloads, row order and other source bytes are preserved.`;output.append(layerTable(report),outlines(report));return true;
    }catch(error){if(error.name!=='AbortError'&&!closed&&generation===token){status.textContent=error.message;onError(error);}return false;}
    finally{if(controller===activeController){controller=null;pending=false;setBusy(false);}refresh();}
  }
  form.oninput=()=>{if(closed)return;withdraw();pending=false;status.textContent='Inputs changed; review cells again.';refresh();};
  form.onsubmit=async event=>{event.preventDefault();if(pending||busy()!==false||!isCurrent()||!form.reportValidity())return false;try{return await load(values(),'set');}catch(error){status.textContent=error.message;onError(error);return false;}};
  clear.onclick=()=>load(null,'clear');
  for(const button of inspectionButtons)button.onclick=()=>{
    if(pending||busy()!==false||!reviewed||!isCurrent()||!dialog.open)return false;
    inspectionLayer=button.dataset.inspect;note.textContent=`${inspectionLayer==='imported'?'Retail':inspectionLayer==='current'?'Current':'Proposed'} trigger cell · Y=0 reference plane · scene outline preview only`;strip.hidden=false;retainedClose=true;dialog.close();onInspection(reviewed,inspectionLayer);onFrame(reviewed,inspectionLayer);refresh();return true;
  };
  frame.onclick=()=>{if(pending||busy()!==false||!reviewed||!isCurrent())return false;onFrame(reviewed,inspectionLayer??'proposed');return true;};
  apply.onclick=async()=>{
    if(pending||busy()!==false||!reviewed?.project_change||!isCurrent()||!dialog.open)return false;
    const report=reviewed,token=++generation;pending=true;refresh();
    try{const result=await api('/api/trigger-cells-apply',{type:'apply_trigger_cells',trigger_id:report.trigger_id,values:report.requested_values,action:report.action,review_key:report.review_key});if(result===true){dispose();return true;}if(closed||generation!==token)return false;withdraw();status.textContent='Trigger cells were rejected. Review current source cells again.';return false;}
    catch(error){if(!closed&&generation===token){withdraw();status.textContent=error.message;onError(error);}return false;}
    finally{if(!closed){pending=false;refresh();}}
  };
  returnButton.onclick=()=>{if(pending||busy()!==false||!reviewed||!isCurrent())return false;restoreInspection();dialog.showModal();refresh();return true;};restoreButton.onclick=dispose;close.onclick=cancel.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{if(retainedClose){retainedClose=false;return;}dispose();});dialog.dispose=dispose;dialog.restore=dispose;dialog.refresh=refresh;
  document.body.append(dialog,strip);dialog.showModal();refresh();void load(null,'set',true);return dialog;
}

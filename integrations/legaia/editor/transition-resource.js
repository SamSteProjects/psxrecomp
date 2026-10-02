// These coordinates describe a destination arrival, never a source trigger.
const ENTRY_FIELDS=['entry_x_encoded','entry_z_encoded','direction_encoded'];
const REQUIRED=['id','source','target','script_id','script_name','owner_id','partition','script_status','script_stop_count','source_record','reference','reachability','entry_layers','semantic_id','asset_kind','read_only','name','coverage','limitations','arrival_layers','trigger_position','runtime_verified'];
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const text=(value,max=8192)=>typeof value==='string'&&value.length>0&&value.length<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const fail=message=>{throw new Error(message);};
function detached(value,depth=0,budget={nodes:0,characters:0}){
  if(depth>12||++budget.nodes>20000)fail('Transition metadata exceeds the inspector bound.');
  if(value===null||typeof value==='boolean')return value;
  if(typeof value==='number'){if(!Number.isFinite(value))fail('Invalid transition metadata number.');return value;}
  if(typeof value==='string'){budget.characters+=value.length;if(value.length>8192||budget.characters>1024*1024)fail('Transition metadata text exceeds the inspector bound.');return value;}
  if(Array.isArray(value)){if(value.length>1024)fail('Transition metadata list exceeds the inspector bound.');return value.map(row=>detached(row,depth+1,budget));}
  if(!object(value)||Object.keys(value).length>128)fail('Invalid transition metadata object.');
  return Object.fromEntries(Object.entries(value).map(([key,child])=>{if(!text(key,256)||['raw_hex','encoded_hex','raw_bytes','payload','tokens','rgba'].includes(key))fail('Transition resources require bounded metadata only.');budget.characters+=key.length;return [key,detached(child,depth+1,budget)];}));
}
function arrival(values){
  const coordinate=value=>(value&127)*128+(value&128?128:64);
  return {x:coordinate(values.entry_x_encoded),z:coordinate(values.entry_z_encoded),facing_angle_12bit:(values.direction_encoded&7)*512,evidence:'retail_static_handler_and_table',runtime_verified:false,retail_source:'SCUS-94254 PROT[897] offset66312; SCUS_942.54 table80073F04',source:'crates/engine-core/src/world/field_loop.rs:275-308'};
}
function sameArrival(value,expected){return exact(value,Object.keys(expected))&&Object.entries(expected).every(([key,item])=>value[key]===item);}
export function decodeTransitionResource(data){
  const value=detached(data),allowed=new Set([...REQUIRED,'kind','layer','scene_id','catalog_limitations']);
  if(!object(value)||REQUIRED.some(key=>!Object.hasOwn(value,key))||Object.keys(value).some(key=>!allowed.has(key))||value.asset_kind!=='transition'||value.read_only!==true||value.trigger_position!==null||value.runtime_verified!==false||value.id!==value.semantic_id||!text(value.name,512)||!text(value.script_name,512)||value.reachability!=='not_evaluated'||!['decoded_supported_paths','partial'].includes(value.script_status)||!integer(value.script_stop_count,0,65536))fail('Invalid read-only transition resource.');
  const match=text(value.script_id,512)&&/^script:\/\/([A-Za-z0-9_-]+)\/(actors\/man-p1|scripts\/man-p2)\/([0-9]{4})$/.exec(value.script_id);
  if(!match)fail('Transition requires a source-qualified script identity.');
  const partition=match[2]==='actors/man-p1'?1:2,sourceId='scene://'+match[1],reference=value.reference,record=value.source_record;
  if(value.source!==sourceId||value.partition!==partition||value.owner_id!=='scene://'+value.script_id.slice(9)||Object.hasOwn(value,'kind')&&value.kind!=='transition'||Object.hasOwn(value,'layer')&&value.layer!=='derived'||Object.hasOwn(value,'scene_id')&&value.scene_id!==sourceId)fail('Transition owner differs from its source scene or script.');
  if(!exact(reference,['pc','byte_offset','mnemonic','extended_target','target_scene_name','target_in_scene_index','status','name_byte_length','name_sha256','entry_x_encoded','entry_z_encoded','direction_encoded','reachability'])||!integer(reference.pc,0,65535)||!integer(reference.byte_offset,0,0xffffffff)||reference.mnemonic!=='SCENE_CHANGE'||reference.extended_target!==null&&!integer(reference.extended_target,0,255)||!integer(reference.name_byte_length,0,255)||!hash(reference.name_sha256)||reference.reachability!=='not_evaluated'||ENTRY_FIELDS.some(key=>!integer(reference[key],0,255)))fail('Invalid encoded transition instruction.');
  const pc=reference.pc.toString(16).padStart(4,'0'),identity=value.script_id.replace('script://','transition://')+'/'+pc;
  if(value.id!==identity)fail('Transition identity differs from its exact source instruction.');
  const named=reference.target_scene_name!==null;
  if(named?(typeof reference.target_scene_name!=='string'||!/^[a-z0-9]{1,12}$/.test(reference.target_scene_name)||reference.target_scene_name.length!==reference.name_byte_length||typeof reference.target_in_scene_index!=='boolean'||reference.status!=='encoded_named_reference'||value.target!=='scene://'+reference.target_scene_name):(reference.target_in_scene_index!==null||reference.status!=='unsupported_name_encoding'||value.target!==identity+'/unresolved-target'))fail('Transition destination differs from its encoded source label.');
  if(!object(record)||['byte_offset','byte_length','record_index','partition','byte_coordinate_space','sha256'].some(key=>!Object.hasOwn(record,key))||!text(record.byte_coordinate_space,256)||!hash(record.sha256))fail('Transition source provenance is unavailable.');
  for(const [key,min,max] of [['byte_offset',0,0xffffffff],['byte_length',1,65536],['record_index',0,9999],['partition',1,2],['prot_entry_index',0,0xffffffff],['compressed_stream_offset',0,0xffffffff],['compressed_bytes_consumed',1,0xffffffff]])if(Object.hasOwn(record,key)&&!integer(record[key],min,max))fail('Invalid transition source record bounds.');
  if(Object.hasOwn(record,'partition')&&record.partition!==partition||Object.hasOwn(record,'record_index')&&record.record_index!==Number(match[3])||Object.hasOwn(record,'sha256')&&!hash(record.sha256)||Object.hasOwn(record,'prot_entry_name')&&record.prot_entry_name!==match[1]||Object.hasOwn(record,'iso_file')&&record.iso_file!=='PROT.DAT'||Object.hasOwn(record,'disc')&&(!exact(record.disc,['sha256','serial'])||!hash(record.disc.sha256)||record.disc.serial!=='SCUS-94254'))fail('Transition provenance differs from its source identity.');
  if(Object.hasOwn(record,'byte_offset')&&reference.byte_offset!==record.byte_offset+reference.pc||Object.hasOwn(record,'byte_length')&&reference.pc+7+Number(reference.extended_target!==null)+reference.name_byte_length>record.byte_length||Object.hasOwn(record,'compressed_stream_offset')&&Object.hasOwn(record,'compressed_bytes_consumed')&&record.compressed_bytes_consumed>0xffffffff-record.compressed_stream_offset)fail('Transition instruction is outside its source record.');
  const entries=value.entry_layers;
  if(!exact(entries,['imported','authored','effective','validation','transition_id'])||!exact(entries.imported,ENTRY_FIELDS)||!exact(entries.effective,ENTRY_FIELDS)||!object(entries.authored)||Object.keys(entries.authored).some(key=>!ENTRY_FIELDS.includes(key))||ENTRY_FIELDS.some(key=>entries.imported[key]!==reference[key]||!integer(entries.effective[key],0,255)||Object.hasOwn(entries.authored,key)&&!integer(entries.authored[key],0,255)||entries.effective[key]!==((Object.hasOwn(entries.authored,key)?entries.authored:entries.imported)[key]))||entries.transition_id!==value.script_id+'/transition/'+pc||entries.validation!==(Object.keys(entries.authored).length?'reverified_on_build':'imported_reference'))fail('Transition entry layers differ from the source bytes or authored annotations.');
  if(Object.keys(entries.authored).length&&(value.script_stop_count!==0||!named))fail('Authored arrival annotations require a named source instruction without decoder stops.');
  if(!exact(value.arrival_layers,['imported','effective'])||!sameArrival(value.arrival_layers.imported,arrival(entries.imported))||!sameArrival(value.arrival_layers.effective,arrival(entries.effective)))fail('Transition arrival interpretation differs from its encoded destination bytes.');
  const coverage=value.coverage;
  const validLimits=notes=>Array.isArray(notes)&&notes.length<=64&&notes.every(note=>text(note));
  if(!object(coverage)||!integer(coverage.script_count,1,1024)||!integer(coverage.partial_script_count,0,coverage.script_count)||!integer(coverage.unavailable_script_count,0,coverage.script_count)||coverage.partial_script_count+coverage.unavailable_script_count>coverage.script_count||value.script_status==='partial'&&coverage.partial_script_count===0||!validLimits(value.limitations)||Object.hasOwn(value,'catalog_limitations')&&!validLimits(value.catalog_limitations))fail('Invalid transition source coverage or limitations.');
  return value;
}
export function transitionResourceNavigationAllowed(data,action,{current,busy,canInspect,canNavigate,open=true,pending=false}={}){
  if(open!==true||pending!==false||current!==true||busy!==false||data?.read_only!==true||data.asset_kind!=='transition'||data.runtime_verified!==false||data.trigger_position!==null)return false;
  if(action==='parent'||action==='instruction')return canInspect===true&&integer(data.reference?.pc,0,65535);
  return action==='destination'&&canNavigate===true&&typeof data.reference?.target_scene_name==='string'&&/^[a-z0-9]{1,12}$/.test(data.reference.target_scene_name)&&data.target==='scene://'+data.reference.target_scene_name;
}
const pcLabel=value=>'0x'+value.toString(16).padStart(4,'0').toUpperCase();
const byteLabel=value=>`${value} (0x${value.toString(16).padStart(2,'0').toUpperCase()})`;
function element(tag,value,className){const node=document.createElement(tag);if(value!==undefined)node.textContent=value;if(className)node.className=className;return node;}
function property(host,label,value){const row=element('dl',undefined,'property');row.style.gridTemplateColumns='160px 1fr';row.append(element('dt',label),element('dd',value));host.append(row);}
function table(host,headings,rows){const wrap=element('div',undefined,'script-table-wrap'),table=element('table'),head=element('tr');for(const heading of headings)head.append(element('th',heading));table.append(head);for(const values of rows){const row=element('tr');for(const value of values)row.append(element('td',value));table.append(row);}wrap.append(table);host.append(wrap);}
export function openTransitionResource({record,current,busy,canInspect,canNavigate,onInspect,onNavigate,onError=()=>{}}){
  let data;
  try{
    if([current,busy,canInspect,canNavigate,onInspect,onNavigate].some(callback=>typeof callback!=='function'))fail('Transition navigation requires editor context guards.');
    if(busy()||!current())return null;
    data=decodeTransitionResource(record?.data);
    if(record.type!=='transition'||record.id!==data.semantic_id||record.sceneId!==data.source||!text(record.label,512)||!text(record.source,512))fail('Transition resource differs from its catalog selection.');
  }catch(error){onError(error);return null;}
  const dialog=element('dialog');dialog.id='transition-resource-dialog';dialog.className='project-dialog';dialog.style.width='min(1040px,calc(100vw - 35px))';dialog.style.maxHeight='90vh';dialog.style.overflow='auto';
  const heading=element('div',undefined,'dialog-heading'),close=element('button','×');close.type='button';close.setAttribute('aria-label','Close transition resource');heading.append(element('h2',record.label),close);dialog.append(heading);
  dialog.append(element('p','Destination arrival coordinates describe where a scene-change instruction enters its target scene. They do not identify a source trigger location. Reachability and runtime behavior remain unknown.'));
  property(dialog,'Stable source ID',data.semantic_id);property(dialog,'Source scene',record.source);property(dialog,'Source script',data.script_name);property(dialog,'Source owner',data.owner_id);property(dialog,'Exact source PC',pcLabel(data.reference.pc));property(dialog,'Script inspection',data.script_status==='partial'?'Partial inspection · unknown or unvisited paths remain outside coverage':'Decoded supported paths · execution is not established');property(dialog,'Decoder stops',`${data.script_stop_count} · source tools independently verify the entry`);
  property(dialog,'Dispatch context',data.reference.extended_target===null?'Current script context':`Extended target ${data.reference.extended_target} · unresolved`);
  property(dialog,'Destination label',data.reference.target_scene_name??'Unsupported name encoding · destination unresolved');property(dialog,'Scene index',data.reference.target_in_scene_index===null?'Unknown':data.reference.target_in_scene_index?'Encoded label identified in source scene index':'Encoded label absent from source scene index');
  property(dialog,'Source trigger','Unknown · no source marker');property(dialog,'Runtime verification','Not observed');property(dialog,'Reachability','Not evaluated');property(dialog,'Scene coverage',`${data.coverage.script_count} scripts · ${data.coverage.partial_script_count} partial · ${data.coverage.unavailable_script_count} unavailable`);
  dialog.append(element('h3','Imported, authored and effective destination bytes'));table(dialog,['Entry byte','Imported','Authored','Effective'],ENTRY_FIELDS.map((key,index)=>[['Entry X','Entry Z','Direction'][index],byteLabel(data.entry_layers.imported[key]),Object.hasOwn(data.entry_layers.authored,key)?byteLabel(data.entry_layers.authored[key]):'None · inherit',byteLabel(data.entry_layers.effective[key])]));
  dialog.append(element('h3','Static destination arrival interpretation'));table(dialog,['Arrival property','Imported','Effective'],[['X',data.arrival_layers.imported.x,data.arrival_layers.effective.x],['Z',data.arrival_layers.imported.z,data.arrival_layers.effective.z],['Facing angle / 4096',data.arrival_layers.imported.facing_angle_12bit,data.arrival_layers.effective.facing_angle_12bit]]);
  dialog.append(element('p','The target source label is identified when present. Destination map geometry is unknown until that scene is loaded. Static arrival interpretation is not a live player position.','field-note'));
  const actions=element('div',undefined,'dialog-actions');actions.style.flexWrap='wrap';actions.style.justifyContent='flex-start';const parent=element('button','Inspect parent script'),instruction=element('button',`Inspect transition ${pcLabel(data.reference.pc)}`),destination=element('button','Open imported destination');for(const button of [parent,instruction,destination])button.type='button';actions.append(parent,instruction,destination);dialog.append(actions);
  const status=element('p');status.setAttribute('role','status');dialog.append(status);
  const limits=element('ul');for(const note of new Set(data.limitations))limits.append(element('li',note));dialog.append(element('h3','Source limits'),limits);
  const provenance=element('details'),summary=element('summary','Source provenance and static interpretation'),pre=element('pre',JSON.stringify({source_record:data.source_record,reference:data.reference,entry_layers:data.entry_layers,arrival_layers:data.arrival_layers,coverage:data.coverage},null,2),'diagnostic-detail');provenance.append(summary,pre);dialog.append(provenance);
  const error=element('p',undefined,'dialog-error');error.setAttribute('role','alert');dialog.append(error);let generation=0,pending=false;
  function gates(){return {current:current()===true,busy:busy()!==false,canInspect:canInspect()===true,canNavigate:data.reference.target_scene_name!==null&&canNavigate(data.target)===true,open:dialog.open,pending};}
  function update(){const context=gates();parent.disabled=!transitionResourceNavigationAllowed(data,'parent',context);instruction.disabled=!transitionResourceNavigationAllowed(data,'instruction',context);destination.disabled=!transitionResourceNavigationAllowed(data,'destination',context);status.textContent=!context.current?'Catalog context changed. Reopen this transition to navigate.':context.busy?'Another editor operation is in progress.':pending?'Opening the verified source selection…':!context.canNavigate?'Inspect the exact source instruction. The destination is unresolved or has not been imported.':'Inspect the exact source instruction or open its imported destination.';}
  async function navigate(action){
    if(!transitionResourceNavigationAllowed(data,action,gates())){update();return false;}
    const token=++generation;pending=true;error.textContent='';update();
    try{const result=await (action==='destination'?onNavigate(data.target):onInspect(action==='parent'?null:data.reference.pc));if(token!==generation||!dialog.open)return false;if(result===false){error.textContent='The verified transition selection could not be opened.';return false;}dialog.close();return true;}
    catch(cause){if(token===generation&&dialog.open){error.textContent=cause.message??String(cause);onError(cause);}return false;}
    finally{if(token===generation&&dialog.open){pending=false;update();}}
  }
  parent.onclick=()=>navigate('parent');instruction.onclick=()=>navigate('instruction');destination.onclick=()=>navigate('destination');close.onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{generation++;pending=false;for(const button of [parent,instruction,destination,close])button.onclick=null;dialog.remove();},{once:true});
  document.body.append(dialog);dialog.showModal();update();return dialog;
}

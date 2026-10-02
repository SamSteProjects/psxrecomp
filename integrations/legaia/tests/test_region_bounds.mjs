import assert from 'node:assert/strict';
import {decodeRegionBoundsReview,regionBoundsGeometry,decodeRegionBoundsAnnotations,openRegionBounds} from '../editor/region-bounds.js';

const FIELDS=['x0','z0','x1','z1'],BOUNDS=['x_min','x_max','z_min','z_max'],scene='scene://fixture',id='region://fixture/field-map/primary/0000';
const key='a'.repeat(64),mapHash='b'.repeat(64),rowHash='c'.repeat(64),blockHash='d'.repeat(64),imported={x0:14,z0:19,x1:8,z1:3};
const clone=value=>structuredClone(value),equal=(a,b)=>FIELDS.every(field=>a[field]===b[field]);
function tiles(values){let x_min=Math.min(values.x0,values.x1),x_max=Math.max(values.x0,values.x1),z_min=Math.min(values.z0,values.z1),z_max=Math.max(values.z0,values.z1);if(x_min===x_max)x_max+=2;if(z_min===z_max)z_min-=2;return {x_min,x_max,z_min,z_max};}
const world=values=>Object.fromEntries(BOUNDS.map(field=>[field,values[field]*128+64]));
const source={disc:{sha256:'e'.repeat(64),serial:'SCUS-94254'},iso_file:'PROT.DAT',prot_entry_index:1,prot_entry_name:'fixture',prot_start_lba:203,byte_offset:66692,byte_length:8,byte_coordinate_space:'prot_entry',sha256:rowHash,containing_span_sha256:blockHash,table_source:'primary',table_kind:3,record_index:0,containing_span_byte_offset:65536,containing_span_byte_length:8192};
const record={id,type:'region',sceneId:scene,label:'<literal region>',source:'fixture',data:{semantic_id:id,asset_kind:'region',table_source:'primary',table_kind:3,record_index:0,encoded:{...imported,type:7},tile_bounds:tiles(imported),source_record:source}};
const state={project:{mode:'edit'},scene:{id:scene},project_copy_source_key:key,scene_selection_map_sha256:mapHash};
function review(requested={x0:255,z0:0,x1:255,z1:0},action='set',authored={}){
  const current=Object.keys(authored).length?authored:imported,proposed=action==='clear'?imported:requested??current;
  const tileLayers=Object.fromEntries([['imported',imported],['current',current],['proposed',proposed]].map(([layer,values])=>[layer,tiles(values)]));
  return {schema_version:'legaia.region-bounds-review.v1',read_only:true,project_source_key:key,scene_id:scene,region_id:id,review_key:'f'.repeat(64),source:{map_sha256:mapHash,row_sha256:rowHash,record_index:0,byte_offset:source.byte_offset,byte_length:8},region_type:7,values_layers:{imported:{...imported},authored:{...authored},current:{...current},proposed:{...proposed}},tile_bounds_layers:tileLayers,world_bounds_layers:Object.fromEntries(Object.entries(tileLayers).map(([layer,values])=>[layer,world(values)])),requested_values:requested===null?null:{...requested},action,effective_change_count:FIELDS.filter(field=>current[field]!==proposed[field]).length,project_change:requested===null&&action==='set'?false:!equal(current,proposed)||action==='clear'&&Object.keys(authored).length>0,value:{source_sha256:mapHash,edits:equal(imported,proposed)?[]:[{region_id:id,...proposed}]},scope:'source-MAP-region-bounds-only',height_status:'unknown',activation:'not_evaluated',gameplay_verified:false};
}
const sourceReview=review(),snapshot=clone(sourceReview),decoded=decodeRegionBoundsReview(sourceReview,record,state);
assert.deepEqual(decoded,sourceReview);decoded.values_layers.proposed.x0=0;decoded.value.edits[0].x0=0;assert.deepEqual(sourceReview,snapshot);
assert.deepEqual(regionBoundsGeometry(sourceReview,'proposed'),{id,kind:'region',world_bounds:{x_min:32704,x_max:32960,z_min:-192,z_max:64},world_center:{x:32832,y:0,z:-64}});
assert.deepEqual(regionBoundsGeometry(sourceReview,'imported').world_bounds,{x_min:1088,x_max:1856,z_min:448,z_max:2496});
assert.throws(()=>regionBoundsGeometry(sourceReview,'live'));
const noMapState=clone(state);delete noMapState.scene_selection_map_sha256;assert.deepEqual(decodeRegionBoundsReview(sourceReview,record,noMapState),sourceReview);
assert.deepEqual(decodeRegionBoundsReview(review(null),record,state).values_layers.current,imported);
assert.deepEqual(decodeRegionBoundsReview(review(null,'clear',{x0:1,z0:2,x1:3,z1:4}),record,state).values_layers.proposed,imported);
function invalid(edit){const report=review();edit(report);assert.throws(()=>decodeRegionBoundsReview(report,record,state));}
for(const edit of [
  report=>report.schema_version='legaia.region-bounds-review.v2',report=>report.extra='unbounded',report=>report.read_only=false,
  report=>report.project_source_key='0'.repeat(64),report=>report.scene_id='scene://other',report=>report.region_id=id.replace('primary','fallback'),report=>report.review_key='invalid',
  report=>report.source.map_sha256=blockHash,report=>report.source.row_sha256=mapHash,report=>report.source.record_index=1,report=>report.source.byte_offset++,report=>report.source.byte_length=4,report=>report.source.extra=true,
  report=>report.region_type=8,report=>report.height_status='known',report=>report.activation='active',report=>report.gameplay_verified=true,report=>report.scope='all-MAP-bytes',
  report=>report.effective_change_count=0,report=>report.project_change=false,report=>report.project_change=1,
  report=>report.values_layers.imported.x0++,report=>report.values_layers.authored={x0:1},report=>report.values_layers.current.x0=1,
  report=>report.values_layers.proposed.x0=true,report=>report.values_layers.proposed.z0=-1,report=>report.values_layers.proposed.x1=256,report=>report.values_layers.proposed.z1=1.5,
  report=>report.tile_bounds_layers.proposed.x_max=255,report=>report.tile_bounds_layers.proposed.z_min=0,report=>report.world_bounds_layers.proposed.x_min-=64,report=>report.world_bounds_layers.proposed.y=0,
  report=>report.action='translate',report=>report.action='clear',report=>report.requested_values={x0:1},report=>report.requested_values.x0=1,
  report=>report.value.source_sha256=rowHash,report=>report.value.edits=[],report=>report.value.edits[0].x0=1,report=>report.value.edits.push(clone(report.value.edits[0])),report=>report.value.edits[0].region_id=id.replace('fixture','other'),report=>report.value.edits[0].region_id=id.replace('0000','1021'),report=>report.value.edits[0].type=2,
])invalid(edit);
for(const changes of [{type:'trigger'},{sceneId:'scene://other'},{id:id.replace('0000','0001')}])assert.throws(()=>decodeRegionBoundsReview(sourceReview,{...record,...changes},state));
for(const changes of [{project:{mode:'live'}},{scene:{id:'scene://other'}},{scene_selection_map_sha256:blockHash}])assert.throws(()=>decodeRegionBoundsReview(sourceReview,record,{...state,...changes}));
for(const modify of [source=>source.sha256=mapHash,source=>source.table_source='fallback',source=>source.byte_offset=65553,source=>source.byte_coordinate_space='ram',source=>source.containing_span_byte_length=73728]){const changed=clone(record);modify(changed.data.source_record);assert.throws(()=>decodeRegionBoundsReview(sourceReview,changed,state));}
const geometryBad=clone(sourceReview);geometryBad.world_bounds_layers.current.z_min++;assert.throws(()=>regionBoundsGeometry(geometryBad,'current'));

function spatial(){const bounds=world(tiles(imported));return {schema_version:'legaia.field-spatial.v1',scene_id:scene,coordinate_system:'psx_guest_xz',units:'guest_integer_world_units',display_y:0,height_status:'unknown',quantization:{trigger:{tile_size:128,world_bias:0,rule:'tile = world >> 7'},region:{tile_size:128,world_bias:64,rule:'tile = (world - 64) >> 7'}},records:[{id,kind:'region',label:'Source region',table_source:'primary',table_kind:3,record_index:0,trigger_type:null,world_bounds:bounds,world_center:{x:(bounds.x_min+bounds.x_max)/2,y:0,z:(bounds.z_min+bounds.z_max)/2},source_tile_bounds:tiles(imported),source_record:clone(source),activation:'not_evaluated',height_status:'unknown'}]};}
function annotation(){return {region_id:id,row_sha256:rowHash,values_layers:{imported:{...imported},authored:{...sourceReview.values_layers.proposed},effective:{...sourceReview.values_layers.proposed}},tile_bounds_layers:{imported:tiles(imported),effective:clone(sourceReview.tile_bounds_layers.proposed)},world_bounds_layers:{imported:world(tiles(imported)),effective:clone(sourceReview.world_bounds_layers.proposed)}};}
const annotations=[annotation()],immutableSpatial=spatial(),spatialSnapshot=clone(immutableSpatial),detached=decodeRegionBoundsAnnotations(annotations,immutableSpatial);detached[0].values_layers.effective.x0=0;assert.deepEqual(immutableSpatial,spatialSnapshot);assert.equal(annotations[0].values_layers.effective.x0,255);assert.deepEqual(decodeRegionBoundsAnnotations([],immutableSpatial),[]);
for(const mutate of [row=>row.row_sha256=mapHash,row=>row.region_id=id.replace('primary','fallback'),row=>row.values_layers.imported.x0++,row=>row.values_layers.authored.x0=0,row=>row.values_layers.effective.x1=255.5,row=>row.tile_bounds_layers.effective.x_max=255,row=>row.tile_bounds_layers.effective.z_min=0,row=>row.world_bounds_layers.effective.x_min-=64,row=>row.extra=true]){const bad=annotation();mutate(bad);assert.throws(()=>decodeRegionBoundsAnnotations([bad],immutableSpatial));}
assert.throws(()=>decodeRegionBoundsAnnotations([annotation(),annotation()],immutableSpatial));assert.throws(()=>decodeRegionBoundsAnnotations(Array(1022).fill(annotation()),immutableSpatial));assert.throws(()=>decodeRegionBoundsAnnotations([annotation()],{...immutableSpatial,height_status:'known'}));

// A small DOM double proves atomic command routing and stale/close/pending guards.
class Node{
  constructor(tag,namespace=null){this.tagName=tag;this.namespaceURI=namespace;this.children=[];this.style={};this.dataset={};this.attributes={};this.listeners=new Map();this.open=false;this.hidden=false;this.textContent='';this.value='';this.disabled=false;this.removed=false;}
  append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[...nodes];}setAttribute(key,value){this.attributes[key]=String(value);}addEventListener(type,callback){const rows=this.listeners.get(type)??[];rows.push(callback);this.listeners.set(type,rows);}showModal(){this.open=true;}close(){this.open=false;for(const callback of this.listeners.get('close')??[])callback();}remove(){this.removed=true;}reportValidity(){return true;}
}
const savedDocument=globalThis.document,savedFetch=globalThis.fetch;
globalThis.document={createElement:tag=>new Node(tag),createElementNS:(namespace,tag)=>new Node(tag,namespace),body:new Node('body')};
const descendants=node=>node.removed?[]:[node,...node.children.flatMap(descendants)],button=(dialog,text)=>descendants(dialog).find(node=>node.tagName==='button'&&node.textContent===text),input=(dialog,name)=>descendants(dialog).find(node=>node.tagName==='input'&&node.name===name),form=dialog=>descendants(dialog).find(node=>node.tagName==='form'),tick=()=>new Promise(resolve=>setImmediate(resolve));
let mutableState=clone(state),current=true,busy=false,requests=[],commands=[],inspections=[],frames=[],errors=[];
const settings={record,getState:()=>mutableState,busy:()=>busy,setBusy:value=>{busy=value;},current:()=>current,onInspection:(report,layer)=>inspections.push([report,layer]),onFrame:(report,layer)=>frames.push([report,layer]),onError:error=>errors.push(error),api:async(path,body)=>{commands.push([path,body]);return true;}};
function defaultFetch(path,options){requests.push([path,clone(JSON.parse(options.body)),options.signal]);return Promise.resolve({ok:true,json:async()=>review(JSON.parse(options.body).values,JSON.parse(options.body).action)});}
globalThis.fetch=defaultFetch;
try{
  let dialog=openRegionBounds(settings);await tick();assert.equal(dialog.open,true);assert.equal(busy,false);assert.deepEqual(requests[0].slice(0,2),['/api/region-bounds-review',{region_id:id,values:null,action:'set'}]);assert.equal(input(dialog,'x0').value,'14');assert.equal(button(dialog,'Apply region bounds').disabled,true);
  input(dialog,'x0').value='20';form(dialog).oninput();assert.equal(button(dialog,'Inspect proposed bounds').disabled,true);assert.equal(await form(dialog).onsubmit({preventDefault(){}}),true);assert.deepEqual(requests.at(-1)[1],{region_id:id,values:{x0:20,z0:19,x1:8,z1:3},action:'set'});assert.equal(button(dialog,'Apply region bounds').disabled,false);
  assert.equal(button(dialog,'Inspect proposed bounds').onclick(),true);assert.equal(dialog.open,false);assert.equal(inspections.at(-1)[1],'proposed');assert.equal(frames.at(-1)[1],'proposed');const strip=descendants(document.body).find(node=>node.id==='region-bounds-preview');assert.equal(strip.hidden,false);assert.equal(button(strip,'Return to region review').onclick(),true);assert.equal(dialog.open,true);assert.equal(inspections.at(-1)[0],null);assert.equal(strip.hidden,true);
  busy=true;assert.equal(button(dialog,'Inspect current bounds').onclick(),false);assert.equal(await button(dialog,'Apply region bounds').onclick(),false);busy=false;
  assert.equal(await button(dialog,'Apply region bounds').onclick(),true);assert.deepEqual(commands.at(-1),['/api/region-bounds-apply',{type:'apply_region_bounds',region_id:id,values:{x0:20,z0:19,x1:8,z1:3},action:'set',review_key:'f'.repeat(64)}]);assert.equal(dialog.removed,true);assert.equal(strip.removed,true);dialog.dispose();

  dialog=openRegionBounds(settings);await tick();await button(dialog,'Review retail reset').onclick();assert.equal(requests.at(-1)[1].action,'clear');assert.equal(requests.at(-1)[1].values,null);assert.equal(button(dialog,'Apply region bounds').disabled,true);dialog.dispose();

  dialog=openRegionBounds(settings);await tick();button(dialog,'Inspect current bounds').onclick();mutableState.project_copy_source_key='0'.repeat(64);dialog.refresh();assert.equal(inspections.at(-1)[0],null);assert.equal(button(dialog,'Review bounds').disabled,true);assert.equal(button(dialog,'Apply region bounds').disabled,true);assert.equal(await form(dialog).onsubmit({preventDefault(){}}),false);dialog.dispose();mutableState=clone(state);

  let finish,signal;globalThis.fetch=(path,options)=>{signal=options.signal;return new Promise(resolve=>{finish=resolve;});};dialog=openRegionBounds(settings);assert.equal(busy,true);dialog.dispose();assert.equal(signal.aborted,true);assert.equal(busy,false);finish({ok:true,json:async()=>review(null)});await tick();assert.equal(dialog.removed,true);assert.equal(descendants(dialog).length,0);

  globalThis.fetch=defaultFetch;dialog=openRegionBounds({...settings,api:async()=>{dialog.dispose();mutableState.project_copy_source_key='0'.repeat(64);return true;}});await tick();input(dialog,'x0').value='20';form(dialog).oninput();await form(dialog).onsubmit({preventDefault(){}});assert.equal(await button(dialog,'Apply region bounds').onclick(),true);assert.equal(dialog.removed,true);mutableState=clone(state);

  let finishApply,calls=0;dialog=openRegionBounds({...settings,api:()=>{calls++;return new Promise(resolve=>{finishApply=resolve;});}});await tick();input(dialog,'x0').value='20';form(dialog).oninput();await form(dialog).onsubmit({preventDefault(){}});const applying=button(dialog,'Apply region bounds').onclick();assert.equal(await button(dialog,'Apply region bounds').onclick(),false);assert.equal(calls,1);dialog.dispose();finishApply(true);assert.equal(await applying,true);

  dialog=openRegionBounds({...settings,api:async()=>false});await tick();input(dialog,'x0').value='20';form(dialog).oninput();await form(dialog).onsubmit({preventDefault(){}});assert.equal(await button(dialog,'Apply region bounds').onclick(),false);assert.equal(dialog.open,true);assert.equal(button(dialog,'Apply region bounds').disabled,true);dialog.dispose();

  globalThis.fetch=async()=>({ok:true,json:async()=>({...review(null),source:{...review(null).source,row_sha256:mapHash}})});dialog=openRegionBounds(settings);await tick();assert.equal(button(dialog,'Apply region bounds').disabled,true);assert.equal(errors.length,1);dialog.dispose();
  current=false;assert.equal(openRegionBounds(settings),null);current=true;busy=true;assert.equal(openRegionBounds(settings),null);busy=false;assert.deepEqual(record.data.encoded,{...imported,type:7});assert.deepEqual(immutableSpatial,spatialSnapshot);
}finally{if(savedDocument===undefined)delete globalThis.document;else globalThis.document=savedDocument;if(savedFetch===undefined)delete globalThis.fetch;else globalThis.fetch=savedFetch;}
console.log('Region bounds: source/row/key guards, separated layers, rectangle normalization, biased world plane, detached annotations, Review/Clear/Apply, viewport Return and stale/pending/dispose guards passed.');

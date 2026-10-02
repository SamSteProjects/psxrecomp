import assert from 'node:assert/strict';
import {decodeFieldSpatial,drawFieldSpatial,hitFieldSpatial,fieldSpatialFrame} from '../editor/field-spatial.js';

const scene='scene://town01',hash='a'.repeat(64);
function record({kind='trigger',tableKind=0,index=0,source='primary',tiles={x_min:2,x_max:3,z_min:4,z_max:5}}={}){
  const region=kind==='region',bias=region?64:0,stride=region?8:4,base=source==='primary'?65536:0,tableOffset=({0:64,1:1024,3:2048})[tableKind];
  const bounds=Object.fromEntries(Object.entries(tiles).map(([key,value])=>[key,value*128+bias]));
  return {id:region?`region://town01/field-map/${source}/${String(index).padStart(4,'0')}`:`trigger://town01/field-map/${source}/kind-${tableKind}/${String(index).padStart(4,'0')}`,kind,label:`Source ${kind} ${index}`,table_source:source,table_kind:tableKind,record_index:index,trigger_type:region?null:tableKind===0?'intra_scene_teleport':'partition_2_trigger',world_bounds:bounds,world_center:{x:(bounds.x_min+bounds.x_max)/2,y:0,z:(bounds.z_min+bounds.z_max)/2},source_tile_bounds:{...tiles},source_record:{disc:{sha256:hash,serial:'SCUS-94254'},iso_file:'PROT.DAT',prot_entry_index:10,prot_entry_name:'town01',prot_start_lba:100,byte_offset:base+tableOffset+index*stride,byte_length:stride,byte_coordinate_space:'prot_entry',sha256:'b'.repeat(64),containing_span_sha256:'c'.repeat(64),table_source:source,table_kind:tableKind,record_index:index,containing_span_byte_offset:base,containing_span_byte_length:8192},activation:'not_evaluated',height_status:'unknown'};
}
function envelope(records=[record()]){
  return {schema_version:'legaia.field-spatial.v1',scene_id:scene,coordinate_system:'psx_guest_xz',units:'guest_integer_world_units',display_y:0,height_status:'unknown',quantization:{trigger:{tile_size:128,world_bias:0,rule:'tile = world >> 7'},region:{tile_size:128,world_bias:64,rule:'tile = (world - 64) >> 7'}},records};
}
const clone=value=>structuredClone(value);
function invalid(edit){const value=envelope();edit(value);assert.throws(()=>decodeFieldSpatial(value,scene));}

// Trigger dispatch uses an unbiased grid; region lookup alone uses the 64-unit bias.
const source=envelope([record(),record({kind:'region',tableKind:3,tiles:{x_min:255,x_max:257,z_min:-2,z_max:0}}),record({tableKind:1,source:'fallback'})]);
const decoded=decodeFieldSpatial(source,scene);
assert.deepEqual(decoded.records[0].world_bounds,{x_min:256,x_max:384,z_min:512,z_max:640});
assert.deepEqual(decoded.records[1].world_bounds,{x_min:32704,x_max:32960,z_min:-192,z_max:64});
assert.equal(decoded.records[1].world_center.y,0);
decoded.records[0].label='Detached';decoded.records[0].source_record.disc.sha256='d'.repeat(64);decoded.records[1].world_bounds.x_min=0;
assert.equal(source.records[0].label,'Source trigger 0');assert.equal(source.records[0].source_record.disc.sha256,hash);assert.equal(source.records[1].world_bounds.x_min,32704);
assert.deepEqual(decodeFieldSpatial(envelope([]),scene).records,[]);
assert.throws(()=>decodeFieldSpatial(source,'scene://other'));
assert.throws(()=>decodeFieldSpatial(source,'town01'));
assert.throws(()=>decodeFieldSpatial(Object.create({records:[]}),scene));
for(const edit of [
  value=>value.schema_version='legaia.field-spatial.v2',
  value=>value.extra=true,
  value=>value.display_y=1,
  value=>value.height_status='known',
  value=>value.coordinate_system='browser_xyz',
  value=>value.units='tiles',
  value=>value.quantization.trigger.world_bias=64,
  value=>value.quantization.region.world_bias=0,
  value=>value.quantization.region.rule='tile = world >> 7',
  value=>value.quantization.trigger.tile_size=64,
  value=>value.quantization.extra=true,
  value=>value.records=Array(4097).fill(record()),
  value=>value.records[0].extra=true,
  value=>value.records[0].id='trigger://other/field-map/primary/kind-0/0000',
  value=>value.records.push(clone(value.records[0])),
  value=>value.records[0].label='Bad\0label',
  value=>value.records[0].label='x'.repeat(513),
  value=>value.records[0].table_kind=2,
  value=>value.records[0].trigger_type='partition_2_trigger',
  value=>value.records[0].activation='active',
  value=>value.records[0].height_status='known',
  value=>value.records[0].world_center.y=-100,
  value=>value.records[0].world_center.x+=1,
  value=>value.records[0].world_bounds.x_min+=64,
  value=>value.records[0].world_bounds.x_max=Infinity,
  value=>value.records[0].source_tile_bounds.x_min=-1,
  value=>value.records[0].source_tile_bounds.x_max=4,
  value=>value.records[0].source_record.extra=true,
  value=>value.records[0].source_record.disc.serial='OTHER',
  value=>value.records[0].source_record.disc.sha256='short',
  value=>value.records[0].source_record.iso_file='MAN.DAT',
  value=>value.records[0].source_record.prot_entry_name='other',
  value=>value.records[0].source_record.prot_entry_index=-1,
  value=>value.records[0].source_record.prot_start_lba=1.5,
  value=>value.records[0].source_record.sha256='A'.repeat(64),
  value=>value.records[0].source_record.containing_span_sha256=null,
  value=>value.records[0].source_record.byte_coordinate_space='decompressed_script',
  value=>value.records[0].source_record.byte_length=8,
  value=>value.records[0].source_record.table_source='fallback',
  value=>value.records[0].source_record.table_kind=1,
  value=>value.records[0].source_record.record_index=1,
  value=>value.records[0].source_record.containing_span_byte_offset=0,
  value=>value.records[0].source_record.containing_span_byte_length=8191,
  value=>value.records[0].source_record.byte_offset=65536+17,
  value=>value.records[0].source_record.byte_offset=65536+8190,
])invalid(edit);
const unsupportedFallback=envelope([record({source:'fallback'})]);assert.throws(()=>decodeFieldSpatial(unsupportedFallback,scene));
const rowOrigin=envelope([record(),record({index:1})]);rowOrigin.records[1].source_record.byte_offset+=4;assert.throws(()=>decodeFieldSpatial(rowOrigin,scene));
const tableOverlap=envelope([record(),record({tableKind:1})]);tableOverlap.records[1].source_record.byte_offset=tableOverlap.records[0].source_record.byte_offset;assert.throws(()=>decodeFieldSpatial(tableOverlap,scene));
const mixedDisc=envelope([record(),record({tableKind:1})]);mixedDisc.records[1].source_record.disc.sha256='d'.repeat(64);assert.throws(()=>decodeFieldSpatial(mixedDisc,scene));
const mixedSource=envelope([record(),record({tableKind:1})]);mixedSource.records[1].source_record.containing_span_sha256='d'.repeat(64);assert.throws(()=>decodeFieldSpatial(mixedSource,scene));
const indexPastOrigin=envelope([record({index:2000})]);indexPastOrigin.records[0].source_record.byte_offset=65536+64;assert.throws(()=>decodeFieldSpatial(indexPastOrigin,scene));
const regionBad=envelope([record({kind:'region',tableKind:3})]);regionBad.records[0].trigger_type='unknown_gate';assert.throws(()=>decodeFieldSpatial(regionBad,scene));
const unknown=envelope([record({tableKind:1})]);unknown.records[0].trigger_type='unknown_gate';assert.equal(decodeFieldSpatial(unknown,scene).records[0].trigger_type,'unknown_gate');

class Canvas{
  constructor(){this.calls=[];this.depth=0;this.globalAlpha=.8;}
  save(){this.calls.push(['save']);this.saved={fillStyle:this.fillStyle,strokeStyle:this.strokeStyle,lineWidth:this.lineWidth,globalAlpha:this.globalAlpha};this.depth++;}
  restore(){this.calls.push(['restore']);Object.assign(this,this.saved);this.depth--;}
  beginPath(){this.calls.push(['begin']);}
  rect(...args){this.calls.push(['rect',...args]);}
  clip(){this.calls.push(['clip']);}
  moveTo(...args){this.calls.push(['move',...args]);}
  lineTo(...args){this.calls.push(['line',...args]);}
  closePath(){this.calls.push(['close']);}
  fill(){this.calls.push(['fill',this.fillStyle]);if(this.failFill)throw new Error('canvas failure');}
  stroke(){this.calls.push(['stroke',this.strokeStyle,this.lineWidth]);}
  arc(...args){this.calls.push(['arc',...args]);}
}
const projection=point=>({x:point.x/4,y:point.z/4,depth:1000});
const rows=decodeFieldSpatial(envelope([record(),record({tableKind:1})]),scene).records;
const ctx=new Canvas();ctx.fillStyle='original';ctx.strokeStyle='original';ctx.lineWidth=9;
assert.equal(drawFieldSpatial(ctx,rows,projection,800,600,rows[0].id),2);
assert.deepEqual(ctx.calls.slice(0,4),[['save'],['begin'],['rect',0,0,800,600],['clip']]);
assert.equal(ctx.calls.at(-1)[0],'restore');assert.equal(ctx.depth,0);assert.equal(ctx.fillStyle,'original');assert.equal(ctx.strokeStyle,'original');assert.equal(ctx.lineWidth,9);assert.equal(ctx.globalAlpha,.8);
assert.deepEqual(ctx.calls.filter(call=>call[0]==='stroke').map(call=>call.slice(1)),[['#5bd4dc',1.2],['#f5f8ff',2.5]]);
assert.equal(drawFieldSpatial(new Canvas(),rows,p=>({x:p.x+10000,y:p.z+10000,depth:1}),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,p=>p.x===256?null:projection(p),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,p=>p.x===320?null:projection(p),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,p=>({...projection(p),depth:p.x===256?0:1}),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,()=>({x:NaN,y:0,depth:1}),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,()=>({x:1e8,y:0,depth:1}),800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,()=>{throw new Error('project');},800,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,projection,0,600),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,projection,800,Infinity),0);
assert.equal(drawFieldSpatial(new Canvas(),rows,null,800,600),0);
const failure=new Canvas();failure.failFill=true;assert.throws(()=>drawFieldSpatial(failure,rows,projection,800,600));assert.equal(failure.depth,0);assert.equal(failure.calls.at(-1)[0],'restore');

// Source order resolves coincident rows; repeated clicks cycle only that same center.
const center=projection(rows[0].world_center);
assert.equal(hitFieldSpatial(rows,projection,center.x,center.y),rows[0].id);
assert.equal(hitFieldSpatial(rows,projection,center.x,center.y,rows[0].id),rows[1].id);
assert.equal(hitFieldSpatial(rows,projection,center.x,center.y,rows[1].id),rows[0].id);
assert.equal(hitFieldSpatial(rows,projection,center.x,center.y,'unrelated'),rows[0].id);
assert.equal(hitFieldSpatial(rows,projection,10,10),null);
assert.equal(hitFieldSpatial(rows,projection,NaN,center.y),null);
assert.equal(hitFieldSpatial(rows,()=>({x:0,y:0,depth:-1}),0,0),null);
assert.equal(hitFieldSpatial(rows,()=>({x:NaN,y:0,depth:1}),0,0),null);
assert.equal(hitFieldSpatial(rows,()=>null,0,0),null);
assert.equal(hitFieldSpatial(rows,p=>p.x===256?null:projection(p),center.x,center.y),null);
assert.equal(hitFieldSpatial(rows,null,center.x,center.y),null);
// The six-pixel edge tolerance includes near misses and leaves distant misses alone.
assert.equal(hitFieldSpatial([rows[0]],projection,59,center.y),rows[0].id);
assert.equal(hitFieldSpatial([rows[0]],projection,57,center.y),null);
const broad=record({kind:'region',tableKind:3,tiles:{x_min:0,x_max:10,z_min:0,z_max:10}});
assert.equal(hitFieldSpatial([broad,rows[0]],projection,center.x,center.y),rows[0].id);
assert.equal(hitFieldSpatial([broad,rows[0]],projection,20,20),broad.id);
// A floor edge viewed side-on can still be selected through its center marker.
const edgeProjection=point=>({x:point.x/4,y:50,depth:100});
assert.equal(hitFieldSpatial([rows[0]],edgeProjection,80,57),rows[0].id);
assert.equal(hitFieldSpatial([rows[0]],edgeProjection,80,60),null);

const framed=fieldSpatialFrame(source.records[1]);assert.deepEqual(framed.target,{x:32832,y:0,z:-64});assert.equal(framed.distance,Math.hypot(256,256)*1.5);
assert.deepEqual(fieldSpatialFrame(rows[0]),{target:{x:320,y:0,z:576},distance:512});
assert.throws(()=>fieldSpatialFrame({...rows[0],world_center:{x:320,y:-64,z:576}}));
assert.throws(()=>fieldSpatialFrame({...rows[0],world_bounds:{x_min:1,x_max:1,z_min:0,z_max:1}}));
assert.throws(()=>fieldSpatialFrame(null));
const large={...broad,world_bounds:{x_min:-65536,x_max:65536,z_min:-65536,z_max:65536},world_center:{x:0,y:0,z:0}};assert.equal(fieldSpatialFrame(large).distance,65536);
console.log('Field spatial source validation, projection, picking and framing passed.');

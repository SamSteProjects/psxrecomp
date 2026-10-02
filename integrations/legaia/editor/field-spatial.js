// Source field tables occupy XZ cells. Y=0 is an inspection plane, not floor height.
const TOP_KEYS=['schema_version','scene_id','coordinate_system','units','display_y','height_status','quantization','records'];
const RECORD_KEYS=['id','kind','label','table_source','table_kind','record_index','trigger_type','world_bounds','world_center','source_tile_bounds','source_record','activation','height_status'];
const BOUNDS_KEYS=['x_min','x_max','z_min','z_max'];
const SOURCE_KEYS=['disc','iso_file','prot_entry_index','prot_entry_name','prot_start_lba','byte_offset','byte_length','byte_coordinate_space','sha256','containing_span_sha256','table_source','table_kind','record_index','containing_span_byte_offset','containing_span_byte_length'];
const TRIGGER_TYPES=new Set(['intra_scene_teleport','object_bind','partition_2_trigger','unknown_gate']);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const exact=(value,keys)=>object(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
const integer=(value,min,max)=>Number.isSafeInteger(value)&&value>=min&&value<=max;
const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const text=value=>typeof value==='string'&&value.length>0&&value.length<=512&&!/[\u0000-\u001f]/.test(value);
const fail=message=>{throw new Error(message);};
const same=(a,b)=>Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(key=>a[key]===b[key]);

function quantization(value,bias,rule){
  return exact(value,['tile_size','world_bias','rule'])&&value.tile_size===128&&value.world_bias===bias&&value.rule===rule;
}

export function decodeFieldSpatial(value,sceneId){
  const scene=typeof sceneId==='string'&&/^scene:\/\/([A-Za-z0-9_-]{1,128})$/.exec(sceneId);
  if(!scene||!exact(value,TOP_KEYS)||value.schema_version!=='legaia.field-spatial.v1'||value.scene_id!==sceneId||value.coordinate_system!=='psx_guest_xz'||value.units!=='guest_integer_world_units'||value.display_y!==0||value.height_status!=='unknown'||!exact(value.quantization,['trigger','region'])||!quantization(value.quantization.trigger,0,'tile = world >> 7')||!quantization(value.quantization.region,64,'tile = (world - 64) >> 7')||!Array.isArray(value.records)||value.records.length>4096)fail('Invalid source field spatial envelope.');
  const identifiers=new Set(),sources=new Map(),origins=new Map(),tableRanges=new Map();let discHash=null;
  for(const record of value.records){
    if(!exact(record,RECORD_KEYS)||!['trigger','region'].includes(record.kind)||!text(record.label)||!['primary','fallback'].includes(record.table_source)||!integer(record.record_index,0,9999)||record.activation!=='not_evaluated'||record.height_status!=='unknown')fail('Invalid source field spatial record.');
    const region=record.kind==='region',kind=record.table_kind,stride=region?8:4;
    if(region?kind!==3||record.trigger_type!==null:![0,1].includes(kind)||!TRIGGER_TYPES.has(record.trigger_type))fail('Invalid field table kind or trigger interpretation.');
    if(record.table_source==='fallback'&&kind!==1||!region&&(kind===0)!==(record.trigger_type==='intra_scene_teleport'))fail('Field trigger interpretation differs from its source table.');
    const expected=region?`region://${scene[1]}/field-map/${record.table_source}/${String(record.record_index).padStart(4,'0')}`:`trigger://${scene[1]}/field-map/${record.table_source}/kind-${kind}/${String(record.record_index).padStart(4,'0')}`;
    if(record.id!==expected||identifiers.has(record.id))fail('Field record identity is duplicated or differs from its source.');
    identifiers.add(record.id);
    const tiles=record.source_tile_bounds,bounds=record.world_bounds,center=record.world_center,bias=region?64:0;
    if(!exact(tiles,BOUNDS_KEYS)||BOUNDS_KEYS.some(key=>!integer(tiles[key],region?-2:0,region?257:256))||tiles.x_max<=tiles.x_min||tiles.z_max<=tiles.z_min||!region&&(tiles.x_min>255||tiles.z_min>255||tiles.x_max!==tiles.x_min+1||tiles.z_max!==tiles.z_min+1)||!exact(bounds,BOUNDS_KEYS)||BOUNDS_KEYS.some(key=>bounds[key]!==tiles[key]*128+bias)||!exact(center,['x','y','z'])||center.x!==(bounds.x_min+bounds.x_max)/2||center.y!==0||center.z!==(bounds.z_min+bounds.z_max)/2)fail('Field spatial bounds differ from source tile quantization.');
    const source=record.source_record,base=record.table_source==='primary'?65536:0;
    if(!exact(source,SOURCE_KEYS)||!exact(source.disc,['sha256','serial'])||!hash(source.disc.sha256)||source.disc.serial!=='SCUS-94254'||source.iso_file!=='PROT.DAT'||source.prot_entry_name!==scene[1]||!integer(source.prot_entry_index,0,0xffffffff)||!integer(source.prot_start_lba,0,0xffffffff)||!hash(source.sha256)||!hash(source.containing_span_sha256)||source.byte_coordinate_space!=='prot_entry'||source.byte_length!==stride||source.table_source!==record.table_source||source.table_kind!==kind||source.record_index!==record.record_index||source.containing_span_byte_offset!==base||source.containing_span_byte_length!==8192||!integer(source.byte_offset,base+18,base+8192-stride)||source.byte_offset-record.record_index*stride<base+18)fail('Invalid field source record provenance or byte extent.');
    if(discHash!==null&&discHash!==source.disc.sha256)fail('Field records differ in source disc identity.');
    discHash=source.disc.sha256;
    const sourceIdentity={prot_entry_index:source.prot_entry_index,prot_start_lba:source.prot_start_lba,containing_span_sha256:source.containing_span_sha256};
    const priorSource=sources.get(record.table_source);
    if(priorSource&&!same(priorSource,sourceIdentity))fail('Field rows differ in their containing source table.');
    sources.set(record.table_source,sourceIdentity);
    const tableId=record.table_source+'/'+kind,origin=source.byte_offset-record.record_index*stride;
    if(origins.has(tableId)&&origins.get(tableId)!==origin)fail('Field row index differs from its source table byte origin.');
    origins.set(tableId,origin);
    const range=tableRanges.get(tableId);
    tableRanges.set(tableId,{source:record.table_source,start:origin,end:Math.max(range?.end??0,source.byte_offset+stride)});
  }
  const ranges=[...tableRanges.values()];
  for(let i=0;i<ranges.length;i++)for(let j=i+1;j<ranges.length;j++)if(ranges[i].source===ranges[j].source&&ranges[i].start<ranges[j].end&&ranges[j].start<ranges[i].end)fail('Field table byte ranges overlap ambiguously.');
  return structuredClone(value);
}

function geometry(record){
  const bounds=record?.world_bounds,center=record?.world_center;
  if(!record||typeof record.id!=='string'||!['trigger','region'].includes(record.kind)||!exact(bounds,BOUNDS_KEYS)||BOUNDS_KEYS.some(key=>!Number.isFinite(bounds[key])||Math.abs(bounds[key])>65536)||bounds.x_max<=bounds.x_min||bounds.z_max<=bounds.z_min||!exact(center,['x','y','z'])||center.y!==0||center.x!==(bounds.x_min+bounds.x_max)/2||center.z!==(bounds.z_min+bounds.z_max)/2)return null;
  return {bounds,center,corners:[{x:bounds.x_min,y:0,z:bounds.z_min},{x:bounds.x_max,y:0,z:bounds.z_min},{x:bounds.x_max,y:0,z:bounds.z_max},{x:bounds.x_min,y:0,z:bounds.z_max}]};
}
function projected(point,project){
  let result;try{result=project(point);}catch{return null;}
  return result&&['x','y','depth'].every(key=>Number.isFinite(result[key]))&&result.depth>0&&Math.abs(result.x)<=1e7&&Math.abs(result.y)<=1e7?result:null;
}
function projectedRecord(record,project){
  const world=geometry(record);if(!world)return null;
  const corners=world.corners.map(point=>projected(point,project)),center=projected(world.center,project);
  if(!center||corners.some(point=>!point))return null;
  return {record,corners,center};
}

export function drawFieldSpatial(ctx,records,project,width,height,selectedId=null){
  if(!Array.isArray(records)||records.length>4096||typeof project!=='function'||!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0||width>32768||height>32768||!ctx||['save','restore','beginPath','rect','clip','moveTo','lineTo','closePath','fill','stroke','arc'].some(key=>typeof ctx[key]!=='function'))return 0;
  const visible=[];
  for(const record of records){
    const result=projectedRecord(record,project);if(!result)continue;
    const xs=result.corners.map(point=>point.x),ys=result.corners.map(point=>point.y);
    if(Math.max(...xs)<-8||Math.min(...xs)>width+8||Math.max(...ys)<-8||Math.min(...ys)>height+8)continue;
    visible.push(result);
  }
  // Keep the selected source row legible over other rows sharing its tile.
  visible.sort((a,b)=>Number(a.record.id===selectedId)-Number(b.record.id===selectedId));
  ctx.save();
  try{
    ctx.beginPath();ctx.rect(0,0,width,height);ctx.clip();
    for(const {record,corners,center} of visible){
      const selected=record.id===selectedId,region=record.kind==='region';
      ctx.fillStyle=region?(selected?'rgba(247,191,79,.24)':'rgba(247,191,79,.10)'):(selected?'rgba(91,212,220,.28)':'rgba(91,212,220,.12)');
      ctx.strokeStyle=selected?'#f5f8ff':region?'#f7bf4f':'#5bd4dc';ctx.lineWidth=selected?2.5:1.2;
      ctx.beginPath();ctx.moveTo(corners[0].x,corners[0].y);for(const point of corners.slice(1))ctx.lineTo(point.x,point.y);ctx.closePath();ctx.fill();ctx.stroke();
      ctx.beginPath();ctx.arc(center.x,center.y,selected?5:3,0,Math.PI*2);ctx.fillStyle=ctx.strokeStyle;ctx.fill();
    }
  }finally{ctx.restore();}
  return visible.length;
}

function segmentDistanceSquared(x,y,a,b){
  const dx=b.x-a.x,dy=b.y-a.y,length=dx*dx+dy*dy,t=length?Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/length)):0;
  return (x-a.x-t*dx)**2+(y-a.y-t*dy)**2;
}
function polygonHit(x,y,corners){
  let inside=false;
  for(let i=0,j=corners.length-1;i<corners.length;j=i++){
    const a=corners[j],b=corners[i];
    if(segmentDistanceSquared(x,y,a,b)<=36)return true;
    if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;
  }
  return inside;
}
export function hitFieldSpatial(records,project,x,y,selectedId=null){
  if(!Array.isArray(records)||records.length>4096||typeof project!=='function'||!Number.isFinite(x)||!Number.isFinite(y)||Math.abs(x)>1e7||Math.abs(y)>1e7)return null;
  const hits=[];
  for(const record of records){
    const result=projectedRecord(record,project);if(!result)continue;
    const distance=(x-result.center.x)**2+(y-result.center.y)**2;
    if(distance<=64||polygonHit(x,y,result.corners))hits.push({...result,distance});
  }
  if(!hits.length)return null;
  let nearest=hits[0];for(const hit of hits)if(hit.distance<nearest.distance)nearest=hit;
  const coincident=hits.filter(hit=>Math.abs(hit.center.x-nearest.center.x)<=1e-6&&Math.abs(hit.center.y-nearest.center.y)<=1e-6);
  const selected=coincident.findIndex(hit=>hit.record.id===selectedId);
  return coincident[selected<0?0:(selected+1)%coincident.length].record.id;
}

export function fieldSpatialFrame(record){
  const world=geometry(record);if(!world)fail('Cannot frame an invalid source field record.');
  return {target:{...world.center},distance:Math.max(512,Math.min(65536,Math.hypot(world.bounds.x_max-world.bounds.x_min,world.bounds.z_max-world.bounds.z_min)*1.5))};
}

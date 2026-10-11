import {placementDigest as digest,equalWorldPlacementBytes as equalBytes,replayWorldPlacementAllocations,composeWorldPlacementTransforms,decodeWorldPlacementSeeds} from './worldmap-placement-replay.js';
import {worldMapTriggerTables,worldManRecordSpans,replayScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
const fail=m=>{throw Error(m);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===[...keys].sort().join(',');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const integer=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const view=b=>new DataView(b.buffer,b.byteOffset,b.byteLength);
const bytes=(s,length)=>{if(typeof s!=='string'||s.length!==4*Math.ceil(length/3)||!/^[A-Za-z0-9+/]*={0,2}$/.test(s))fail('Current MAP native byte witness has invalid bounds.');const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));if(b.length!==length)fail('Current MAP byte footprint differs.');return b;};
const families=['Environment','Collision','FloorTiers','RegionBounds','TriggerCells','TriggerScripts'];
function merge(raw,current,patched,masks){
  const result=current.slice();
  for(let i=0;i<raw.length;i++)if(raw[i]!==patched[i]){
    const mask=masks?.get(i)??255,held=current[i]&mask,old=raw[i]&mask,wanted=patched[i]&mask;
    if(held!==old&&held!==wanted)fail('Current MAP coauthors conflict on a native field.');
    result[i]=(current[i]&~mask)|(patched[i]&mask);
  }
  return result;
}
function transform(data,edit,record){
  const result=data.slice(),v=view(result),fields=['offset','rotation_psx'];
  if(!fields.some(k=>Object.hasOwn(edit,k)))fail('Environment transform has no authored axes.');
  for(const field of fields)if(Object.hasOwn(edit,field)){
    const axes=edit[field];if(!axes||Array.isArray(axes)||!Object.keys(axes).length||Object.keys(axes).some(k=>!['x','y','z'].includes(k)))fail('Environment axes differ.');
    for(const [axis,value] of Object.entries(axes)){
      if(!integer(value,field==='offset'?-32768:0,field==='offset'?32767:4095))fail('Environment axis domain differs.');
      const at=record*32+(field==='offset'?0:8)+2*'xyz'.indexOf(axis);
      if(field==='offset')v.setInt16(at,value,true);else v.setUint16(at,value,true);
    }
  }
  return result;
}
function environment(raw,binding){
  if(!binding||!Object.hasOwn(binding,'source_sha256')||Object.keys(binding).some(k=>!['source_sha256','edits','instances'].includes(k)))fail('Environment binding schema differs.');
  const shared=binding.edits??[],local=binding.instances??[];
  if(!Array.isArray(shared)||shared.length>512||!Array.isArray(local)||local.length>512)fail('Environment edits exceed their budget.');
  const refs=new Set();for(let c=0;c<16384;c++)refs.add(view(raw).getUint16(32768+2*c,true)&511);
  let result=raw.slice();const seen=new Set();
  for(const e of shared){
    if(!e||Object.keys(e).some(k=>!['record_index','offset','rotation_psx'].includes(k))||!integer(e.record_index,0,511)||seen.has(e.record_index)||!refs.has(e.record_index))fail('Environment record owner differs.');
    seen.add(e.record_index);const patched=transform(raw,e,e.record_index);result.set(patched.slice(e.record_index*32,e.record_index*32+32),e.record_index*32);
  }
  const baseline=result.slice(),v=view(baseline),cells=new Set(),prepared=[];
  for(const e of local){
    if(!e||Object.keys(e).some(k=>!['cell_index','offset','rotation_psx'].includes(k))||!integer(e.cell_index,0,16383)||cells.has(e.cell_index))fail('Environment instance owner differs.');
    cells.add(e.cell_index);const word=v.getUint16(32768+2*e.cell_index,true),record=word&511;
    if(record<4||!(word&8192)||v.getUint16(record*32+18,true)&4)fail('Environment instance lacks a static native descriptor.');
    const patched=transform(baseline,e,record),descriptor=patched.slice(record*32,record*32+32);
    if(!equalBytes(descriptor,baseline.slice(record*32,record*32+32)))prepared.push({cell:e.cell_index,word,descriptor});
  }
  const free=[];for(let r=4;r<512;r++)if(!refs.has(r)&&baseline.slice(r*32,r*32+32).every(n=>n===0))free.push(r);
  if(prepared.length>free.length)fail('Environment instance has no unused zero descriptor.');
  prepared.sort((a,b)=>a.cell-b.cell).forEach((p,i)=>{result.set(p.descriptor,free[i]*32);view(result).setUint16(32768+p.cell*2,(p.word&~511)|free[i],true);});
  return result;
}
export async function composeWorldMapCoauthors(raw,normal,scene,components,retailMan){
  if(!(raw instanceof Uint8Array)||raw.length!==73728||!(normal instanceof Uint8Array)||normal.length!==raw.length||!['map01','map02','map03'].includes(scene)||!components||Array.isArray(components)||Object.keys(components).some(k=>!families.includes(k)))fail('Current MAP coauthor inputs differ.');
  const sourceHash=await digest(raw),tables=worldMapTriggerTables(raw.slice(65536)).tables;
  let current=normal.slice();
  for(const name of families){
    const b=components[name];if(b===undefined)continue;
    if(b.source_sha256!==sourceHash)fail('Current MAP coauthor source hash differs.');
    if(name==='Environment'){current=merge(raw,current,environment(raw,b));continue;}
    if(!exact(b,['source_sha256','edits'])||!Array.isArray(b.edits))fail('Current MAP coauthor binding schema differs.');
    const max=name==='RegionBounds'?1021:['TriggerCells','TriggerScripts'].includes(name)?2043:4096;
    if(b.edits.length>max)fail('Current MAP coauthor exceeds its edit budget.');
    const patched=raw.slice(),masks=new Map(),seen=new Set();
    for(const e of b.edits){
      if(name==='Collision'||name==='FloorTiers'){
        const wall=name==='Collision',keys=wall?['row','column','quadrant','blocked']:['row','column','tier'];
        if(!exact(e,keys)||!integer(e.row,wall?1:0,127)||!integer(e.column,0,127)||wall&&(!integer(e.quadrant,0,3)||typeof e.blocked!=='boolean')||!wall&&!integer(e.tier,0,15))fail('Current MAP wall/floor domain differs.');
        const id=`${e.row},${e.column},${wall?e.quadrant:''}`;if(seen.has(id))fail('Current MAP grid edit is duplicated.');seen.add(id);
        const at=16384+e.row*128+e.column,mask=wall?1<<(4+e.quadrant):15;
        const value=wall?(e.blocked?mask:0):e.tier;patched[at]=(patched[at]&~mask)|value;
        if((raw[at]&mask)!==value)masks.set(at,(masks.get(at)??0)|mask);
        continue;
      }
      const region=name==='RegionBounds',script=name==='TriggerScripts',id=region?e.region_id:e.trigger_id;
      const fields=region?['x0','z0','x1','z1']:script?['script_id','script_sha256']:['tile_x','tile_z'];
      if(!exact(e,[region?'region_id':'trigger_id',...fields])||typeof id!=='string'||seen.has(id))fail('Current MAP table identity differs.');seen.add(id);
      const match=(region?new RegExp(`^region://${scene}/field-map/primary/([0-9]{4})$`):new RegExp(`^trigger://${scene}/field-map/primary/kind-([01])/([0-9]{4})$`)).exec(id);
      if(!match)fail('Current MAP row belongs to another table.');
      const kind=region?3:Number(match[1]),index=Number(match[region?1:2]),table=tables[kind],row=table.rows[index];
      if(!row)fail('Current MAP table row is unavailable.');const at=65536+table.at+index*(region?8:4);
      if(script){
        const target=typeof e.script_id==='string'&&new RegExp(`^script://${scene}/scripts/man-p2/([0-9]{4})$`).exec(e.script_id);
        if(kind!==1||row[3]!==1||!target||Number(target[1])>255||!hash(e.script_sha256))fail('Current MAP trigger script lacks its gate-one P2 owner.');
        const span=worldManRecordSpans(retailMan).find(r=>r.partition===2&&r.index===Number(target[1]));
        if(!span||await digest(retailMan.slice(span.at,span.at+span.length))!==e.script_sha256)fail('Current MAP trigger script differs from native MAN ownership.');
        patched[at+2]=Number(target[1]);
      }else fields.forEach((field,i)=>{if(!integer(e[field],0,255))fail('Current MAP table coordinate domain differs.');patched[at+i]=e[field];});
    }
    current=merge(raw,current,patched,['Collision','FloorTiers'].includes(name)?masks:null);
  }
  return current;
}
export async function qualifyCurrentWorldMap(value,retail,man,{path,key,overrides}){
  const scene=retail.scene,p=value.source_record;
  if(!exact(value,['schema_version','scene','source_key','project_path','source_record','retail_map_base64','normal_map_base64','current_map_base64','normal_map_sha256','current_map_sha256','fallback_base64','source_man_sha256','current_man_sha256','scene_components','transform_binding','decoration_binding','scripted_binding','retained_base_map_base64','read_only','project_changed','gameplay_verified'])||value.schema_version!=='legaia.worldmap-current-map.v1'||value.scene!==scene||value.source_key!==key||retail.project_source_key!==key||value.project_path!==path||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||
      !exact(p,['scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256'])||p.scene!==scene||p.source_disc_sha256!==retail.source_record.disc_sha256||p.source_map_sha256!==retail.source_record.map_sha256||p.source_floor_lut_sha256!==retail.source_record.floor_lut_sha256)fail('Current MAP source identity or scope differs.');
  const raw=bytes(value.retail_map_base64,73728),normal=bytes(value.normal_map_base64,73728),current=bytes(value.current_map_base64,73728),fallback=bytes(value.fallback_base64,8192);
  if(await digest(raw)!==p.source_map_sha256||await digest(normal)!==value.normal_map_sha256||await digest(current)!==value.current_map_sha256||await digest(man.retail)!==value.source_man_sha256||await digest(man.current)!==value.current_man_sha256||await digest(man.retail.slice(2,34))!==p.source_floor_lut_sha256)fail('Current MAP complete byte hashes or MAN inputs differ.');
  if(!same(man.floor,Array.from({length:16},(_,i)=>view(man.current).getInt16(2+i*2,true))))fail('Current MAP floor coordinates differ from qualified MAN bytes.');
  const transform=overrides?.[`worldmap://${scene}/placements`]?.WorldMapPlacements??null,decoration=overrides?.[`worldmap://${scene}/placement-allocations`]?.WorldMapPlacementAllocations??null,scripted=overrides?.[`worldmap://${scene}/scripted-placement-allocations`]?.WorldMapScriptedPlacementAllocations??null;
  const components=Object.fromEntries(Object.entries(overrides?.[`scene://${scene}`]??{}).filter(([k])=>families.includes(k)));
  if(!same(value.transform_binding,transform)||!same(value.decoration_binding,decoration)||!same(value.scripted_binding,scripted)||!same(value.scene_components,components))fail('Current MAP witness differs from project bindings.');
  if(transform&&(!exact(transform,[...Object.keys(p),'entries'])||!Object.keys(p).every(k=>transform[k]===p[k])))fail('Current MAP source transform provenance differs.');
  const floor=Array.from({length:16},(_,i)=>view(man.retail).getInt16(2+i*2,true)),decor=await replayWorldPlacementAllocations(raw,floor,scene,decoration,p);
  const transformed=await composeWorldPlacementTransforms(raw,decor.bytes,floor,scene,transform?.entries??{}),composed=await composeWorldMapCoauthors(raw,transformed,scene,components,man.retail);
  if(!equalBytes(composed,normal))fail('Current MAP differs from complete independent coauthor replay.');
  let candidate=normal;let allocations=[];
  if(scripted){
    const base=bytes(value.retained_base_map_base64,73728),provenance={...p,source_man_sha256:value.source_man_sha256,fallback_sha256:await digest(fallback)};
    const retained=await replayScriptedWorldPlacements(base,fallback,man.current,man.floor,scripted,provenance);
    candidate=await mergeScriptedWorldCurrent(base,retained.bytes,normal,man.floor,scene,retained.audits);allocations=retained.audits.flatMap(a=>a.allocations);
  }else if(value.retained_base_map_base64!==null)fail('Current MAP has an unowned retained base.');
  if(!equalBytes(candidate,current))fail('Current MAP differs from complete scripted replay and ownership merge.');
  const decoded=await decodeWorldPlacementSeeds(current,man.floor,scene),seeds=new Map(decoded.placements.map(s=>[s.source_cell,s]));
  const refresh=rows=>rows.map(a=>{const seed=seeds.get(a.target_cell);if(!seed)fail('Current MAP lost an authored seed.');return {...structuredClone(a),native_seed:seed};});
  return {retail:raw,normal,current,decorations:refresh(decor.allocations),scripted:refresh(allocations)};
}

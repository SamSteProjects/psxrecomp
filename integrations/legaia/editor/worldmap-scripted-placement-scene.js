import {qualifyCurrentWorldMan} from './worldmap-current-man.js';
import {qualifyCurrentWorldMap} from './worldmap-current-map.js';
import {decodeWorldPlacementSeeds, equalWorldPlacementBytes} from './worldmap-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
import {qualifyCurrentWorldModels, currentWorldModelView} from './worldmap-current-models.js';
import {qualifyScriptedCreationReview} from './worldmap-scripted-creation-state.js';
const fail=m=>{throw Error(m);};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const bytes=s=>{if(typeof s!=='string'||s.length>5592408||s.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(s))fail('Scripted scene native witness exceeds its bounds.');return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};

export async function qualifyScriptedWorldScene(retail,current,options){
  const scene=retail?.scene,key=retail?.project_source_key,graph=current?.scene_graph,source=current?.placement_source;
  if(current?.schema_version!=='legaia.worldmap-scripted-placement-scene.v1'||current.representation!=='current-scripted-placement-source'||current.scene!==scene||current.project_source_key!==key||current.ground_layer!=='retail'||current.placement_layer!=='current'||current.project_changed!==false||current.gameplay_verified!==false||!graph||!Array.isArray(graph.entities)||graph.entities.length>512||
    source?.schema_version!=='legaia.worldmap-scripted-placement-source.v1'||source.scene!==scene||source.source_key!==key||source.project_path!==options.path||source.read_only!==true||source.project_changed!==false||source.gameplay_verified!==false)fail('Scripted Current scene source identity or scope differs.');
  const qualification={path:options.path,key,overrides:options.overrides};
  const man=await qualifyCurrentWorldMan(options.manWitness,retail,qualification);
  const map=await qualifyCurrentWorldMap(options.mapWitness,retail,man,qualification);
  const witness=options.mapWitness;
  if(!same(source.source_record,witness.source_record)||source.source_man_sha256!==witness.source_man_sha256||source.current_man_sha256!==witness.current_man_sha256||source.current_map_sha256!==witness.current_map_sha256||!equalWorldPlacementBytes(bytes(source.source_map_base64),map.retail)||!equalWorldPlacementBytes(bytes(source.current_map_base64),map.current)||!equalWorldPlacementBytes(bytes(source.source_man_base64),man.retail)||!equalWorldPlacementBytes(bytes(source.current_man_base64),man.current)||source.fallback_base64!==witness.fallback_base64||!same(source.floor_lut,man.floor)||!same(source.binding,witness.scripted_binding)||!nativeWorldPlacementMatches(source.authored_decorations,map.decorations)||!nativeWorldPlacementMatches(source.authored_scripted_placements,map.scripted)||(source.retained_base_map_base64??null)!==witness.retained_base_map_base64)fail('Scripted scene receipt differs from independent complete native qualification.');
  const decoded=await decodeWorldPlacementSeeds(map.current,man.floor,scene);
  const retailFloor=Array.from({length:16},(_,i)=>new DataView(man.retail.buffer,man.retail.byteOffset,man.retail.byteLength).getInt16(2+i*2,true));
  if(!same(retail.floor_height_lut,retailFloor))fail('Scripted scene Retail floor differs from immutable native MAN.');
  const originalDecoded=await decodeWorldPlacementSeeds(map.retail,retailFloor,scene),originalSeeds=new Map(originalDecoded.placements.map(e=>[e.entity_id,e]));
  const originals=new Map(retail.scene_graph.entities.filter(e=>e.placement_scope!=='source_ground').map(e=>[e.entity_id,e]));
  for(const [id,e] of originals){const seed=originalSeeds.get(id);if(!seed||Object.entries(seed).some(([k,v])=>!nativeWorldPlacementMatches(e[k],v,k)))fail('Scripted scene Retail entity differs from literal native seed ownership.');}
  const ground=retail.scene_graph.entities.filter(e=>e.placement_scope==='source_ground');
  if(ground.length!==1||originals.size+1!==retail.scene_graph.entities.length)fail('Scripted scene original owners are ambiguous.');
  const allocations=[...map.decorations,...map.scripted],authored=new Map(allocations.map(a=>[a.native_seed.entity_id,a]));
  if(authored.size!==allocations.length)fail('Scripted scene authored seeds share ownership.');
  const scripted=new Set(map.scripted.map(a=>a.placement_id)),expected=[structuredClone(ground[0])],seen=new Set(),unresolved=structuredClone(decoded.unresolved);
  const failures=new Map(retail.scene_graph.coverage.unresolved.filter(e=>e.entity_id).map(e=>[e.entity_id,e]));
  let changed=0;
  for(const seed of decoded.placements){
    const allocation=authored.get(seed.entity_id),original=originals.get(seed.entity_id);
    if(allocation){
      if(original||!nativeWorldPlacementMatches(allocation.native_seed,seed))fail('Scripted scene authored seed conflicts with original ownership.');
      const kind=scripted.has(allocation.placement_id)?'scripted':'decoration';
      expected.push({...structuredClone(seed),entity_id:`scene://${scene}/worldmap/authored-placements/${allocation.placement_id.split('/').pop()}`,asset_id:`asset://${scene}/worldmap/models/${String(seed.model_pool_index).padStart(4,'0')}`,renderable:true,native_entity_id:seed.entity_id,authored_placement:structuredClone(allocation),authored_placement_kind:kind,retail_seed:null,placement_scope:kind==='scripted'?'authored_scripted_seed':'authored_spawn_seed'});
    }else if(original){
      if(seed.object_record_index!==original.object_record_index||seed.model_pool_index!==original.model_pool_index)fail('Scripted scene changed an original model owner.');
      changed+=Object.entries(seed).some(([k,v])=>!nativeWorldPlacementMatches(original[k],v,k))?1:0;
      expected.push({...structuredClone(seed),asset_id:`asset://${scene}/worldmap/models/${String(seed.model_pool_index).padStart(4,'0')}`,renderable:true,retail_seed:structuredClone(original)});
    }else{
      const failure=failures.get(seed.entity_id);if(!failure||typeof failure.reason!=='string')fail('Scripted scene lost an unsupported Retail model witness.');
      unresolved.push({...structuredClone(failure),...structuredClone(seed)});
    }
    seen.add(seed.entity_id);
  }
  if([...originals.keys(),...authored.keys()].some(id=>!seen.has(id)))fail('Scripted scene lost a retained native owner.');
  if(current.changed_source_entity_count!==changed||current.authored_entity_count!==allocations.length)fail(`Scripted scene counts differ: changed ${changed}/${current.changed_source_entity_count}, authored ${allocations.length}/${current.authored_entity_count}.`);
  if(!nativeWorldPlacementMatches(graph.entities,expected)){
    const index=expected.findIndex((e,i)=>!nativeWorldPlacementMatches(graph.entities[i],e));
    const fields=Object.keys(expected[index]??{}).filter(k=>!nativeWorldPlacementMatches(graph.entities[index]?.[k],expected[index][k],k));
    fail(`Scripted scene entity ${index} native fields differ: ${fields.join(', ')}.`);
  }
  const coverage={...decoded.coverage,resolved_count:expected.length-1,rendered_count:expected.length-1,unresolved_count:unresolved.length,unresolved};
  const limitations=[...retail.scene_graph.limitations,'Current scripted placements retain shared scripts; runtime visibility and resting transforms are unverified.'];
  const assets=new Map(graph.assets.map(a=>[a.asset_id,a]));
  let drawn=0;
  for(const e of expected){const p=assets.get(e.asset_id)?.preview;if(!p?.vertices?.length||!p.triangles?.length)fail('Scripted scene lacks a drawable qualified model.');drawn+=p.triangles.length;}
  const modelAuthored=Object.entries(options.bindings??{}).some(([id,b])=>id.startsWith(`asset://${scene}/worldmap/models/`)&&b.asset_sha256!==b.source_sha256);
  if(drawn>200000||graph.metrics.entity_count!==expected.length||graph.metrics.drawn_triangle_count!==drawn||!nativeWorldPlacementMatches(graph.coverage,coverage)||!same(graph.limitations,limitations)||current.authored_geometry!==!!(modelAuthored||allocations.length||changed))fail('Scripted scene coverage, counts or authored layer claim differs.');
  const normalized=structuredClone(current);
  for(const k of ['placement_source','ground_layer','placement_layer','changed_source_entity_count','authored_entity_count'])delete normalized[k];
  normalized.schema_version=retail.schema_version;normalized.representation='current-source';normalized.authored_geometry=modelAuthored;
  normalized.scene_graph.entities=structuredClone(retail.scene_graph.entities);normalized.scene_graph.coverage=structuredClone(retail.scene_graph.coverage);normalized.scene_graph.limitations=structuredClone(retail.scene_graph.limitations);
  normalized.scene_graph.metrics.entity_count=retail.scene_graph.entities.length;
  normalized.scene_graph.metrics.drawn_triangle_count=retail.scene_graph.entities.reduce((n,e)=>n+assets.get(e.asset_id).preview.triangles.length,0);
  const qualified=options.sources?await qualifyCurrentWorldModels(retail,normalized,options):await currentWorldModelView(retail,normalized,options);
  return {assets:qualified.assets,entities:expected.map(entity=>{
    const matrix=[];for(let row=0;row<4;row++)for(let col=0;col<4;col++)matrix.push(entity.source_to_world[col*4+row]*(row===1?-1:1));
    return {...entity,geometry_key:entity.asset_id,model_to_scene:matrix,authored_source_position:entity.placement_scope==='source_ground'?null:entity.source_position,preview_layer:'Current authored seeds'};
  })};
}

export async function qualifyProposedScriptedWorldScene(retail,proposed,review,creation,options){
  await qualifyScriptedCreationReview(review,creation,review.requests);
  if(proposed?.schema_version!=='legaia.worldmap-scripted-placement-proposed-scene.v1'||proposed.representation!=='proposed-scripted-placement-source'||proposed.placement_layer!=='proposed'||!nativeWorldPlacementMatches(proposed.scripted_proposal,review))fail('Proposed scripted scene differs from the independently reviewed native proposal.');
  const normalized=structuredClone(proposed);delete normalized.scripted_proposal;
  normalized.schema_version='legaia.worldmap-scripted-placement-scene.v1';normalized.representation='current-scripted-placement-source';normalized.placement_layer='current';
  const mapWitness=structuredClone(creation.mapWitness),overrides=structuredClone(options.overrides);
  mapWitness.current_map_base64=review.proposed_map_base64;mapWitness.current_map_sha256=review.proposed_map_sha256;mapWitness.scripted_binding=structuredClone(review.binding);
  mapWitness.retained_base_map_base64=creation.source.binding?creation.mapWitness.retained_base_map_base64:creation.source.current_map_base64;
  overrides[`worldmap://${retail.scene}/scripted-placement-allocations`]={WorldMapScriptedPlacementAllocations:structuredClone(review.binding)};
  const view=await qualifyScriptedWorldScene(retail,normalized,{...options,mapWitness,overrides});
  return {...view,entities:view.entities.map(e=>({...e,preview_layer:'Proposed authored seeds'}))};
}

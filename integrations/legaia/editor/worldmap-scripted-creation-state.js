import {qualifyCurrentWorldMan} from './worldmap-current-man.js';
import {qualifyCurrentWorldMap} from './worldmap-current-map.js';
import {placementDigest,decodeWorldPlacementSeeds,equalWorldPlacementBytes,worldPlacementInventory} from './worldmap-placement-replay.js';
import {allocateScriptedWorldPlacements,replayScriptedWorldPlacements,mergeScriptedWorldCurrent} from './worldmap-scripted-placement-replay.js';
import {nativeWorldPlacementMatches} from './worldmap-current-placements.js';
const fail=m=>{throw Error(m);},hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;
const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const bytes=v=>{if(typeof v!=='string'||v.length>5592408||v.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(v))fail('Scripted creation byte witness exceeds its bounds.');return Uint8Array.from(atob(v),c=>c.charCodeAt(0));};
export async function qualifyScriptedCreationSource(source,retail,manWitness,mapWitness,{path,key,overrides}){
 const options={path,key,overrides},man=await qualifyCurrentWorldMan(manWitness,retail,options),map=await qualifyCurrentWorldMap(mapWitness,retail,man,options);
 if(source?.schema_version!=='legaia.worldmap-scripted-placement-source.v1'||source.scene!==retail.scene||source.source_key!==key||source.project_path!==path||source.read_only!==true||source.project_changed!==false||source.gameplay_verified!==false||!same(source.source_record,mapWitness.source_record)||!same(source.binding,mapWitness.scripted_binding)||source.current_map_sha256!==mapWitness.current_map_sha256||source.current_man_sha256!==mapWitness.current_man_sha256||!equalWorldPlacementBytes(bytes(source.current_map_base64),map.current)||!equalWorldPlacementBytes(bytes(source.current_man_base64),man.current)||source.fallback_base64!==mapWitness.fallback_base64||source.fallback_sha256!==await placementDigest(bytes(source.fallback_base64))||!same(source.floor_lut,man.floor)||!nativeWorldPlacementMatches(source.authored_decorations,map.decorations)||!nativeWorldPlacementMatches(source.authored_scripted_placements,map.scripted))fail('Scripted creation source differs from qualified project native bytes.');
 const count=(source.binding?.operations??[]).reduce((n,op)=>n+op.requests.length,0);
 if(source.remaining_creation_capacity!==32-count||!Array.isArray(source.donors)||source.donors.length>511||!Array.isArray(source.free_record_indices)||source.free_record_indices.length>508||!Array.isArray(source.target_cells)||source.target_cells.length>16384)fail('Scripted creation source candidates exceed their native bounds.');
 const seeds=new Map((await decodeWorldPlacementSeeds(map.current,man.floor,retail.scene)).placements.map(s=>[s.source_cell,s])),seen=new Set();
 for(const donor of source.donors){if(!donor?.seed||seen.has(donor.seed.source_cell)||!nativeWorldPlacementMatches(donor.seed,seeds.get(donor.seed.source_cell))||donor.shared_script_required!==true)fail('Scripted creation donor differs from a native seed.');seen.add(donor.seed.source_cell);}
 for(const list of [source.free_record_indices,source.target_cells])if(new Set(list).size!==list.length||list.some(n=>!Number.isSafeInteger(n)||n<0||n>16383))fail('Scripted creation candidates are duplicated or outside their bounds.');
 const inventory=await worldPlacementInventory(map.current,man.floor,retail.scene);
 if(!same(source.free_record_indices,inventory.free_record_indices)||!same(source.target_cells,inventory.target_cells))fail('Scripted creation candidates differ from complete native inventory.');
 return {source:structuredClone(source),man,map,mapWitness:structuredClone(mapWitness),manWitness:structuredClone(manWitness)};
}
export async function qualifyScriptedCreationReview(value,qualified,requests){
 const {source,man,map,mapWitness}=qualified;
 if(value?.schema_version!=='legaia.worldmap-scripted-placement-review.v1'||value.project_path!==source.project_path||value.scene!==source.scene||value.source_key!==source.source_key||!same(value.requests,requests)||!same(value.source_record,source.source_record)||value.current_map_sha256!==source.current_map_sha256||value.current_man_sha256!==source.current_man_sha256||value.fallback_sha256!==source.fallback_sha256||!same(value.before_binding,source.binding)||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||!hash(value.review_key)||value.relocation_offset!==source.relocation_offset)fail('Scripted creation Review differs from fresh source or draft.');
 const fallback=bytes(source.fallback_base64),candidate=await allocateScriptedWorldPlacements(map.current,fallback,man.current,man.floor,source.scene,requests,value.relocation_offset);
 if(await placementDigest(candidate.bytes)!==value.proposed_map_sha256||!equalWorldPlacementBytes(candidate.bytes,bytes(value.proposed_map_base64))||!nativeWorldPlacementMatches(candidate.audit,value.audit))fail('Scripted creation Review differs from independent complete native allocation.');
 const binding=value.binding,before=source.binding,operations=binding?.operations;
 if(!Array.isArray(operations)||operations.length!==(before?.operations.length??0)+1||!same(operations.slice(0,-1),before?.operations??[])||!same(operations.at(-1).requests,requests)||operations.at(-1).relocation_offset!==value.relocation_offset)fail('Scripted creation Review changed retained operations.');
 const base=before?bytes(mapWitness.retained_base_map_base64):map.current;
 const provenance={...source.source_record,source_man_sha256:mapWitness.source_man_sha256,fallback_sha256:source.fallback_sha256};
 const replay=await replayScriptedWorldPlacements(base,fallback,man.current,man.floor,binding,provenance);
 const merged=await mergeScriptedWorldCurrent(base,replay.bytes,map.normal,man.floor,source.scene,replay.audits);
 if(!equalWorldPlacementBytes(merged,candidate.bytes))fail('Scripted creation retained ledger differs from the reviewed Current proposal.');
 return structuredClone(value);
}

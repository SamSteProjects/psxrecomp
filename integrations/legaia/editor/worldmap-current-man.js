import {placementDigest as digest,equalWorldPlacementBytes as equalBytes} from './worldmap-placement-replay.js';
import {worldManRecordSpans} from './worldmap-scripted-placement-replay.js';
import {qualifyWorldScriptOperands} from './world-script-animation-operands.js';
import {qualifyWorldScriptGraph} from './world-script-graph.js';
import {worldBranchTarget} from './world-script-branch-bytes.js';
const fail=m=>{throw Error(m);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===[...keys].sort().join(',');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const integer=(v,lo,hi)=>Number.isSafeInteger(v)&&v>=lo&&v<=hi;
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const bytes=v=>{if(typeof v!=='string'||v.length>5592408||v.length%4||!/^[A-Za-z0-9+/]*={0,2}$/.test(v))fail('Current MAN byte witness exceeds its bounds.');return Uint8Array.from(atob(v),c=>c.charCodeAt(0));};
export async function qualifyCurrentWorldMan(value,retail,{path,key,overrides}) {
  const scene=retail?.scene,source=retail?.source_record;
  if(!['map01','map02','map03'].includes(scene)||!exact(value,['schema_version','scene','source_key','project_path','source_record','retail_man_base64','current_man_base64','current_man_sha256','script_components','branch_components','floor_heights','records','read_only','project_changed','gameplay_verified'])||
    value.schema_version!=='legaia.worldmap-current-man.v1'||value.scene!==scene||value.source_key!==key||retail.project_source_key!==key||value.project_path!==path||value.read_only!==true||value.project_changed!==false||value.gameplay_verified!==false||
    !exact(value.source_record,['source_disc_sha256','source_man_sha256'])||value.source_record.source_disc_sha256!==source.disc_sha256||value.source_record.source_man_sha256!==source.man_slot.decoded_sha256||!hash(value.current_man_sha256))fail('Current MAN source identity or scope differs.');
  const script=overrides?.[`worldmap://${scene}/script-operands`]??{},branch=overrides?.[`worldmap://${scene}/script-branches`]??{},heights=overrides?.[`scene://${scene}`]?.FloorHeights??null;
  if(!same(value.script_components,script)||!same(value.branch_components,branch)||!same(value.floor_heights,heights))fail('Current MAN witness differs from project authored bindings.');
  if(Object.keys(script).length>1||Object.keys(script).some(k=>!['WorldScriptOperands','WorldScriptAnimationOperands'].includes(k))||Object.keys(branch).some(k=>k!=='WorldScriptBranches'))fail('Current MAN has an unsupported authored owner.');
  const fixed=Object.values(script)[0]??null,branched=branch.WorldScriptBranches??null;
  for(const binding of [fixed,branched].filter(Boolean))if(!exact(binding,['source_disc_sha256','source_man_sha256','entries'])||!same({source_disc_sha256:binding.source_disc_sha256,source_man_sha256:binding.source_man_sha256},value.source_record)||!binding.entries||Array.isArray(binding.entries)||!integer(Object.keys(binding.entries).length,1,512))fail('Current MAN script binding source or budget differs.');
  const original=bytes(value.retail_man_base64),current=bytes(value.current_man_base64);
  if(original.length!==source.man_slot.decoded_byte_length||current.length!==original.length||await digest(original)!==value.source_record.source_man_sha256||await digest(current)!==value.current_man_sha256)fail('Current MAN complete byte hashes differ.');
  const spans=worldManRecordSpans(original),expected=original.slice(),scripts=[...new Set([...Object.keys(fixed?.entries??{}),...Object.keys(branched?.entries??{})])].sort();
  if(!Array.isArray(value.records)||value.records.length!==scripts.length)fail('Current MAN edited record coverage differs.');
  let operandCount=0,branchCount=0;
  for(let i=0;i<scripts.length;i++){
    const witness=value.records[i],id=scripts[i];
    if(!exact(witness,['record','source','retail_graph'])||!exact(witness.record,['id','kind','source_record','entry_pc','source_instance_ids'])||witness.record.id!==id||!new RegExp(`^script://${scene}/worldmap/man-p0/[0-9]{4}$`).test(id))fail('Current MAN record witness owner differs.');
    const record=witness.record,index=Number(id.split('/').pop()),span=spans.find(r=>r.partition===0&&r.index===index),native=record.source_record;
    if(!span||native.byte_offset!==span.at||native.byte_length!==span.length||native.disc_sha256!==source.disc_sha256||native.man_slot.decoded_sha256!==value.source_record.source_man_sha256||record.entry_pc!==2+2*original[span.at])fail('Current MAN record differs from its native offset table.');
    const q=await qualifyWorldScriptOperands(witness.source,record,key,path),raw=bytes(q.record_base64),edited=bytes(q.current_record_base64);
    if(!equalBytes(raw,original.slice(span.at,span.at+span.length)))fail('Current MAN source record bytes differ.');
    qualifyWorldScriptGraph(witness.retail_graph,raw,q);
    const fixedEntry=fixed?.entries[id],branchEntry=branched?.entries[id];
    for(const [entry,field] of [[fixedEntry,'operands'],[branchEntry,'branches']])if(entry){
      if(!exact(entry,['source_record_sha256','shared_record',field])||entry.source_record_sha256!==native.sha256||typeof entry.shared_record!=='boolean'||record.source_instance_ids.length>1&&entry.shared_record!==true||!entry[field]||Array.isArray(entry[field])||!Object.keys(entry[field]).length)fail('Current MAN source record binding or shared consent differs.');
      if(Object.keys(entry[field]).some(pc=>!/^[0-9a-f]{4}$/.test(pc)))fail('Current MAN authored PC domain differs.');
    }
    const fixedValues=Object.fromEntries(q.targets.filter(t=>t.authored_values!==null).map(t=>[t.pc.toString(16).padStart(4,'0'),t.authored_values]));
    if(!same(fixedValues,fixedEntry?.operands??{}))fail('Current MAN argument witness omits or invents authored fields.');
    operandCount+=Object.keys(fixedValues).length;
    const edits=new Map((q.branch_changes??[]).map(e=>[e.pc,e]));
    for(const [pc,values] of Object.entries(branchEntry?.branches??{})){
      const n=parseInt(pc,16),node=witness.retail_graph.instructions.find(r=>r.pc===n),target=node?worldBranchTarget(node,raw):null,edit=edits.get(n);
      if(!exact(values,['target_pc'])||!integer(values.target_pc,0,32767)||!target||witness.retail_graph.stops.length||
        values.target_pc!==(edit?.authored_target_pc??target.target_pc))fail('Current MAN branch witness differs from project destinations.');
      edits.delete(n);branchCount++;
    }
    if(edits.size||operandCount>1024||branchCount>1024)fail('Current MAN branch coverage or argument budget differs.');
    expected.set(edited,span.at);
  }
  if(heights){
    if(!exact(heights,['source_sha256','edits'])||heights.source_sha256!==value.source_record.source_man_sha256||!Array.isArray(heights.edits)||heights.edits.length>16)fail('Current MAN height binding differs.');
    const used=new Set(),v=new DataView(expected.buffer);
    for(const e of heights.edits){if(!exact(e,['tier','height'])||!integer(e.tier,0,15)||!integer(e.height,-32768,32767)||used.has(e.tier))fail('Current MAN height tier or value differs.');used.add(e.tier);v.setInt16(2+e.tier*2,e.height,true);}
  }
  if(!equalBytes(current,expected))fail('Current MAN changes bytes outside qualified script and height owners.');
  return {retail:original,current,floor:Array.from({length:16},(_,i)=>new DataView(current.buffer).getInt16(2+i*2,true))};
}

import {scriptBranchContext,inspectBranchReport} from './script-branches.js';
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),valid=v=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===1&&Number.isSafeInteger(v.bit)&&v.bit>=0&&v.bit<=31;
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=()=>{throw Error('Controller flag-bit snapshot differs from its qualified source.');};
const nodes=r=>inspectBranchReport({...r,instructions:[...r.instructions,...(r.unvisited_instructions??[])],dialogues:[...r.dialogues,...(r.unvisited_dialogues??[])]});
function bit(node){
 if(!node||!Number.isSafeInteger(node.byte_offset)||node.byte_offset<0||typeof node.raw_hex!=='string'||!/^[a-f0-9]+$/.test(node.raw_hex)||node.raw_hex.length!==node.length*2)fail();
 const bytes=node.raw_hex.match(/../g).map(v=>parseInt(v,16)),opcode=bytes[0]&127,header=bytes[0]&128?2:1;
 if(opcode<0x2b||opcode>0x33||node.mnemonic!==['LFLAG','GFLAG','CFLAG'][Math.floor((opcode-0x2b)/3)]+'_'+['SET','CLEAR','TEST'][(opcode-0x2b)%3]||node.length!==header+1||node.target_context!==(header===2?bytes[1]:null)||node.operands?.bit!==(bytes[header]&31)||!same(node.successors,[{pc:node.pc+node.length,condition:'encoded_continuation'}]))fail();
 const value=bytes[header]&31;if(opcode<=0x2d&&value>=16||opcode===0x31&&value===8||opcode===0x32&&value===10)fail();
 return {value,header,bytes};
}
export function decodeControllerFlagBitSnapshot(raw,owner,context){
 context=scriptBranchContext(context);
 if(owner!==context.sceneId+'/controllers/man-p1/0000'||raw?.schema_version!=='legaia.controller-flag-bits.v1'||raw.owner_id!==owner||raw.state_key!==context.scriptKey||!hash(raw.source_record_sha256)||!hash(raw.current_record_sha256)||raw.gameplay_verified!==false||!Array.isArray(raw.targets)||raw.targets.length>1024||raw.supported!==(raw.targets.length>0)||raw.source?.owner_id!==owner||raw.source.record_kind!=='man_partition_1_scene_controller'||raw.source.runtime_execution!=='not_asserted')fail();
 const source=nodes(raw.source_report),current=nodes(raw.current_report),seen=new Set();
 for(const t of raw.targets){const original=source.get(t.pc),now=current.get(t.pc),a=bit(original),b=bit(now);
  if(t.semantic_id!==owner.replace('scene://','script://')+'/flag-bit/'+t.pc.toString(16).padStart(4,'0')||seen.has(t.semantic_id)||t.owner_id!==owner||t.mnemonic!==original.mnemonic||t.target_context!==original.target_context||t.source_record_sha256!==raw.source_record_sha256||t.bit_mask!==31||t.preserved_bits!==(a.bytes[a.header]&224)||t.maximum!==(original.mnemonic.startsWith('LFLAG_')?15:31)||t.decoded_byte_offset!==original.byte_offset+a.header||now.byte_offset!==original.byte_offset||now.mnemonic!==original.mnemonic||a.header!==b.header||!same(a.bytes.slice(0,a.header),b.bytes.slice(0,b.header))||(b.bytes[b.header]&224)!==t.preserved_bits||!valid(t.values)||t.values.bit!==a.value||!valid(t.current_values)||t.current_values.bit!==b.value||!(t.authored_values===null||valid(t.authored_values))||!same(t.current_values,t.authored_values??t.values))fail();seen.add(t.semantic_id);
 }
 if(raw.targets.length&&raw.source_report.stops.length)fail();
 return structuredClone(raw);
}

const fail=message=>{throw Error(message);};
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const hex=v=>Array.from(v,n=>n.toString(16).padStart(2,'0')).join('');
export function qualifyWorldScriptGraph(graph,data,source){
 if(!exact(graph,['status','entry_pc','instructions','dialogues','opaque_regions','stops'])||!['partial','decoded_supported_paths'].includes(graph.status)||graph.entry_pc!==source.entry_pc)fail('World instruction graph has an invalid source entry or status.');
 const used=new Uint8Array(data.length);
 for(const family of ['instructions','dialogues','opaque_regions']){
  if(!Array.isArray(graph[family])||graph[family].length>4096)fail('World instruction graph exceeds its row budget.');
  for(const row of graph[family]){
   if(!Number.isSafeInteger(row.pc)||!Number.isSafeInteger(row.length)||row.pc<source.entry_pc||row.length<1||row.pc+row.length>data.length||row.byte_offset!==source.source_record.byte_offset+row.pc||row.raw_hex!==hex(data.slice(row.pc,row.pc+row.length)))fail('World graph row differs from its exact record bytes.');
   for(let n=row.pc;n<row.pc+row.length;n++){if(used[n])fail('World graph record ownership overlaps.');used[n]=1;}
   if(family==='instructions'){
    if(typeof row.mnemonic!=='string'||row.mnemonic.length>128||row.opcode!==(data[row.pc]&127)||!row.operands||typeof row.operands!=='object'||Array.isArray(row.operands)||!Array.isArray(row.successors)||row.successors.length>8||!(row.target_context===null||Number.isSafeInteger(row.target_context)&&row.target_context>=0&&row.target_context<=255))fail('World instruction metadata is invalid.');
    for(const edge of row.successors)if(!exact(edge,['pc','condition'])||!Number.isSafeInteger(edge.pc)||edge.pc<0||edge.pc>65535||typeof edge.condition!=='string'||edge.condition.length>256)fail('World static branch edge is invalid.');
    // Message-picker leads mask bit 7 without introducing an actor context.
    const header=(data[row.pc]&128)&&![0x27,0x28,0x29].includes(row.opcode)?2:1;
    if(row.length<header||row.target_context!==(header===2?data[row.pc+1]:null)||row.operands.encoded_hex!==hex(data.slice(row.pc+header,row.pc+row.length)))fail('World instruction context or encoded operands differ from bytes.');
   }
  }
 }
 if(used.slice(source.entry_pc).some(n=>!n)||!Array.isArray(graph.stops)||graph.stops.length>4096||(graph.opaque_regions.length||graph.stops.length)&&graph.status!=='partial')fail('World graph coverage or unknown regions are inconsistent.');
}

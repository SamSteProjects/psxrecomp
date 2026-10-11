import assert from 'node:assert/strict';
import {locateWorldScriptPc,qualifyWorldScriptInspection} from '../editor/world-script-inspection.js';

// A branch may land at an instruction, inside one, in opaque bytes or at the
// record boundary. Navigation reports ownership without inventing a target.
const graph={entry_pc:4,instructions:[{pc:4,length:3},{pc:10,length:2}],dialogues:[{pc:7,length:3}],opaque_regions:[{pc:12,length:4}]};
assert.deepEqual(locateWorldScriptPc(graph,4,16),{kind:'instructions',pc:4,offset:0});
assert.deepEqual(locateWorldScriptPc(graph,6,16),{kind:'instructions',pc:4,offset:2});
assert.deepEqual(locateWorldScriptPc(graph,8,16),{kind:'dialogues',pc:7,offset:1});
assert.deepEqual(locateWorldScriptPc(graph,15,16),{kind:'opaque_regions',pc:12,offset:3});
assert.deepEqual(locateWorldScriptPc(graph,3,16),{kind:'header',pc:3});
assert.deepEqual(locateWorldScriptPc(graph,16,16),{kind:'record_end',pc:16});
assert.deepEqual(locateWorldScriptPc(graph,65535,16),{kind:'outside_record',pc:65535});
for(const pc of [-1,65536,1.5,NaN,'4'])assert.throws(()=>locateWorldScriptPc(graph,pc,16));
assert.throws(()=>locateWorldScriptPc({...graph,opaque_regions:[]},12,16));
// Two complete MES labels and table targets at record end. The high-bit
// picker lead uses a one-byte header; it is not an actor-target context.
const data=Buffer.from('0000a70a0008001f41001f4200','hex'),sourceRecord={byte_offset:64,byte_length:13,sha256:Buffer.from(await crypto.subtle.digest('SHA-256',data)).toString('hex')};
const record={kind:'script',id:'script://map01/worldmap/man-p0/0000',entry_pc:2,source_record:sourceRecord,source_instance_ids:[]};
const source={schema_version:'legaia.world-script-animation-operands.v1',project_path:'private',source_key:'key',script_id:record.id,source_record:sourceRecord,entry_pc:2,source_instance_ids:[],record_base64:data.toString('base64'),current_record_base64:data.toString('base64'),targets:[],limitations:[],project_changed:false,gameplay_verified:false};
const picker={status:'partial',entry_pc:2,instructions:[{pc:2,length:11,opcode:0x27,mnemonic:'DIALOGUE_PICKER',operands:{encoded_hex:'0a0008001f41001f4200'},raw_hex:'a70a0008001f41001f4200',target_context:null,successors:[{pc:13,condition:'menu_choice_0'},{pc:13,condition:'menu_choice_1'}],byte_offset:66}],dialogues:[],opaque_regions:[],stops:[{pc:2,kind:'known_instruction_unresolved_control_flow'}]};
const snapshot={schema_version:'legaia.world-script-inspection.v1',source,retail_graph:picker,current_graph:structuredClone(picker),read_only:true,project_changed:false,gameplay_verified:false};
await qualifyWorldScriptInspection(snapshot,record,'key','private');
const forged=structuredClone(snapshot);forged.current_graph.instructions[0].target_context=10;await assert.rejects(()=>qualifyWorldScriptInspection(forged,record,'key','private'));
console.log('World script PC ownership, boundaries and picker header checks passed');

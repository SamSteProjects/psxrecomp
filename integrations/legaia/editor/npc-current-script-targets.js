import {decodeNpcCurrentScript} from './npc-current-script.js';
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
const coordinate=v=>(v&127)*128+(v&128?128:64);
function target(row,record,known,path){
 const source=known.get(row.pc),header=record[row.pc]&128?2:1,start=row.pc+header,npc=row.mnemonic==='NPC_RUN',size=header+(npc?5:2),op=record[row.pc]&127,args=row.operands;
 if(!source||source.mnemonic!==row.mnemonic||source.length!==row.length||!integer(row.pc,0,65535)||row.pc+size>record.length||row.length!==size||op!==(npc?0x4c:0x23)||npc&&record[start]!==0x51||row.target_context!==(header===2?record[row.pc+1]:null)||args?.coordinate_system!=='retail_field_world_units'||args.runtime_effect!=='not_evaluated'||row.raw_hex!==Array.from(record.slice(row.pc,row.pc+size),b=>b.toString(16).padStart(2,'0')).join(''))throw Error('NPC scene target differs from its qualified instruction bytes.');
 const at=start+(npc?1:0),x=record[at],z=record[at+1],position={x:coordinate(x),y:null,z:coordinate(z)},parked=npc&&(x&127)===127&&(z&127)===127;
 if(!args.target_position||Object.keys(args.target_position).length!==3||['x','y','z'].some(k=>args.target_position[k]!==position[k])||npc&&(args.x_encoded!==x||args.z_encoded!==z||args.depth_encoded!==record[at+2]||args.move_id!==record[at+3]||args.parked_target!==parked)||!npc&&(!Array.isArray(args.encoded_xz)||args.encoded_xz.length!==2||args.encoded_xz[0]!==x||args.encoded_xz[1]!==z||!Array.isArray(args.world_xz)||args.world_xz.length!==2||args.world_xz[0]!==position.x||args.world_xz[1]!==position.z))throw Error('NPC scene target coordinates differ from their native encoding.');
 return {pc:row.pc,mnemonic:row.mnemonic,context:row.target_context,position,parked,path_status:path,move_id:npc?args.move_id:null};
}
export async function npcCurrentScriptTargetOverlay(value,layer,height,state,paths='reached'){
 const accepted=await decodeNpcCurrentScript(value,value.entity_id,state);
 if(!['retail','authored'].includes(layer)||!['reached','all_anchors'].includes(paths)||!Number.isFinite(height)||Math.abs(height)>10000000)throw Error('Choose a qualified target layer, path scope and explicit reference Y.');
 const source=accepted.donor.inspection,report=layer==='retail'?source:accepted.inspection,known=new Map(source.instructions.map(r=>[r.pc,r]));
 if(!Array.isArray(report.unvisited_instructions??[])||report.instructions.length+(report.unvisited_instructions?.length??0)>4096)throw Error('NPC scene target path bounds are invalid.');
 const record=Uint8Array.from(report.record.raw_hex.match(/../g),v=>parseInt(v,16)),rows=[...report.instructions.map(r=>[r,'decoded_reached']),...(paths==='all_anchors'?(report.unvisited_instructions??[]).map(r=>[r,'source_unvisited']):[])],seen=new Set(),targets=[];
 for(const [row,path] of rows){if(!integer(row.pc,0,65535)||seen.has(row.pc))throw Error('Duplicate or invalid NPC source instruction boundary.');seen.add(row.pc);if(!['MOVE_TO','NPC_RUN'].includes(row.mnemonic))continue;if(row.byte_offset!==report.record.byte_offset+row.pc)throw Error('NPC scene target offset differs from its source record.');targets.push(target(row,record,known,path));}
 if(!targets.length)throw Error('This path scope has no qualified X/Z destinations. Move selectors alone do not define a scene position.');
 return {schema_version:'legaia.npc-current-script-targets.v1',entity_id:accepted.entity_id,donor_entity_id:accepted.draft.donor_entity_id,project_source_key:accepted.project_source_key,state_key:accepted.state_key,source_record_sha256:source.record.sha256,current_record_sha256:accepted.inspection.record.sha256,representation:layer,paths,height,targets:targets.sort((a,b)=>a.pc-b.pc),partial:report.status==='partial',runtime_dispatch:'not_asserted',gameplay_verified:false};
}

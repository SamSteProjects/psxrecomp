// Read-only presentation of a source-qualified, unresolved capture descriptor.
export function captureInstructionSummary(row){
  const args=row?.operands,payload=args?.capture_payload,paths=args?.conditional_continuations;
  if(row?.mnemonic!=='EFFECT_SPAWN_PACKET'||row.opcode!==0x34||!Number.isSafeInteger(row.pc)||row.pc<0||
      ![13,14].includes(row.length)||typeof row.raw_hex!=='string'||!/^[0-9a-f]+$/i.test(row.raw_hex)||
      row.raw_hex.length!==row.length*2||args?.following_byte!==0x40||
      args.runtime_actor_match!=='not_observed'||args.runtime_effect!=='not_evaluated'||
      typeof args.unresolved_control_flow!=='string'||!args.unresolved_control_flow||
      !Array.isArray(row.successors)||row.successors.length||!payload||!paths)return null;
  const bytes=row.raw_hex.match(/../g).map(byte=>parseInt(byte,16)),extended=!!(bytes[0]&0x80),header=extended?2:1;
  if((bytes[0]&0x7f)!==0x34||row.length!==header+12||bytes[header]>>4!==1||
      args.raw_selector!==bytes[header]||args.sub_op!==1||
      (extended?row.target_context!==bytes[1]:row.target_context!==null)||
      !Array.isArray(args.packet_bytes)||args.packet_bytes.length!==11||
      args.packet_bytes.some((byte,index)=>byte!==bytes[header+1+index]))return null;
  if(!Number.isSafeInteger(payload.length)||payload.length<0||payload.length>255||
      payload.pc!==row.pc+row.length+2||typeof payload.encoded_hex!=='string'||
      !/^(?:[0-9a-f]{2})*$/i.test(payload.encoded_hex)||payload.encoded_hex.length!==payload.length*2||
      paths.existing_actor!==row.pc+row.length||paths.new_actor_capture!==payload.pc+payload.length||
      !Number.isSafeInteger(paths.new_actor_capture))return null;
  return {payload_pc:payload.pc,payload_length:payload.length,
    existing_actor_pc:paths.existing_actor,new_actor_pc:paths.new_actor_capture};
}

export function appendCaptureSummary(cell,row){
  const summary=captureInstructionSummary(row);if(!summary)return false;
  const offset=pc=>`0x${pc.toString(16).toUpperCase()}`;
  const card=document.createElement('section');card.dataset.captureSummary=String(row.pc);
  const heading=document.createElement('p');heading.textContent=`Conditional capture · ${summary.payload_length} bytes`;
  const list=document.createElement('ul');
  for(const text of [
    `Payload starts at ${offset(summary.payload_pc)} (${summary.payload_length} bytes).`,
    `Existing actor match: continuation ${offset(summary.existing_actor_pc)}.`,
    `New actor capture: continuation ${offset(summary.new_actor_pc)}.`
  ]){const item=document.createElement('li');item.textContent=text;list.append(item);}
  const note=document.createElement('p');note.className='field-note';
  note.textContent='Actor match and payload ownership are unresolved. These offsets are not confirmed parent instruction boundaries.';
  card.append(heading,list,note);cell.append(card);return true;
}

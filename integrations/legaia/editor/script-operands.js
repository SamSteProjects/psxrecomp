/** Match verified authoring metadata to retail instructions without mutating either. */
export function instructionOperandEditors(report){
  const instructions=report?.instructions??[];
  if(!Array.isArray(instructions)||instructions.length>16384)return new Map();
  const source=new Map(instructions.map(row=>[row.pc,row]));
  const output=new Map(),ambiguous=new Set();let budget=0;
  for(const [kind,key] of [['movement','movement_authoring'],['flag','flag_authoring'],['wait','wait_authoring']]){
    const authoring=report?.[key];if(authoring?.supported!==true)continue;
    const targets=authoring.targets;
    if(!Array.isArray(targets)||(budget+=targets.length)>4096)return new Map();
    for(const target of targets){
      const row=source.get(target.pc),values=target.values,authored=target.authored_values,effective=target.effective_values;
      if(!row||!Number.isInteger(target.pc)||row.mnemonic!==target.mnemonic||row.target_context!==target.target_context||
        typeof target.semantic_id!=='string'||!values||!authored||!effective)continue;
      const fields=Object.keys(values);if(!fields.length||fields.length>3)continue;
      const expected=kind==='flag'?{bit:row.operands?.bit}:kind==='wait'?{duration_ticks:row.operands?.duration_ticks}:
        {...row.operands?.target_position,move_id:row.operands?.move_id};
      if(fields.some(field=>!Number.isInteger(values[field])||expected[field]!==values[field]||!Number.isInteger(effective[field]))||
        Object.keys(authored).some(field=>!fields.includes(field)||!Number.isInteger(authored[field]))||
        Object.keys(effective).length!==fields.length||fields.some(field=>effective[field]!== (authored[field]??values[field])))continue;
      if(output.has(target.pc)||ambiguous.has(target.pc)){output.delete(target.pc);ambiguous.add(target.pc);continue;}
      output.set(target.pc,{kind,id:target.semantic_id,pc:target.pc,fields,
        retail:{...values},authored:{...authored},effective:{...effective}});
    }
  }
  return output;
}

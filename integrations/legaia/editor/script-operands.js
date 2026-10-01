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


/** Bind label forms to exact retail picker/option/token spans, never execution. */
export function menuLabelEditors(report){
  const authoring=report?.dialogue_authoring,rows=report?.instructions;
  if(authoring?.supported!==true||!Array.isArray(authoring.runs)||authoring.runs.length>1024||
     !Array.isArray(rows)||rows.length>16384||typeof authoring.actor_id!=='string'||
     !/^scene:\/\/[A-Za-z0-9_-]+\/(?:actors\/man-p1|scripts\/man-p2)\/[0-9]{4}$/.test(authoring.actor_id??''))return new Map();
  const owner=authoring.actor_id,prefix='script://'+owner.slice(8),identity=report.semantic_id??report.script_id;
  if(identity!==prefix)return new Map();
  const pc=value=>Number.isInteger(value)&&value>=0&&value<=65535;
  const source=new Map(),ambiguousPC=new Set();
  for(const row of rows){if(!row||!pc(row.pc))continue;if(source.has(row.pc)){ambiguousPC.add(row.pc);source.delete(row.pc);}else if(!ambiguousPC.has(row.pc))source.set(row.pc,row);}
  const result=new Map(),seen=new Set(),ambiguous=new Set();
  const hex=value=>value.toString(16).padStart(4,'0');
  const plain=value=>typeof value==='string'&&/^[\x20-\x7e]*$/.test(value)&&!value.includes('^');
  for(const run of authoring.runs){
    if(run?.kind!=='menu_label'||run.actor_id!==owner||!pc(run.menu_pc)||!pc(run.pc))continue;
    const row=source.get(run.menu_pc),options=row?.operands?.options,count=row?.operands?.option_count;
    if(row?.mnemonic!=='DIALOGUE_PICKER'||![2,3,4].includes(count)||!Array.isArray(options)||options.length!==count||
       options.some((option,index)=>option?.index!==index)||!Number.isInteger(run.option_index)||run.option_index<0||run.option_index>=count)continue;
    const option=options[run.option_index],size=run.byte_length,tokens=option.label_tokens;
    if(run.option_count!==count||run.entry_pc!==option.entry_pc||run.relative_jump!==option.relative_jump||run.encoded_target!==option.encoded_target||
       !pc(option.label_pc)||!Number.isInteger(option.label_length)||option.label_length<2||option.label_pc+option.label_length>65536||
       !Number.isInteger(size)||size<1||size>4096||run.max_length!==size||!plain(run.text)||run.text.length!==size||
       run.pc<=option.label_pc||run.pc+size>=option.label_pc+option.label_length||
       run.semantic_id!==`${prefix}/menu/${hex(run.menu_pc)}/option/${run.option_index}/run/${hex(run.pc)}`||
       !Array.isArray(tokens)||tokens.length>4096)continue;
    const span=tokens.filter(token=>token&&token.pc>=run.pc&&token.pc<run.pc+size);
    if(span.length!==size||span.some((token,index)=>token.pc!==run.pc+index||token.kind!=='glyph'||token.length!==1||token.value!==run.text.charCodeAt(index)||token.text!==run.text[index]))continue;
    const authored=run.authored_text;
    if(authored!==null&&(!plain(authored)||authored.length>size)||run.effective_text!==(authored===null?run.text:authored.padEnd(size,' ')))continue;
    const key=`${run.menu_pc}:${run.option_index}`;
    if(seen.has(run.semantic_id)){result.delete(key);ambiguous.add(key);continue;}
    seen.add(run.semantic_id);if(ambiguous.has(key))continue;
    if(!result.has(key))result.set(key,[]);
    result.get(key).push({id:run.semantic_id,pc:run.pc,retail:run.text,authored,effective:run.effective_text});
  }
  for(const runs of result.values())runs.sort((a,b)=>a.pc-b.pc);
  return result;
}

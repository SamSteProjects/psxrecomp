import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {qualifyCurrentWorldMan as qualify} from '../editor/worldmap-current-man.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
const bytes=s=>Buffer.from(s,'base64'),hash=b=>createHash('sha256').update(b).digest('hex');
for(const c of cases){
  const held=JSON.stringify(c),result=await qualify(c.value,c.retail,c.options);
  assert.deepEqual(Buffer.from(result.current),bytes(c.value.current_man_base64));assert.deepEqual(Buffer.from(result.retail),bytes(c.value.retail_man_base64));
  result.floor.forEach((v,i)=>assert.equal(v,bytes(c.value.current_man_base64).readInt16LE(2+i*2)));
  for(const key of ['source_key','project_path','current_man_sha256','scene']){
    const bad=structuredClone(c.value);bad[key]='wrong';await assert.rejects(()=>qualify(bad,c.retail,c.options));refusals++;
  }
  for(const key of ['script_components','branch_components']){
    const bad=structuredClone(c.value);bad[key]={};await assert.rejects(()=>qualify(bad,c.retail,c.options));refusals++;
  }
  for(const key of ['read_only','project_changed','gameplay_verified']){
    const bad=structuredClone(c.value);bad[key]=!bad[key];await assert.rejects(()=>qualify(bad,c.retail,c.options));refusals++;
  }
  for(const at of [0,2,34,40,bytes(c.value.current_man_base64).length-1]){
    const bad=structuredClone(c.value),data=bytes(bad.current_man_base64);data[at]^=1;bad.current_man_base64=data.toString('base64');bad.current_man_sha256=hash(data);
    await assert.rejects(()=>qualify(bad,c.retail,c.options));refusals++;
  }
  for(const field of ['byte_offset','byte_length']){
    const bad=structuredClone(c.value);bad.records[0].record.source_record[field]++;
    await assert.rejects(()=>qualify(bad,c.retail,c.options));refusals++;
  }
  const omitted=structuredClone(c.value);omitted.records.pop();await assert.rejects(()=>qualify(omitted,c.retail,c.options));refusals++;
  for(const [component,field,owner] of [['script_components','operands',`worldmap://${c.value.scene}/script-operands`],['branch_components','branches',`worldmap://${c.value.scene}/script-branches`]]){
    const bad=structuredClone(c.value),options=structuredClone(c.options),binding=Object.values(bad[component])[0],entry=Object.values(binding.entries)[0],values=Object.values(entry[field])[0],name=Object.keys(values)[0];
    values[name]++;options.overrides[owner]=structuredClone(bad[component]);
    await assert.rejects(()=>qualify(bad,c.retail,options));refusals++;
  }
  const extra=structuredClone(c.value);extra.extra=true;await assert.rejects(()=>qualify(extra,c.retail,c.options));refusals++;
  assert.equal(JSON.stringify(c),held);console.log(c.name,'complete Current MAN qualified');
}
const proof={cases:cases.length,refusals,complete_current_man_match:true,inputs_unchanged:true,browser_rendered:false,gameplay_verified:false};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));

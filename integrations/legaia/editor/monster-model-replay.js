import {placementDigest} from './worldmap-placement-replay.js';
const ordered=v=>Array.isArray(v)?v.map(ordered):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,ordered(v[k])])):v;const same=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b)),fail=()=>{throw Error('Monster Current model byte ledger changed.');};
const decode=s=>{if(typeof s!=='string'||s.length>11200000)fail();return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
export async function qualifyMonsterModelBytes(v,record,currentField='source_tmd_base64'){
 const current=decode(v[currentField]),binding=v.model_binding;
 if(!binding){if(current.length!==record.source_record.byte_length||await placementDigest(current)!==record.source_record.sha256)fail();return current;}
 const retail=decode(v.retail_tmd_base64),a=binding.source_record,b=record.source_record;
 if(retail.length!==record.source_record.byte_length||current.length!==retail.length||await placementDigest(retail)!==record.source_record.sha256||binding.schema_version!=='legaia.monster-model-override.v1'||binding.asset_id!==record.semantic_id||binding.byte_length!==retail.length||!same(a,b)||!Array.isArray(binding.edits)||binding.edits.length<1||binding.edits.length>retail.length)fail();
 const expected=new Uint8Array(retail);let previous=-1;
 for(const row of binding.edits){const {byte_offset:i,before_byte:before,after_byte:after}=row;if(!Number.isSafeInteger(i)||i<=previous||i>=retail.length||!Number.isSafeInteger(before)||before!==retail[i]||!Number.isSafeInteger(after)||after<0||after>255||before===after)fail();expected[i]=after;previous=i;}
 const header=12+new DataView(retail.buffer).getUint32(8,true)*28;
 if(!same([...retail.subarray(0,header)],[...expected.subarray(0,header)])||!same([...expected],[...current])||await placementDigest(expected)!==binding.current_tmd_sha256)fail();return current;
}

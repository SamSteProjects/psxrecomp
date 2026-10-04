// A copied native object has its own identity and no Retail object counterpart.
const exact=(row,keys)=>row&&typeof row==='object'&&!Array.isArray(row)&&JSON.stringify(Object.keys(row).sort())===JSON.stringify(keys.sort());
export function validateObjectOwnership(rows,currentCount,retailCount){
  const bad=()=>{throw new Error('Native object ownership differs from stable source or clone identities.');};
  if(!Number.isSafeInteger(currentCount)||!Number.isSafeInteger(retailCount)||retailCount<1||currentCount<retailCount||currentCount>1024||currentCount-retailCount>64||!Array.isArray(rows)||rows.length!==currentCount)bad();
  const ids=new Set();let baseHash=null;
  for(const [owner,row] of rows.entries()){
    if(!exact(row,['object_index','retail_index','object_id','donor_object_id'])||row.object_index!==owner||typeof row.object_id!=='string'||ids.has(row.object_id))bad();
    if(owner<retailCount){const match=/^object:\/\/source\/([0-9a-f]{64})\/(0|[1-9][0-9]*)$/.exec(row.object_id);if(!match||Number(match[2])!==owner||row.retail_index!==owner||row.donor_object_id!==null||baseHash!==null&&baseHash!==match[1])bad();baseHash=match[1];}
    else if(!/^object:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(row.object_id)||row.retail_index!==null||typeof row.donor_object_id!=='string'||!ids.has(row.donor_object_id))bad();
    ids.add(row.object_id);
  }
  return structuredClone(rows);
}

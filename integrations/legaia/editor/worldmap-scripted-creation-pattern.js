// Draft planning only. Native Review retains footprint, script and bind ownership.
export function scriptedPlacementPattern(source,draft,ids){
 const fail=m=>{throw Error(m);},integer=(n,min,max)=>Number.isSafeInteger(n)&&n>=min&&n<=max;
 if(!draft||Object.keys(draft).sort().join(',')!=='col_step,count,donor_cell,record_index,row_step,shared_script,target_cell,values'||draft.shared_script!==true)fail('Pattern creation requires explicit shared-script consent.');
 const {count,col_step:dc,row_step:dr,target_cell:start,donor_cell:donor,record_index:record,values}=draft;
 if(!integer(count,1,32)||!integer(dc,-127,127)||!integer(dr,-127,127)||!integer(start,0,16383)||!integer(record,1,511)||!integer(donor,0,16383)||count>1&&dc===0&&dr===0)fail('Enter a count of 1..32 and distinct bounded native cell spacing.');
 if(!values||Object.keys(values).sort().join(',')!=='offset,yaw_units'||!values.offset||Object.keys(values.offset).sort().join(',')!=='x,y,z'||Object.values(values.offset).some(n=>!integer(n,-32768,32767))||!integer(values.yaw_units,0,4095))fail('Pattern offsets and heading require bounded whole native units.');
 if(!source.donors.some(d=>d.seed.source_cell===donor)||count>source.remaining_creation_capacity)fail('Pattern exceeds the qualified donor or remaining creation capacity.');
 const index=source.free_record_indices.indexOf(record),records=source.free_record_indices.slice(index,index+count);
 if(index<0||records.length!==count)fail('Choose a free starting record with enough following free records.');
 if(!Array.isArray(ids)||ids.length<count||new Set(ids.slice(0,count)).size!==count||ids.slice(0,count).some(id=>typeof id!=='string'||!/^placement:\/\/authored\/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id)))fail('Pattern requires distinct draft UUIDs.');
 return Array.from({length:count},(_,i)=>{
  const col=start%128+i*dc,row=Math.floor(start/128)+i*dr;
  if(!integer(col,0,127)||!integer(row,0,127))fail('Pattern leaves the native grid; column spacing cannot wrap into another row.');
  const target=row*128+col;if(!source.target_cells.includes(target))fail('Pattern target has another Current owner.');
  return {placement_id:ids[i],donor_cell:donor,target_cell:target,record_index:records[i],values:structuredClone(values),shared_script:true};
 });
}

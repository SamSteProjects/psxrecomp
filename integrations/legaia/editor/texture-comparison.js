export function decodeRetailComparison(value,sourceHash,profile){
  if(value===undefined)return null;
  const keys=['schema_version','source_sha256','baseline_sha256','bpp','source_width','source_height','proposed_width','proposed_height','added_pixels','removed_pixels','fill_value','baseline'];
  const integer=(v,min,max)=>Number.isInteger(v)&&v>=min&&v<=max,hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
  const fail=()=>{throw new Error('Resized Retail comparison differs from its source or dimensions.');};
  if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||!keys.every(k=>Object.hasOwn(value,k))||value.schema_version!=='legaia.texture-retail-comparison.v1'||value.source_sha256!==sourceHash||!hash(sourceHash)||!hash(value.baseline_sha256)||value.baseline_sha256===sourceHash||value.bpp!==profile.bpp||![4,8,16,24].includes(value.bpp)||value.proposed_width!==profile.width||value.proposed_height!==profile.height||value.fill_value!==0||value.baseline!=='Retail-top-left-overlap-with-zero-filled-new-pixels')fail();
  for(const [w,h] of [[value.source_width,value.source_height],[value.proposed_width,value.proposed_height]])if(!integer(w,1,4096)||!integer(h,1,512)||!integer(w*value.bpp/16,1,1024))fail();
  const shared=Math.min(value.source_width,value.proposed_width)*Math.min(value.source_height,value.proposed_height);
  if(value.source_width===value.proposed_width&&value.source_height===value.proposed_height||value.added_pixels!==value.proposed_width*value.proposed_height-shared||value.removed_pixels!==value.source_width*value.source_height-shared)fail();
  return structuredClone(value);
}

export function retailComparisonLabel(value){
  return value?`Retail fitted to current dimensions · ${value.added_pixels} added pixels zero-filled · ${value.removed_pixels} removed pixels`:'Retail texture';
}

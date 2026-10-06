// Names are UI metadata only; the SDK verifies the chosen clip and whole-file hash.
export function glbAnimationChoices(bytes){
  if(!(bytes instanceof Uint8Array)||bytes.length<28||bytes.length>32*1024*1024)throw new Error('Choose a bounded GLB 2.0 file.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),size=view.getUint32(12,true);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2||view.getUint32(8,true)!==bytes.length||view.getUint32(16,true)!==0x4e4f534a||size%4||size<4||size>bytes.length-20)throw new Error('GLB animation metadata is malformed.');
  const doc=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(20,20+size))),clips=doc?.animations??[];
  if(!doc||typeof doc!=='object'||Array.isArray(doc)||!Array.isArray(clips)||clips.length>64||clips.some(c=>!c||typeof c!=='object'||Array.isArray(c)||c.name!==undefined&&typeof c.name!=='string'))throw new Error('GLB requires at most 64 named animation entries.');
  return clips.map((clip,index)=>({index,label:`${index} · ${(clip.name??'Unnamed clip').replace(/[\x00-\x1f]/g,' ').slice(0,128)}`}));
}

export function populateGlbClipSelect(select,choices){
  select.replaceChildren();
  const option=(value,label)=>{const node=document.createElement('option');node.value=value;node.textContent=label;select.append(node);};
  if(choices.length>1){option('','Choose an animation');for(const row of choices)option(String(row.index),row.label);}
  else option('',choices.length?choices[0].label:'Static node transforms · no animation');
  select.value='';
}

export function selectedGlbClipIndex(select,choices){
  if(choices.length<=1)return null;
  const index=Number(select.value);
  if(select.value===''||!Number.isSafeInteger(index)||!choices.some(row=>row.index===index))throw new Error('Choose an animation from this GLB before Review.');
  return index;
}

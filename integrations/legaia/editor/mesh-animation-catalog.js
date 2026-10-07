// Names identify original source clips; inspection must still qualify sampling.
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===keys.slice().sort().join(',');
const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
export function decodeMeshAnimationCatalog(value,hash,byteLength){
  if(!exact(value,['schema_version','glb_sha256','byte_length','node_count','clips','payloads_decoded','sampling_qualified','project_changed'])||value.schema_version!=='legaia.model-mesh-animation-catalog.v1'||!/^[0-9a-f]{64}$/.test(hash)||value.glb_sha256!==hash||!integer(byteLength,28,32*1024*1024)||value.byte_length!==byteLength||!integer(value.node_count,1,64)||!Array.isArray(value.clips)||value.clips.length>64||value.payloads_decoded!==false||value.sampling_qualified!==false||value.project_changed!==false)throw Error('Animation clip catalog differs from the original GLB.');
  let channels=0;for(const [i,row] of value.clips.entries()){
    if(!exact(row,['animation_index','name','channel_count','sampler_count','target_nodes','target_paths'])||row.animation_index!==i||!(row.name===null||typeof row.name==='string'&&row.name.length<=512)||!integer(row.channel_count,1,256)||!integer(row.sampler_count,1,256)||!Array.isArray(row.target_nodes)||!row.target_nodes.length||row.target_nodes.length>Math.min(value.node_count,row.channel_count)||row.target_nodes.some((n,j)=>!integer(n,0,value.node_count-1)||j&&n<=row.target_nodes[j-1])||!Array.isArray(row.target_paths)||!row.target_paths.length||row.target_paths.length>Math.min(4,row.channel_count)||row.target_paths.some((p,j)=>!['rotation','scale','translation','weights'].includes(p)||j&&p<=row.target_paths[j-1]))throw Error('Invalid animation clip source ownership.');
    channels+=row.channel_count;
  }
  if(channels>256)throw Error('Animation clip catalog exceeds its channel budget.');
  return structuredClone(value);
}
export function populateMeshAnimationClips(select,catalog,index){
  select.replaceChildren();for(const row of catalog.clips){const option=document.createElement('option');option.value=String(row.animation_index);option.textContent=`Clip ${row.animation_index}${row.name?' · '+row.name:''} · ${row.channel_count} channels`;select.append(option);}
  if(!catalog.clips.some(row=>row.animation_index===index)){const option=document.createElement('option');option.value=String(index);option.textContent=catalog.clips.length?`Clip ${index} unavailable — choose an existing source clip`:'No source animation clips';option.disabled=true;select.append(option);}
  select.value=String(index);
}

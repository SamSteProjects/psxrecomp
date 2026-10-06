// Read-only recovery of original inputs retained by reviewed native imports.
const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
export function decodeMeshSources(value,asset,key){
  if(value?.schema_version!=='legaia.model-mesh-sources.v1'||value.asset_id!==asset||value.project_source_key!==key||value.project_changed!==false||!Array.isArray(value.imports)||value.imports.length>32)throw Error('Mesh source catalogue differs from Current.');
  for(const row of value.imports)if(row.asset_id!==asset||row.schema_version!=='legaia.model-mesh-source.v1'||!hash(row.glb_sha256)||!hash(row.receipt_key)||!Number.isSafeInteger(row.byte_length)||row.byte_length<28||row.byte_length>32*1024*1024||!['single','batch'].includes(row.recipe?.kind))throw Error('Invalid retained mesh source receipt.');
  return value;
}
function save(bytes,name,type){const url=URL.createObjectURL(new Blob([bytes],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export async function openMeshSources({assetId,key,current,onError}){
  const dialog=document.createElement('dialog');dialog.className='diagnostic-dialog';
  const heading=document.createElement('h2');heading.textContent='Retained mesh sources';
  const note=document.createElement('p');note.textContent='Original GLBs and import settings from Current native mesh imports. Settings describe the original import; reviewing a new import requires choosing Current donors.';
  const status=document.createElement('p');status.role='status';status.textContent='Checking retained inputsâ€¦';
  const list=document.createElement('section'),close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();dialog.onclose=()=>dialog.remove();dialog.append(heading,note,status,list,close);document.body.append(dialog);dialog.showModal();
  const live=()=>dialog.isConnected&&current();
  async function request(route,extra={}){if(!live())throw Error('Current model context changed.');const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({asset_id:assetId,source_key:key,...extra})}),value=await response.json();if(!response.ok)throw Error(value.error||'Mesh source recovery failed.');if(!live())throw Error('Current model context changed.');return decodeMeshSources(value,assetId,key);}
  try{const value=await request('/api/model-mesh-sources');status.textContent=value.imports.length?`${value.imports.length} retained import(s).`:'No retained original GLBs in Current. Older imports may contain native geometry only.';
    for(const [i,row] of value.imports.entries()){const host=document.createElement('section'),label=document.createElement('p'),settings=document.createElement('details'),summary=document.createElement('summary'),code=document.createElement('pre');label.textContent=`Import ${i+1} | ${row.recipe.kind} | ${row.byte_length} bytes | GLB ${row.glb_sha256}`;summary.textContent='Import settings';code.textContent=JSON.stringify(row.recipe,null,2);code.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';settings.append(summary,code);
      const glb=document.createElement('button');glb.textContent='Download original GLB';glb.onclick=async()=>{glb.disabled=true;try{const result=await request('/api/model-mesh-source-download',{receipt_key:row.receipt_key});if(result.selected?.receipt_key!==row.receipt_key||result.selected.glb_sha256!==row.glb_sha256||typeof result.content_base64!=='string')throw Error('Downloaded source receipt changed.');const bytes=Uint8Array.from(atob(result.content_base64),c=>c.charCodeAt(0));if(bytes.length!==row.byte_length)throw Error('Downloaded source length changed.');const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');if(digest!==row.glb_sha256||!live())throw Error('Downloaded source or Current context changed.');save(bytes,`${row.glb_sha256}.glb`,'model/gltf-binary');status.textContent='Original GLB downloaded.';}catch(error){status.textContent=error.message;onError(error);}finally{glb.disabled=!live();}};
      const recipe=document.createElement('button');recipe.textContent='Download import receipt';recipe.onclick=()=>{if(!live()){status.textContent='Current model context changed.';return;}save(JSON.stringify(row,null,2),`${row.receipt_key}.json`,'application/json');};host.append(label,settings,glb,recipe);list.append(host);
    }
  }catch(error){if(dialog.isConnected){status.textContent=error.message;onError(error);}}
  return dialog;
}

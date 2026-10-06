// Metadata evidence only: exporting never opens a source tool or authors bytes.
const KINDS=new Set(['audio','actor','scene','template','worldmap','model','texture','animation','script','dialogue','flag','transition','collision','trigger','region']);
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const metadata=(value,depth=0,seen=new Set())=>{
  if(depth>64)throw new Error('Asset evidence exceeds the metadata depth limit.');
  if(value===null||typeof value==='string'||typeof value==='boolean')return;
  if(typeof value==='number'&&Number.isFinite(value))return;
  if(typeof value!=='object'||seen.has(value)||(!Array.isArray(value)&&![Object.prototype,null].includes(Object.getPrototypeOf(value))))throw new Error('Asset evidence requires finite, acyclic JSON metadata.');
  seen.add(value);
  if(Array.isArray(value)){
    for(let i=0;i<value.length;i++){if(!Object.hasOwn(value,i))throw new Error('Asset evidence requires dense JSON arrays.');metadata(value[i],depth+1,seen);}
  }else for(const item of Object.values(value)){if(item!==undefined)metadata(item,depth+1,seen);}
  seen.delete(value);
};
export function assetEvidenceContext(state){
  if(!hash(state?.asset_reference_source_key)||typeof state?.project?.path!=='string'||!state.project.path)throw new Error('Asset evidence source identity is unavailable.');
  return {source_key:state.asset_reference_source_key,project_assets_source_key:state.project_assets_source_key??null,
    build_input_key:state.build_review_source_key??null,project_path:state.project.path,project_name:state.project.name??null,
    active_scene_id:state.scene?.id??null,authored_assets:state.authored_assets??[]};
}
export function assetRecordDownload(record,context){
  if(!KINDS.has(record?.type)||typeof record.id!=='string'||record.id.length>1024||!/^[a-z][a-z0-9-]*:\/\/[^\s\x00-\x20\x7f<>"']+$/.test(record.id)||!hash(context?.source_key))throw new Error('Asset evidence requires a supported stable record identity and current source key.');
  const report={schema_version:'legaia.asset-record-evidence.v1',read_only:true,source_context:context,record,
    limitations:['This is the selected editor catalog metadata snapshot, not a native payload, editable interchange file or Build package.',
      'Imported data, authored settings and separate project source memberships retain their original fields. Memberships and bindings do not prove runtime use.',
      'Source keys identify recorded inputs and observed source freshness; exporting does not reread or verify every native payload. Gameplay remains unverified.']};
  metadata(report);
  const text=JSON.stringify(report,null,2)+'\n';
  if(new TextEncoder().encode(text).byteLength>32*1024*1024)throw new Error('Asset evidence download exceeds 32 MiB.');
  return {text,filename:`legaia-asset-${record.type}-${context.source_key.slice(0,16)}.json`};
}
export function mountAssetRecordDownload(host,{record,getState,current,busy,onError,request=fetch}){
  const context=assetEvidenceContext(getState()),snapshot=JSON.stringify(context);
  // Qualify the immutable export now, so unsupported metadata never enables it.
  const file=assetRecordDownload(record,context),button=document.createElement('button'),status=document.createElement('p');
  button.textContent='Save asset evidence…';button.dataset.assetRecordDownload='';status.setAttribute('role','status');status.className='field-note';
  host.append(button,status);let pending=false;
  const fresh=()=>current()&&snapshot===JSON.stringify(assetEvidenceContext(getState()));
  button.onclick=async()=>{
    if(busy()||pending)return;
    try{
      if(!fresh())throw new Error('Asset source or membership changed. Reopen asset details.');
      pending=true;button.disabled=true;status.textContent='Checking current project inputs…';
      const response=await request('/api/state',{cache:'no-store'});
      if(!response.ok)throw new Error('Could not check current asset inputs. Reopen asset details.');
      const latest=await response.json();
      if(!fresh()||snapshot!==JSON.stringify(assetEvidenceContext(latest)))throw new Error('Asset source or membership changed. Reopen asset details.');
      const url=URL.createObjectURL(new Blob([file.text],{type:'application/json;charset=utf-8'})),link=document.createElement('a');
      try{link.href=url;link.download=file.filename;document.body.append(link);link.click();}finally{link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
      status.textContent='Saved selected asset metadata evidence. Gameplay remains unverified.';button.disabled=false;
    }catch(error){status.textContent=error.message;button.disabled=true;onError(error);}
    finally{pending=false;}
  };
  return button;
}

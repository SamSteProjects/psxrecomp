// Recover exact original input bytes for an older texture receipt.
export function qualifyRetention(report, request, receipt, byteLength, applied=false){
  if(!report||report.schema_version!=='legaia.texture-source-retention.v1'||report.asset_id!==request.asset_id||report.effective_sha256!==request.expected_sha256||report.project_source_key!==request.source_key||report.native_bytes_changed!==false||report.project_changed!==applied||report.gameplay_verified!==false||!/^[a-f0-9]{64}$/.test(report.review_key)||!report.source||Object.keys(report.source).length!==5||report.source.glb_byte_length!==byteLength||Object.keys(receipt).some(k=>report.source[k]!==receipt[k]))throw new Error('Original source review differs from this texture or file.');
  return report;
}

export function openTextureSourceRetention({assetId,binding,getContext,busy,setBusy,onApplied}){
  const context=JSON.stringify(getContext()),receipt=structuredClone(binding.glb_source);
  const dialog=document.createElement('dialog');dialog.innerHTML='<h2>Retain original GLB source</h2><p>Choose the exact original GLB recorded in this texture receipt. This adds a recoverable source file and leaves all native texture bytes unchanged. It does not reconstruct the original palette or STP import settings.</p><label>Original GLB file<input type="file" accept=".glb" aria-label="Original GLB file"></label><p data-status></p><button data-review disabled>Review original source</button><button data-apply disabled>Retain reviewed source</button><button data-close>Close</button><p role="alert"></p>';
  document.body.append(dialog);const input=dialog.querySelector('input'),reviewButton=dialog.querySelector('[data-review]'),applyButton=dialog.querySelector('[data-apply]'),closeButton=dialog.querySelector('[data-close]'),status=dialog.querySelector('[data-status]'),error=dialog.querySelector('[role=alert]');
  let reviewed=null,request=null,selected=null,pending=false;
  const current=()=>dialog.open&&context===JSON.stringify(getContext())&&getContext().mode==='edit'&&input.files[0]===selected;
  const controls=()=>{input.disabled=pending;reviewButton.disabled=pending||!input.files[0]||busy();applyButton.disabled=pending||!reviewed||!current()||busy();closeButton.disabled=pending;};
  const post=async(route,body)=>{const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw new Error(result.error||'Original source request failed');return result;};
  input.onchange=()=>{reviewed=null;request=null;selected=input.files[0];status.textContent='Review the selected file before retaining it.';error.textContent='';controls();};
  reviewButton.onclick=async()=>{if(pending||busy())return;reviewed=null;selected=input.files[0];pending=true;setBusy(true);controls();error.textContent='';try{
    if(!current()||!selected||selected.size<28||selected.size>32*1024*1024)throw new Error('Choose the original GLB, at most 32 MiB, in the current Edit context.');
    const bytes=new Uint8Array(await selected.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
    request={asset_id:assetId,expected_sha256:binding.asset_sha256,source_key:getContext().sourceKey,content_base64:btoa(binary)};
    const report=await post('/api/texture-glb-retain-review',request);if(!current())throw new Error('Texture context changed; reopen source retention.');
    reviewed=qualifyRetention(report,request,receipt,selected.size);status.textContent=`Verified original GLB: ${receipt.glb_sha256}. Native texture bytes unchanged. Retain, then Save project.`;
  }catch(e){reviewed=null;error.textContent=e.message;}finally{pending=false;setBusy(false);controls();}};
  applyButton.onclick=async()=>{if(pending||busy()||!reviewed||!current())return;pending=true;setBusy(true);controls();error.textContent='';try{
    const key=reviewed.review_key,next=await post('/api/texture-glb-retain',{...request,review_key:key});
    qualifyRetention(next.retention_report,request,receipt,selected.size,true);if(next.retention_report.review_key!==key||!current())throw new Error('Retention response changed; refresh the project.');
    dialog.close();onApplied(next);
  }catch(e){reviewed=null;error.textContent=e.message;}finally{pending=false;setBusy(false);controls();}};
  closeButton.onclick=()=>dialog.close();dialog.oncancel=e=>{if(pending)e.preventDefault();};dialog.onclose=()=>dialog.remove();dialog.showModal();controls();return dialog;
}

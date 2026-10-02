const hash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
export function decodeBuildHistory(value){
  if(!Array.isArray(value?.builds)||value.builds.length>256||typeof value.truncated!=='boolean'||value.coverage!=='project_Builds_only_identity_order')throw new Error('Invalid saved Build history');
  const seen=new Set();
  for(const row of value.builds){
    if(!row||typeof row.id!=='string'||!/^[0-9a-f]{16}$/.test(row.id)||seen.has(row.id)||!['completed','legacy_or_incomplete','invalid'].includes(row.status)||row.gameplay_verified!==false)throw new Error('Invalid saved Build entry');
    seen.add(row.id);
    if(row.status==='completed'&&(typeof row.matches_current_inputs!=='boolean'||row.integrity!=='not_checked'||!hash(row.archive_sha256)||!hash(row.source_disc_sha256)||!['retail','authored'].includes(row.build_kind)||!Number.isSafeInteger(row.change_count)||row.change_count<0||typeof row.archive_path!=='string'))throw new Error('Invalid saved Build receipt');
  }
  return structuredClone(value);
}
export function decodeBuildVerification(value,id){
  const r=value?.report;
  if(value?.id!==id||value.integrity!=='verified'||value.gameplay_verified!==false||typeof value.matches_current_inputs!=='boolean'||value.source_disc_integrity!=='not_checked'||value.runtime_status!=='package_built_not_launched'||value.scope!=='receipt_audit_manifest_package_source_files_and_ZIP_members'||r?.schema_version!=='legaia.build-report.v1'||!Array.isArray(r.changes)||r.changes.length>65536||r.change_count!==r.changes.length||!Number.isSafeInteger(r.overlay_bytes)||r.overlay_bytes<0||r.validation?.live_runtime!=='not_run')throw new Error('Invalid saved Build verification');
  for(const row of r.changes)if(!row||!['asset_id','scene','field','scope'].every(key=>typeof row[key]==='string')||!('before' in row)||!('after' in row))throw new Error('Invalid saved Build change');
  return structuredClone(value);
}
export function mountBuildHistory({after,getState,busy,setBusy}){
  const button=document.createElement('button');button.id='build-history-button';button.textContent='Build history';after.after(button);
  button.onclick=async()=>{
    if(busy())return;
    const initial=getState(),root=initial.project.path,key=initial.build_review_source_key;
    const dialog=document.createElement('dialog');dialog.id='build-history-dialog';dialog.className='project-dialog';dialog.style.width='min(1100px,90vw)';dialog.style.maxWidth='90vw';
    const title=document.createElement('h2');title.textContent='Saved Builds';const status=document.createElement('p');status.setAttribute('role','status');status.textContent='Loading saved completion receipts…';
    const list=document.createElement('div');list.style.maxHeight='60vh';list.style.overflow='auto';const close=document.createElement('button');close.textContent='Close';close.onclick=()=>dialog.close();const controller=new AbortController();
    dialog.append(title,status,list,close);document.body.append(dialog);dialog.showModal();dialog.addEventListener('close',()=>{controller.abort();dialog.remove();});
    const context=()=>dialog.open&&getState().project.path===root&&getState().build_review_source_key===key;
    const request=async(route,body)=>{if(!context())throw new Error('Project inputs changed. Reopen Build history.');const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});const value=await response.json();if(!response.ok)throw new Error(value.error||'Saved Build request failed');if(!context())throw new Error('Project inputs changed. Reopen Build history.');return value;};
    setBusy(true);
    try{
      const result=decodeBuildHistory(await request('/api/builds',{}));
      status.textContent=result.builds.length?`${result.builds.length} saved Build entries in identity order${result.truncated?' · bounded scan; additional entries may be omitted':''}. File integrity is checked separately. Gameplay remains unverified.`:'No normal Builds saved in this project. Choose Build to create a package and completion receipt.';
      for(const item of result.builds){
        const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=item.id;section.append(heading);
        const summary=document.createElement('p');section.append(summary);
        if(item.status!=='completed'){summary.textContent=item.status==='legacy_or_incomplete'?'No completion receipt: older or incomplete Build. Input match and integrity unavailable. Rebuild to record a receipt.':`Invalid saved Build: ${item.error||'Metadata could not be read'}`;list.append(section);continue;}
        summary.textContent=`${item.build_kind==='retail'?'Retail baseline':'Authored package'} · ${item.change_count} audited changes · ${item.matches_current_inputs?'Matches current authored inputs':'Different authored inputs'}`;
        const provenance=document.createElement('details'),label=document.createElement('summary'),paths=document.createElement('pre');label.textContent='Saved package and recorded hashes';paths.style.overflowWrap='anywhere';paths.style.whiteSpace='pre-wrap';paths.textContent=`Package: ${item.archive_path}\nArchive SHA-256: ${item.archive_sha256}\nSource disc SHA-256: ${item.source_disc_sha256}`;provenance.append(label,paths);section.append(provenance);
        const check=document.createElement('button');check.textContent='Verify saved files and open report';const outcome=document.createElement('p');outcome.setAttribute('role','status');outcome.textContent='Package integrity not checked. Source disc and gameplay not checked.';const report=document.createElement('div');
        check.onclick=async()=>{
          if(busy())return;check.disabled=true;setBusy(true);outcome.textContent='Checking receipt, audit, manifest, payload files and package ZIP…';report.replaceChildren();
          try{const verified=decodeBuildVerification(await request('/api/builds/verify',{id:item.id}),item.id);outcome.textContent=`Saved package integrity verified · ${verified.matches_current_inputs?'matches current authored inputs':'different authored inputs'}. Source disc integrity and gameplay remain unverified.`;
            const counts=document.createElement('p');counts.textContent=`${verified.report.change_count} changes · ${verified.report.overlay_bytes.toLocaleString()} overlay bytes`;report.append(counts);
            const table=document.createElement('table');table.className='build-change-table';const head=document.createElement('tr');for(const name of ['Asset','Field','Before','After']){const cell=document.createElement('th');cell.textContent=name;head.append(cell);}table.append(head);
            for(const change of verified.report.changes.slice(0,256)){const row=document.createElement('tr');for(const value of [change.asset_id,change.field,change.before,change.after]){const cell=document.createElement('td');cell.style.overflowWrap='anywhere';cell.textContent=typeof value==='string'?value:JSON.stringify(value);row.append(cell);}table.append(row);}const wrap=document.createElement('div');wrap.style.overflowX='auto';wrap.append(table);report.append(wrap);
            if(verified.report.changes.length>256){const note=document.createElement('p');note.textContent='First 256 changes shown; the saved audit retains the full report.';report.append(note);}
          }catch(error){if(context())outcome.textContent=`Verification failed: ${error.message}`;}finally{check.disabled=false;setBusy(false);}
        };
        section.append(check,outcome,report);list.append(section);
      }
    }catch(error){if(dialog.open)status.textContent=`Could not load saved Builds: ${error.message}`;}finally{setBusy(false);}
  };
}

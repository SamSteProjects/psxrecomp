import {decodeBuildRuntimeSources,renderBuildRuntimeSources} from './sdk-stability-sources.js';
import {openBuildWavs} from './build-wav-inputs.js';
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
export function decodeBuildDelivery(value){
  const exact=(row,keys)=>row&&typeof row==='object'&&!Array.isArray(row)&&Object.keys(row).length===keys.length&&keys.every(key=>Object.hasOwn(row,key));
  const count=value=>Number.isSafeInteger(value)&&value>=0;
  if(!exact(value,['schema_version','representation','embedded_overlay_count','payload_bytes','files'])||value.schema_version!=='legaia.build-delivery.v1'||!['disc_relocation','standalone_overlays'].includes(value.representation)||!count(value.embedded_overlay_count)||value.embedded_overlay_count>4096||!count(value.payload_bytes)||!Array.isArray(value.files)||value.files.length>4096)throw new Error('Invalid delivered Build payload inventory');
  const relocation=value.representation==='disc_relocation',seen=new Set();let bytes=0;
  for(const row of value.files){
    if(!exact(row,['file','sha256','size','kind'])||typeof row.file!=='string'||!/^assets\/[A-Za-z0-9_.-]+$/.test(row.file)||seen.has(row.file)||!hash(row.sha256)||!count(row.size)||row.size<(relocation?96:1)||row.size>(relocation?256:64)*1024*1024||row.kind!==(relocation?'disc_relocation':'overlay'))throw new Error('Invalid delivered Build payload file');
    seen.add(row.file);bytes+=row.size;
  }
  if(bytes!==value.payload_bytes||relocation&&value.files.length!==1||!relocation&&value.embedded_overlay_count!==0)throw new Error('Delivered Build payload totals or representation differ');
  return structuredClone(value);
}
export function appendBuildDelivery(host,value){
  if(value===undefined){const note=document.createElement('p');note.textContent='Delivered file inventory is unavailable from this server.';host.append(note);return;}
  const delivery=decodeBuildDelivery(value),heading=document.createElement('h3');heading.textContent='Delivered payload files';host.append(heading);
  const note=document.createElement('p');note.textContent=delivery.representation==='disc_relocation'?`One relocation payload (${delivery.payload_bytes.toLocaleString()} bytes) embeds ${delivery.embedded_overlay_count} audited overlay region(s). Those edits are not separate files in this package.`:`${delivery.files.length} standalone overlay file(s), ${delivery.payload_bytes.toLocaleString()} payload bytes.`;host.append(note);
  const table=document.createElement('table');table.className='build-change-table';const header=document.createElement('tr');for(const text of ['File','Bytes','SHA-256']){const cell=document.createElement('th');cell.textContent=text;header.append(cell);}table.append(header);
  for(const file of delivery.files.slice(0,256)){const row=document.createElement('tr');for(const value of [file.file,file.size.toLocaleString(),file.sha256]){const cell=document.createElement('td');cell.style.overflowWrap='anywhere';cell.textContent=value;row.append(cell);}table.append(row);}
  const wrap=document.createElement('div');wrap.style.overflowX='auto';wrap.append(table);host.append(wrap);
  if(delivery.files.length>256){const note=document.createElement('p');note.textContent='First 256 payload files shown; the verified inventory contains all files.';host.append(note);}
}
export function decodeBuildVerification(value,id){
  const r=value?.report;
  if(value?.id!==id||value.integrity!=='verified'||value.gameplay_verified!==false||typeof value.matches_current_inputs!=='boolean'||value.source_disc_integrity!=='not_checked'||value.runtime_status!=='package_built_not_launched'||value.scope!=='receipt_audit_manifest_package_source_files_and_ZIP_members'||r?.schema_version!=='legaia.build-report.v1'||!Array.isArray(r.changes)||r.changes.length>65536||r.change_count!==r.changes.length||!Number.isSafeInteger(r.overlay_bytes)||r.overlay_bytes<0||r.validation?.live_runtime!=='not_run')throw new Error('Invalid saved Build verification');
  if(r.validation.runtime_source_inclusion!==undefined)decodeBuildRuntimeSources(r.validation.runtime_source_inclusion);
  for(const row of r.changes)if(!row||!['asset_id','scene','field','scope'].every(key=>typeof row[key]==='string')||!('before' in row)||!('after' in row))throw new Error('Invalid saved Build change');
  if(value.delivery!==undefined)decodeBuildDelivery(value.delivery);
  return structuredClone(value);
}
export function decodeBuildVerificationForEntry(value,entry,key){
  if(!hash(key)||entry?.status!=='completed'||!/^[a-f0-9]{16}$/.test(entry.id)||!hash(entry.archive_sha256)||!hash(entry.source_disc_sha256)||!['retail','authored'].includes(entry.build_kind)||!Number.isSafeInteger(entry.change_count)||entry.change_count<0)throw new Error('Unsupported saved Build receipt identity.');
  const verified=decodeBuildVerification(value,entry.id),receipt=verified.receipt;
  if(!receipt||!hash(receipt.authored_state_key)||receipt.archive_sha256!==entry.archive_sha256||receipt.source_disc_sha256!==entry.source_disc_sha256||receipt.build_kind!==entry.build_kind||verified.report.change_count!==entry.change_count||verified.matches_current_inputs!==(receipt.authored_state_key===key))throw new Error('Saved Build receipt or current inputs changed. Reopen Build history.');
  return verified;
}
export function decodeBuildComparison(value,left,right,key){
  if(value?.schema_version!=='legaia.build-comparison.v1'||value.left_id!==left||value.right_id!==right||left===right||value.project_source_key!==key||!hash(key)||!hash(value.source_disc_sha256)||value.integrity!=='both_packages_verified'||value.gameplay_verified!==false||value.source_disc_integrity!=='not_checked'||value.comparison_scope!=='saved_audit_records_only'||!Array.isArray(value.differences)||value.differences.length>65536||value.difference_count!==value.differences.length||!Number.isSafeInteger(value.unchanged_change_count)||value.unchanged_change_count<0)throw new Error('Invalid or stale saved Build comparison');
  for(const row of value.differences){if(!['only_left_audit','only_right_audit','different_audit'].includes(row.status)||!['scene','owner_id','asset_id','field','scope'].every(k=>typeof row.identity?.[k]==='string')||row.status==='only_left_audit'&&(row.left===null||row.right!==null)||row.status==='only_right_audit'&&(row.right===null||row.left!==null)||row.status==='different_audit'&&(!row.left||!row.right))throw new Error('Invalid compared audit record');for(const side of ['left','right'])if(row[side]!==null&&(!row[side]||!('before' in row[side])||!('after' in row[side])))throw new Error('Missing compared audit values');}
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
    let wavRecovery=null;dialog.addEventListener('close',()=>wavRecovery?.dispose());
    const context=()=>dialog.open&&getState().project.path===root&&getState().build_review_source_key===key;
    const request=async(route,body)=>{
      if(!context())throw new Error('Project inputs changed. Reopen Build history.');
      const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
      const value=await response.json();if(!response.ok)throw new Error(value.error||'Saved Build request failed');
      if(!context())throw new Error('Project inputs changed. Reopen Build history.');
      const currentResponse=await fetch('/api/state',{cache:'no-store',signal:controller.signal});
      if(!currentResponse.ok)throw new Error('Could not qualify current server inputs. Reopen Build history.');
      const latest=await currentResponse.json();
      if(!context()||latest.project?.path!==root||latest.build_review_source_key!==key||!hash(key))throw new Error('Server project inputs changed. Reopen Build history.');
      return value;
    };
    setBusy(true);
    try{
      const result=decodeBuildHistory(await request('/api/builds',{}));
      status.textContent=result.builds.length?`${result.builds.length} saved Build entries in identity order${result.truncated?' · bounded scan; additional entries may be omitted':''}. File integrity is checked separately. Gameplay remains unverified.`:'No normal Builds saved in this project. Choose Build to create a package and completion receipt.';
      const completed=result.builds.filter(item=>item.status==='completed');
      const packageOutcomes=new Map();
      if(completed.length>=2){
        const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent='Compare saved audits';const left=document.createElement('select'),right=document.createElement('select');left.id='build-compare-left';right.id='build-compare-right';left.setAttribute('aria-label','Left saved Build');right.setAttribute('aria-label','Right saved Build');
        for(const item of completed)for(const select of [left,right]){const option=document.createElement('option');option.value=item.id;option.textContent=`${item.id} · ${item.change_count} changes`;select.append(option);}right.selectedIndex=1;
        const compare=document.createElement('button');compare.id='build-compare-button';compare.textContent='Verify both and compare';const outcome=document.createElement('p');outcome.setAttribute('role','status');outcome.textContent='Compares saved audit records. Absence from an audit does not prove a runtime value or deletion.';const report=document.createElement('div');
        compare.onclick=async()=>{if(busy())return;const a=left.value,b=right.value;if(a===b){outcome.textContent='Choose two different saved Builds.';return;}setBusy(true);compare.disabled=true;outcome.textContent='Verifying both saved packages and comparing their audits…';report.replaceChildren();
          try{const value=decodeBuildComparison(await request('/api/builds/compare',{left_id:a,right_id:b}),a,b,key);outcome.textContent=`Both saved packages verified · ${value.difference_count} different audit records · ${value.unchanged_change_count} identical records. Source disc integrity and gameplay remain unverified.`;for(const id of [a,b])if(packageOutcomes.has(id))packageOutcomes.get(id).textContent='Package integrity verified during comparison. Source disc and gameplay remain unverified.';
            const note=document.createElement('p');note.textContent=value.limitation;report.append(note);const table=document.createElement('table');table.className='build-change-table';table.style.width='100%';const heading=document.createElement('tr');for(const name of ['Asset / field','Left audit','Right audit']){const cell=document.createElement('th');cell.style.padding='.4rem .75rem';cell.style.textAlign='left';cell.textContent=name;heading.append(cell);}table.append(heading);
            for(const change of value.differences.slice(0,256)){const row=document.createElement('tr'),label=document.createElement('td');label.style.overflowWrap='anywhere';label.textContent=`${change.identity.asset_id} · ${change.identity.field}`+(change.frame_index===null?'':` · frame ${change.frame_index}, object ${change.object_index}`);row.append(label);for(const side of ['left','right']){const cell=document.createElement('td');cell.style.overflowWrap='anywhere';const item=change[side];cell.textContent=item?`${JSON.stringify(item.before)} → ${JSON.stringify(item.after)}`:'Not recorded in this audit';row.append(cell);}const detail=document.createElement('details'),summary=document.createElement('summary'),data=document.createElement('pre');summary.textContent='Full compared record';data.style.whiteSpace='pre-wrap';data.textContent=JSON.stringify(change,null,2);detail.append(summary,data);label.append(detail);table.append(row);}const wrap=document.createElement('div');wrap.style.overflowX='auto';wrap.append(table);report.append(wrap);if(value.difference_count>256){const note=document.createElement('p');note.textContent='First 256 differences shown; counts cover the full comparison.';report.append(note);}
            for(const cell of table.querySelectorAll('td'))cell.style.padding='.4rem .75rem';
          }catch(error){if(context()){outcome.textContent=`Comparison failed: ${error.message}`;for(const id of [a,b])if(packageOutcomes.has(id))packageOutcomes.get(id).textContent='Comparison verification failed. Recheck saved package integrity. Source disc and gameplay unverified.';}}finally{setBusy(false);compare.disabled=false;}
        };const leftLabel=document.createElement('label'),rightLabel=document.createElement('label');leftLabel.textContent='Left audit ';rightLabel.textContent='Right audit ';leftLabel.append(left);rightLabel.append(right);section.append(heading,leftLabel,rightLabel,compare,outcome,report);list.append(section);
      }
      for(const item of result.builds){
        const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=item.id;section.append(heading);
        const summary=document.createElement('p');section.append(summary);
        if(item.status!=='completed'){summary.textContent=item.status==='legacy_or_incomplete'?'No completion receipt: older or incomplete Build. Input match and integrity unavailable. Rebuild to record a receipt.':`Invalid saved Build: ${item.error||'Metadata could not be read'}`;list.append(section);continue;}
        summary.textContent=`${item.build_kind==='retail'?'Retail baseline':'Authored package'} · ${item.change_count} audited changes · ${item.matches_current_inputs?'Matched inputs when listed':'Different inputs when listed'}`;
        const provenance=document.createElement('details'),label=document.createElement('summary'),paths=document.createElement('pre');label.textContent='Saved package and recorded hashes';paths.style.overflowWrap='anywhere';paths.style.whiteSpace='pre-wrap';paths.textContent=`Package: ${item.archive_path}\nArchive SHA-256: ${item.archive_sha256}\nSource disc SHA-256: ${item.source_disc_sha256}`;provenance.append(label,paths);section.append(provenance);
        const check=document.createElement('button');check.textContent='Verify saved files and open report';const outcome=document.createElement('p');outcome.setAttribute('role','status');outcome.textContent='Package integrity not checked. Source disc and gameplay not checked.';const report=document.createElement('div');
        packageOutcomes.set(item.id,outcome);
        check.onclick=async()=>{
          if(busy())return;check.disabled=true;setBusy(true);outcome.textContent='Checking receipt, audit, manifest, payload files and package ZIP…';report.replaceChildren();
          try{const verified=decodeBuildVerificationForEntry(await request('/api/builds/verify',{id:item.id}),item,key);outcome.textContent=`Saved package integrity verified · ${verified.matches_current_inputs?'matches current authored inputs':'different authored inputs'}. Source disc integrity and gameplay remain unverified.`;
            const counts=document.createElement('p');counts.textContent=`${verified.report.change_count} changes · ${verified.report.overlay_bytes.toLocaleString()} audited fixed-span bytes`;report.append(counts);appendBuildDelivery(report,verified.delivery);renderBuildRuntimeSources(report,verified.report.validation.runtime_source_inclusion);
            const table=document.createElement('table');table.className='build-change-table';const head=document.createElement('tr');for(const name of ['Asset','Field','Before','After']){const cell=document.createElement('th');cell.textContent=name;head.append(cell);}table.append(head);
            for(const change of verified.report.changes.slice(0,256)){const row=document.createElement('tr');for(const value of [change.asset_id,change.field,change.before,change.after]){const cell=document.createElement('td');cell.style.overflowWrap='anywhere';cell.textContent=typeof value==='string'?value:JSON.stringify(value);row.append(cell);}table.append(row);}const wrap=document.createElement('div');wrap.style.overflowX='auto';wrap.append(table);report.append(wrap);
            if(verified.report.changes.length>256){const note=document.createElement('p');note.textContent='First 256 changes shown; the saved audit retains the full report.';report.append(note);}
          }catch(error){if(context())outcome.textContent=`Verification failed: ${error.message}`;}finally{check.disabled=false;setBusy(false);}
        };
        const wav=document.createElement('button');wav.textContent='Browse saved WAV inputs';wav.onclick=()=>{if(busy()||!context())return;wavRecovery?.dispose();wavRecovery=openBuildWavs({entry:item,key,fresh:context});};section.append(check,wav,outcome,report);list.append(section);
      }
    }catch(error){if(dialog.open)status.textContent=`Could not load saved Builds: ${error.message}`;}finally{setBusy(false);}
  };
}

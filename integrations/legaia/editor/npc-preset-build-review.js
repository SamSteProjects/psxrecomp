import {decodeBuildReview} from './build-review.js';
const canonical=value=>JSON.stringify(value&&typeof value==='object'?Array.isArray(value)?value.map(v=>JSON.parse(canonical(v))):Object.fromEntries(Object.keys(value).sort().map(k=>[k,JSON.parse(canonical(value[k]))])):value);

export function decodeNpcPresetBuildReview(value,accepted,existingCount){
  if(value?.schema_version!=='legaia.npc-preset-build-review.v1'||canonical(value.review)!==canonical(accepted)||value.read_only!==true||value.project_changed!==false||value.output_written!==false||value.gameplay_verified!==false||value.assessment_scope!=='complete_supported_project_with_one_preset_instance'||!Number.isSafeInteger(existingCount)||existingCount<0||value.existing_npc_draft_count!==existingCount||value.proposed_npc_draft_count!==existingCount+1||!Number.isSafeInteger(value.proposed_npc_draft_count)||value.proposed_npc_draft_count>8192||!/^[a-f0-9]{64}$/.test(value.prospective_build_source_key??''))throw Error('NPC preset Build review has stale inputs, incomplete coverage or unsupported mutation claims.');
  const build=decodeBuildReview(value.build_review,value.prospective_build_source_key);
  if(build.schema_version!=='legaia.build-review.v2'||build.included_npc_draft_count!==value.proposed_npc_draft_count)throw Error('Preset instance is missing from the complete project Build review.');
  return structuredClone(value);
}

export function renderNpcPresetBuildReview(container,value){
  const build=value.build_review;container.replaceChildren();container.hidden=false;
  const status=document.createElement('p');status.setAttribute('role','status');status.textContent=build.normal_build_ready?'Proposed inputs passed source serialization and package-fit review. NPC not created; package not written; gameplay unverified.':`Proposed project Build is blocked (${build.blockers.length} blocker(s)). NPC not created; package not written.`;container.append(status);
  const scope=document.createElement('p');scope.textContent=`${value.existing_npc_draft_count} existing NPC draft(s) + 1 prospective preset instance. ${build.assessment?'All supported authored inputs were assessed.':'Serialization stopped at a blocker; later inputs are not claimed to have passed.'} Apply the instance and review the saved project again before Build.`;container.append(scope);
  for(const row of build.blockers){const p=document.createElement('p');p.textContent=row.message;p.className='dialog-error';p.style.overflowWrap='anywhere';container.append(p);}
  const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Build review scope and limitations';details.append(summary);for(const text of build.limitations){const p=document.createElement('p');p.textContent=text;details.append(p);}container.append(details);
}

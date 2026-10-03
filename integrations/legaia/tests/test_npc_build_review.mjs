import assert from 'node:assert/strict';
import {decodeBuildReview} from '../editor/build-review.js';

const key='a'.repeat(64);
const review=()=>({schema_version:'legaia.build-review.v2',source_key:key,read_only:true,
  status:'ready_for_build',normal_build_ready:true,blockers:[],excluded_npc_draft_count:0,included_npc_draft_count:2,
  assessment_scope:'all_supported_authored_content_including_source_qualified_npc_drafts',
  npc_build_scope:'fixed_span_compressed_man_source_candidates',npc_gameplay_verified:false,
  limitations:['Source candidates; no gameplay acceptance.'],assessment:{output_written:false,
    archive_packing:'not_run',runtime_status:'not_run',audit_sha256:key,manifest_sha256:key,source_disc_sha256:key,
    overlay_count:1,build_kind:'authored',change_kinds:['npc_draft'],report:{schema_version:'legaia.build-report.v1',
      change_count:2,scene_count:1,overlay_bytes:128,validation:{retail_provenance:'fresh_import_match',live_runtime:'not_run',unchanged_opaque_bytes:true},
      changes:[{owner_id:'draft://fixture/one',field:'npc.appended_record',scope:'source-man-donor-append-candidate',before:null,after:{source_record_index:2}},
        {owner_id:'scene://fixture',field:'npc.composed_candidate',scope:'source-man-draft-composed-overrides',
          before:null,after:1,composition_changes:[{kind:'facing',opaque_audit:{word_offset:17}}]}]}}});

const source=review(),snapshot=JSON.stringify(source),decoded=decodeBuildReview(source,key);
assert.deepEqual(decoded,source);decoded.assessment.report.changes[1].composition_changes[0].opaque_audit.word_offset=99;
assert.equal(JSON.stringify(source),snapshot,'Review detaches candidate audits without authoring state.');
const blocked=review();Object.assign(blocked,{status:'blocked',normal_build_ready:false,assessment:null,
  blockers:[{kind:'serialization',owner_id:null,message:'Fixed source span does not fit requested candidates.'}]});
assert.equal(decodeBuildReview(blocked,key).included_npc_draft_count,2,'Blocked coverage counts requested candidates, without claiming validation.');
const qualifiedBlock=review();Object.assign(qualifiedBlock,{status:'blocked',normal_build_ready:false,
  blockers:[{kind:'npc_draft',owner_id:'draft://fixture/one',message:'Source donor qualification failed.'}]});
assert.equal(decodeBuildReview(qualifiedBlock,key).excluded_npc_draft_count,0);
for(const mutate of [
  r=>r.schema_version='legaia.build-review.v3',r=>r.included_npc_draft_count=-1,
  r=>r.included_npc_draft_count=8193,r=>r.included_npc_draft_count=1.5,r=>r.included_npc_draft_count=true,
  r=>delete r.included_npc_draft_count,r=>r.excluded_npc_draft_count=1,
  r=>r.assessment_scope='existing_imported_content_and_supported_overrides_excluding_npc_drafts',
  r=>r.npc_build_scope='native_allocation_and_spawn',r=>r.npc_gameplay_verified=true,r=>delete r.npc_gameplay_verified,
  r=>r.source_key='b'.repeat(64),r=>r.read_only=false,r=>r.assessment.output_written=true,
  r=>r.assessment.report.validation.live_runtime='passed',r=>r.assessment=null,
  r=>r.assessment.report.changes[1].composition_changes={},
  r=>r.assessment.report.changes[1].composition_changes=Array(4097).fill({}),
]){const invalid=review();mutate(invalid);assert.throws(()=>decodeBuildReview(invalid,key));}
const maximum=review();maximum.included_npc_draft_count=8192;assert.equal(decodeBuildReview(maximum,key).included_npc_draft_count,8192);
console.log('NPC Build review v2 preserves source-only ready/blocked candidate audits and rejects coverage, stale-source and gameplay claims.');

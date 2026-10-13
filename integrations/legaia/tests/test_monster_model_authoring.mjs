import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyMonsterAuthoringExport,qualifyMonsterAuthoringReview} from '../editor/monster-model-authoring.js';
const proof=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0,vertices=0;
for(const c of proof.cases){
 const e=c.export,v=c.review,report={project_path:e.project_path,project_source_key:e.project_source_key,catalog:{source_key:e.catalog_source_key,models:[e.record],textures:e.texture_record?[e.texture_record]:[]}},record={id:e.record.semantic_id},input=Uint8Array.from(atob(c.input_glb_base64),c=>c.charCodeAt(0));
 await qualifyMonsterAuthoringExport(e,report,record);await qualifyMonsterAuthoringReview(v,e,report,record,input);vertices+=v.geometry.vertices.length;
 for(const change of [v=>v.project_source_key='foreign',v=>v.input_sha256='0'.repeat(64),v=>v.geometry.vertices[0][0]++,v=>v.candidate_tmd_base64=Buffer.from('changed').toString('base64'),v=>v.binding.current_block_sha256='0'.repeat(64),v=>v.source_pool_base64=Buffer.from('changed').toString('base64'),v=>v.persistence='applied']){const changed=structuredClone(v);change(changed);await assert.rejects(qualifyMonsterAuthoringReview(changed,e,report,record,input));refusals++;}
 for(const change of [v=>v.glb_sha256='0'.repeat(64),v=>v.filename='../input.glb',v=>v.binding.profile.effective_sha256='0'.repeat(64)]){const changed=structuredClone(e);change(changed);await assert.rejects(qualifyMonsterAuthoringExport(changed,report,record));refusals++;}
}
console.log(`Three native authoring exports and ${vertices} literal Proposed vertices qualify; ${refusals} altered receipts refuse`);

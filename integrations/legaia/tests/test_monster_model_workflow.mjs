import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyMonsterPreview} from '../editor/monster-archive.js';
import {qualifyMonsterPose} from '../editor/monster-motion.js';
import {qualifyMonsterModelBytes} from '../editor/monster-model-replay.js';
import {qualifyMonsterAuthoringExport} from '../editor/monster-model-authoring.js';
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),v=c.current,record={id:v.record.semantic_id},report={project_path:v.project_path,project_source_key:v.project_source_key,catalog:{source_key:v.catalog_source_key,models:[v.record],textures:[v.texture_record],animations:[c.pose.clip]}};
const geometry=await qualifyMonsterPreview(v,report,record,'current');await qualifyMonsterPose(c.pose,report,record,c.pose.animation_id,c.pose.frame_index,geometry,'current');
await qualifyMonsterAuthoringExport(c.export,{...report,project_source_key:c.export.project_source_key},record);
let refusals=0;
for(const change of [v=>v.model_binding.edits[0].after_byte^=1,v=>v.model_binding.current_tmd_sha256='0'.repeat(64),v=>v.model_binding.edits.reverse(),v=>v.model_binding.source_record.byte_offset++,v=>v.source_tmd_base64=Buffer.from('changed').toString('base64'),v=>v.retail_tmd_base64=Buffer.from('changed').toString('base64')]){const changed=structuredClone(v);change(changed);await assert.rejects(qualifyMonsterModelBytes(changed,v.record));refusals++;}
console.log(`Saved Current native model and stored pose qualify; ${refusals} altered model witnesses refuse`);

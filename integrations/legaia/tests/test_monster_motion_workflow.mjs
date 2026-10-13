import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyMonsterPreview} from '../editor/monster-archive.js';
import {qualifyMonsterPose} from '../editor/monster-motion.js';
import {qualifyMonsterFrameInspection} from '../editor/monster-motion-authoring.js';
import {qualifyMonsterMotionBytes,qualifyMonsterMotionEntry} from '../editor/monster-motion-replay.js';
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),v=c.pose,b=v.base_preview,record={id:b.record.semantic_id},report={project_path:b.project_path,project_source_key:b.project_source_key,catalog:{source_key:b.catalog_source_key,models:[b.record],textures:[b.texture_record],animations:[v.clip]}};
const geometry=await qualifyMonsterPreview(b,report,record,'current');await qualifyMonsterPose(v,report,record,v.animation_id,v.frame_index,geometry,'current');const i=c.inspection;
await qualifyMonsterFrameInspection(i,{...report,project_source_key:i.project_source_key},record,{animation_id:i.clip.semantic_id,frame_index:i.frame_index},i.part_index);
let refusals=0;for(const change of [v=>v.motion_binding.edits[0].translation[0]++,v=>v.motion_binding.current_motion_sha256='0'.repeat(64),v=>v.retail_motion_base64=Buffer.from('changed').toString('base64'),v=>v.source_motion_base64=Buffer.from('changed').toString('base64'),v=>v.motion_binding.edits[0].frame_index=999]){const changed=structuredClone(v);change(changed);await assert.rejects(qualifyMonsterMotionBytes(changed,v.clip));refusals++;}
const changed=structuredClone(v),entry=Buffer.from(changed.source_entry_base64,'base64');entry[1]^=1;changed.source_entry_base64=entry.toString('base64');await assert.rejects(qualifyMonsterMotionEntry(changed,v.clip));refusals++;
console.log(`Saved Current motion, model and pose qualify; ${refusals} altered native motion witnesses refuse`);

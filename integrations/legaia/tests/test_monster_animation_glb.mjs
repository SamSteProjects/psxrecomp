import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyMonsterMotionGlbReview} from '../editor/monster-motion-glb.js';
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let refusals=0;
for(const row of c.cases){const bytes=Uint8Array.from(atob(row.input_glb_base64),c=>c.charCodeAt(0));await qualifyMonsterMotionGlbReview(row.review,row.inspection,bytes,24);
 for(const change of [v=>v.input_sha256='0'.repeat(64),v=>v.fps=25,v=>v.analysis.edits[0].translation[0]++,v=>v.analysis.edits.reverse(),v=>v.candidate_motion_base64=Buffer.from('changed').toString('base64'),v=>v.analysis.maximum_angular_error_degrees=2,v=>v.persistence='applied',v=>v.current_block_sha256='0'.repeat(64)]){const altered=structuredClone(row.review);change(altered);await assert.rejects(qualifyMonsterMotionGlbReview(altered,row.inspection,bytes,24));refusals++;}}
console.log(`Three GLB native motion Reviews qualify; ${refusals} altered input/sampling/channel receipts refuse`);

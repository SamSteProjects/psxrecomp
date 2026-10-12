import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyPlayerActionGLB} from '../editor/player-action-editor.js';
const {report,record,inspection,review,input}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
await qualifyPlayerActionGLB(review,inspection,report,record,input);let refused=0;
for(const change of [v=>v.glb_import.glb_sha256='0'.repeat(64),v=>v.glb_import.fps=30,v=>v.glb_import.rotation_step_psx=16,v=>v.glb_import.edits[0].translation.x++,v=>v.retained_input.glb_byte_length++,v=>v.retained_input.source_file_sha256='0'.repeat(64),v=>v.operation='edit',v=>v.proposed_action_base64=v.current_action_base64]){const v=structuredClone(review);change(v);await assert.rejects(qualifyPlayerActionGLB(v,inspection,report,record,input));refused++;}
console.log(`PLAYER GLB native proposed replay and ${refused} altered import receipts pass`);

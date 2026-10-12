import fs from 'node:fs';import assert from 'node:assert/strict';
import {playerActionChannelTrack} from '../editor/player-action-timeline.js';
const {inspection,review}=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const streams=[inspection.original_action_base64,inspection.current_action_base64,review.proposed_action_base64].map(s=>Buffer.from(s,'base64'));
let samples=0;
for(let part=0;part<inspection.current_clip.part_count;part++)for(const field of ['translation','rotation_psx'])for(const axis of 'xyz'){
 const track=playerActionChannelTrack(inspection,part,field,axis,review),n='xyz'.indexOf(axis);
 for(const row of track.samples)for(const [layer,b] of [['retail',streams[0]],['current',streams[1]],['proposed',streams[2]]]){
  const at=2+(row.frame*inspection.current_clip.part_count+part)*9;
  const words=field==='translation'?[b[at]+(b[at+2]%16)*256,b[at+1]+Math.floor(b[at+2]/16)*256,b[at+3]+(b[at+5]%16)*256]:[b[at+4]+Math.floor(b[at+5]/16)*256,b[at+6]+(b[at+8]%16)*256,b[at+7]+Math.floor(b[at+8]/16)*256];
  const expected=field==='translation'&&words[n]>=2048?words[n]-4096:words[n];assert.equal(row[layer],expected);samples++;
 }
}
for(const args of [[-1,'translation','x'],[99,'translation','x'],[0,'foreign','x'],[0,'rotation_psx','q']])assert.throws(()=>playerActionChannelTrack(inspection,...args,review));
const bad=structuredClone(review);bad.proposed_action_base64=bad.proposed_action_base64.slice(4);assert.throws(()=>playerActionChannelTrack(inspection,0,'translation','x',bad));
console.log(`${samples} Retail/Current/Proposed native timeline axis samples and invalid channel/stream refusals pass`);

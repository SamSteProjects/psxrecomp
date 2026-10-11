import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldAnimationOffsetRangeDraft} from '../editor/worldmap-animation-editor.js';
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),held=fixture.held??fixture,object=1,p=held.preview,bytes=Buffer.from(p.record_base64,'base64');
const pose={translation:Object.fromEntries([...'xyz'].map((a,i)=>[a,p.object_transforms[object].translation[i]+(i===0?16:0)])),rotation_psx:Object.fromEntries([...'xyz'].map((a,i)=>[a,(p.object_transforms[object].rotation_psx[i]+(i===2?16:0))%4096]))};
const before=JSON.stringify(held),draft=await worldAnimationOffsetRangeDraft(held,object,pose,0,p.frame_count-1);assert.equal(JSON.stringify(held),before);
const signed=n=>n&2048?n-4096:n;
for(let frame=0;frame<p.frame_count;frame++){
 const at=8+(frame*p.channel_count+object)*8,d=bytes.subarray(at,at+8),row=draft.find(e=>e.frame_index===frame&&e.object_index===object);
 assert.deepEqual(row.translation,{x:signed(d[0]+(d[2]&15)*256)+16,y:signed(d[1]+(d[2]>>4)*256),z:signed(d[3]+(d[4]&15)*256)});
 assert.deepEqual(row.rotation_psx,{x:d[5]*16,y:d[6]*16,z:(d[7]*16+16)%4096});
}
for(const row of held.binding?.entries[String(p.record_index).padStart(4,'0')]?.edits??[])if(row.object_index!==object)assert.deepEqual(draft.find(e=>e.frame_index===row.frame_index&&e.object_index===row.object_index),row);
const partial=await worldAnimationOffsetRangeDraft(held,object,pose,p.frame_index,p.frame_index);assert(partial.filter(e=>e.object_index===object&&e.frame_index!==p.frame_index).every(e=>held.binding.entries[String(p.record_index).padStart(4,'0')].edits.some(r=>JSON.stringify(r)===JSON.stringify(e))));
const altered=structuredClone(held);altered.preview.record_base64=Buffer.from('altered').toString('base64');await assert.rejects(worldAnimationOffsetRangeDraft(altered,object,pose,0,p.frame_count-1));
let refused=1;for(const [obj,values,start,end] of [[64,pose,0,p.frame_count-1],[object,pose,-1,p.frame_count-1],[object,pose,0,p.frame_count],[object,{...pose,translation:{...pose.translation,x:2048}},0,p.frame_count-1],[object,{...pose,rotation_psx:{...pose.rotation_psx,z:1}},0,p.frame_count-1]]){await assert.rejects(worldAnimationOffsetRangeDraft(held,obj,values,start,end));refused++;}
if(p.frame_index===0&&draft.some(e=>e.object_index===object&&e.translation.x>16)){await assert.rejects(worldAnimationOffsetRangeDraft(held,object,{...pose,translation:{...pose.translation,x:2047}},0,p.frame_count-1),/capacity/);refused++;}
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(draft));console.log(`Current range offsets match ${p.frame_count} independent native frame decodes, preserve sibling rows and receipt, and refuse ${refused} invalid proposals`);

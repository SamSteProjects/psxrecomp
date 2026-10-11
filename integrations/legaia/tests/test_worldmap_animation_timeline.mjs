import fs from 'node:fs';import assert from 'node:assert/strict';
import {qualifyWorldAnimationChannels} from '../editor/worldmap-animation-channels.js';
import {qualifyWorldClipChannelReview} from '../editor/worldmap-clip-channels.js';
import {worldAnimationChannelTrack,worldAnimationTimelineFrame} from '../editor/worldmap-animation-timeline.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let tracks=0,samples=0;
for(const row of rows){const v=row.response,plan=await qualifyWorldAnimationChannels(v,v.record,v.project_path,v.source_key,v.binding),held=JSON.stringify(v);
 for(let o=0;o<v.record.channel_count;o++)for(const field of ['translation','rotation_psx'])for(const [index,axis] of [...'xyz'].entries()){
  const track=worldAnimationChannelTrack(plan,o,field,axis);assert.equal(track.samples.length,v.record.frame_count);assert(Object.isFrozen(track)&&Object.isFrozen(track.samples));const expected=[];
  for(const sample of track.samples){for(const layer of ['retail','current']){const native=row[layer+'_frames'][sample.frame].object_transforms[o][field][index];assert.equal(sample[layer],native);expected.push(native);}samples++;}
  assert.equal(track.min,Math.min(...expected));assert.equal(track.max,Math.max(...expected));assert.throws(()=>{track.samples[0].retail=999;});tracks++;
 }
 assert.equal(JSON.stringify(v),held);
 for(const args of [[-1,'translation','x'],[v.record.channel_count,'translation','x'],[0,'unknown','x'],[0,'translation','w'],[.5,'translation','x']])assert.throws(()=>worldAnimationChannelTrack(plan,...args));
}
for(const count of [1,2,30,512]){for(let f=0;f<count;f++){const x=48+(count===1?288:f/(count-1)*576);assert.equal(worldAnimationTimelineFrame(20+x/640*320,20,320,count),f);}assert.equal(worldAnimationTimelineFrame(-100,0,320,count),0);assert.equal(worldAnimationTimelineFrame(999,0,320,count),count-1);}
for(const args of [[0,0,0,30],[NaN,0,320,30],[0,0,320,0],[0,0,320,513]])assert.throws(()=>worldAnimationTimelineFrame(...args));
console.log(`${rows.length} clips, ${tracks} channel tracks and ${samples} independent native samples pass immutable timeline and pointer mapping checks`);

if(process.argv[3]){const reviews=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));let proposedSamples=0;
 for(const item of reviews){const source=item.source,before=await qualifyWorldAnimationChannels(source,source.record,source.project_path,source.source_key,source.binding),after=(await qualifyWorldClipChannelReview(item.review,source,before,item.review.edits)).proposed,bytes=Buffer.from(item.review.proposed_bank_base64,'base64'),span=source.record.source_record,held=JSON.stringify(source),signed=n=>n&2048?n-4096:n;
  for(let object=0;object<source.record.channel_count;object++)for(const field of ['translation','rotation_psx'])for(const [i,axis] of [...'xyz'].entries()){
   const track=worldAnimationChannelTrack(before,object,field,axis,after),base=worldAnimationChannelTrack(before,object,field,axis);
   for(const sample of track.samples){const at=span.byte_offset+8+(sample.frame*source.record.channel_count+object)*8,b=bytes.subarray(at,at+8),values=field==='translation'?[signed(b[0]+(b[2]&15)*256),signed(b[1]+(b[2]>>4)*256),signed(b[3]+(b[4]&15)*256)]:[b[5]*16,b[6]*16,b[7]*16];assert.equal(sample.proposed,values[i]);assert.equal(sample.retail,base.samples[sample.frame].retail);assert.equal(sample.current,base.samples[sample.frame].current);proposedSamples++;}
  }
  assert.equal(JSON.stringify(source),held);for(const mutate of [r=>r.id='foreign',r=>r.frame_count++,r=>r.source_record.sha256='0'.repeat(64)]){const foreign={...after,record:structuredClone(after.record)};mutate(foreign.record);assert.throws(()=>worldAnimationChannelTrack(before,0,'translation','x',foreign));}
 }
 console.log(`${proposedSamples} independently decoded Proposed hold/offset/restoration samples preserve immutable Retail and Current tracks; foreign clip refusals pass`);
}

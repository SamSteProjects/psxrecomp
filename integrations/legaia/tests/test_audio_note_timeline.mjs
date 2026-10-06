import assert from 'node:assert/strict';
import {analyzeSequenceNotes} from '../editor/audio-note-timeline.js';
const events=[],add=(kind,channel,key,velocity,ticks)=>events.push({index:events.length,kind,channel,values:[key,velocity],ticks,time_seconds:ticks/480});
add('note_off',0,60,0,0); // Release without an encoded start.
add('note_on',0,60,100,10);add('note_on',1,60,70,20);add('note_on',0,60,90,30);
add('note_off',0,60,0,40);add('note_on',0,60,0,50); // Velocity-zero source release.
add('note_off',1,60,0,60);add('note_on',0,60,20,70); // New nonoverlapping start stays open.
const report={events,complete:false,decoded_ticks:80},before=structuredClone(report),result=analyzeSequenceNotes(report);
assert.deepEqual(report,before);assert.equal(result.policy,'same-channel-key-first-in-first-out');assert.equal(result.sustain_evaluated,false);assert.equal(result.complete_source,false);
assert.deepEqual(result.notes.map(n=>[n.start_event,n.end_event,n.ambiguous]),[[1,4,true],[2,6,false],[3,5,true],[7,null,false]]);
assert.deepEqual(result.unmatched_releases,[0]);assert.deepEqual(result.unmatched_starts,[7]);assert.equal(result.overlap_count,1);assert.equal(result.notes[0].end_ticks,40);assert.equal(result.notes[3].end_seconds,null);
const dense={events:Array.from({length:32768},(_,index)=>({index,kind:'note_on',channel:0,values:[127,127],ticks:index,time_seconds:index})),complete:true,decoded_ticks:32768};
const many=analyzeSequenceNotes(dense);assert.equal(many.notes.length,32768);assert.equal(many.overlap_count,32767);assert.equal(many.unmatched_starts.length,32768);assert(many.notes.every(n=>n.end_ticks===null&&n.ambiguous));
assert.deepEqual(analyzeSequenceNotes({events:[],complete:true,decoded_ticks:0}).notes,[]);
console.log('Channel-isolated FIFO note pairing, overlap uncertainty, velocity-zero releases, partial/unmatched boundaries, immutable source and maximum event budget passed.');

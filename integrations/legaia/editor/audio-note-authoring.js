import {analyzeSequenceNotes} from './audio-note-timeline.js';

// Encoded event pairing is an editor policy, not a runtime voice identity.
export function qualifyNotePair(report,index){
 const event=report.events[index];
 if(!event||!['note_on','note_off'].includes(event.kind))throw Error('Choose an encoded note start or release.');
 const note=analyzeSequenceNotes(report).notes.find(n=>n.start_event===index||n.end_event===index);
 if(!note)throw Error('This encoded release has no paired start.');
 if(note.ambiguous)throw Error('Overlapping starts make this encoded pairing ambiguous.');
 if(note.end_event===null)throw Error('This encoded start has no release in the decoded prefix.');
 return structuredClone(note);
}

export function pairedNoteEdits(report,index,values){
 const note=qualifyNotePair(report,index),event=report.events[index];
 if(!Array.isArray(values)||values.length!==2||!values.every(v=>Number.isSafeInteger(v)&&v>=0&&v<=127))throw Error('Paired note operands require two encoded 7-bit values.');
 const isStart=index===note.start_event;
 if(isStart&&values[1]===0)throw Error('A paired start requires positive velocity; zero encodes a release.');
 const release=report.events[note.end_event];
 if(!isStart&&release.kind==='note_on'&&values[1]!==0)throw Error('A velocity-zero release must remain zero in paired mode.');
 const key=values[0];
 if(key!==note.key&&analyzeSequenceNotes(report).notes.some(other=>other.start_event!==note.start_event&&other.channel===note.channel&&other.key===key&&other.start_event<note.end_event&&(other.end_event??Infinity)>note.start_event))throw Error('The destination key overlaps another encoded note on this channel.');
 if(key!==note.key&&report.events.some(e=>e.index>note.start_event&&e.index<note.end_event&&e.channel===note.channel&&e.values[0]===key&&(e.kind==='note_off'||e.kind==='note_on'&&e.values[1]===0)))throw Error('An intervening destination-key release would change this encoded pairing.');
 const start=report.events[note.start_event];
 return [
  {event_offset:start.offset,values:[key,isStart?values[1]:start.values[1]]},
  {event_offset:release.offset,values:[key,isStart?release.values[1]:values[1]]}
 ].sort((a,b)=>a.event_offset-b.event_offset);
}

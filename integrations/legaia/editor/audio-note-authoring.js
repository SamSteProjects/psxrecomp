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

// Transpose every fully paired Current note on one encoded channel atomically.
export function channelTransposeEdits(options,channel,semitones){
 if(!Number.isSafeInteger(channel)||channel<0||channel>15)throw Error('Choose an encoded channel from 0 through 15.');
 if(!Number.isSafeInteger(semitones)||semitones===0||semitones< -127||semitones>127)throw Error('Choose a nonzero whole-number transpose from -127 through 127.');
 const report=options.current,analysis=analyzeSequenceNotes(report),notes=analysis.notes.filter(n=>n.channel===channel);
 if(!notes.length)throw Error('This channel has no encoded note starts.');
 if(notes.some(n=>n.ambiguous||n.end_event===null))throw Error('Every channel note must have an unambiguous encoded release in the decoded prefix.');
 if(notes.length>128)throw Error('Channel transpose exceeds the 256-event request budget.');
 const edits=[];
 for(const note of notes){
  const key=note.key+semitones;
  if(key<0||key>127)throw Error('Transpose would move an encoded note key outside 0 through 127.');
  for(const index of [note.start_event,note.end_event]){
   const event=report.events[index];edits.push({event_offset:event.offset,values:[key,event.values[1]]});
  }
 }
 edits.sort((a,b)=>a.event_offset-b.event_offset);
 const changed=new Map(edits.map(e=>[e.event_offset,e.values])),candidate={...report,events:report.events.map(e=>({...e,values:changed.get(e.offset)??e.values}))};
 const pairing=a=>JSON.stringify([a.notes.map(n=>[n.start_event,n.end_event,n.ambiguous]),a.unmatched_releases,a.unmatched_starts]);
 if(pairing(analyzeSequenceNotes(candidate))!==pairing(analysis))throw Error('Transpose would change encoded start/release pairing.');
 const retail=new Map(options.retail.events.map(e=>[e.offset,e.values])),merged=new Map(options.authored_edits.map(e=>[e.event_offset,e.values]));
 for(const edit of edits)merged.set(edit.event_offset,edit.values);
 const count=[...merged].filter(([offset,values])=>JSON.stringify(values)!==JSON.stringify(retail.get(offset))).length;
 if(count>256)throw Error('Transpose exceeds the 256-event authored binding budget.');
 return edits;
}

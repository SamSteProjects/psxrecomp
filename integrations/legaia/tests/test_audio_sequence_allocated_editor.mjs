import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeSequenceAuthoring,decodeSequenceReview,decodeProposedSequence} from '../editor/audio-sequence-authoring.js';
if(process.argv.length<3)throw Error('Provide freshly qualified moved-carrier SEQ fixtures.');
let cases=0,refusals=0;
for(const file of process.argv.slice(2)){
 const f=JSON.parse(fs.readFileSync(file,'utf8')),o=decodeSequenceAuthoring(f.options,f.context),r=decodeSequenceReview(f.review,o,f.edits);
 assert.equal(o.schema_version,'legaia.audio-sequence-authoring.v2');assert.equal(r.native_audit.sequence_offset,o.current_sequence_offset);
 decodeProposedSequence(f.proposed,o,r,f.context);
 for(const [field,value] of [['current_sequence_offset',o.source_record.sequence_offset],['current_entry_size_bytes',1],['samples_authored',false]]){assert.throws(()=>decodeSequenceAuthoring({...f.options,[field]:value},f.context));refusals++;}
 for(const [field,value] of [['sequence_offset',o.source_record.sequence_offset],['source_sequence_offset',0],['current_entry_size_bytes',1]]){assert.throws(()=>decodeSequenceReview({...f.review,native_audit:{...f.review.native_audit,[field]:value}},o,f.edits));refusals++;}
 assert.throws(()=>decodeSequenceReview({...f.review,native_audit:{...f.review.native_audit,changed_entry_byte_offsets:f.review.native_audit.changed_entry_byte_offsets.map(i=>i+16)}},o,f.edits));refusals++;
 assert.throws(()=>decodeProposedSequence({...f.proposed,current_sequence_offset:o.source_record.sequence_offset},o,r,f.context));refusals++;
 assert.throws(()=>decodeProposedSequence({...f.proposed,current_entry_size_bytes:1},o,r,f.context));refusals++;cases++;
}
console.log(JSON.stringify({moved_current_review_proposed_cases:cases,forged_layout_refusals:refusals}));

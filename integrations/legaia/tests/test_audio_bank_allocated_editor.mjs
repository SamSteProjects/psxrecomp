import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeBankAuthoring,decodeBankReview} from '../editor/audio-bank-authoring.js';
import {decodeNoteLinks,encodedToneCandidates} from '../editor/audio-note-links.js';
if(process.argv.length<3)throw Error('Provide freshly qualified allocated bank fixtures.');
let cases=0,refusals=0;
for(const file of process.argv.slice(2)){
 const f=JSON.parse(fs.readFileSync(file,'utf8')),o=decodeBankAuthoring(f.options,f.context,f.bank);decodeBankReview(f.review,o,f.edits);const links=decodeNoteLinks(f.links,f.sequence,f.note_index,f.context);encodedToneCandidates(links);
 assert.equal(o.schema_version,'legaia.audio-bank-authoring.v2');assert.notEqual(o.current.header.declared_size,o.retail.header.declared_size);assert.equal(links.bank.source_record.entry_sha256,f.context.entryHash);assert.equal(links.bank.current_layout.entry_sha256,o.current_entry_sha256);
 for(const [field,value] of [['entry_size_bytes',1],['bank_size_bytes',1],['entry_sha256','0'.repeat(64)]]){assert.throws(()=>decodeBankAuthoring({...f.options,current_layout:{...o.current_layout,[field]:value}},f.context,f.bank));refusals++;}
 let bad=structuredClone(f.options);bad.current_layout.pieces[0].entry_offset+=4;assert.throws(()=>decodeBankAuthoring(bad,f.context,f.bank));refusals++;
 bad=structuredClone(f.options);bad.current.header.program_count++;assert.throws(()=>decodeBankAuthoring(bad,f.context,f.bank));refusals++;
 bad=structuredClone(f.links);bad.bank.current_layout.entry_size_bytes+=16;assert.throws(()=>decodeNoteLinks(bad,f.sequence,f.note_index,f.context));refusals++;
 bad=structuredClone(f.links);bad.bank.samples[1].offset+=16;assert.throws(()=>decodeNoteLinks(bad,f.sequence,f.note_index,f.context));refusals++;
 bad=structuredClone(f.links);bad.bank.source_record.disc_sha256='0'.repeat(64);assert.throws(()=>decodeNoteLinks(bad,f.sequence,f.note_index,f.context));refusals++;
 bad=structuredClone(f.links);bad.bank.schema_version='legaia.audio-bank-inspection.v1';assert.throws(()=>decodeNoteLinks(bad,f.sequence,f.note_index,f.context));refusals++;
 cases++;
}
console.log(JSON.stringify({allocated_bank_review_note_cases:cases,forged_layout_provenance_refusals:refusals}));

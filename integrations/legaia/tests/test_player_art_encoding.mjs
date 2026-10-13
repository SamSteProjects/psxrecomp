import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeArtArchive,encodeArtChannels,replaceArtEntry} from '../editor/player-art-codec.js';
const original=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),expected=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));let count=0;
for(const [i,c]of original.entries()){const slot=new Uint8Array(Buffer.from(c.source_base64,'base64'));let candidate=slot.slice();for(const r of decodeArtArchive(slot)){const changed=r.decoded.slice();changed[2]^=1;candidate=replaceArtEntry(candidate,r.entry_index,changed);assert(encodeArtChannels(changed,slot[r.byte_offset]).length<=r.byte_length);count++;}assert.deepEqual(Buffer.from(candidate),Buffer.from(expected[i].source_base64,'base64'));}
for(const bad of [new Uint8Array(),new Uint8Array([0,1]),new Uint8Array([1,1])])assert.throws(()=>encodeArtChannels(bad));
assert.throws(()=>encodeArtChannels(new Uint8Array([1,1,...Array(9).fill(0)]),true));
assert.equal(count,87);console.log('87 independent canonical ME encodings and complete fixed-body replacements match Python candidates byte-for-byte');

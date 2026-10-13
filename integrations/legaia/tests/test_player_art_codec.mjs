import fs from 'node:fs';
import assert from 'node:assert/strict';
import {decodeArtArchive,decodeArtChannels} from '../editor/player-art-codec.js';
const cases = JSON.parse(fs.readFileSync(process.argv[2],'utf8')); let streams = 0, bytes = 0, refusals = 0;
for (const c of cases) {
  const source = Uint8Array.from(Buffer.from(c.source_base64,'base64')), result = decodeArtArchive(source);
  assert.equal(result.length,c.entries.length);
  for (const [index,r] of result.entries()) {
    const expected = c.entries[index];
    for (const key of ['entry_index','size_word','byte_offset','byte_length']) assert.equal(r[key],expected[key]);
    assert.deepEqual(Buffer.from(r.decoded),Buffer.from(expected.decoded_base64,'base64')); streams++; bytes += r.decoded.length;
    const body = source.slice(r.byte_offset,r.byte_offset+r.byte_length);
    for (const edit of [v=>v[0]=0x80,v=>{v[1]=255;v[2]=255;},v=>{v[3]=0;v[4]=0;}]) { const changed = body.slice(); edit(changed); assert.throws(()=>decodeArtChannels(changed)); refusals++; }
  }
  for (const edit of [v=>v[0]=0,v=>v[2]=255,v=>{v[3]=255;v[4]=127;}]) { const changed=source.slice();edit(changed);assert.throws(()=>decodeArtArchive(changed));refusals++; }
}
assert.equal(streams,87);
console.log(`Eight archives / ${streams} independent native stream decodes / ${bytes} exact bytes / ${refusals} malformed source refusals pass`);

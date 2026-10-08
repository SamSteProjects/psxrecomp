import assert from 'node:assert/strict';
import fs from 'node:fs';
import {webcrypto} from 'node:crypto';
import {assetInspectorRegistry} from '../editor/asset-inspector.js';
import {decodeMidiInput,decodeMidiInputDownload} from '../editor/midi-input-assets.js';
const f=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),v=f.dto;
if(!globalThis.crypto)Object.defineProperty(globalThis,"crypto",{value:webcrypto});
const c={assetId:v.asset_id,sourceKey:v.source_key,projectPath:v.project_path};
const {midi_base64,...report}=v;
const decoded=decodeMidiInput(report,c);decoded.record.midi_input.byte_length++;assert.notEqual(decoded.record.midi_input.byte_length,report.record.midi_input.byte_length);
const result=await decodeMidiInputDownload(v,c);assert.deepEqual(Buffer.from(result.bytes),Buffer.from(midi_base64,'base64'));
for(const mutate of [r=>r.current_binding='verified',r=>r.runtime_binding='verified',r=>r.gameplay_verified=true,r=>r.read_only=false,r=>r.record.midi_input.ppqn=0,r=>r.record.source_record.relative_path='../outside.mid',r=>r.receipts[0].midi_sha256='f'.repeat(64),r=>r.receipts.push(r.receipts[0]),r=>r.source_key='f'.repeat(64)]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMidiInput(bad,c));}
for(const b of ['!',midi_base64.slice(4),Buffer.alloc(result.bytes.length).toString('base64')])await assert.rejects(()=>decodeMidiInputDownload({...v,midi_base64:b},c));
console.log('Fresh MIDI asset DTO, exact download/hash, ownership/claim/path/duplicate/refusal and detached metadata passed');

assert.deepEqual(Object.keys(assetInspectorRegistry({type:'audio',data:report.record},()=>{})),['inspect-midi-input']);

import fs from 'node:fs';import assert from 'node:assert/strict';
import {transformUvRows} from '../editor/model-uv-workspace.js';
import {worldModelUvCandidate} from '../editor/worldmap-model-uv.js';
const cases=JSON.parse(fs.readFileSync(process.argv[2]));
for(const row of cases){const original=new Uint8Array(Buffer.from(row.tmd_base64,'base64')),held=original.slice(),current=structuredClone(row.face.current),draft=transformUvRows(current,row.operation,row.du,row.dv);assert.deepEqual(draft,row.draft);assert.deepEqual(worldModelUvCandidate({tmd:original,metadata:{layer:'current'}},row.face.object_index,row.face.primitive_index,draft),new Uint8Array(Buffer.from(row.candidate_base64,'base64')));assert.deepEqual(original,held);assert.deepEqual(current,row.face.current);}
console.log(cases.length+' UV transforms match independent complete native/synthetic bytes and immutable Current corners.');

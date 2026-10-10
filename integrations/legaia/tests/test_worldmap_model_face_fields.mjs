import fs from 'node:fs';import assert from 'node:assert/strict';
import {worldFaceObjects} from '../editor/worldmap-model-face-replay.js';
import {worldFaceDraft} from '../editor/worldmap-model-faces.js';
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(const row of rows)assert.deepEqual(worldFaceObjects(new Uint8Array(Buffer.from(row.candidate,'base64'))),row.objects);
const faceSource={faces:new Map([['donor',{owner:0,group:0,index:0}]])};assert.deepEqual(worldFaceDraft(faceSource,'donor','0, 1 2','{"uvs":[[1,2],[3,4],[5,6]]}','id'),{face_id:'id',donor_face_id:'donor',fields:{vertices:[0,1,2],uvs:[[1,2],[3,4],[5,6]]}});
for(const args of [['foreign','0 1 2',''],['donor','-1 1 2',''],['donor','1.5 1 2',''],['donor','0 1 2','[]'],['donor','0 1 2','{"tpage":1}'],['donor','0 1 2','{"vertices":[0,1,2]}']])assert.throws(()=>worldFaceDraft(faceSource,...args,'id'));
console.log(`${rows.length} literal native donor field sets and bounded draft parsing passed.`);

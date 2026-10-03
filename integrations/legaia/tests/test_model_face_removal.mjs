import assert from 'node:assert/strict';
import {decodeFaceRemovalSource,faceRemovalSelections,decodeFaceRemovalReview} from '../editor/model-face-removal.js';
const key='a'.repeat(64),asset='asset://fixture/model/1';
const source={schema_version:'legaia.model-face-removal-source.v1',asset_id:asset,project_source_key:key,source_sha256:key,effective_sha256:key,objects:[{object_index:0,vertex_count:3,primitives:[{primitive_index:0,corner_count:3},{primitive_index:1,corner_count:4}]}],removed_faces:[]};
decodeFaceRemovalSource(source,asset,key);
assert.deepEqual(faceRemovalSelections(source,0,'1, 0'),[{object_index:0,primitive_index:0},{object_index:0,primitive_index:1}]);
for(const text of ['1,1','2','-1','0,','NaN'])assert.throws(()=>faceRemovalSelections(source,0,text));
const selections=faceRemovalSelections(source,0,'1'),mesh={vertices:[[0,0,0],[1,0,0],[0,1,0]],objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_count:3}]};
const report={schema_version:'legaia.model-face-removal.v1',asset_id:asset,source_sha256:key,effective_sha256:key,proposed_sha256:'b'.repeat(64),project_source_key:key,selections,previous_removed_faces:[],removed_faces:[{object_index:0,primitive_index:1}],current_preview:mesh,preview:{...mesh,objects:[{...mesh.objects[0],triangle_count:1}]},project_changed:false,gameplay_verified:false};
decodeFaceRemovalReview(report,source,selections);
for(const mutate of [v=>v.project_changed=true,v=>v.removed_faces=[],v=>v.effective_sha256='c'.repeat(64),v=>v.preview.objects[0].vertex_count=2,v=>v.preview.objects[0].triangle_count=2,v=>v.proposed_sha256=key]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeFaceRemovalReview(bad,source,selections));}
console.log('Exact source face selection, duplicate/domain guards, reviewed topology counts, vertex preservation and source hashes passed.');

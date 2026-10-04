import assert from 'node:assert/strict';
import {decodeFaceRemovalSource,faceRemovalSelections,decodeFaceRemovalReview,faceRestorationSelections,decodeFaceRestorationReview} from '../editor/model-face-removal.js';
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

const restoreSource={...source,schema_version:'legaia.model-face-removal-source.v2',retail_objects:structuredClone(source.objects),objects:[{...source.objects[0],primitives:[{primitive_index:0,corner_count:3}]}],removed_faces:[{object_index:0,primitive_index:1}]};
decodeFaceRemovalSource(restoreSource,asset,key);const restoring=faceRestorationSelections(restoreSource,0,'1');assert.throws(()=>faceRestorationSelections(restoreSource,0,'0'));
const restoration={...report,schema_version:'legaia.model-face-restoration.v1',selections:restoring,previous_removed_faces:restoreSource.removed_faces,removed_faces:[],current_preview:report.preview,preview:report.current_preview};
decodeFaceRestorationReview(restoration,restoreSource,restoring);
for(const mutate of [v=>v.removed_faces=restoreSource.removed_faces,v=>v.preview.objects[0].triangle_count=2,v=>v.proposed_sha256=key]){const bad=structuredClone(restoration);mutate(bad);assert.throws(()=>decodeFaceRestorationReview(bad,restoreSource,restoring));}
console.log('Restored Retail selection, count/hash and unchanged removal identity guards passed.');

const sourceFace={face_id:`face://source/${key}/0/0`,origin:'source',object_index:0,group_index:0,source_primitive_index:0,current_primitive_index:0};
const authoredFace={face_id:'face://authored/00000000-0000-4000-8000-000000000001',origin:'authored',object_index:0,group_index:1,current_primitive_index:1,donor_face_id:sourceFace.face_id};
const ledgerSource={...source,schema_version:'legaia.model-face-removal-source.v3',face_topology:[sourceFace,authoredFace],removed_face_ids:[],restoration_available:false};
const ledgerReport={schema_version:'legaia.model-face-removal.v2',asset_id:asset,source_sha256:key,effective_sha256:key,proposed_sha256:'b'.repeat(64),project_source_key:key,selections,removed_face_ids:[authoredFace.face_id],previous_removed_face_ids:[],topology:{proposed_sha256:'b'.repeat(64),faces:[sourceFace],removed_face_ids:[authoredFace.face_id]},current_preview:mesh,preview:report.preview,project_changed:false,gameplay_verified:false};
const decoded=decodeFaceRemovalSource(ledgerSource,asset,key);decoded.face_topology[0].group_index=9;assert.equal(ledgerSource.face_topology[0].group_index,0);
decodeFaceRemovalReview(ledgerReport,ledgerSource,selections);assert.throws(()=>faceRestorationSelections(ledgerSource,0,'1'));
for(const mutate of [v=>v.face_topology.pop(),v=>v.face_topology[1].current_primitive_index=0,v=>v.face_topology[1].face_id=sourceFace.face_id,v=>v.removed_face_ids=[sourceFace.face_id],v=>v.restoration_available=true,v=>v.face_topology[0].source_primitive_index=2]){const bad=structuredClone(ledgerSource);mutate(bad);assert.throws(()=>decodeFaceRemovalSource(bad,asset,key));}
for(const mutate of [v=>v.removed_face_ids=[sourceFace.face_id],v=>v.topology.faces[0].group_index=1,v=>v.topology.faces[0].face_id=authoredFace.face_id,v=>v.topology.removed_face_ids=[],v=>v.previous_removed_face_ids=[sourceFace.face_id],v=>v.preview.objects[0].triangle_count=2,v=>v.proposed_sha256=key]){const bad=structuredClone(ledgerReport);mutate(bad);assert.throws(()=>decodeFaceRemovalReview(bad,ledgerSource,selections));}
const sourceFirst={...ledgerSource,face_topology:[{...sourceFace,group_index:0},{...authoredFace,group_index:1}]},dropSource=[{object_index:0,primitive_index:0}];
const authoredOnly={...ledgerReport,selections:dropSource,removed_face_ids:[sourceFace.face_id],topology:{proposed_sha256:'b'.repeat(64),faces:[{...authoredFace,group_index:0,current_primitive_index:0}],removed_face_ids:[sourceFace.face_id]},preview:{...mesh,objects:[{...mesh.objects[0],triangle_count:2}]}};
decodeFaceRemovalReview(authoredOnly,sourceFirst,dropSource);
console.log('V3 stable removal source and V2 review validate authored deletions, authored-only survivors, group compaction and reject identity/count tampering.');

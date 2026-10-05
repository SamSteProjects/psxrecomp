import assert from 'node:assert/strict';
import {vertexMovePreview,pickProjectedVertex,objectMovePreview,qualifyObjectMoveReview} from '../editor/model-vertex-move.js';
const source={preview:{objects:[{object_index:0,vertex_start:0,vertex_count:1},{object_index:1,vertex_start:1,vertex_count:2}],vertices:[[1,2,3],[4,5,6],[7,8,9]],triangles:[[0,1,2]],normals:[[0,4096,0]]}},before=structuredClone(source);
const proposed=vertexMovePreview(source,1,1,[-32768,16,32767]);
assert.deepEqual(proposed.vertices,[[1,2,3],[4,5,6],[-32768,16,32767]]);assert.deepEqual(source,before);assert.deepEqual(proposed.triangles,source.preview.triangles);assert.deepEqual(proposed.normals,source.preview.normals);proposed.vertices[0][0]=99;assert.deepEqual(source,before);
for(const [object,index,values] of [[2,0,[0,0,0]],[0,1,[0,0,0]],[1,-1,[0,0,0]],[1,0,[0,0,32768]],[1,0,[0,0,-32769]],[1,0,[0,0,.5]],[1,0,[0,NaN,0]],[1,0,[0,0]]])assert.throws(()=>vertexMovePreview(source,object,index,values));
console.log('Vertex draft: exact object-local row, signed16 bounds, immutable Current and retained topology/normals passed');
assert.equal(pickProjectedVertex([{index:8,x:10,y:10,depth:9},{index:3,x:10,y:10,depth:4},{index:2,x:10,y:10,depth:4}],10,10),2);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2},{index:1,x:11,y:11,depth:1}],11,11),1);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2}],20,10),0);
assert.equal(pickProjectedVertex([{index:0,x:10,y:10,depth:2}],20.1,10),null);
assert.equal(pickProjectedVertex([null,{index:0,x:NaN,y:10,depth:2}],10,10),null);
assert.throws(()=>pickProjectedVertex([],Infinity,0));assert.throws(()=>pickProjectedVertex([],0,0,33));
console.log('Vertex picking: bounded screen radius, nearest point, depth/index ties and malformed projections passed');

const translated=objectMovePreview(source,1,[16,-8,32]);
assert.deepEqual(translated.vertices,[[1,2,3],[20,-3,38],[23,0,41]]);assert.deepEqual(source,before);assert.deepEqual(translated.normals,source.preview.normals);assert.deepEqual(translated.triangles,source.preview.triangles);
for(const [owner,offset] of [[2,[0,0,0]],[1,[32767,0,0]],[1,[0,-32769,0]],[1,[0,0,.5]],[1,[0,0,NaN]],[1,[0,0]]])assert.throws(()=>objectMovePreview(source,owner,offset));
console.log('Object translation: all owned rows, other object unchanged, immutable Current, overflow and retained normals/topology passed');
assert.throws(()=>objectMovePreview({preview:{objects:[{object_index:0,vertex_start:0,vertex_count:1}],vertices:[[-32768,0,0]]}},0,[-1,0,0]));

const boundSource=structuredClone(source);boundSource.preview.bounds={min:[1,2,3],max:[7,8,9]};const boundMove=objectMovePreview(boundSource,1,[16,-8,32]);assert.deepEqual(boundMove.bounds,{min:[1,-3,3],max:[23,2,41]});
const request={asset_id:'asset://fixture/model/0',object_index:1,expected_sha256:'a'.repeat(64)},expected={source_sha256:'b'.repeat(64),current_preview:source.preview,preview:translated},report={asset_id:request.asset_id,object_index:1,operation:'translation',source_sha256:expected.source_sha256,effective_sha256:request.expected_sha256,project_changed:false,proposed_sha256:'c'.repeat(64),current_preview:source.preview,preview:translated};
assert.deepEqual(qualifyObjectMoveReview(report,request,expected),report);
for(const mutation of [r=>r.object_index=0,r=>r.source_sha256='d'.repeat(64),r=>r.effective_sha256='d'.repeat(64),r=>r.project_changed=true,r=>r.proposed_sha256=request.expected_sha256,r=>r.preview.vertices[0][0]++,r=>r.current_preview.normals[0][0]++]){const changed=structuredClone(report);mutation(changed);assert.throws(()=>qualifyObjectMoveReview(changed,request,expected));}
console.log('Movement review: complete Current/Proposed geometry, exact source/owner/hash, bounds and forged/no-op replies passed');
assert.deepEqual(qualifyObjectMoveReview({...report,preview:Object.fromEntries(Object.entries(report.preview).reverse())},request,expected).preview,report.preview);
const enriched=structuredClone(report);enriched.preview.textures=[];enriched.current_preview.animation_support={status:'unposed'};assert.deepEqual(qualifyObjectMoveReview(enriched,request,expected),enriched);

const vectorRequest={...request,operation:'vector',kind:'vertices',vector_index:1,values:[16,17,18]},vectorExpected={...expected,preview:vertexMovePreview(source,1,1,vectorRequest.values)},vectorReport={...report,operation:'vector',kind:'vertices',vector_index:1,values:vectorRequest.values,preview:vectorExpected.preview};
assert.deepEqual(qualifyObjectMoveReview(vectorReport,vectorRequest,vectorExpected),vectorReport);
for(const changes of [{vector_index:0},{kind:'normals'},{values:[16,17,19]},{operation:'translation'}])assert.throws(()=>qualifyObjectMoveReview({...vectorReport,...changes},vectorRequest,vectorExpected));
console.log('Vertex scene review: exact vector owner/index/kind/XYZ and candidate geometry passed');

const {retailMovementSource,retailMovementVertex}=await import('../editor/model-vertex-move.js');
const retail={schema_version:'legaia.model-preview.v1',coordinate_system:'retail_tmd_object_local',posed:false,objects:[{object_index:0,vertex_start:0,vertex_count:3,triangle_start:0,triangle_count:1}],vertices:[[1,2,3],[4,5,6],[7,8,9]],triangles:[[0,1,2]]};
const current={preview:{objects:[{object_index:0,vertex_count:4},{object_index:1,vertex_count:3}]},retail_preview:retail},baseline=retailMovementSource(current);
assert.deepEqual(baseline,retail);assert.deepEqual(retailMovementVertex(baseline,0,1),[4,5,6]);
const copied=retailMovementVertex(baseline,0,1);copied[0]=99;assert.equal(baseline.vertices[1][0],4);baseline.vertices[0][0]=99;assert.equal(retail.vertices[0][0],1);
for(const [owner,index] of [[0,3],[1,0],[-1,0],[0,-1],[0,.5]])assert.equal(retailMovementVertex(baseline,owner,index),null);
for(const mutate of [p=>p.posed=true,p=>p.coordinate_system='scene',p=>p.objects[0].vertex_start=1,p=>p.objects[0].vertex_count=5,p=>p.objects[0].triangle_count=2,p=>p.triangles[0][0]=3,p=>p.vertices[0][0]=32768,p=>p.vertices[0][0]=.5]){const bad=structuredClone(current);mutate(bad.retail_preview);assert.throws(()=>retailMovementSource(bad));}
assert.throws(()=>retailMovementSource({preview:current.preview}));
console.log('Retail movement: independent topology, immutable source/row copies, absent appended rows/objects and malformed ranges/coordinates passed');

const {parseVertexGroup,vertexGroupMovePreview}=await import('../editor/model-vertex-move.js');
assert.deepEqual(parseVertexGroup('2, 0',3),[0,2]);
for(const text of ['',',','0,0','-1','3','1.5','0,','x','1e0'])assert.throws(()=>parseVertexGroup(text,3));
const grouped=vertexGroupMovePreview(source,1,[0,1],[16,-8,32]);assert.deepEqual(grouped,translated);assert.deepEqual(source,before);
assert.deepEqual(vertexGroupMovePreview(source,1,[1],[1,2,3]).vertices,[[1,2,3],[4,5,6],[8,10,12]]);
for(const [indices,offset] of [[[],[0,0,0]],[[0,0],[0,0,0]],[[2],[0,0,0]],[[true],[0,0,0]],[[0],[32767,0,0]]])assert.throws(()=>vertexGroupMovePreview(source,1,indices,offset));
const groupRequest={...request,operation:'vertex_translation',values:{indices:[0,1],offset:[16,-8,32]}},groupReport={...report,operation:'vertex_translation',values:groupRequest.values};
assert.deepEqual(qualifyObjectMoveReview(groupReport,groupRequest,expected),groupReport);assert.throws(()=>qualifyObjectMoveReview({...groupReport,values:{indices:[0],offset:[16,-8,32]}},groupRequest,expected));
console.log('Vertex groups: bounded unique local indices, exact subset movement, immutable Current, overflow and scene review identity passed');

const {qualifyVertexGroupRecall}=await import('../editor/model-vertex-move.js');
const savedGroup={id:'vertex-group://fixture',name:'Region',scene_id:'scene://fixture',import_sha256:'a'.repeat(64),asset_id:request.asset_id,object_index:1,indices:[0,1],source_sha256:'b'.repeat(64),allocation_key:null,review_key:'c'.repeat(64)},recall={schema_version:'legaia.model-vertex-group-review.v1',...savedGroup,project_source_key:'d'.repeat(64),read_only:true};
assert.deepEqual(qualifyVertexGroupRecall(recall,savedGroup,recall.project_source_key,request.asset_id,source.preview.objects),recall);
for(const changed of [{read_only:false},{indices:[1]},{object_index:0},{project_source_key:'a'.repeat(64)},{review_key:'a'.repeat(64)},{asset_id:'asset://other'}])assert.throws(()=>qualifyVertexGroupRecall({...recall,...changed},savedGroup,recall.project_source_key,request.asset_id,source.preview.objects));
console.log('Saved vertex groups: exact source, object, membership, saved review identity and read-only recall qualification passed');

const {vertexGroupAlignPreview}=await import('../editor/model-vertex-move.js');
assert.deepEqual(vertexGroupAlignPreview(source,1,[0,1],'x','center').vertices,[[1,2,3],[6,5,6],[6,8,9]]);assert.deepEqual(vertexGroupAlignPreview(source,1,[0,1],'z','min').vertices,[[1,2,3],[4,5,6],[7,8,6]]);assert.deepEqual(source,before);
const neg={preview:{objects:[{object_index:0,vertex_start:0,vertex_count:2}],vertices:[[-4,0,0],[3,0,0]]}};assert.equal(vertexGroupAlignPreview(neg,0,[0,1],'x','center').vertices[0][0],-1);
for(const [axis,anchor] of [['w','min'],['x','mean'],[true,'center']])assert.throws(()=>vertexGroupAlignPreview(source,1,[0,1],axis,anchor));
const alignRequest={...request,operation:'vertex_alignment',values:{indices:[0,1],axis:'x',anchor:'center'}},alignPreview=vertexGroupAlignPreview(source,1,[0,1],'x','center'),alignReport={...report,operation:'vertex_alignment',values:alignRequest.values,preview:alignPreview};assert.deepEqual(qualifyObjectMoveReview(alignReport,alignRequest,{...expected,preview:alignPreview}),alignReport);assert.throws(()=>qualifyObjectMoveReview({...alignReport,values:{...alignRequest.values,axis:'z'}},alignRequest,{...expected,preview:alignPreview}));
console.log('Vertex alignment: exact selected axis/plane, immutable other rows, signed centre rounding and review identity passed');
const {vertexGroupScalePreview}=await import('../editor/model-vertex-move.js');
assert.deepEqual(vertexGroupScalePreview(source,1,[0,1],200,'origin').vertices,[[1,2,3],[8,10,12],[14,16,18]]);
assert.deepEqual(vertexGroupScalePreview(source,1,[0,1],200,'center').vertices,[[1,2,3],[3,4,5],[9,10,11]]);
assert.deepEqual(vertexGroupScalePreview(neg,0,[0,1],150,'center').vertices,[[-6,0,0],[5,0,0]]);
assert.deepEqual(vertexGroupScalePreview(source,1,[0,1],100,'center').vertices,source.preview.vertices);assert.deepEqual(source,before);
for(const [percent,pivot] of [[0,'origin'],[1001,'origin'],[true,'center'],[1.5,'center'],[100,'mean']])assert.throws(()=>vertexGroupScalePreview(source,1,[0,1],percent,pivot));
assert.throws(()=>vertexGroupScalePreview({preview:{objects:[{object_index:0,vertex_start:0,vertex_count:1}],vertices:[[32767,0,0]]}},0,[0],200,'origin'));
const scaleRequest={...request,operation:'vertex_scaling',values:{indices:[0,1],percent:150,pivot:'center'}},scalePreview=vertexGroupScalePreview(source,1,[0,1],150,'center'),scaleReport={...report,operation:'vertex_scaling',values:scaleRequest.values,preview:scalePreview};
qualifyObjectMoveReview(scaleReport,scaleRequest,{...expected,preview:scalePreview});assert.throws(()=>qualifyObjectMoveReview({...scaleReport,values:{...scaleRequest.values,pivot:'origin'}},scaleRequest,{...expected,preview:scalePreview}));
console.log('Vertex scaling: exact subset, origin/bounds pivot, signed half-away rounding, no-op, overflow and scene-review identity passed');

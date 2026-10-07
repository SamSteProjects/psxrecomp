import assert from 'node:assert/strict';
import {nearestSceneVertex,sceneMeasurement} from '../editor/scene-ruler.js';
import {SceneRenderer} from '../editor/scene-renderer.js';
const hit={entity_id:'environment://town01/field-map/cells/00001',geometry_key:'geometry:0',asset_id:'asset://town01/models/0',triangle_index:0},vertices=[[0,0,0],[10,0,0],[0,10,0]],matrix=[2,0,0,100,0,-1,0,40,0,0,3,200,0,0,0,1],project=p=>({x:p.x,y:p.y});
const a=nearestSceneVertex(hit,vertices,[0,1,2],matrix,project,{x:101,y:40});assert.equal(a.vertex_index,0);assert.deepEqual(a.display_position,{x:100,y:40,z:200});assert.deepEqual(a.decoded_model_position,[0,0,0]);
const b=nearestSceneVertex(hit,vertices,[0,1,2],matrix,project,{x:120,y:40});assert.equal(b.vertex_index,1);assert.deepEqual(b.display_position,{x:120,y:40,z:200});
assert.equal(nearestSceneVertex(hit,vertices,[0,1,2],matrix,project,{x:500,y:500}),null);assert.equal(nearestSceneVertex(hit,vertices,[0,1,2],matrix,()=>null,{x:0,y:0}),null);
assert.equal(nearestSceneVertex(hit,vertices,[2,0,1],matrix,project,{x:110,y:40}).vertex_index,0); // deterministic tied projected corners
const context={project_path:'project',scene_id:'scene://town01',source_key:'a'.repeat(64)},measurement=sceneMeasurement(context,a,b);assert.deepEqual(measurement.display_delta_b_minus_a,{x:20,y:0,z:0});assert.equal(measurement.distance_display_units,20);assert.equal(measurement.read_only,true);
const c=nearestSceneVertex(hit,vertices,[0,1,2],matrix,project,{x:100,y:30});assert.deepEqual(c.display_position,{x:100,y:30,z:200});assert.equal(sceneMeasurement(context,a,c).distance_display_units,10);
const diagonal=sceneMeasurement(context,a,{...b,display_position:{x:100,y:43,z:204}});assert.deepEqual(diagonal.display_delta_b_minus_a,{x:0,y:3,z:4});assert.equal(diagonal.distance_display_units,5);
measurement.endpoints.a.decoded_model_position[0]=99;assert.deepEqual(a.decoded_model_position,[0,0,0]);assert.throws(()=>sceneMeasurement(context,a,{display_position:{x:Infinity,y:0,z:0}}));
for(const triangle of [[0,1,99],[0,1],[true,1,2]])assert.throws(()=>nearestSceneVertex(hit,vertices,triangle,matrix,project,{x:0,y:0}));
assert.throws(()=>nearestSceneVertex(hit,vertices,[0,1,2],[...matrix.slice(0,12),0,0,1,1],project,{x:0,y:0}));
const instance={entity_id:hit.entity_id,geometry_key:hit.geometry_key,model_to_scene:matrix},renderer=Object.create(SceneRenderer.prototype);renderer.instances=[instance];renderer.scene={assets:[{geometry_key:hit.geometry_key,asset_id:hit.asset_id,preview:{vertices}}]};renderer.meshes=new Map([[hit.geometry_key,{triangles:[[0,1,2]]}]]);renderer.pickSurface=()=>hit;renderer.projectPoint=project;
const override=[1,0,0,5,0,-1,0,6,0,0,1,7,0,0,0,1],view={positions:new Map([[hit.entity_id,{x:50,y:60,z:70}]]),transforms:new Map([[hit.entity_id,override]])};
assert.deepEqual(renderer.pickSurfaceVertex(50,60,view).display_position,{x:50,y:60,z:70});assert.equal(renderer.pickSurfaceVertex(60,60,view).vertex_index,1);renderer.pickSurface=()=>null;assert.equal(renderer.pickSurfaceVertex(0,0,view),null);
console.log('Scene ruler: exact instance overrides/Y reflection, bounded triangle snapping, ties, missing hits and immutable distance evidence passed.');

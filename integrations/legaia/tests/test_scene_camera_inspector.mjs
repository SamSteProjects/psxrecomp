import assert from 'node:assert/strict';
import {sceneCameraDraft,cameraFromSceneDraft,parseSceneCameraDraft,MIN_CAMERA_PITCH_DEGREES} from '../editor/scene-camera-inspector.js';
import {sceneCameraBasis} from '../editor/scene-camera.js';
import {SceneRenderer} from '../editor/scene-renderer.js';
const current={projection:'perspective',target:{x:120,y:-360,z:490},distance:2000,yaw:-.65,pitch:.66},before=structuredClone(current);
const values=sceneCameraDraft(current),restored=cameraFromSceneDraft(values);assert.deepEqual(restored.target,current.target);assert.equal(restored.distance,current.distance);assert(Math.abs(restored.yaw-current.yaw)<1e-15);assert(Math.abs(restored.pitch-current.pitch)<1e-15);restored.target.x++;assert.deepEqual(current,before);
const raw=Object.fromEntries(Object.entries(values).map(([k,v])=>[k,String(v)]));assert.deepEqual(parseSceneCameraDraft(raw),values);assert.deepEqual(current,before);
for(const projection of ['perspective','orthographic'])for(const pitch of [projection==='perspective'?MIN_CAMERA_PITCH_DEGREES:0,45,90])for(const yaw of [-360,-90,0,180,360]){
 const camera=cameraFromSceneDraft({...values,projection,pitch,yaw});assert.equal(camera.projection,projection);assert(camera.pitch>=0&&camera.pitch<=Math.PI/2);if(projection==='perspective')assert(camera.pitch>=.12);
 const renderer=Object.create(SceneRenderer.prototype),view={width:900,height:600,camera,basis:sceneCameraBasis(camera)},pixel=renderer.projectPoint(camera.target,view);assert(Math.abs(pixel.x-450)<.001);assert(Math.abs(pixel.y-300)<.001);
 assert(Math.abs(sceneCameraDraft(camera).yaw)<=180);
}
const scientific=parseSceneCameraDraft({...raw,x:'-1.2e3',y:'+.5',z:' 3. ',distance:'2e3'});assert.equal(scientific.x,-1200);assert.equal(scientific.y,.5);assert.equal(scientific.z,3);
for(const [field,bad] of [['x',''],['y','0x10'],['z','Infinity'],['distance','NaN'],['yaw','1_000'],['pitch',null],['pitch',true],['x','1e999']])assert.throws(()=>parseSceneCameraDraft({...raw,[field]:bad}));
for(const bad of [{...values,projection:'fish'},{...values,distance:19},{...values,distance:1e8+1},{...values,x:1e12+1},{...values,yaw:361},{...values,pitch:MIN_CAMERA_PITCH_DEGREES-1e-9},{...values,projection:'orthographic',pitch:-1},{...values,pitch:91},{...values,x:NaN},{...values,distance:true},{...values,extra:1}])assert.throws(()=>cameraFromSceneDraft(bad));
for(const bad of [{...current,pitch:0},{...current,distance:0},{...current,target:{x:0,y:null,z:1}},{...current,yaw:Infinity}])assert.throws(()=>sceneCameraDraft(bad));
assert.deepEqual(current,before);console.log('Camera numeric drafts: coordinate/angle conversion, detached state, renderer projection, supported bounds and decimal refusal passed.');

import assert from 'node:assert/strict';
import {sceneCameraDraft,cameraFromSceneDraft,parseSceneCameraDraft,MIN_WORLD_CAMERA_PITCH_DEGREES} from '../editor/scene-camera-inspector.js';
const camera={projection:'perspective',yaw:-.65,pitch:.05,distance:10,target:{x:1234.5,y:-12.25,z:8000}},held=structuredClone(camera),draft=sceneCameraDraft(camera,'world');
const next=cameraFromSceneDraft(draft,'world');assert.deepEqual(next.target,camera.target);assert.equal(next.distance,10);assert.equal(next.pitch,.05);assert(Math.abs(next.yaw-camera.yaw)<1e-15);next.target.x++;assert.deepEqual(camera,held);
assert.throws(()=>sceneCameraDraft(camera)); // Field's prior minimums remain independent.
const raw=Object.fromEntries(Object.entries(draft).map(([k,v])=>[k,String(v)]));assert.deepEqual(parseSceneCameraDraft(raw,'world'),draft);
for(const projection of ['perspective','orthographic'])for(const pitch of [projection==='perspective'?MIN_WORLD_CAMERA_PITCH_DEGREES:0,45,90])for(const distance of [10,1e6]){const view=cameraFromSceneDraft({...draft,projection,pitch,distance},'world');assert.equal(view.distance,distance);assert(view.pitch>=0&&view.pitch<=Math.PI/2);assert.equal(sceneCameraDraft(view,'world').projection,projection);}
for(const change of [{distance:9.9},{distance:1e6+1},{x:1e8+1},{y:-1e8-1},{yaw:361},{pitch:MIN_WORLD_CAMERA_PITCH_DEGREES-1e-9},{projection:'orthographic',pitch:-1},{pitch:91},{distance:Infinity},{distance:true},{extra:0}])assert.throws(()=>cameraFromSceneDraft({...draft,...change},'world'));
for(const rawValue of ['', '0x10','Infinity','NaN','1e999','1_000'])assert.throws(()=>parseSceneCameraDraft({...raw,x:rawValue},'world'));
assert.throws(()=>sceneCameraDraft(camera,'unknown'));assert.throws(()=>cameraFromSceneDraft(draft,'unknown'));assert.deepEqual(camera,held);
console.log('World camera numeric profile: exact minimum pitch, display limits, detached conversion, decimal refusal and independent field defaults passed.');

import assert from 'node:assert/strict';
import {sceneCameraBasis,sceneCameraPlanePoint,sceneAxisCamera} from '../editor/scene-camera.js';
import {SceneRenderer} from '../editor/scene-renderer.js';
const original={projection:'perspective',yaw:-.65,pitch:.66,distance:1000,target:{x:100,y:200,z:300}},before=structuredClone(original),viewport={width:900,height:600},renderer=Object.create(SceneRenderer.prototype);
// Renderer matrices are Float32; compare well below one screen pixel.
const close=(a,b)=>assert(Math.abs(a-b)<1e-3,`${a} != ${b}`);
for(const axis of ['top','front','side']){
 const camera=sceneAxisCamera(original,axis),basis=sceneCameraBasis(camera),view={...viewport,camera,basis};
 assert.equal(camera.projection,'orthographic');assert.deepEqual(camera.target,original.target);camera.target.x++;assert.deepEqual(original,before);camera.target.x--;
 for(const [x,y] of [[450,300],[200,100],[800,500]]){
  const point=sceneCameraPlanePoint(camera,viewport,x,y),projected=renderer.projectPoint(point,view);close(projected.x,x);close(projected.y,y);
  const deeper={...point};for(const a of ['x','y','z'])deeper[a]+=basis.forward[a]*500;const distant=renderer.projectPoint(deeper,view);close(distant.x,x);close(distant.y,y);
  const zoom=structuredClone(camera),anchored=sceneCameraPlanePoint(zoom,viewport,x,y);zoom.distance*=.6;const shifted=sceneCameraPlanePoint(zoom,viewport,x,y);for(const a of ['x','y','z'])zoom.target[a]+=anchored[a]-shifted[a];const stable=renderer.projectPoint(anchored,{...view,camera:zoom});close(stable.x,x);close(stable.y,y);
 }
}
const front=sceneAxisCamera(original,'front'),side=sceneAxisCamera(original,'side');assert.equal(front.pitch,0);assert.equal(side.pitch,0);const f=sceneCameraPlanePoint(front,viewport,450,200),s=sceneCameraPlanePoint(side,viewport,550,300);assert(f.y>front.target.y);close(f.z,front.target.z);assert(s.z<side.target.z);close(s.x,side.target.x);
assert.throws(()=>sceneAxisCamera(original,'bottom'));for(const camera of [{...original,distance:0},{...original,pitch:NaN},{...original,target:{x:0,y:null,z:0}}])assert.throws(()=>sceneAxisCamera(camera,'front'));assert.throws(()=>sceneCameraPlanePoint(original,{width:0,height:10},0,0));assert.deepEqual(original,before);
console.log('Top/front/side camera orientation, GPU projection agreement, depth-independent coordinates, cursor zoom and detached display state passed.');

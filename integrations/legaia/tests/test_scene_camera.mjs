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

const {sceneFrameCamera}=await import('../editor/scene-camera.js');const corners=[...Array(8)].map((_,i)=>({x:i&1?5400:2800,y:i&2?300:-160,z:i&4?6100:4000}));
for(const projection of ['perspective','orthographic'])for(const shape of [{width:900,height:600},{width:300,height:1200},{width:1200,height:350}])for(const angles of [{yaw:-.65,pitch:.66},{yaw:0,pitch:projection==='orthographic'?0:.12},{yaw:Math.PI/2,pitch:Math.PI/2}]){
 const current={...original,projection,...angles},copy=structuredClone(current),geometry=structuredClone(corners),framed=sceneFrameCamera(current,shape,corners);assert.equal(framed.projection,projection);assert.equal(framed.yaw,current.yaw);assert.equal(framed.pitch,current.pitch);assert.deepEqual(current,copy);assert.deepEqual(corners,geometry);assert.notEqual(framed.target,current.target);
 for(const point of corners){const pixel=renderer.projectPoint(point,{...shape,camera:framed,basis:sceneCameraBasis(framed)});assert(pixel);assert(pixel.x>=shape.width*.1-.001&&pixel.x<=shape.width*.9+.001);assert(pixel.y>=shape.height*.1-.001&&pixel.y<=shape.height*.9+.001);}
}
const tiny=sceneFrameCamera(original,viewport,[{x:0,y:0,z:0}]);assert(tiny.distance>=20);for(const bad of [[],new Array(2),Array(4097).fill(corners[0]),[{x:0,y:NaN,z:0}],[{x:1e13,y:0,z:0}],[{x:0,y:null,z:0}],corners.map(p=>({...p,x:p.x*1e9}))])assert.throws(()=>sceneFrameCamera(original,viewport,bad));assert.throws(()=>sceneFrameCamera(original,{width:0,height:600},corners));assert.throws(()=>sceneFrameCamera({...original,projection:'unknown'},viewport,corners));assert.deepEqual(original,before);console.log('Bounded group framing: aspect-aware perspective/orthographic GPU fit, edge padding, preserved angles and detached display state passed.');

const {sceneFrameAllCamera}=await import('../editor/scene-camera.js');
const scenePoints=Array.from({length:8192},(_,i)=>({x:(i%73)*400-7000,y:(i%11)*100-200,z:(i%37)*300-5000}));
const sceneCopy=structuredClone(scenePoints);
for(const projection of ['perspective','orthographic'])for(const shape of [{width:1600,height:400},{width:280,height:1100}]){
 const current={...original,projection},framed=sceneFrameAllCamera(current,shape,scenePoints);
 assert.equal(framed.yaw,current.yaw);assert.equal(framed.pitch,current.pitch);assert.equal(framed.projection,projection);
 for(const point of scenePoints){const pixel=renderer.projectPoint(point,{...shape,camera:framed,basis:sceneCameraBasis(framed)});assert(pixel&&pixel.x>=shape.width*.1-.001&&pixel.x<=shape.width*.9+.001&&pixel.y>=shape.height*.1-.001&&pixel.y<=shape.height*.9+.001);}
}
assert.deepEqual(scenePoints,sceneCopy);assert.deepEqual(original,before);
for(const bad of [[],[{}],[{x:0,y:NaN,z:0}],Array(262145).fill(corners[0])])assert.throws(()=>sceneFrameAllCamera(original,viewport,bad));
console.log('Whole-scene framing retains every display point beyond the group bound, with padded wide/tall perspective and orthographic fits.');

const {sceneFrameMarkerCamera}=await import('../editor/scene-camera.js');
const markers=[{x:-18000,y:-900,z:400},{x:25000,y:1700,z:13000}];
for(const projection of ['perspective','orthographic'])for(const shape of [{width:1200,height:300},{width:250,height:1200}]){
 const current={...original,projection},framed=sceneFrameMarkerCamera(current,shape,markers);
 assert(framed.distance>=800);assert.equal(framed.yaw,current.yaw);assert.equal(framed.pitch,current.pitch);assert.equal(framed.projection,projection);
 for(const point of markers){const pixel=renderer.projectPoint(point,{...shape,camera:framed,basis:sceneCameraBasis(framed)});assert(pixel.x>=shape.width*.1-.001&&pixel.x<=shape.width*.9+.001&&pixel.y>=shape.height*.1-.001&&pixel.y<=shape.height*.9+.001);}
}
assert.equal(sceneFrameMarkerCamera(original,viewport,[{x:0,y:0,z:0}]).distance,800);
assert.throws(()=>sceneFrameMarkerCamera(original,viewport,[]));assert.deepEqual(original,before);
console.log('Display marker framing preserves context distance, angles/projection and padded wide/tall fits.');

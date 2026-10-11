import {worldmapCameraBasis as worldBasis} from '../editor/worldmap-camera.js';
import assert from 'node:assert/strict';
import {sceneCameraBasis,sceneAxisCamera,sceneScreenPan,sceneScreenZoom} from '../editor/scene-camera.js';
import {SceneRenderer} from '../editor/scene-renderer.js';
const renderer=Object.create(SceneRenderer.prototype),limits={minDistance:10,maxDistance:1e6,targetLimit:1e8};
const base={projection:'perspective',yaw:-.65,pitch:.8,distance:2048,target:{x:1024,y:-50,z:256}},viewport={width:900,height:600};

let comparisons=0;
for(const getBasis of [worldBasis,sceneCameraBasis])for(const projection of ['perspective','orthographic'])for(const axis of ['orbit','top','front','side']){
 const camera=axis==='orbit'?{...structuredClone(base),projection}:sceneAxisCamera(base,axis),basis=getBasis(camera),held=JSON.stringify(camera),x=650,y=180,scale=camera.distance/(Math.min(viewport.width,viewport.height)*.9),point={};
 for(const a of ['x','y','z'])point[a]=camera.target[a]+((x-viewport.width/2)*basis.right[a]-(y-viewport.height/2)*basis.up[a])*scale;
 for(const [a,b] of [['right','up'],['right','forward'],['up','forward']])assert(Math.abs(['x','y','z'].reduce((n,axis)=>n+basis[a][axis]*basis[b][axis],0))<1e-12);
 const before=renderer.projectPoint(point,{...viewport,camera,basis}),pan=sceneScreenPan(camera,viewport,basis,35,-20,limits),after=renderer.projectPoint(point,{...viewport,camera:pan,basis});
 assert(Math.abs(after.x-before.x-35)<.002);assert(Math.abs(after.y-before.y+20)<.002);assert.equal(pan.projection,camera.projection);
 for(const factor of [.5,2]){const zoom=sceneScreenZoom(camera,viewport,basis,x,y,factor,limits),shown=renderer.projectPoint(point,{...viewport,camera:zoom,basis});assert(Math.abs(shown.x-x)<.002);assert(Math.abs(shown.y-y)<.002);assert.equal(zoom.projection,camera.projection);comparisons++;}
 assert.equal(JSON.stringify(camera),held);
}
const b=worldBasis(base);assert.equal(sceneScreenZoom(base,viewport,b,450,300,1e9,limits).distance,1e6);assert.equal(sceneScreenZoom(base,viewport,b,450,300,1e-9,limits).distance,10);
for(const call of [()=>sceneScreenPan(base,viewport,b,Infinity,0,limits),()=>sceneScreenPan(base,viewport,{...b,forward:{...b.forward,y:-b.forward.y}},1,0,limits),()=>sceneScreenPan(base,viewport,{...b,right:{x:2,y:0,z:0}},1,0,limits),()=>sceneScreenZoom(base,viewport,b,-1,0,1,limits),()=>sceneScreenZoom(base,viewport,b,0,0,0,limits),()=>sceneScreenPan({...base,target:{x:1e8,y:0,z:0}},viewport,b,-1e6,0,limits)])assert.throws(call);
console.log(`${comparisons} independent World/field GPU cursor zoom comparisons, pan signs, axis views, clamped distance and finite/basis/target refusals pass.`);

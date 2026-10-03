import assert from 'node:assert/strict';
import {rotateSourceYaw,sourcePlaneAngle} from '../editor/worldmap-placement-yaw.js';
const values={offset:{x:1280,y:256,z:-128},yaw_units:3968};
assert.deepEqual(rotateSourceYaw(values,Math.PI/2,1),{offset:{x:1280,y:256,z:-128},yaw_units:896});
assert.equal(rotateSourceYaw(values,-Math.PI/2,1).yaw_units,2944);
assert.equal(rotateSourceYaw(values,Math.PI*2,1).yaw_units,3968);
assert.equal(rotateSourceYaw({...values,yaw_units:0},-Math.PI/4,512).yaw_units,3584);
assert.equal(rotateSourceYaw({...values,yaw_units:17},0,16).yaw_units,16);
assert.equal(values.yaw_units,3968);assert.notEqual(rotateSourceYaw(values,0).offset,values.offset);
for(const matrix of [[1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1],[1,0,0,.2,0,0,1,0,0,1,0,.3,0,0,0,5]]){
 const plane={matrix,pivot:{x:.1,y:0,z:.2},radius:.4,width:900,height:600};
 for(let units=0;units<4096;units+=31){const angle=units*Math.PI/2048,x=plane.pivot.x+Math.cos(angle)*plane.radius,z=plane.pivot.z-Math.sin(angle)*plane.radius,w=matrix[3]*x+matrix[11]*z+matrix[15],point={x:(x/w+1)*450,y:(1-z/w)*300},actual=sourcePlaneAngle(point,plane);assert(Math.abs(Math.atan2(Math.sin(actual-angle),Math.cos(actual-angle)))<1e-12);}
 assert.throws(()=>sourcePlaneAngle({x:(plane.pivot.x/(matrix[3]*plane.pivot.x+matrix[11]*plane.pivot.z+matrix[15])+1)*450,y:(1-plane.pivot.z/(matrix[3]*plane.pivot.x+matrix[11]*plane.pivot.z+matrix[15]))*300},plane),/origin/);
}
for(const [angle,step] of [[NaN,1],[Infinity,1],[1e308,1],[0,2]])assert.throws(()=>rotateSourceYaw(values,angle,step));
assert.throws(()=>rotateSourceYaw({...values,yaw_units:4096},0));
assert.throws(()=>sourcePlaneAngle({x:10,y:20},{matrix:Array(16).fill(0),pivot:{x:0,y:0,z:0},width:100,height:100,radius:10}),/edge-on/);
console.log('Source yaw signs, wrapping, absolute snapping, offset preservation and independent perspective plane inversion passed');

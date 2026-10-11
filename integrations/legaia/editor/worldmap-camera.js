// Native World display orientation, separate from field camera handedness.
export function worldmapCameraBasis(camera){
 if(!Number.isFinite(camera?.yaw)||!Number.isFinite(camera?.pitch))throw Error('World camera requires finite display angles.');
 const sy=Math.sin(camera.yaw),cy=Math.cos(camera.yaw),sp=Math.sin(camera.pitch),cp=Math.cos(camera.pitch);
 return {right:{x:cy,y:0,z:-sy},up:{x:sy*sp,y:cp,z:cy*sp},forward:{x:sy*cp,y:-sp,z:cy*cp}};
}

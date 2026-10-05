// Editor display coordinates only. These helpers never author entity transforms.
const finite=v=>typeof v==='number'&&Number.isFinite(v);
export function sceneCameraBasis(camera){
 if(!finite(camera?.yaw)||!finite(camera?.pitch))throw new Error('Invalid scene camera angles.');
 const s=Math.sin(camera.yaw),c=Math.cos(camera.yaw),sp=Math.sin(camera.pitch),cp=Math.cos(camera.pitch);
 return {right:{x:c,y:0,z:-s},up:{x:-s*sp,y:cp,z:-c*sp},forward:{x:-s*cp,y:-sp,z:-c*cp}};
}
export function sceneCameraPlanePoint(camera,viewport,x,y){
 if(!finite(camera?.distance)||camera.distance<=0||!['x','y','z'].every(a=>finite(camera.target?.[a]))||!finite(viewport?.width)||!finite(viewport?.height)||viewport.width<=0||viewport.height<=0||!finite(x)||!finite(y))throw new Error('Invalid scene camera plane coordinates.');
 const b=sceneCameraBasis(camera),scale=camera.distance/(Math.min(viewport.width,viewport.height)*.9),point={};
 for(const a of ['x','y','z'])point[a]=camera.target[a]+((x-viewport.width/2)*b.right[a]-(y-viewport.height/2)*b.up[a])*scale;
 return point;
}
export function sceneAxisCamera(camera,axis){
 const angles={top:[0,Math.PI/2],front:[0,0],side:[Math.PI/2,0]};
 if(!Object.hasOwn(angles,axis))throw new Error('Choose Top, Front or Side scene view.');
 sceneCameraPlanePoint(camera,{width:1,height:1},.5,.5);
 return {...camera,projection:'orthographic',yaw:angles[axis][0],pitch:angles[axis][1],target:{...camera.target}};
}

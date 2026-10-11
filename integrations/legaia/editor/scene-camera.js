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

// Fit current rendered bounds with ten percent screen padding on each edge.
export function sceneFrameCamera(camera,viewport,points,frameBasis=null){
 if(!['perspective','orthographic'].includes(camera?.projection)||!finite(viewport?.width)||!finite(viewport?.height)||viewport.width<1||viewport.height<1||viewport.width>1e6||viewport.height>1e6||!Array.isArray(points)||points.length<1||points.length>4096)throw new Error('Framing requires a current camera, viewport and bounded mesh corners.');
 sceneCameraPlanePoint(camera,viewport,viewport.width/2,viewport.height/2);
 const axes=['x','y','z'],lo={x:Infinity,y:Infinity,z:Infinity},hi={x:-Infinity,y:-Infinity,z:-Infinity};
 for(const point of points){if(!point||axes.some(a=>!finite(point[a])||Math.abs(point[a])>1e12))throw new Error('Framing bounds contain an invalid display point.');for(const a of axes){lo[a]=Math.min(lo[a],point[a]);hi[a]=Math.max(hi[a],point[a]);}}
 const target=Object.fromEntries(axes.map(a=>[a,(lo[a]+hi[a])/2])),basis=frameBasis??sceneCameraBasis(camera),focal=Math.min(viewport.width,viewport.height)*.9;
 screenCameraInputs(camera,viewport,basis,navigationLimits);
 let distance=20;
 for(const point of points){
  const relative=Object.fromEntries(axes.map(a=>[a,point[a]-target[a]])),dot=v=>axes.reduce((sum,a)=>sum+relative[a]*v[a],0),depth=dot(basis.forward);
  const horizontal=focal*Math.abs(dot(basis.right))/(viewport.width*.4),vertical=focal*Math.abs(dot(basis.up))/(viewport.height*.4);
  distance=Math.max(distance,horizontal-(camera.projection==='perspective'?depth:0),vertical-(camera.projection==='perspective'?depth:0),(-depth+.02)/.99999);
 }
 distance*=1.001; // Keep exact edge/near-plane corners inside the Float32 renderer.
 if(!finite(distance)||distance>1e8)throw new Error('Framing exceeds the supported camera distance.');
 return {...camera,target,distance};
}


// A whole visible scene may exceed the selected-group corner bound. Fit its
// enclosing box conservatively without discarding any loaded mesh or marker.
export function sceneFrameAllCamera(camera,viewport,points,frameBasis=null){
 if(!Array.isArray(points)||points.length<1||points.length>262144)throw Error('Scene framing requires bounded visible display points.');
 const axes=['x','y','z'],lo={x:Infinity,y:Infinity,z:Infinity},hi={x:-Infinity,y:-Infinity,z:-Infinity};
 for(const point of points){if(!point||axes.some(a=>!finite(point[a])||Math.abs(point[a])>1e12))throw Error('Scene framing contains invalid display bounds.');for(const a of axes){lo[a]=Math.min(lo[a],point[a]);hi[a]=Math.max(hi[a],point[a]);}}
 const corners=Array.from({length:8},(_,i)=>({x:(i&1?hi:lo).x,y:(i&2?hi:lo).y,z:(i&4?hi:lo).z}));
 return sceneFrameCamera(camera,viewport,corners,frameBasis);
}


// Marker views retain a useful context distance while fitting all display points.
export function sceneFrameMarkerCamera(camera,viewport,points){
 const framed=sceneFrameCamera(camera,viewport,points);
 return {...framed,distance:Math.max(800,framed.distance)};
}

// Use the renderer's supplied basis; camera navigation never changes native placements.
function screenCameraInputs(camera,viewport,basis,limits){
 const axes=['x','y','z'];
 if(!['perspective','orthographic'].includes(camera?.projection)||!finite(camera.yaw)||!finite(camera.pitch)||!finite(camera.distance)||camera.distance<=0||!axes.every(a=>finite(camera.target?.[a]))||!finite(viewport?.width)||!finite(viewport?.height)||viewport.width<=0||viewport.height<=0||viewport.width>1e6||viewport.height>1e6||!['right','up','forward'].every(row=>axes.every(a=>finite(basis?.[row]?.[a])))||!finite(limits?.minDistance)||!finite(limits.maxDistance)||!finite(limits.targetLimit)||limits.minDistance<=0||limits.maxDistance<limits.minDistance||limits.targetLimit<=0)throw Error('Camera navigation requires finite display inputs and limits.');
 for(const row of ['right','up','forward'])if(Math.abs(axes.reduce((n,a)=>n+basis[row][a]**2,0)-1)>1e-6)throw Error('Camera screen basis must have unit axes.');
 if([['right','up'],['right','forward'],['up','forward']].some(([a,b])=>Math.abs(axes.reduce((n,axis)=>n+basis[a][axis]*basis[b][axis],0))>1e-6))throw Error('Camera screen basis axes must be perpendicular.');
}
const navigationLimits={minDistance:20,maxDistance:1e8,targetLimit:1e12};
export function sceneScreenPan(camera,viewport,basis,dx,dy,limits=navigationLimits){
 screenCameraInputs(camera,viewport,basis,limits);if(!finite(dx)||!finite(dy)||Math.abs(dx)>1e6||Math.abs(dy)>1e6)throw Error('Camera pan exceeds its pointer budget.');
 const scale=camera.distance/(Math.min(viewport.width,viewport.height)*.9),target={};
 for(const a of ['x','y','z']){target[a]=camera.target[a]+(-dx*basis.right[a]+dy*basis.up[a])*scale;if(!finite(target[a])||Math.abs(target[a])>limits.targetLimit)throw Error('Camera pan exceeds its display coordinate bounds.');}
 return {...camera,target};
}
export function sceneScreenZoom(camera,viewport,basis,x,y,factor,limits=navigationLimits){
 screenCameraInputs(camera,viewport,basis,limits);if(!finite(x)||!finite(y)||x<0||y<0||x>viewport.width||y>viewport.height||!finite(factor)||factor<=0)throw Error('Camera zoom requires a bounded viewport cursor and positive factor.');
 const distance=Math.max(limits.minDistance,Math.min(limits.maxDistance,camera.distance*factor)),scale=(camera.distance-distance)/(Math.min(viewport.width,viewport.height)*.9),target={};
 for(const a of ['x','y','z']){target[a]=camera.target[a]+((x-viewport.width/2)*basis.right[a]-(y-viewport.height/2)*basis.up[a])*scale;if(!finite(target[a])||Math.abs(target[a])>limits.targetLimit)throw Error('Camera zoom exceeds its display coordinate bounds.');}
 return {...camera,target,distance};
}

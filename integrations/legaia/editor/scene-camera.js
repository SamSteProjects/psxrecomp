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
export function sceneFrameCamera(camera,viewport,points){
 if(!['perspective','orthographic'].includes(camera?.projection)||!finite(viewport?.width)||!finite(viewport?.height)||viewport.width<1||viewport.height<1||viewport.width>1e6||viewport.height>1e6||!Array.isArray(points)||points.length<1||points.length>4096)throw new Error('Framing requires a current camera, viewport and bounded mesh corners.');
 sceneCameraPlanePoint(camera,viewport,viewport.width/2,viewport.height/2);
 const axes=['x','y','z'],lo={x:Infinity,y:Infinity,z:Infinity},hi={x:-Infinity,y:-Infinity,z:-Infinity};
 for(const point of points){if(!point||axes.some(a=>!finite(point[a])||Math.abs(point[a])>1e12))throw new Error('Framing bounds contain an invalid display point.');for(const a of axes){lo[a]=Math.min(lo[a],point[a]);hi[a]=Math.max(hi[a],point[a]);}}
 const target=Object.fromEntries(axes.map(a=>[a,(lo[a]+hi[a])/2])),basis=sceneCameraBasis(camera),focal=Math.min(viewport.width,viewport.height)*.9;
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
export function sceneFrameAllCamera(camera,viewport,points){
 if(!Array.isArray(points)||points.length<1||points.length>262144)throw Error('Scene framing requires bounded visible display points.');
 const axes=['x','y','z'],lo={x:Infinity,y:Infinity,z:Infinity},hi={x:-Infinity,y:-Infinity,z:-Infinity};
 for(const point of points){if(!point||axes.some(a=>!finite(point[a])||Math.abs(point[a])>1e12))throw Error('Scene framing contains invalid display bounds.');for(const a of axes){lo[a]=Math.min(lo[a],point[a]);hi[a]=Math.max(hi[a],point[a]);}}
 const corners=Array.from({length:8},(_,i)=>({x:(i&1?hi:lo).x,y:(i&2?hi:lo).y,z:(i&4?hi:lo).z}));
 return sceneFrameCamera(camera,viewport,corners);
}

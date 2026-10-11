// Display reference geometry only; no floor, collision or native authoring writes.
export function sceneGridGeometry(view){
 const camera=view?.camera;if(!camera||![camera.distance,camera.target?.x,camera.target?.z].every(Number.isFinite)||camera.distance<=0||camera.distance>1e9||Math.abs(camera.target.x)>1e12||Math.abs(camera.target.z)>1e12)throw Error('Grid requires a finite positive camera distance.');
 const native=view.grid==='world-native';if(!native&&view.grid!==true)throw Error('Unsupported scene grid profile.');
 const spacing=native?128:10**Math.floor(Math.log10(camera.distance/7));
 if(!Number.isFinite(spacing)||spacing<=0)throw Error('Grid spacing is outside its finite display domain.');
 const radius=native?Math.min(64,Math.max(12,Math.ceil(camera.distance/spacing))):12;
 const cx=Math.round(camera.target.x/spacing)*spacing,cz=Math.round(camera.target.z/spacing)*spacing,half=spacing*radius;
 const data=[],add=(x,y,z,color)=>data.push(x,y,z,...color,0,0),line=(a,b,color)=>{add(...a,color);add(...b,color);};
 for(let i=-radius;i<=radius;i++){
  const color=n=>native&&n%8===0?[.25,.42,.45]:[.16,.23,.24];
  line([cx+i*spacing,0,cz-half],[cx+i*spacing,0,cz+half],color(cx/spacing+i));
  line([cx-half,0,cz+i*spacing],[cx+half,0,cz+i*spacing],color(cz/spacing+i));
 }
 if(native){const axis=512;line([0,0,0],[axis,0,0],[1,.28,.24]);line([0,0,0],[0,-axis,0],[.35,.85,.35]);line([0,0,0],[0,0,axis],[.3,.55,1]);}
 return {key:[view.grid,spacing,radius,cx,cz].join('/'),vertices:new Float32Array(data),count:data.length/8,spacing,radius};
}

// Editor display bounds only; never collision or runtime visibility evidence.
export function selectionBounds(points){
  if(!Array.isArray(points)||!points.length||points.length>256||points.some(p=>!p||['x','y','z'].some(a=>!Number.isFinite(p[a])||!Number.isFinite(Math.fround(p[a])))))throw Error('Selection needs finite bounded display points.');
  const min=['x','y','z'].map(a=>Math.min(...points.map(p=>p[a]))),max=['x','y','z'].map(a=>Math.max(...points.map(p=>p[a])));
  return {min,max,target:Object.fromEntries(['x','y','z'].map((a,i)=>[a,(min[i]+max[i])/2])),distance:Math.max(300,Math.hypot(...max.map((n,i)=>n-min[i]))*1.4)};
}
export function selectionBoundsLines(points){
  const {min,max}=selectionBounds(points),data=[];
  for(let corner=0;corner<8;corner++)for(const axis of [1,2,4])if(!(corner&axis))for(const c of [corner,corner|axis])data.push(c&1?max[0]:min[0],c&2?max[1]:min[1],c&4?max[2]:min[2],1,.8,.15,0,0);
  return new Float32Array(data);
}

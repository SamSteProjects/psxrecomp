// Screen-space selection includes hidden projected rows, independent of marker cap.
export function selectVertexRectangle(points,start,end,width,height,existing=[],add=false){
  if(!Array.isArray(points)||points.length>524288||![start,end].every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite))||![width,height].every(v=>Number.isFinite(v)&&v>0&&v<=65536)||typeof add!=='boolean'||!Array.isArray(existing)||existing.length>4096||existing.some(i=>!Number.isSafeInteger(i)||i<0)||new Set(existing).size!==existing.length)throw new Error('Invalid vertex marquee bounds or existing selection.');
  const min=start.map((v,a)=>Math.max(0,Math.min(v,end[a]))),max=start.map((v,a)=>Math.min(a?height:width,Math.max(v,end[a]))),selected=new Set(add?existing:[]);
  for(const point of points){if(!point||!Number.isSafeInteger(point.index)||point.index<0||![point.x,point.y,point.depth].every(Number.isFinite)||point.x<min[0]||point.x>max[0]||point.y<min[1]||point.y>max[1])continue;selected.add(point.index);if(selected.size>4096)throw new Error('Marquee exceeds 4096 vertices; selection was retained.');}
  return [...selected].sort((a,b)=>a-b);
}

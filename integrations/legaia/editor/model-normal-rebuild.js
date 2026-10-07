// Exact integer normalization; no floating-point cross products or square roots.
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function words(rows){if(!Array.isArray(rows)||!rows.length||rows.length>8192)throw Error('Normal rebuild needs bounded vectors.');return Array.from(rows,row=>{if(!Array.isArray(row)||row.length!==3||[0,1,2].some(i=>!Number.isInteger(row[i])||row[i]<-32768||row[i]>32767))throw Error('Normal rebuild requires signed16 XYZ.');return row.map(BigInt);});}
function root(n){if(n<2n)return n;let x=n,y=(x+1n)/2n;while(y<x){x=y;y=(x+n/x)/2n;}return x;}
export function rebuildNormalWords(vertices,normals,faces,direction){
 if(!['winding','reverse'].includes(direction)||!Array.isArray(faces)||faces.length>4096)throw Error('Choose bounded faces and a normal direction.');
 const v=words(vertices),n=words(normals),sums=new Map();
 for(const f of faces){if(f.normal_indices===null)continue;const count=f.corner_count,refs=f.normal_indices;
  if(![3,4].includes(count)||typeof f.gouraud!=='boolean'||!Array.isArray(f.vertices)||f.vertices.length!==count||f.vertices.some(i=>!Number.isInteger(i)||i<0||i>=v.length)||!Array.isArray(refs)||refs.length!==(f.gouraud?count:1)||refs.some(i=>!Number.isInteger(i)||i<0||i>=n.length))throw Error('Normal rebuild face references are invalid.');
  for(const corners of count===4?[[0,1,2],[1,3,2]]:[[0,1,2]]){const [a,b,c]=corners.map(i=>v[f.vertices[i]]),u=b.map((x,i)=>x-a[i]),w=c.map((x,i)=>x-a[i]),cross=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];if(cross.every(x=>x===0n))throw Error('Degenerate lit triangle.');
   for(const i of new Set(f.gouraud?corners.map(i=>refs[i]):refs)){const sum=sums.get(i)??[0n,0n,0n];sums.set(i,sum.map((x,a)=>x+cross[a]));}
  }
 }
 if(!sums.size)throw Error('No existing lit normal references.');const result=normals.map(row=>[...row]);
 for(const [i,sum] of sums){const squared=sum.reduce((s,x)=>s+x*x,0n);if(!squared)throw Error('Cancelling face directions.');result[i]=sum.map(x=>{const a=(x<0n?-x:x)*4096n;let q=root(a*a/squared);if(4n*a*a>=(2n*q+1n)**2n*squared)q++;return Number(q)*(x<0n?-1:1)*(direction==='reverse'?-1:1)||0;});}return result;
}
export function qualifyNormalRebuild(report,obj,values){
 const expected=rebuildNormalWords(obj.vertices,obj.normals,report.normal_rebuild_faces,values.direction);
 if(!equal(report.values,values)||!equal(report.normal_rebuild_words?.current,obj.normals)||!equal(report.normal_rebuild_words?.proposed,expected)||!equal(report.preview.vertices,report.current_preview.vertices)||!equal(report.preview.triangles,report.current_preview.triangles)||!Array.isArray(report.changes_from_current)||report.changes_from_current.some(row=>row.kind!=='normal'||row.object_index!==report.object_index))throw Error('Normal rebuild review differs from exact native words.');return expected;
}

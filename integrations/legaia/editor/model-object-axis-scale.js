const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function scaleObjectWords(object,values){
 const {percents,pivot}=values;
 if(!Array.isArray(percents)||percents.length!==3||[0,1,2].some(a=>!Number.isSafeInteger(percents[a])||percents[a]<1||percents[a]>1000)||!['origin','center'].includes(pivot)||!Array.isArray(object?.vertices)||object.vertices.length<1||object.vertices.length>8192||!Array.isArray(object.normals)||object.normals.length>8192)throw Error('Choose three integer scale percents1..1000 and origin or center pivot.');
 const rows=kind=>Array.from(object[kind],row=>{if(!Array.isArray(row)||row.length!==3||[0,1,2].some(a=>!Number.isSafeInteger(row[a])||row[a]< -32768||row[a]>32767))throw Error('Object vectors require signed16 XYZ.');return row;});
 const vertices=rows('vertices'),normals=rows('normals'),center2=[0,1,2].map(a=>pivot==='origin'?0:Math.min(...vertices.map(v=>v[a]))+Math.max(...vertices.map(v=>v[a]))),checked=v=>{if(v< -32768||v>32767)throw Error('Object axis scale exceeds signed16 bounds.');return v||0;};
 return {vertices:vertices.map(row=>row.map((v,a)=>{const n=(2*v-center2[a])*percents[a]+100*center2[a];return checked(Math.sign(n)*Math.floor((Math.abs(n)+100)/200));})),normals:normals.map(row=>{
  const length2=row.reduce((s,v)=>s+BigInt(v)**2n,0n);if(!length2)return [0,0,0];
  const weights=row.map((v,a)=>BigInt(v)*BigInt(percents[(a+1)%3])*BigInt(percents[(a+2)%3])),denominator=weights.reduce((s,v)=>s+v*v,0n);
  return weights.map(v=>{const numerator=v*v*length2;let low=0n,high=65537n;while(high-low>1n){const mid=(low+high)/2n;if(mid*mid*denominator<=numerator)low=mid;else high=mid;}if(4n*numerator>=denominator*(2n*low+1n)**2n)low++;return checked(Number(v<0n?-low:low));});
 })};
}
export function qualifyObjectAxisScale(report,object,values){
 const current={vertices:object.vertices,normals:object.normals},expected=scaleObjectWords(object,values);
 if(!equal(report.values,values)||!equal(report.object_axis_scale_words?.current,current)||!equal(report.object_axis_scale_words?.proposed,expected)||!equal(report.preview.triangles,report.current_preview.triangles)||!Array.isArray(report.changes_from_current)||report.changes_from_current.some(row=>!['vertex','normal'].includes(row.kind)||row.object_index!==report.object_index))throw Error('Object scale review differs from exact local vector words.');
 return expected;
}

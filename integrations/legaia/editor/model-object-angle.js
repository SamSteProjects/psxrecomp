import {sourceYawSinCos,SOURCE_YAW_Q30} from './environment-rotation-math.js';
import {rotateStoredNormals} from './model-normal-rotation.js';
export function rotateObjectWords(object,values){
 const {axis,angle_units:angle,pivot}=values;
 if(!['x','y','z'].includes(axis)||!Number.isSafeInteger(angle)||angle<0||angle>4095||!['origin','center'].includes(pivot)||!Array.isArray(object?.vertices)||object.vertices.length<1||object.vertices.length>8192||!Array.isArray(object.normals)||object.normals.length>8192)throw Error('Choose object vectors, an axis, native angle and origin or center pivot.');
 const rows=Array.from(object.vertices,row=>{if(!Array.isArray(row)||row.length!==3||[0,1,2].some(i=>!Number.isSafeInteger(row[i])||row[i]< -32768||row[i]>32767))throw Error('Object vertices require signed16 XYZ.');return row;});
 const center=[0,1,2].map(a=>pivot==='origin'?0:rows.reduce((v,r)=>Math.min(v,r[a]),Infinity)+rows.reduce((v,r)=>Math.max(v,r[a]),-Infinity)),{sin,cos}=sourceYawSinCos(angle),s=BigInt(sin),c=BigInt(cos),q=SOURCE_YAW_Q30;
 const round=n=>{const a=n<0n?-n:n,v=Number((a+q)/(2n*q))*(n<0n?-1:1);if(v< -32768||v>32767)throw Error('Object rotation exceeds signed16 bounds.');return v||0;};
 const vertices=rows.map(row=>{const [x,y,z]=row.map((v,a)=>BigInt(2*v-center[a])),rotated=axis==='x'?[x*q,y*c-z*s,z*c+y*s]:axis==='y'?[x*c+z*s,y*q,z*c-x*s]:[x*c-y*s,y*c+x*s,z*q];return rotated.map((n,a)=>round(n+BigInt(center[a])*q));});
 return {vertices,normals:object.normals.length?rotateStoredNormals(object.normals,axis,angle):[]};
}
export function qualifyObjectAngle(report,object,values){
 const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b),current={vertices:object.vertices,normals:object.normals},expected=rotateObjectWords(object,values);
 if(!equal(report.values,values)||!equal(report.object_rotation_words?.current,current)||!equal(report.object_rotation_words?.proposed,expected)||!equal(report.preview.triangles,report.current_preview.triangles)||!Array.isArray(report.changes_from_current)||report.changes_from_current.some(row=>!['vertex','normal'].includes(row.kind)||row.object_index!==report.object_index))throw Error('Object angle review differs from exact local vector words.');
 return expected;
}

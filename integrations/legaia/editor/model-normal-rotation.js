import {sourceYawSinCos,SOURCE_YAW_Q30} from './environment-rotation-math.js';
export function normalAngleUnits(degrees){
 if(!Number.isFinite(degrees)||degrees< -360||degrees>360)throw Error('Choose normal rotation degrees from -360 through 360.');
 const magnitude=Math.floor(Math.abs(degrees)*4096/360+.5),signed=degrees<0?-magnitude:magnitude;return (signed%4096+4096)%4096;
}
export function rotateStoredNormals(normals,axis,angleUnits){
 if(!['x','y','z'].includes(axis)||!Number.isSafeInteger(angleUnits)||angleUnits<0||angleUnits>4095||!Array.isArray(normals)||normals.length<1||normals.length>8192)throw Error('Choose an axis, native angle and 1..8192 stored normal rows.');
 const {sin,cos}=sourceYawSinCos(angleUnits),s=BigInt(sin),c=BigInt(cos),q=SOURCE_YAW_Q30;
 const round=n=>{const a=n<0n?-n:n,value=Number((a+q/2n)/q)*(n<0n?-1:1);if(value< -32768||value>32767)throw Error('Normal rotation exceeds signed16 bounds.');return value||0;};
 return Array.from(normals,row=>{
  if(!Array.isArray(row)||row.length!==3||[0,1,2].some(i=>!Number.isSafeInteger(row[i])||row[i]< -32768||row[i]>32767))throw Error('Stored normal rows require signed16 XYZ.');
  const [x,y,z]=row.map(BigInt),rotated=axis==='x'?[x*q,y*c-z*s,z*c+y*s]:axis==='y'?[x*c+z*s,y*q,z*c-x*s]:[x*c-y*s,y*c+x*s,z*q];return rotated.map(round);
 });
}
export function qualifyNormalRotation(report,words,values){
 const expected=rotateStoredNormals(words,values.axis,values.angle_units),equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 if(!equal(report.values,values)||!equal(report.normal_rotation_words?.current,words)||!equal(report.normal_rotation_words?.proposed,expected)||!equal(report.preview.vertices,report.current_preview.vertices)||!equal(report.preview.triangles,report.current_preview.triangles)||!Array.isArray(report.changes_from_current)||report.changes_from_current.some(row=>row.kind!=='normal'||row.object_index!==report.object_index))throw Error('Normal rotation review differs from the exact local normal words.');
 return expected;
}

// Source-vector direction diagnostic; this does not simulate retail GTE lighting.
const finite=value=>typeof value==='number'&&Number.isFinite(value);
export function sourceNormalMatrix(matrix){
  if(!Array.isArray(matrix)||matrix.length!==16||!matrix.every(finite)||matrix[12]!==0||matrix[13]!==0||matrix[14]!==0||matrix[15]!==1)throw new Error('Source normal diagnostic requires a finite affine model matrix.');
  const values=[0,1,2,4,5,6,8,9,10].map(i=>matrix[i]),scale=Math.max(...values.map(Math.abs));
  if(scale===0)return null;
  const [a,b,c,d,e,f,g,h,i]=values.map(value=>value/scale);
  const cofactors=[e*i-f*h,f*g-d*i,d*h-e*g,c*h-b*i,a*i-c*g,b*g-a*h,b*f-c*e,c*d-a*f,a*e-b*d];
  const determinant=a*cofactors[0]+b*cofactors[1]+c*cofactors[2];
  if(!finite(determinant)||Math.abs(determinant)<=1e-8)return null;
  const result=cofactors.map(value=>value/determinant/scale);
  return result.every(finite)?result:null;
}
export function sourceNormalDirection(vector,matrix){
  const neutral=status=>({status,color:[.5,.5,.5]});
  if(vector===null)return neutral('unavailable');
  if(!Array.isArray(vector)||vector.length!==3||vector.some(value=>!Number.isInteger(value)||value<-32768||value>32767))throw new Error('Invalid qualified source normal.');
  if(vector.every(value=>value===0))return neutral('zero');
  if(matrix===null)return neutral('singular');
  if(!Array.isArray(matrix)||matrix.length!==9||!matrix.every(finite))throw new Error('Invalid source normal direction matrix.');
  const direction=[0,1,2].map(row=>vector.reduce((sum,value,col)=>sum+matrix[row*3+col]*value,0));
  const length=Math.hypot(...direction);return length>0&&finite(length)?{status:'direction',color:direction.map(value=>value/length*.5+.5)}:neutral('singular');
}
export function sourceNormalColor(vector,matrix){return sourceNormalDirection(vector,matrix).color;}
export function qualifySourceNormals(preview){
  const normals=preview.triangle_normals,metadata=preview.normal_preview;
  if(normals!==undefined&&(!Array.isArray(normals)||normals.length!==preview.triangles.length||normals.some(row=>row!==null&&(!Array.isArray(row)||row.length!==3||row.some(vector=>!Array.isArray(vector)||vector.length!==3||vector.some(value=>!Number.isInteger(value)||value<-32768||value>32767))))))throw new Error('Model source normals differ from its qualified triangle layout.');
  if(metadata!==undefined&&(!metadata||metadata.status!=='source_unposed'||metadata.coordinate_system!=='retail_tmd_object_local'))throw new Error('Model source normal qualification is invalid.');
  return normals!==undefined&&metadata!==undefined&&preview.posed===false&&!preview.frames?.length;
}

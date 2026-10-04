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
  const rigid=metadata?.status==='source_rigid_pose';
  const validVector=vector=>Array.isArray(vector)&&vector.length===3&&(rigid?vector.every(finite)&&Math.hypot(...vector)<=Math.sqrt(3)*32768+1e-6:vector.every(value=>Number.isInteger(value)&&value>=-32768&&value<=32767));
  if(normals!==undefined&&(!Array.isArray(normals)||normals.length!==preview.triangles.length||normals.some(row=>row!==null&&(!Array.isArray(row)||row.length!==3||row.some(vector=>!validVector(vector))))))throw new Error('Model source normals differ from its qualified triangle layout.');
  if(metadata!==undefined&&(!metadata||(rigid?metadata.coordinate_system!=='retail_psx_actor_local_y_down'||metadata.transform!=='sdk_analytic_rz_ry_rx':metadata.status!=='source_unposed'||metadata.coordinate_system!=='retail_tmd_object_local')))throw new Error('Model source normal qualification is invalid.');
  return normals!==undefined&&metadata!==undefined&&preview.posed===rigid&&!preview.frames?.length;
}

// One frame at a time. Raw source arrays remain unchanged; translation never
// affects directions. This matches animation.py's independent rigid channels.
export function qualifyRigidPoseScope(scope,vertexCount,objects=null){
  const keys=['kind','object_count','posed_object_count','unposed_object_indices','unposed_vertex_start'];
  if(!scope||Object.keys(scope).length!==keys.length||keys.some(key=>!Object.hasOwn(scope,key))||scope.kind!=='existing_channel_prefix'||!Number.isSafeInteger(scope.object_count)||scope.object_count<2||scope.object_count>1024||!Number.isSafeInteger(scope.posed_object_count)||scope.posed_object_count<1||scope.posed_object_count>=scope.object_count||!Array.isArray(scope.unposed_object_indices)||JSON.stringify(scope.unposed_object_indices)!==JSON.stringify(Array.from({length:scope.object_count-scope.posed_object_count},(_,i)=>i+scope.posed_object_count))||!Number.isSafeInteger(scope.unposed_vertex_start)||scope.unposed_vertex_start<0||scope.unposed_vertex_start>vertexCount)throw new Error('Invalid explicit unposed native object scope.');
  if(objects&&(objects.length!==scope.object_count||objects.slice(0,scope.posed_object_count).reduce((count,obj)=>count+obj.vertex_count,0)!==scope.unposed_vertex_start))throw new Error('Unposed native scope differs from its object ranges.');
  return scope;
}
export function rigidFrameNormals(source,frame){
  if(source?.posed!==false||source.normal_preview?.status!=='source_unposed'||!qualifySourceNormals({...source,frames:undefined}))throw new Error('Rigid normals require qualified unposed source vectors.');
  if(frame?.posed!==true||frame.coordinate_system!=='retail_psx_actor_local_y_down'||!Array.isArray(source.objects)||!Array.isArray(frame.object_transforms)||source.triangles.length>100000||source.vertices.length>100000)throw new Error('Rigid normal channel mapping is unavailable.');
  const scope=source.pose_scope===undefined?null:qualifyRigidPoseScope(source.pose_scope,source.vertices.length,source.objects),known=scope?.posed_object_count??source.objects.length;
  if(known!==frame.object_transforms.length)throw new Error('Rigid normal channel count differs from its explicit pose scope.');
  const normals=new Array(source.triangles.length),vertexOwners=new Int32Array(source.vertices.length).fill(-1),seen=new Set();
  for(let i=0;i<source.objects.length;i++){
    const object=source.objects[i],channel=i<known?frame.object_transforms[i]:{object_index:i,rotation_psx:[0,0,0],translation:[0,0,0]};
    if(!Number.isInteger(object.object_index)||object.object_index<0||seen.has(object.object_index)||channel?.object_index!==object.object_index)throw new Error('Rigid normal channel does not match its source object.');
    seen.add(object.object_index);
    for(const [start,count,bound] of [[object.vertex_start,object.vertex_count,source.vertices.length],[object.triangle_start,object.triangle_count,normals.length]])if(!Number.isInteger(start)||!Number.isInteger(count)||start<0||count<0||start+count>bound)throw new Error('Rigid normal object span is invalid.');
    for(let v=object.vertex_start;v<object.vertex_start+object.vertex_count;v++){if(vertexOwners[v]!==-1)throw new Error('Rigid normal vertex spans overlap.');vertexOwners[v]=i;}
    if(!Array.isArray(channel.rotation_psx)||channel.rotation_psx.length!==3||channel.rotation_psx.some(v=>!Number.isInteger(v)||v<0||v>=4096)||!Array.isArray(channel.translation)||channel.translation.length!==3||!channel.translation.every(finite))throw new Error('Rigid normal transform components are invalid.');
    const [rx,ry,rz]=channel.rotation_psx.map(v=>v*Math.PI*2/4096),sx=Math.sin(rx),cx=Math.cos(rx),sy=Math.sin(ry),cy=Math.cos(ry),sz=Math.sin(rz),cz=Math.cos(rz);
    const rotate=vector=>{let [x,y,z]=vector;[y,z]=[y*cx-z*sx,y*sx+z*cx];[x,z]=[x*cy+z*sy,-x*sy+z*cy];return [x*cz-y*sz,x*sz+y*cz,z];};
    for(let t=object.triangle_start;t<object.triangle_start+object.triangle_count;t++){
      if(normals[t]!==undefined)throw new Error('Rigid normal triangle spans overlap.');
      const triangle=source.triangles[t];if(!Array.isArray(triangle)||triangle.length!==3||triangle.some(v=>!Number.isInteger(v)||v<object.vertex_start||v>=object.vertex_start+object.vertex_count))throw new Error('Rigid normal triangle crosses its source object.');
      normals[t]=source.triangle_normals[t]?.map(rotate)??null;
    }
  }
  if(vertexOwners.some(v=>v===-1)||normals.includes(undefined))throw new Error('Rigid normals leave geometry without an evidenced channel.');
  return {triangle_normals:normals,normal_preview:{...source.normal_preview,status:'source_rigid_pose',coordinate_system:'retail_psx_actor_local_y_down',transform:'sdk_analytic_rz_ry_rx',...(scope?{pose_scope:structuredClone(scope)}:{})},posed:true,frames:undefined};
}

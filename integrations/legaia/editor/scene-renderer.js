// SDK geometry only: no retail format, address, pose or scale interpretation.
const IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const finite=value=>typeof value==='number'&&Number.isFinite(value);
const columnMajor=matrix=>new Float32Array([0,4,8,12,1,5,9,13,2,6,10,14,3,7,11,15].map(i=>matrix[i]));
const dot=(a,b)=>a.x*b.x+a.y*b.y+a.z*b.z;

export function transformPoint(matrix,point){
  return {x:matrix[0]*point.x+matrix[1]*point.y+matrix[2]*point.z+matrix[3],
          y:matrix[4]*point.x+matrix[5]*point.y+matrix[6]*point.z+matrix[7],
          z:matrix[8]*point.x+matrix[9]*point.y+matrix[10]*point.z+matrix[11]};
}

export class SceneRenderer {
  constructor(canvas,onStatus=()=>{}){
    this.canvas=canvas;this.onStatus=onStatus;this.meshes=new Map();this.instances=[];this.scene=null;this.lost=false;
    this.gl=canvas.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:false});
    if(!this.gl)throw new Error('WebGL is unavailable. The scene remains usable with placement markers.');
    this.initialize();
    canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();this.lost=true;this.onStatus('Graphics context lost; placement markers remain available.');});
    canvas.addEventListener('webglcontextrestored',()=>{
      // The restored context invalidates every old GPU handle, including cached meshes.
      const scene=this.scene;this.meshes.clear();this.instances=[];
      try{this.initialize();this.lost=false;if(scene){const failures=this.load(scene);if(failures.length)throw new Error('Graphics recovery could not upload scene meshes: '+failures.join('; '));}this.onStatus(null);}catch(error){this.lost=true;this.onStatus(error.message);}
    });
  }

  initialize(){
    const gl=this.gl;
    const shader=(type,source)=>{const item=gl.createShader(type);gl.shaderSource(item,source);gl.compileShader(item);if(!gl.getShaderParameter(item,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(item);gl.deleteShader(item);throw new Error(message);}return item;};
    let vertex=null,fragment=null;
    try{
    vertex=shader(gl.VERTEX_SHADER,`attribute vec3 a_position;attribute vec3 a_color;attribute vec2 a_uv;
      uniform mat4 u_view;uniform mat4 u_model;varying vec3 v_color;varying vec2 v_uv;
      void main(){gl_Position=u_view*u_model*vec4(a_position,1.0);v_color=a_color;v_uv=a_uv;}`);
    fragment=shader(gl.FRAGMENT_SHADER,`precision mediump float;varying vec3 v_color;varying vec2 v_uv;
      uniform sampler2D u_texture;uniform bool u_textured;uniform bool u_picking;uniform vec3 u_pick;uniform bool u_semi;uniform int u_pass;
      void main(){vec4 color=vec4(v_color,1.0);bool semi=u_semi;if(u_textured){vec4 texel=texture2D(u_texture,v_uv);if(texel.a<0.01)discard;color.rgb*=texel.rgb;semi=semi&&texel.a<0.75;}
      if(!u_picking&&((u_pass==0&&semi)||(u_pass==1&&!semi)))discard;
      gl_FragColor=u_picking?vec4(u_pick,1.0):color;}`);
    this.program=gl.createProgram();gl.attachShader(this.program,vertex);gl.attachShader(this.program,fragment);gl.linkProgram(this.program);
    if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(this.program));
    }catch(error){if(this.program)gl.deleteProgram(this.program);this.program=null;throw error;}
    finally{if(vertex)gl.deleteShader(vertex);if(fragment)gl.deleteShader(fragment);}
    this.locations={};for(const name of ['position','color','uv'])this.locations[name]=gl.getAttribLocation(this.program,'a_'+name);
    for(const name of ['view','model','texture','textured','picking','pick','semi','pass'])this.locations[name]=gl.getUniformLocation(this.program,'u_'+name);
    this.gridBuffer=gl.createBuffer();this.gridKey=null;this.gridCount=0;this.pickTarget=null;
    this.whiteTexture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.whiteTexture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.disable(gl.CULL_FACE);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);
  }

  clear(){
    const gl=this.gl;
    for(const mesh of this.meshes.values())for(const batch of mesh.batches){gl.deleteBuffer(batch.buffer);if(batch.wireBuffer)gl.deleteBuffer(batch.wireBuffer);if(batch.texture)gl.deleteTexture(batch.texture);}
    this.meshes.clear();this.instances=[];this.scene=null;
    if(!this.lost){gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);}
  }

  load(scene){
    if(!Array.isArray(scene.assets)||!Array.isArray(scene.entities)||scene.assets.length>128||scene.entities.length>2048)throw new Error('Scene preview exceeds supported asset or instance bounds.');
    this.clear();this.scene=scene;const failures=[];
    for(const asset of scene.assets){
      if(typeof asset.geometry_key!=='string'||this.meshes.has(asset.geometry_key))continue;
      try{this.meshes.set(asset.geometry_key,this.createMesh(asset.preview));}catch(error){failures.push(error.message);}
    }
    this.instances=scene.entities.filter(item=>item.renderable&&this.meshes.has(item.geometry_key)&&Array.isArray(item.model_to_scene)&&item.model_to_scene.length===16&&item.model_to_scene.every(finite));
    return failures;
  }

  createMesh(preview){
    const gl=this.gl,vertices=preview?.vertices,triangles=preview?.triangles;
    if(!Array.isArray(vertices)||!Array.isArray(triangles)||!vertices.length||!triangles.length||vertices.length>100000||triangles.length>100000)throw new Error('Model geometry is empty or exceeds scene preview bounds.');
    if(vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(finite)))throw new Error('Model has invalid vertex coordinates.');
    const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(const vertex of vertices)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertex[axis]);max[axis]=Math.max(max[axis],vertex[axis]);}
    const textureData=new Map((preview.textures??[]).filter(t=>t.status==='address_match'&&t.rgba_base64).map(t=>[t.material_index,t]));
    const groups=new Map();
    for(let index=0;index<triangles.length;index++){
      const triangle=triangles[index],material=preview.triangle_materials?.[index]??-1;
      if(!Array.isArray(triangle)||triangle.length!==3||triangle.some(v=>!Number.isInteger(v)||v<0||v>=vertices.length))throw new Error('Model has an invalid triangle index.');
      if(!groups.has(material)){const group=[];group.vertexIndices=[];groups.set(material,group);}
      const data=groups.get(material),texture=textureData.get(material),uvs=preview.triangle_uvs?.[index],colors=preview.triangle_colors?.[index];
      for(let corner=0;corner<3;corner++){
        const raw=Array.isArray(colors?.[corner])&&colors[corner].length>=3?colors[corner]:[153,187,167],color=raw.slice(0,3).map(value=>finite(value)?Math.max(0,value)/(texture?128:255):.6);
        const uv=texture&&Array.isArray(uvs?.[corner])?[(uvs[corner][0]-texture.uv_origin[0]+.5)/texture.width,(uvs[corner][1]-texture.uv_origin[1]+.5)/texture.height]:[0,0];
        if(texture&&(!Array.isArray(uvs?.[corner])||!uv.every(finite)))throw new Error('Matched texture has invalid UV coordinates.');
        data.push(...vertices[triangle[corner]],...color,...uv);data.vertexIndices.push(triangle[corner]);
      }
    }
    const batches=[];
    try{
      for(const [material,data] of groups){
        const blend=preview.materials?.[material]?.blend;
        if(blend&&(!Number.isInteger(blend.mode)||blend.mode<0||blend.mode>3||typeof blend.enabled!=='boolean'))throw new Error('Invalid material blend metadata.');
        const batch={buffer:gl.createBuffer(),data:new Float32Array(data),vertexIndices:data.vertexIndices,count:data.length/8,texture:null,semi:blend?.enabled===true,blendMode:blend?.mode??0};batches.push(batch);
        gl.bindBuffer(gl.ARRAY_BUFFER,batch.buffer);gl.bufferData(gl.ARRAY_BUFFER,batch.data,gl.DYNAMIC_DRAW);
        const texture=textureData.get(material);
        if(texture){
          if(!Number.isInteger(texture.width)||!Number.isInteger(texture.height)||texture.width<1||texture.height<1||texture.width*texture.height>1048576)throw new Error('Texture dimensions exceed scene preview bounds.');
          const bytes=Uint8Array.from(atob(texture.rgba_base64),value=>value.charCodeAt(0));
          if(bytes.length!==texture.width*texture.height*4)throw new Error('Decoded texture size does not match its dimensions.');
          if(texture.stp_base64!==undefined){
            const mask=Uint8Array.from(atob(texture.stp_base64),value=>value.charCodeAt(0));
            if(mask.length!==texture.width*texture.height||mask.some(bit=>bit>1))throw new Error('Invalid texture transparency mask.');
            // Keep transparent-zero texels at 0; encode the separate STP bit in
            // a spare alpha value for the shader, not as blanket opacity.
            for(let i=0;i<mask.length;i++)if(bytes[i*4+3]&&mask[i])bytes[i*4+3]=128;
          }else if(batch.semi)throw new Error('Blend-enabled texture requires its decoded transparency mask.');
          batch.texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,batch.texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
          gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,texture.width,texture.height,0,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
          gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
          gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
        }
      }
    }catch(error){for(const batch of batches){gl.deleteBuffer(batch.buffer);if(batch.texture)gl.deleteTexture(batch.texture);}throw error;}
    return {batches,min,max,vertexCount:vertices.length};
  }

  updateVertices(key,vertices){
    const mesh=this.meshes.get(key);if(!mesh||this.lost)return false;
    if(!Array.isArray(vertices)||vertices.length!==mesh.vertexCount||vertices.some(v=>!Array.isArray(v)||v.length!==3||!v.every(finite)))throw new Error('Animation vertices differ from the loaded mesh layout.');
    const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(const vertex of vertices)for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertex[axis]);max[axis]=Math.max(max[axis],vertex[axis]);}
    for(const batch of mesh.batches){
      for(let i=0;i<batch.vertexIndices.length;i++)batch.data.set(vertices[batch.vertexIndices[i]],i*8);
      this.gl.bindBuffer(this.gl.ARRAY_BUFFER,batch.buffer);this.gl.bufferSubData(this.gl.ARRAY_BUFFER,0,batch.data);
      batch.wireDirty=true;
    }
    mesh.min=min;mesh.max=max;const asset=this.scene?.assets.find(item=>item.geometry_key===key);if(asset)asset.preview={...asset.preview,vertices};return true;
  }

  hasEntity(identifier){return !this.lost&&this.instances.some(item=>item.entity_id===identifier);}

  matrix(instance,positions){
    const result=instance.model_to_scene.slice(),position=positions.get(instance.entity_id);
    if(position){result[3]=position.x;result[7]=position.y;result[11]=position.z;}return result;
  }

  bounds(positions,identifier=null,hiddenEntities=new Set()){
    const points=[];
    for(const instance of this.instances){
      if(hiddenEntities.has(instance.entity_id))continue;
      if(identifier&&instance.entity_id!==identifier)continue;
      const mesh=this.meshes.get(instance.geometry_key),matrix=this.matrix(instance,positions);
      for(let corner=0;corner<8;corner++)points.push(transformPoint(matrix,{x:(corner&1?mesh.max:mesh.min)[0],y:(corner&2?mesh.max:mesh.min)[1],z:(corner&4?mesh.max:mesh.min)[2]}));
    }
    return points;
  }

  viewMatrix(view){
    const {camera,basis,width,height}=view,origin={x:camera.target.x-camera.distance*basis.forward.x,y:camera.target.y-camera.distance*basis.forward.y,z:camera.target.z-camera.distance*basis.forward.z};
    const focal=Math.min(width,height)*.9,near=Math.max(.02,camera.distance*.00001),far=camera.distance*100+100000;
    const a=2*focal/width,b=2*focal/height,c=(far+near)/(far-near),d=-2*far*near/(far-near),r=basis.right,u=basis.up,f=basis.forward;
    if(camera.projection==='orthographic'){
      const sx=a/camera.distance,sy=b/camera.distance,sz=2/(far-near);
      return columnMajor([sx*r.x,sx*r.y,sx*r.z,-sx*dot(origin,r),sy*u.x,sy*u.y,sy*u.z,-sy*dot(origin,u),sz*f.x,sz*f.y,sz*f.z,-(far+near)/(far-near)-sz*dot(origin,f),0,0,0,1]);
    }
    return columnMajor([a*r.x,a*r.y,a*r.z,-a*dot(origin,r),b*u.x,b*u.y,b*u.z,-b*dot(origin,u),c*f.x,c*f.y,c*f.z,d-c*dot(origin,f),f.x,f.y,f.z,-dot(origin,f)]);
  }

  bind(buffer){
    const gl=this.gl,l=this.locations;gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    for(const [name,size,offset] of [['position',3,0],['color',3,12],['uv',2,24]]){gl.enableVertexAttribArray(l[name]);gl.vertexAttribPointer(l[name],size,gl.FLOAT,false,32,offset);}
  }

  draw(view,picking=false){
    if(this.lost||!view.width||!view.height)return;
    const gl=this.gl,l=this.locations,dpr=Math.min(2,window.devicePixelRatio||1),w=Math.max(1,Math.round(view.width*dpr)),h=Math.max(1,Math.round(view.height*dpr));
    if(this.canvas.width!==w||this.canvas.height!==h){this.canvas.width=w;this.canvas.height=h;}
    if(picking)this.preparePick(w,h);else gl.bindFramebuffer(gl.FRAMEBUFFER,null);
    gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);gl.uniformMatrix4fv(l.view,false,this.viewMatrix(view));gl.uniform1i(l.texture,0);gl.uniform1i(l.picking,picking);gl.activeTexture(gl.TEXTURE0);
    gl.disable(gl.DITHER);gl.disable(gl.BLEND);gl.enable(gl.DEPTH_TEST);gl.depthMask(true);
    const drawInstance=(index,pass)=>{
      const instance=this.instances[index],mesh=this.meshes.get(instance.geometry_key),id=index+1;
      if(view.hiddenEntities?.has(instance.entity_id))return;
      gl.uniformMatrix4fv(l.model,false,columnMajor(this.matrix(instance,view.positions)));gl.uniform3f(l.pick,(id&255)/255,((id>>8)&255)/255,((id>>16)&255)/255);
      gl.uniform1i(l.pass,pass);
      for(const batch of mesh.batches){
        if(pass===1&&!batch.semi)continue;
        if(pass===1){
          const mode=batch.blendMode;gl.blendColor(mode===3?.25:.5,mode===3?.25:.5,mode===3?.25:.5,mode===3?.25:.5);
          gl.blendEquationSeparate(mode===2?gl.FUNC_REVERSE_SUBTRACT:gl.FUNC_ADD,gl.FUNC_ADD);
          gl.blendFuncSeparate(mode===0||mode===3?gl.CONSTANT_ALPHA:gl.ONE,mode===0?gl.CONSTANT_ALPHA:gl.ONE,gl.ONE,gl.ZERO);
        }
        this.bind(batch.buffer);gl.uniform1i(l.semi,batch.semi);gl.uniform1i(l.textured,!!batch.texture);gl.bindTexture(gl.TEXTURE_2D,batch.texture??this.whiteTexture);gl.drawArrays(gl.TRIANGLES,0,batch.count);
      }
    };
    for(let index=0;index<this.instances.length;index++)drawInstance(index,0);
    if(!picking){
      // Editor depth approximation: opaque first, then blended instances back
      // to front. This does not reconstruct retail ordering-table submission.
      const order=this.instances.map((instance,index)=>{
        const mesh=this.meshes.get(instance.geometry_key),center=transformPoint(this.matrix(instance,view.positions),{x:(mesh.min[0]+mesh.max[0])/2,y:(mesh.min[1]+mesh.max[1])/2,z:(mesh.min[2]+mesh.max[2])/2});
        return {index,depth:dot(center,view.basis.forward)};
      }).sort((a,b)=>b.depth-a.depth||a.index-b.index);
      gl.enable(gl.BLEND);gl.depthMask(false);for(const item of order)drawInstance(item.index,1);
      gl.disable(gl.BLEND);gl.depthMask(true);gl.blendEquation(gl.FUNC_ADD);
    }
    gl.uniform1i(l.semi,false);gl.uniform1i(l.pass,0);
    if(!picking&&view.wireframe)this.drawWireframe(view);
    if(!picking&&view.grid)this.drawGrid(view);
  }

  projectPoint(point,view){
    if(!point||![point.x,point.y,point.z].every(finite)||!view.width||!view.height)return null;
    const m=this.viewMatrix(view),v=[point.x,point.y,point.z,1];
    const clip=[0,1,2,3].map(row=>v.reduce((sum,value,column)=>sum+m[column*4+row]*value,0));
    if(clip[3]<=0)return null;
    const ndc=clip.slice(0,3).map(value=>value/clip[3]);
    if(ndc.some(value=>!finite(value)||Math.abs(value)>1))return null;
    return {x:(ndc[0]+1)*view.width/2,y:(1-ndc[1])*view.height/2,depth:ndc[2]};
  }

  drawWireframe(view){
    const gl=this.gl,l=this.locations;
    gl.uniform1i(l.textured,false);
    // A diagnostic overlay shows every decoded edge, including hidden edges.
    gl.disable(gl.DEPTH_TEST);gl.depthMask(false);
    try{
      for(const instance of this.instances){
        if(view.hiddenEntities?.has(instance.entity_id))continue;
        gl.uniformMatrix4fv(l.model,false,columnMajor(this.matrix(instance,view.positions)));
        for(const batch of this.meshes.get(instance.geometry_key).batches){
          if(!batch.wireBuffer){batch.wireBuffer=gl.createBuffer();batch.wireDirty=true;}
          if(batch.wireDirty){
            const data=new Float32Array(batch.count*2*8);let offset=0;
            for(let triangle=0;triangle<batch.count;triangle+=3)for(const corner of [0,1,1,2,2,0]){
              const start=(triangle+corner)*8;data.set(batch.data.subarray(start,start+3),offset);data.set([.2,1,1,0,0],offset+3);offset+=8;
            }
            gl.bindBuffer(gl.ARRAY_BUFFER,batch.wireBuffer);gl.bufferData(gl.ARRAY_BUFFER,data,gl.DYNAMIC_DRAW);batch.wireDirty=false;
          }
          this.bind(batch.wireBuffer);gl.drawArrays(gl.LINES,0,batch.count*2);
        }
      }
    }finally{gl.enable(gl.DEPTH_TEST);gl.depthMask(true);}
  }

  drawGrid(view){
    const gl=this.gl,l=this.locations,spacing=10**Math.floor(Math.log10(view.camera.distance/7)),half=spacing*12,cx=Math.round(view.camera.target.x/spacing)*spacing,cz=Math.round(view.camera.target.z/spacing)*spacing,key=[spacing,cx,cz].join('/');
    if(key!==this.gridKey){
      const data=[],add=(x,z)=>data.push(x,0,z,.16,.23,.24,0,0);
      for(let i=-12;i<=12;i++){add(cx+i*spacing,cz-half);add(cx+i*spacing,cz+half);add(cx-half,cz+i*spacing);add(cx+half,cz+i*spacing);}
      gl.bindBuffer(gl.ARRAY_BUFFER,this.gridBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.DYNAMIC_DRAW);this.gridCount=data.length/8;this.gridKey=key;
    }
    gl.uniformMatrix4fv(l.model,false,columnMajor(IDENTITY));gl.uniform1i(l.textured,false);this.bind(this.gridBuffer);gl.drawArrays(gl.LINES,0,this.gridCount);
  }

  preparePick(width,height){
    const gl=this.gl;
    if(!this.pickTarget||this.pickTarget.width!==width||this.pickTarget.height!==height){
      if(this.pickTarget){gl.deleteFramebuffer(this.pickTarget.framebuffer);gl.deleteTexture(this.pickTarget.texture);gl.deleteRenderbuffer(this.pickTarget.depth);}
      const target={width,height,framebuffer:gl.createFramebuffer(),texture:gl.createTexture(),depth:gl.createRenderbuffer()};
      gl.bindTexture(gl.TEXTURE_2D,target.texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,width,height,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.bindRenderbuffer(gl.RENDERBUFFER,target.depth);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,width,height);
      gl.bindFramebuffer(gl.FRAMEBUFFER,target.framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,target.texture,0);gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,target.depth);
      if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE){
        gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.deleteFramebuffer(target.framebuffer);gl.deleteTexture(target.texture);gl.deleteRenderbuffer(target.depth);this.pickTarget=null;
        throw new Error('Scene picking framebuffer is unavailable.');
      }
      this.pickTarget=target;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER,this.pickTarget.framebuffer);
  }

  pick(x,y,view){
    if(this.lost||!this.instances.length)return null;
    try{
      this.draw(view,true);const pixel=new Uint8Array(4),px=Math.min(this.canvas.width-1,Math.max(0,Math.floor(x*this.canvas.width/view.width))),py=Math.min(this.canvas.height-1,Math.max(0,Math.floor((view.height-y)*this.canvas.height/view.height)));
      this.gl.readPixels(px,py,1,1,this.gl.RGBA,this.gl.UNSIGNED_BYTE,pixel);
      return this.instances[(pixel[0]|pixel[1]<<8|pixel[2]<<16)-1]?.entity_id ?? null;
    }finally{this.draw(view);}
  }
}

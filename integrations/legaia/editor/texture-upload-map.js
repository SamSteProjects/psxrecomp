const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
const int=(v,min,max)=>Number.isInteger(v)&&v>=min&&v<=max;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const fail=()=>{throw new Error('Static upload map differs from the reviewed placement or has invalid footprints.');};
export async function decodeTextureUploadMap(v,placement){
 const keys=['schema_version','read_only','project_changed','project_source_key','scene_id','asset_id','excluded_asset_id','coverage','runtime_residency_verified','vram_width_words','vram_height','known_rectangle_count','occupancy_sha256','rectangles'];
 if(!exact(v,keys)||v.schema_version!=='legaia.texture-upload-map.v1'||v.read_only!==true||v.project_changed!==false||v.runtime_residency_verified!==false||v.vram_width_words!==1024||v.vram_height!==512||!hash(v.project_source_key)||!hash(v.occupancy_sha256)||!int(v.known_rectangle_count,0,8192)||!Array.isArray(v.rectangles)||v.rectangles.length!==v.known_rectangle_count)fail();
 for(const key of ['project_source_key','scene_id','asset_id','excluded_asset_id','coverage','known_rectangle_count','occupancy_sha256'])if(v[key]!==placement[key])fail();
 for(const row of v.rectangles){const r=row?.rectangle;
  if(!exact(row,['asset_id','kind','rectangle'])||!['image','flattened-clut','boot-upload'].includes(row.kind)||(row.kind==='boot-upload'?row.asset_id!==null:typeof row.asset_id!=='string'||row.asset_id.length>512||!/^texture(?:-new)?:\/\//.test(row.asset_id))||!exact(r,['x','y','width_words','height'])||!int(r.x,0,1023)||!int(r.y,0,511)||!int(r.width_words,1,1024-r.x)||!int(r.height,1,512-r.y))fail();
 }
 // Match sdk.project.canonical: recursively sorted JSON, two-space indent, final LF.
 const sorted=value=>value===null||typeof value!=='object'?value:Array.isArray(value)?value.map(sorted):Object.fromEntries(Object.keys(value).sort().map(k=>[k,sorted(value[k])]));
 const bytes=new TextEncoder().encode(JSON.stringify(sorted(v.rectangles),null,2)+'\n'),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
 if(digest!==v.occupancy_sha256)fail();
 return structuredClone(v);
}
export function uploadMapHits(map,x,y){
 if(!int(x,0,1023)||!int(y,0,511))return [];
 return map.rectangles.filter(({rectangle:r})=>r.x<=x&&x<r.x+r.width_words&&r.y<=y&&y<r.y+r.height).map(row=>structuredClone(row));
}
const colors={image:'#4588ad','flattened-clut':'#e2ad49','boot-upload':'#87969c',proposedImage:'#66e2a7',proposedClut:'#f190dc'};
export function renderTextureUploadMap(host,map,placement){
 const section=document.createElement('section');section.dataset.textureUploadMap='';
 const title=document.createElement('h3');title.textContent='Static VRAM upload map';
 const help=document.createElement('p');help.textContent='1024 words × 512 rows. Blue: Current images · gold: palettes · grey: boot uploads · green/pink: proposed image/palette. Click or use arrow keys to inspect a word. Static coverage only; runtime residency is unverified.';
 const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=512;canvas.tabIndex=0;canvas.setAttribute('aria-label','Static VRAM upload footprints; arrow keys move inspection by one word');Object.assign(canvas.style,{width:'100%',height:'auto',display:'block',background:'#101a20',border:'1px solid #687a83',touchAction:'manipulation'});
 const status=document.createElement('p');status.setAttribute('role','status');
 const owners=document.createElement('div');let x=0,y=0;
 const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Static upload map needs canvas support.');
 function draw(){ctx.clearRect(0,0,1024,512);ctx.fillStyle='#101a20';ctx.fillRect(0,0,1024,512);for(const row of map.rectangles){const r=row.rectangle;ctx.fillStyle=colors[row.kind];ctx.globalAlpha=.55;ctx.fillRect(r.x,r.y,r.width_words,r.height);}ctx.globalAlpha=1;
  ctx.strokeStyle='#465860';ctx.lineWidth=1;for(let n=0;n<=1024;n+=64){ctx.beginPath();ctx.moveTo(n,0);ctx.lineTo(n,512);ctx.stroke();}for(let n=0;n<=512;n+=64){ctx.beginPath();ctx.moveTo(0,n);ctx.lineTo(1024,n);ctx.stroke();}
  const p=placement.placement;if(p){ctx.strokeStyle=colors.proposedImage;ctx.lineWidth=2;ctx.strokeRect(p.image_x+.5,p.image_y+.5,placement.width_words,placement.height);if(placement.palette_words){ctx.strokeStyle=colors.proposedClut;ctx.strokeRect(p.clut_x+.5,p.clut_y+.5,placement.palette_words,1);}}
  ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x-5,y+.5);ctx.lineTo(x+6,y+.5);ctx.moveTo(x+.5,y-5);ctx.lineTo(x+.5,y+6);ctx.stroke();
 }
 function inspect(){const hits=uploadMapHits(map,x,y);status.textContent=`Word X=${x}, row Y=${y} · ${hits.length} known upload footprint${hits.length===1?'':'s'}. ${hits.length?'':'No known static upload; runtime availability is unverified.'}`;owners.replaceChildren();for(const row of hits.slice(0,32)){const r=row.rectangle,p=document.createElement('p');p.style.overflowWrap='anywhere';p.textContent=`${row.kind} · ${row.asset_id??'Boot upload'} · X [${r.x}, ${r.x+r.width_words}), Y [${r.y}, ${r.y+r.height})`;owners.append(p);}if(hits.length>32){const p=document.createElement('p');p.textContent=`Showing 32 of ${hits.length} overlapping source rectangles.`;owners.append(p);}draw();}
 canvas.onclick=event=>{const r=canvas.getBoundingClientRect(),width=r.width-2*canvas.clientLeft,height=r.height-2*canvas.clientTop;if(width<=0||height<=0)return;x=Math.min(1023,Math.max(0,Math.floor((event.clientX-r.left-canvas.clientLeft)*1024/width)));y=Math.min(511,Math.max(0,Math.floor((event.clientY-r.top-canvas.clientTop)*512/height)));inspect();canvas.focus();};
 canvas.onkeydown=event=>{const delta={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key];if(!delta)return;event.preventDefault();x=Math.min(1023,Math.max(0,x+delta[0]));y=Math.min(511,Math.max(0,y+delta[1]));inspect();};
 section.append(title,help,canvas,status,owners);host.append(section);inspect();return section;
}

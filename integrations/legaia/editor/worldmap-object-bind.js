import {qualifyWorldFootprint} from './worldmap-footprint.js';
import {placementDigest} from './worldmap-placement-replay.js';
const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const refuse=()=>{throw Error('Object bind source witness, header or unresolved scope differs.');};
const keys=(v,list)=>{if(!v||JSON.stringify(Object.keys(v).sort())!==JSON.stringify(list.sort()))refuse();};
export async function qualifyWorldObjectBind(v,current,id,path){
  keys(v,['schema_version','project_path','scene','source_key','entity_id','placement','man_source','bind','source_witness','representation','read_only','project_changed','gameplay_verified']);
  await qualifyWorldFootprint(v.placement,current,id,path);
  if(v.schema_version!=='legaia.worldmap-object-bind-inspection.v1'||v.project_path!==path||v.entity_id!==id||v.scene!==current.scene||v.source_key!==current.project_source_key||v.representation!=='retail-bind-at-current-anchor'||v.read_only!==true||v.project_changed!==false||v.gameplay_verified!==false)refuse();
  const b=v.bind,w=v.source_witness,m=bytes(w.man_base64),source=v.man_source;
  keys(b,['anchor','status','trigger','shadowed_trigger_ids','man_record','encoded_animation_selector','animation_clip','interaction_script','runtime_activation']);
  keys(w,['man_base64','trigger_blocks']);
  if(m.length<43||m.length>4194304||await placementDigest(m)!==source.slot.decoded_sha256||m.length!==source.slot.decoded_byte_length||source.slot.slot_index!==2||source.disc_sha256!==v.placement.source_record.source_disc_sha256)refuse();
  if(b.animation_clip!=='not_resolved'||b.interaction_script!=='not_resolved'||b.runtime_activation!=='not_evaluated'||b.anchor.col!==v.placement.anchor.col||b.anchor.row!==v.placement.anchor.row)refuse();
  if(!Array.isArray(w.trigger_blocks)||w.trigger_blocks.length<1||w.trigger_blocks.length>2)refuse();
  const hits=[];
  for(let k=0;k<w.trigger_blocks.length;k++){
    const block=w.trigger_blocks[k],data=bytes(block.bytes_base64),view=new DataView(data.buffer);
    if(block.table_source!==['primary','fallback'][k]||data.length!==8192)refuse();
    if(k===0){const map=bytes(current.placement_authoring.current_map_base64);if(data.some((n,i)=>n!==map[65536+i]))refuse();}
    const at=view.getInt16(6,true),count=view.getInt16(8,true);
    if(at<0||count<0||(count&&at<18)||at+count*4>8192)refuse();
    for(let i=0;i<count;i++){const p=at+i*4;if(data[p]===b.anchor.col&&data[p+1]===b.anchor.row)hits.push({table_source:block.table_source,record_index:i,encoded:{tile_x:data[p],tile_z:data[p+1],record_index:data[p+2],gate:data[p+3]},row:data.slice(p,p+4)});}
  }
  const ids=hits.slice(1).map(h=>`trigger://${v.scene}/field-map/${h.table_source}/kind-1/${String(h.record_index).padStart(4,'0')}`);
  if(JSON.stringify(ids)!==JSON.stringify(b.shadowed_trigger_ids))refuse();
  if(!hits.length){if(b.status!=='no_source_bind'||b.trigger!==null||b.man_record!==null||b.encoded_animation_selector!==null)refuse();return structuredClone(v);}
  const h=hits[0],t=b.trigger;
  if(t.table_source!==h.table_source||t.record_index!==h.record_index||t.table_kind!==1||t.semantic_id!==`trigger://${v.scene}/field-map/${h.table_source}/kind-1/${String(h.record_index).padStart(4,'0')}`||JSON.stringify(t.encoded)!==JSON.stringify(h.encoded)||await placementDigest(h.row)!==t.source_record.sha256)refuse();
  const view=new DataView(m.buffer),counts=[0,1,2].map(i=>view.getInt16(34+2*i,true)),total=counts.reduce((a,b)=>a+b,0),base=43+3*total;
  if(counts.some(n=>n<0)||total>8192||base>m.length||h.encoded.record_index>=total)refuse();
  const u24=at=>{if(at<0||at+3>m.length)refuse();return m[at]+m[at+1]*256+m[at+2]*65536;};
  const starts=Array.from({length:total},(_,i)=>base+u24(43+3*i));if(starts.some(s=>s>=m.length))refuse();
  const sections=[];let cursor=base+u24(40);
  for(let i=0;i<6;i++){const end=cursor+3+u24(cursor);if(end>m.length)refuse();sections.push([cursor,end]);cursor=end;}
  const flat=h.encoded.record_index,at=starts[flat],end=Math.min(m.length,...starts.filter(s=>s>at),...sections.map(s=>s[0]).filter(s=>s>at));
  let partition=0,local=flat;while(local>=counts[partition]){local-=counts[partition++];}
  const r=b.man_record;
  if(starts.filter(s=>s===at).length!==1||sections.some(s=>at<s[1]&&s[0]<end)||end-at>65536||r.flat_record_index!==flat||r.partition!==partition||r.record_index!==local||r.table_offset!==43+flat*3||r.byte_offset!==at||r.relative_offset!==at-base||r.byte_length!==end-at||r.sha256!==await placementDigest(m.slice(at,end)))refuse();
  if(partition!==0){if(b.status!=='unsupported_header_partition'||b.encoded_animation_selector!==null||r.header!==undefined)refuse();return structuredClone(v);}
  const length=2+2*m[at],header=m.slice(at,at+length);
  if(at+length>end||b.status!=='resolved_source_header'||b.encoded_animation_selector!==header[length-1]||r.header.local_count!==m[at]||r.header.byte_length!==length||r.header.sha256!==await placementDigest(header)||r.header.bytes_base64!==btoa(String.fromCharCode(...header)))refuse();
  return structuredClone(v);
}

export function validateVertexRetarget(report,users,toIndex){
  const hash=v=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
  if(!Number.isInteger(toIndex)||toIndex<0||toIndex>8191||toIndex===users.vertex_index||report.operation!=='vertex_references'||report.asset_id!==users.asset_id||report.object_index!==users.object_index||report.effective_sha256!==users.effective_sha256||!hash(report.proposed_sha256)||report.project_changed!==false||!Array.isArray(report.changes_from_current)||report.changes_from_current.length!==users.current_users.length)throw new Error('Vertex retarget review differs from its qualified Current users.');
  const pending=new Map(users.current_users.map(row=>[row.byte_offset,row]));
  for(const change of report.changes_from_current){const owner=pending.get(change.byte_offset);if(!owner||Object.keys(change).length!==9||change.before_value!==users.vertex_index||change.after_value!==toIndex||['kind','field','object_index','primitive_index','group_index','corner_index','byte_offset'].some(key=>change[key]!==owner[key]))throw new Error('Vertex retarget changed a different source reference.');pending.delete(change.byte_offset);}
  if(pending.size||Boolean(report.changes_from_current.length)!==(report.proposed_sha256!==report.effective_sha256))throw new Error('Vertex retarget hash or reference count conflicts.');return report;
}

"""Exact donor/generated record byte comparison; no behavioral equivalence claim."""
from hashlib import sha256
from .project import ProjectError
from .project_copy import source_key
from .npc_build_script import inspect as inspect_build
from .npc_donor_script import inspect as inspect_donor

def compare_records(retail,generated):
    def payload(record):
        try:data=bytes.fromhex(record['raw_hex'])
        except (TypeError,ValueError,KeyError) as error:raise ProjectError('Script comparison requires exact record bytes') from error
        if not 0<len(data)<=65536 or len(data)!=record.get('byte_length') or sha256(data).hexdigest()!=record.get('sha256') or type(record.get('script_offset')) is not int or not 0<=record['script_offset']<=len(data):raise ProjectError('Script comparison record hash, length or entry differs')
        return data
    a,b=payload(retail),payload(generated);boundary=min(retail['script_offset'],generated['script_offset']);changes=[]
    for offset in range(max(len(a),len(b))):
        left=a[offset] if offset<len(a) else None;right=b[offset] if offset<len(b) else None
        if left!=right:changes.append(dict(relative_offset=offset,retail_byte=left,generated_byte=right,scope='record_header' if offset<boundary else 'script_or_remaining_record_bytes'))
    return dict(comparison_scope='same_relative_record_byte_offsets',retail_length=len(a),generated_length=len(b),changed_byte_count=len(changes),unchanged_common_byte_count=sum(a[i]==b[i] for i in range(min(len(a),len(b)))),record_bytes_equal=a==b,script_tail_bytes_equal=a[retail['script_offset']:]==b[generated['script_offset']:],changes=changes)

def compare(project,entity_id,build_id):
    key=source_key(project);generated=inspect_build(project,entity_id,build_id);retail=inspect_donor(project,entity_id)
    if source_key(project)!=key or generated['project_source_key']!=key or retail['project_source_key']!=key or generated['draft']!=retail['draft']:raise ProjectError('Project or NPC donor changed during script comparison')
    difference=compare_records(retail['inspection']['record'],generated['inspection']['record'])
    return dict(schema_version='legaia.npc-script-comparison.v1',project_source_key=key,entity_id=entity_id,scene_id=project.active_scene,read_only=True,gameplay_verified=False,runtime_binding='not_asserted',retail=retail,generated=generated,difference=difference,limitations=['Relative byte alignment only; different offsets are not instruction or branch equivalence.', 'Script tails include opaque and unvisited data. Equal bytes do not establish equal runtime behavior.', 'Retail offsets and generated MAN offsets are separate. Runtime allocation, scheduling and execution remain unverified.'])

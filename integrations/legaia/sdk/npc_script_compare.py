"""Exact donor/generated record byte comparison; no behavioral equivalence claim."""
from hashlib import sha256
from .project import ProjectError
from .project_copy import source_key
from .npc_build_script import inspect as inspect_build
from .npc_donor_script import inspect as inspect_donor
from .build_history import _load,verify_build

def authored_spans(metadata,entity_id,retail,generated,draft):
    """Qualify receipt rows against both exact records; unexplained bytes stay so."""
    a,b=(bytes.fromhex(r['raw_hex']) for r in (retail,generated))
    spans=[];occupied=set();prefix='script://'+draft['donor_entity_id'].removeprefix('scene://')+'/'
    for key,category in [('npc_appearance_changes','initial_appearance'),('npc_dialogue_changes','own_dialogue'),('npc_wait_changes','own_wait')]:
        value=metadata.get(key)
        if value is None:continue
        if not isinstance(value,dict) or not isinstance(value.get('changes'),list) or len(value['changes'])>2048:
            raise ProjectError('NPC authored comparison audit exceeds its bounds')
        for row in value['changes']:
            if not isinstance(row,dict):raise ProjectError('NPC authored comparison audit row is invalid')
            if row.get('draft_id')!=entity_id:continue
            if type(row.get('record_index')) is not int or row['record_index']!=generated['record_index']:
                raise ProjectError('NPC authored comparison allocation differs')
            source_at,target_at=row.get('source_decoded_byte_offset'),row.get('decoded_byte_offset')
            if type(source_at) is not int or type(target_at) is not int:
                raise ProjectError('NPC authored comparison requires source/generated offsets')
            relative=target_at-generated['byte_offset']
            if relative!=source_at-retail['byte_offset']:
                raise ProjectError('NPC authored comparison has inconsistent relative offsets')
            if category=='initial_appearance':
                if 'appearance' not in draft:raise ProjectError('NPC appearance comparison has no authored binding')
                if row.get('field') not in ('model_index','animation_id') or any(type(row.get(k)) is not int or not 0<=row[k]<=255 for k in ('before_byte','after_byte')):
                    raise ProjectError('NPC appearance comparison requires exact header bytes')
                before,after=bytes([row['before_byte']]),bytes([row['after_byte']]);owner=row['field']
                if relative!=1+a[0]*2+(row['field']=='animation_id'):
                    raise ProjectError('NPC appearance comparison escaped its initial header')
            else:
                try:before,after=(bytes.fromhex(row[k]) for k in ('before_hex','after_hex'))
                except (ValueError,KeyError,TypeError) as error:raise ProjectError('NPC authored comparison requires exact span bytes') from error
                owner=row.get('run_id' if category=='own_dialogue' else 'wait_id')
                if not isinstance(owner,str) or not owner.startswith(prefix) or len(owner)>256:
                    raise ProjectError('NPC authored comparison source operand is unavailable')
                if category=='own_wait' and (row.get('mnemonic')!='WAIT_FRAMES' or len(before)!=2):
                    raise ProjectError('NPC wait comparison requires a two-byte target')
            size=len(before);span=set(range(relative,relative+size))
            if not 1<=size<=4096 or len(after)!=size or row.get('byte_length',size)!=size or not 0<=relative<=min(len(a),len(b))-size or span&occupied or a[relative:relative+size]!=before or b[relative:relative+size]!=after:
                raise ProjectError('NPC authored comparison span/preimage differs from saved and retail records')
            if category=='own_wait':
                requested=draft.get('waits',{}).get('entries',{}).get(owner)
                if requested is None or int.from_bytes(after,'little')!=requested['duration_ticks']:raise ProjectError('NPC wait comparison differs from its authored target')
            if category=='own_dialogue':
                requested=draft.get('dialogue',{}).get('runs',{}).get(owner)
                if requested is None or requested.ljust(size).encode('ascii')!=after:raise ProjectError('NPC dialogue comparison differs from its authored text')
            occupied.update(span)
            spans.append(dict(category=category,source_operand_id=owner,relative_offset=relative,byte_length=size,before_hex=before.hex(),after_hex=after.hex()))
    return sorted(spans,key=lambda r:r['relative_offset'])

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
    _,audit=_load(project,build_id);metadata=audit.get('npc_candidates',{}).get(project.active_scene,{}).get('draft_audit',{})
    spans=authored_spans(metadata,entity_id,retail['inspection']['record'],generated['inspection']['record'],generated['draft'])
    current=verify_build(project,build_id)
    if source_key(project)!=key or not current['matches_current_inputs'] or current['receipt']['archive_sha256']!=generated['build']['archive_sha256']:raise ProjectError('Project or saved Build changed during authored script comparison')
    return dict(schema_version='legaia.npc-script-comparison.v1',project_source_key=key,entity_id=entity_id,scene_id=project.active_scene,read_only=True,gameplay_verified=False,runtime_binding='not_asserted',retail=retail,generated=generated,difference=difference,authored_spans=spans,limitations=['Relative byte alignment only; different offsets are not instruction or branch equivalence.', 'Source-qualified authored spans account only for their exact bytes. Other differences remain unexplained, including append rebasing and opaque data.', 'Script tails include opaque and unvisited data. Equal bytes do not establish equal runtime behavior.', 'Retail offsets and generated MAN offsets are separate. Runtime allocation, scheduling and execution remain unverified.'])

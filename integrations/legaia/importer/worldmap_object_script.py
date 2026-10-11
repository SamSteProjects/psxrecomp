"""Static placed-object P0 script entry; no scheduling or VM execution."""
from hashlib import sha256
from .core import ImportError
from .script_inspection import inspect_record


def inspect_object_script(bind, man, scene):
    if bind.get('status') != 'resolved_source_header':
        raise ImportError('World object script requires a bounded source P0 bind')
    record=bind['man_record'];start,length=record['byte_offset'],record['byte_length']
    if not isinstance(man,bytes) or not 0 <= start < start+length <= len(man):
        raise ImportError('World object script record exceeds the MAN witness')
    payload=man[start:start+length]
    if sha256(payload).hexdigest()!=record['sha256']:
        raise ImportError('World object script record differs from its bind witness')
    entry=2+2*payload[0]
    if record['partition']!=0 or entry!=record['header']['byte_length'] or entry>len(payload):
        raise ImportError('World object script entry differs from its qualified P0 header')
    identity=f'script://{scene}/worldmap/man-p0/{record["record_index"]:04d}'
    graph=inspect_record(payload,entry,semantic_id=identity,base_offset=start)
    return dict(source_record_id=identity,record_index=record['record_index'],
        flat_record_index=record['flat_record_index'],record_sha256=record['sha256'],
        entry_pc=entry,entry_basis='retail_object_init_post_p0_header',
        graph=graph,asset_registration='not_registered',runtime_execution='not_asserted',
        representation='retail_source_script',read_only=True)

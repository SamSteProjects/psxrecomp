"""Saved authored World bind ownership in complete Current MAP/MAN inputs."""
from base64 import b64decode
from hashlib import sha256
from importer.worldmap_object_bind_allocation import _catalog,_tables
from importer.worldmap_object_binds import resolve_object_bind
from .worldmap_scripted_placement_allocation import source,_fresh
from .project import ProjectError


def inspect(project,scene,key,entity_id):
    receipt=source(project,scene,key)
    allocation=next((a for a in receipt['authored_scripted_placements'] if
        entity_id==f"scene://{scene}/worldmap/authored-placements/{a['placement_id'].rsplit('/',1)[1]}"),None)
    if allocation is None:raise ProjectError('Select a saved authored scripted World placement')
    seed=allocation['native_seed'];anchor=seed['source_anchor']
    current_map=b64decode(receipt['current_map_base64']);man=b64decode(receipt['current_man_base64']);retail=b64decode(receipt['source_man_base64'])
    bind=resolve_object_bind(_catalog(current_map[0x10000:],b64decode(receipt['fallback_base64']),scene),man,anchor['col'],anchor['row'])
    if bind['status']!='resolved_source_header' or bind['trigger']['table_source']!='primary' or bind['shadowed_trigger_ids']:
        raise ProjectError('Saved scripted placement lacks unique primary P0 bind ownership')
    row=bind['trigger'];record=bind['man_record'];script_id=f"script://{scene}/worldmap/man-p0/{record['record_index']:04d}"
    if script_id!=allocation['script_id']:raise ProjectError('Saved scripted placement changed its shared script owner')
    offset=_tables(current_map[0x10000:])[0][1][0]+4*row['record_index']+0x10000
    at,length=record['byte_offset'],record['byte_length']
    result=dict(schema_version='legaia.worldmap-scripted-bind.v1',project_path=str(project.root),scene=scene,source_key=key,
        entity_id=entity_id,native_entity_id=seed['entity_id'],placement_id=allocation['placement_id'],anchor=anchor,
        source_record=receipt['source_record'],source_man_sha256=receipt['source_man_sha256'],
        current_map_sha256=receipt['current_map_sha256'],current_man_sha256=receipt['current_man_sha256'],
        trigger=dict(id=row['semantic_id'],table_source='primary',record_index=row['record_index'],byte_offset=offset,
            sha256=sha256(current_map[offset:offset+4]).hexdigest(),encoded=row['encoded']),
        script=dict(id=script_id,partition=0,record_index=record['record_index'],flat_record_index=record['flat_record_index'],
            byte_offset=at,byte_length=length,retail_sha256=sha256(retail[at:at+length]).hexdigest(),current_sha256=record['sha256'],
            entry_pc=record['header']['byte_length'],header_sha256=record['header']['sha256'],encoded_animation_selector=bind['encoded_animation_selector']),
        shared_script=True,runtime_activation='not_evaluated',animation_clip='not_resolved',read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,key)
    return result

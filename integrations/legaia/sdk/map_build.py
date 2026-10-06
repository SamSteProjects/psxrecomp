"""Compose supported scenery and collision into one source-bound MAP patch."""
from hashlib import sha256
from importer.environment import load_environment_placements
from importer.environment_authoring import patch_environment_overrides
from importer.collision_authoring import patch_collision_walls
from .project import ProjectError


def prepare_map_patch(project, scene_id, components, archive):
    if not isinstance(components,dict) or not components or set(components)-{'Environment','Collision','FloorTiers'}:
        raise ProjectError('MAP composition supports scenery and collision only')
    for key,validator in (('Environment',project._validate_environment),('Collision',project._validate_collision),('FloorTiers',project._validate_floor_tiers)):
        if key in components:
            validator(scene_id,components[key])
    scene=project.imports[scene_id]['scene']['name']
    source=load_environment_placements(project.disc_path,scene)['source_record']
    entry=archive.entry(source['map_entry_index'])
    original=archive.read_entry(entry,extended=True)
    changed,environment=patch_environment_overrides(original,components['Environment']) if 'Environment' in components else (original,[])
    walls=[]
    if 'Collision' in components:
        binding=components['Collision']
        wall_data,walls=patch_collision_walls(original,binding['source_sha256'],binding['edits'])
        merged=bytearray(changed)
        for row in walls:
            offset,mask=row['byte_offset'],row['bit_mask']
            if (changed[offset]^original[offset])&mask:
                raise ProjectError('Collision wall edit overlaps scenery changes')
            merged[offset]=(merged[offset]&~mask)|(wall_data[offset]&mask)
        changed=bytes(merged)
    floors=[]
    if 'FloorTiers' in components:
        from importer.floor_authoring import patch_floor_tiers
        binding=components['FloorTiers'];floor_data,floors=patch_floor_tiers(original,binding['source_sha256'],binding['edits']);merged=bytearray(changed)
        for row in floors:
            offset=row['byte_offset']
            if (changed[offset]^original[offset])&15:raise ProjectError('Floor selector overlaps another MAP edit')
            merged[offset]=(merged[offset]&0xf0)|(floor_data[offset]&15)
        changed=bytes(merged)
    if len(changed)!=len(original):
        raise ProjectError('MAP composition changed its source span size')
    return dict(offset=entry.start_lba*2048,payload=changed,expected_sha256=sha256(original).hexdigest()),dict(
        scene_id=scene_id,map_entry_index=entry.index,byte_length=len(changed),environment_changes=environment,collision_changes=walls,floor_changes=floors,
        source_sha256=sha256(original).hexdigest(),result_sha256=sha256(changed).hexdigest())


def verify_rebuilt_maps(prot: bytes, audits: list[dict]) -> None:
    """Resolve MAP entries through the final TOC and verify full authored spans."""
    from importer.core import ProtArchive, IsoNode, parse_scene_table
    class MemoryImage:
        def read_user(self,_lba,offset,length,file_size):
            if offset<0 or length<0 or offset+length>min(file_size,len(prot)):
                raise ProjectError('Rebuilt MAP read exceeds archive')
            return prot[offset:offset+length]
    archive=ProtArchive(MemoryImage(),IsoNode(0,len(prot),False,'PROT.DAT'))
    for audit in audits:
        audit.pop('reopened_payload_verified',None)
        audit.pop('reopened_map_verified',None)
    for audit in audits:
        entry=archive.entry(audit['map_entry_index'])
        relative=audit.get('relative_offset',0)
        streaming = audit.get('streaming_binding')
        if streaming:
            from importer.streaming_man import streaming_chunks
            from importer.prot_layout import locate_physical_span
            span = locate_physical_span(archive, entry.start_lba * 2048)
            raw = prot[span['byte_offset']:span['byte_offset'] + span['byte_length']]
            chunks, terminated = streaming_chunks(raw)
            index = streaming.get('chunk_index')
            if (not terminated or type(index) is not int or not 0 <= index < len(chunks) or
                    chunks[index]['type_byte'] != streaming.get('type_byte') or
                    chunks[index]['size'] != audit['byte_length']):
                raise ProjectError('Rebuilt streaming asset binding is missing or changed')
            relative = chunks[index]['header_offset'] + 4
        binding=audit.get('descriptor_binding')
        if binding:
            raw=archive.read_entry(entry)
            table=parse_scene_table(raw,entry.index,binding['table_offset'])
            matches=[] if table is None else [d for d in table.descriptors if d.index==binding['index'] and d.type_byte==binding['type']]
            if len(matches)!=1:
                raise ProjectError('Rebuilt asset descriptor binding is missing')
            relative=binding['table_offset']+matches[0].data_offset
        payload=archive.image.read_user(0,entry.start_lba*2048+relative,audit['byte_length'],len(prot))
        if sha256(payload).hexdigest()!=audit['result_sha256']:
            raise ProjectError('Rebuilt archive asset differs from authored output')
    for audit in audits:
        audit['reopened_payload_verified']=True
        if 'relative_offset' not in audit:
            audit['reopened_map_verified']=True

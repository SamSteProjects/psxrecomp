"""World type-5 ANM delivery through the shared physical carrier composer."""
from hashlib import sha256
from importer.worldmap_geometry import KINGDOM_BASES,_kingdom_table,_slot
from importer.prot_layout import locate_physical_span
from importer.animation_bank_growth import grow_scene_animation_bank
from .worldmap_animation_binding import owner,COMPONENT,verify
from .worldmap_authoring import state_key
from .project import ProjectError


def prepare(project,archive):
    key=state_key(project);requests=[];reports=[];changes=[]
    for scene,base in KINGDOM_BASES.items():
        if COMPONENT not in project.overrides.get(owner(scene),{}):continue
        bank,current,source,_,audits=verify(project,scene)
        _,index,offset,bundle,carrier=_kingdom_table(archive,base)
        native,native_source=_slot(bundle,carrier,4)
        if native!=bank or native_source!=source:raise ProjectError('World animation Build changed its source bank or carrier')
        entry=archive.entry(index);table=locate_physical_span(archive,entry.start_lba*2048+offset)
        physical=archive.entry(table['entry_index']);table_offset=table['offset_within_span']
        raw=archive.image.read_user(archive.node.extent_lba,table['byte_offset'],table['byte_length'],archive.node.size)
        _,receipt=grow_scene_animation_bank(raw,sha256(raw).hexdigest(),table_offset,4,sha256(bank).hexdigest(),current)
        requests.append(dict(kind='animation-bank',entry_index=physical.index,table_offset=table_offset,
            descriptor_index=4,expected_bank_sha256=sha256(bank).hexdigest(),bank=current))
        reports.append(dict(scene=scene,owner_id=owner(scene),entry_index=physical.index,table_offset=table_offset,
            descriptor_index=4,source_bank_sha256=sha256(bank).hexdigest(),current_bank_sha256=sha256(current).hexdigest(),
            carrier=receipt,record_audits=audits,gameplay_verified=False))
        for audit in audits:
            identifier=f"animation://{scene}/worldmap/anm/{audit['record_index']:04d}"
            for channel in audit['channels']:
                changes.append(dict(channel,scene=scene,semantic_id=identifier,animation_id=identifier,
                    record_index=audit['record_index'],bank_byte_offset=audit['byte_offset']+channel['channel_byte_offset'],
                    source_record_sha256=audit['source_record_sha256'],proposed_record_sha256=audit['proposed_record_sha256'],
                    scope='world-animation-channel-content-only',shared_record=True,authored_owners=[owner(scene)]))
    if state_key(project)!=key:raise ProjectError('Project changed while preparing World animation delivery')
    return requests,dict(schema_version='legaia.world-animation-build-preparation.v1',source_key=key,
        carriers=reports,gameplay_verified=False),changes

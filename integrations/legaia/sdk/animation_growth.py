"""Source-bound compressed ANM allocation requests for normal Build relocation."""
from hashlib import sha256

from importer.core import parse_scene_assets, decompress_lzs
from importer.prot_layout import locate_physical_span
from importer.animation_bank_growth import grow_scene_animation_bank
from .animation_record_ledger import validate, compose, verified_source
from .build import authored_state_key
from .project import ProjectError


def prepare_animation_growth(project,archive,scene_ids):
    key=authored_state_key(project);requests=[];reports=[];edits=[]
    for scene_id in sorted(scene_ids):
        ledger=project.overrides[scene_id]['AnimationRecords']
        validate(project,scene_id,ledger)
        retail,catalog=verified_source(project,scene_id)
        source=catalog.source_bank()[1]
        if source.get('source_kind')=='raw_streaming_anm':
            raise ProjectError('Allocated streaming animation banks require raw chunk relocation; this carrier is not implemented yet')
        entry=archive.entry(source['prot_entry_index'])
        table=locate_physical_span(archive,entry.start_lba*2048+source['scene_table_offset'])
        owner=archive.entry(table['entry_index']);offset=table['offset_within_span']
        raw=archive.image.read_user(archive.node.extent_lba,table['byte_offset'],table['byte_length'],archive.node.size)
        directory=parse_scene_assets(raw,owner.index,offset)
        index=source['descriptor_index']
        if directory is None or type(index) is not int or not 0<=index<len(directory.descriptors):
            raise ProjectError('Allocated animation Build carrier descriptor is missing')
        descriptor=directory.descriptors[index]
        if (descriptor.type_byte!=5 or descriptor.size!=len(retail)
                or table['byte_offset']+offset+descriptor.data_offset!=entry.start_lba*2048+source['compressed_stream_offset']):
            raise ProjectError('Allocated animation source descriptor and physical stream disagree')
        end=min([offset+d.data_offset for d in directory.descriptors if d.data_offset>descriptor.data_offset]+[len(raw)])
        original,_=decompress_lzs(raw[offset+descriptor.data_offset:end],descriptor.size)
        if original!=retail:
            raise ProjectError('Allocated animation physical bank differs from verified Retail')
        candidate,allocation=compose(project,scene_id)
        _,carrier=grow_scene_animation_bank(raw,sha256(raw).hexdigest(),offset,index,sha256(retail).hexdigest(),candidate)
        requests.append(dict(kind='animation-bank',entry_index=owner.index,table_offset=offset,
            descriptor_index=index,expected_bank_sha256=sha256(retail).hexdigest(),bank=candidate))
        active=[dict(record_id=row['record_id'],animation_id=f"animation://{project.imports[scene_id]['scene']['name']}/authored-record/{row['record_id']}",
            record_sha256=row['record_sha256'],entity_id=row['entity_id'],frame_count=len(row['source_frame_indices']),object_count=row['object_count'])
            for row in ledger['records'] if row['record_id'] not in ledger['removed_record_ids']]
        reports.append(dict(scene_id=scene_id,entry_index=owner.index,table_offset=offset,descriptor_index=index,
            carrier=carrier,allocation=allocation,active_records=active,runtime_assigned=False))
        edits.append(dict(semantic_id=scene_id,field='animation.records',scope='animation-bank-allocation-relocation',
            before_sha256=sha256(retail).hexdigest(),after_sha256=sha256(candidate).hexdigest(),
            scene=project.imports[scene_id]['scene']['name'],active_record_count=len(active),runtime_assigned=False))
    if authored_state_key(project)!=key:
        raise ProjectError('Project changed while preparing allocated animation delivery')
    return requests,dict(schema_version='legaia.animation-growth-preparation.v1',authored_state_key=key,
        carriers=reports,gameplay_verified=False),edits

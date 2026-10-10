"""World TMD bindings share the existing model store/history and serializer."""
from importer.worldmap_model_authoring import model_identity, read_worldmap_model
from .project import ProjectError


def owner(identifier):
    identity=model_identity(identifier)
    return 'worldmap://'+identity[0]+'/models' if identity else None


def source(project,identifier):
    if not project.disc_path:raise ProjectError('World model authoring requires the source disc')
    content,_,native=read_worldmap_model(project.disc_path,identifier)
    identities={doc['source']['disc_identity'] for doc in project.imports.values()}
    if identities and identities!={'sha256:'+native['disc_sha256']}:
        raise ProjectError('World model source differs from the imported disc')
    return content,native


def validate(identifier,binding):
    if not isinstance(binding,dict) or binding.get('source_scene_id')!=owner(identifier) or binding.get('format') not in ('tmd-shape','tmd-content-v1','tmd-content-v2','tmd-content-v3','world-tmd-vector-allocation-v1','world-tmd-vector-content-v1'):
        raise ProjectError('World model binding requires canonical native ownership and qualified native content')


def asset(project,identifier,binding):
    validate(identifier,binding);_,native=source(project,identifier)
    normalized=dict(record_kind='decoded_tmd_pack_slot',prot_entry_index=native['prot_entry_index'],
                    container_section=native['slot_index'],byte_offset=native['decoded_member_offset'],
                    byte_length=native['decoded_member_span_end']-native['decoded_member_offset'],
                    containing_size=native['decoded_byte_length'], compressed_stream_offset=native['compressed_stream_offset'])
    return dict(semantic_id=identifier,source_record=normalized),native

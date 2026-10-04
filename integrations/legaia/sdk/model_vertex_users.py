"""Read-only stored vertex-reference users with current/retail source binding."""
from hashlib import sha256
import json
import re
import struct
from .model_reference_faces import mapping, addition_mapping
from importer.model_vertex_references import vertex_users
from importer.pipeline import _disc_context
from .project import ProjectError
from .scene_preview import source_key


def inspect(project, asset_id, object_index, vertex_index, expected_sha256, expected_key):
    if project.mode != 'edit' or not isinstance(expected_key, str) or source_key(project) != expected_key:
        raise ProjectError('Vertex reference source changed; reopen the vector editor')
    if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ProjectError('Vertex references require the inspected model hash')
    scene = project.active_scene
    models = project.imports.get(scene, {}).get('assets', {}).get('models', [])
    if not isinstance(asset_id, str) or not any(row['semantic_id'] == asset_id for row in models) or not project.disc_path:
        raise ProjectError('Vertex references require an imported model in the active scene')
    with _disc_context(project.disc_path):
        retail = project._model_source(asset_id, scene)
        effective = project.read_model_replacement(asset_id, project.model_overrides[asset_id]) if asset_id in project.model_overrides else retail
        source_hash = sha256(retail).hexdigest()
        binding = project.model_overrides.get(asset_id)
        added = binding and binding['format'] == 'tmd-face-addition-v1'
        if added:
            maps, authored = addition_mapping(project, asset_id, retail, effective, binding)
            if type(object_index) is not int or not 0 <= object_index < len(maps):
                raise ProjectError('Reference face mapping requires an existing object')
            face_mapping = maps[object_index]
        else:
            face_mapping = mapping(retail, effective, binding, object_index)
        if sha256(effective).hexdigest() != expected_sha256:
            raise ProjectError('Model changed since vertex vector inspection')
        current_users = vertex_users(effective, object_index, vertex_index)
        retail_count=struct.unpack_from('<I',retail,12+object_index*28+4)[0]
        current_count=struct.unpack_from('<I',effective,12+object_index*28+4)[0]
        retail_owned=vertex_index<retail_count
        retail_users = vertex_users(retail, object_index, vertex_index) if retail_owned else []
        def coordinates(data):
            offset = 12 + struct.unpack_from('<I', data, 12 + object_index * 28)[0] + vertex_index * 8
            return list(struct.unpack_from('<3h', data, offset))
        report = dict(schema_version='legaia.model-vertex-users.v1', asset_id=asset_id, scene_id=scene,
                      project_source_key=expected_key, source_sha256=source_hash, effective_sha256=expected_sha256,
                      object_index=object_index, vertex_index=vertex_index, model_byte_length=len(effective),
                      retail_coordinates=coordinates(retail) if retail_owned else None, current_coordinates=coordinates(effective),
                      retail_users=retail_users, current_users=current_users, face_mapping=face_mapping, read_only=True, gameplay_verified=False,
                      scope='qualified_stored_vertex_reference_operands_in_selected_object')
    if added:
        report.update(schema_version='legaia.model-vertex-users.v2', authored_faces=authored[object_index],
                      current_face_count=sum(row['current_index'] is not None for row in face_mapping)+len(authored[object_index]),
                      retail_model_byte_length=len(retail))
        if binding['ledger']['schema_version'] in ('legaia.model-face-addition-ledger.v5','legaia.model-face-addition-ledger.v6'):
            report.update(schema_version='legaia.model-vertex-users.v3',
                vector_origin='retail' if retail_owned else 'allocated',
                retail_vector_count=retail_count,current_vector_count=current_count)
    if project.mode != 'edit' or project.active_scene != scene or source_key(project) != expected_key:
        raise ProjectError('Project changed while reading vertex references')
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > 4*1024*1024:
        raise ProjectError('Vertex reference metadata exceeds 4 MiB')
    return report

"""Private world-source GLB exports, guarded against project/disc drift."""
import base64
import json

from importer.worldmap_geometry import load_worldmap_geometry
from importer.worldmap_export import encode_worldmap_glb, MAX_WORLDMAP_GLB_BYTES
from importer.export import write_encoded_glb
from .project import ProjectError
from .worldmap_authoring import state_key

MAX_RESPONSE_BYTES = 64 * 1024 * 1024


def export(project, scene, expected_key, scope, entity_id=None):
    if scene not in ('map01', 'map02', 'map03') or not project.disc_path or project.mode != 'edit':
        raise ProjectError('World export requires a supported source kingdom and imported disc in Edit mode')
    if scope not in ('source-scene', 'ground', 'selected') or (scope == 'selected') != (entity_id is not None):
        raise ProjectError('Choose source-scene, ground or selected world export scope')
    key = state_key(project)

    def current():
        if expected_key != key or project.mode != 'edit' or state_key(project) != key:
            raise ProjectError('World export source inputs changed; inspect the current source again')

    current()
    result = load_worldmap_geometry(project.disc_path, scene)
    current()
    identities = {document.get('source', {}).get('disc_identity') for document in project.imports.values()}
    if identities != {'sha256:' + result.get('source_record', {}).get('disc_sha256', '')}:
        raise ProjectError('World export retail disc differs from the imported project identity')
    raw, audit = encode_worldmap_glb(result, key, scope, entity_id)
    current()
    if len(raw) > MAX_WORLDMAP_GLB_BYTES:
        raise ProjectError('World source GLB exceeds its 32 MiB download budget')
    response = dict(schema_version='legaia.worldmap-export.v1', scene=scene, project_source_key=key,
        scope=scope, entity_id=entity_id, glb_base64=base64.b64encode(raw).decode('ascii'),
        gameplay_verified=False, project_changed=False)
    # Include a conservative pathname allowance before the exclusive file write.
    if len(json.dumps({**response, 'audit': audit}, allow_nan=False).encode('utf-8')) + 65536 > MAX_RESPONSE_BYTES:
        raise ProjectError('World source export exceeds its 64 MiB response budget')
    current()
    written = write_encoded_glb(raw, audit, project.root / 'Exports', prefix='scene')
    return {**written, **response}

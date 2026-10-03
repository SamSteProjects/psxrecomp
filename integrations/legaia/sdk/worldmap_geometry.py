"""Source-qualified walk kingdom ground inspection; no authored or live state."""
from copy import deepcopy
import base64
import json
from .project import ProjectError
from .worldmap_authoring import state_key

MAX_TEXTURE_BYTES = 16 * 1024 * 1024
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


def inspect(project, scene, expected_key):
    from importer.worldmap_geometry import load_worldmap_geometry
    if scene not in ('map01', 'map02', 'map03'):
        raise ProjectError('Choose one of the three supported walk kingdoms')
    if not project.disc_path or project.mode != 'edit':
        raise ProjectError('World ground inspection requires an imported disc in Edit mode')
    key = state_key(project)
    if expected_key != key:
        raise ProjectError('World ground source inputs changed; inspect the current project again')
    result = deepcopy(load_worldmap_geometry(project.disc_path, scene))
    previews = [result['preview']] + [asset['preview'] for asset in result.get('scene_graph', {}).get('assets', [])]
    seen = set()
    used = 0
    textures = []
    for preview in previews:
        if id(preview) not in seen:
            seen.add(id(preview))
            textures.extend(preview.get('textures', []))
    for texture in textures:
        for raw, encoded in (('rgba', 'rgba_base64'), ('stp', 'stp_base64')):
            content = texture.pop(raw, None)
            if content is not None:
                if not isinstance(content, bytes):
                    raise ProjectError('World ground texture must be verified byte data')
                used += len(content)
                if used > MAX_TEXTURE_BYTES:
                    raise ProjectError('World ground textures exceed the inspection budget')
                texture[encoded] = base64.b64encode(content).decode('ascii')
    if project.mode != 'edit' or state_key(project) != key:
        raise ProjectError('World ground source inputs changed during inspection')
    result.update(project_source_key=key, project_changed=False, gameplay_verified=False,
                  representation='retail-source', authored_geometry=False)
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_RESPONSE_BYTES:
        raise ProjectError('World ground inspection exceeds its metadata and geometry budget')
    return result

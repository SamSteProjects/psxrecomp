"""Read-only native decoration donors and complete source-bound clone Review."""
from copy import deepcopy
from hashlib import sha256
import base64
import json

from importer.worldmap_placement_allocation import inventory, allocate
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_placements import context


def _fresh(project, key):
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('World placement allocation requires current Edit source inputs')


def _context(project, scene, key):
    _fresh(project, key)
    raw, provenance, records, offset, floor, binding, current, placements = context(project, scene)
    _fresh(project, key)
    return provenance, floor, current


def source(project, scene, key):
    provenance, floor, current = _context(project, scene, key)
    result = dict(schema_version='legaia.worldmap-placement-allocation-source.v1',
        project_path=str(project.root), scene=scene, source_key=key, source_record=provenance,
        current_map_sha256=sha256(current).hexdigest(), current_map_base64=base64.b64encode(current).decode('ascii'),
        floor_lut=floor, **inventory(current, floor, scene), read_only=True, project_changed=False,
        gameplay_verified=False, limitations=[
            'Clones are walk-decoration source seeds, not scripted NPCs or placed landmark actors.',
            'Complete donor placement metadata is copied; target terrain selectors and cell upper flags are preserved.',
            'Collision, script side effects, native visibility and resting positions require gameplay verification.',
            'Project Apply, Current graph composition, editor controls and Build integration remain unfinished.'])
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('World placement allocation source exceeds its response budget')
    _fresh(project, key)
    return result


def review(project, scene, key, requests):
    provenance, floor, current = _context(project, scene, key)
    candidate, audit = allocate(current, floor, scene, requests)
    result = dict(schema_version='legaia.worldmap-placement-allocation-review.v1',
        project_path=str(project.root), scene=scene, source_key=key, source_record=provenance,
        requests=deepcopy(requests), current_map_sha256=sha256(current).hexdigest(),
        proposed_map_sha256=sha256(candidate).hexdigest(), proposed_map_base64=base64.b64encode(candidate).decode('ascii'),
        audit=audit, read_only=True, project_changed=False, gameplay_verified=False, build_ready=False)
    result['review_key'] = digest(result)
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('World placement allocation Review exceeds its response budget')
    _fresh(project, key)
    return result

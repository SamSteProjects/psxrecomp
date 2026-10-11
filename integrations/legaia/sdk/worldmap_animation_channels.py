"""Native channel inspection independent of model or runtime bindings."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import re

from importer.animation import animation_record_ranges, decode_animation_record
from .project import ProjectError
from .worldmap_animation_binding import verify, owner, COMPONENT
from .worldmap_behavior_resources import inspect as resources
from .worldmap_placement_allocation import _fresh


def inspect(project, animation_id, source_key):
    match = re.fullmatch(r'animation://(map0[123])/worldmap/scene-anm/([0-9]{4})', animation_id or '') if isinstance(animation_id, str) else None
    if not match:
        raise ProjectError('Choose a registered World animation clip')
    _fresh(project, source_key)
    scene, index = match[1], int(match[2])
    catalog = resources(project, source_key)
    record = next((r for r in catalog['assets'] if r['id'] == animation_id and r['kind'] == 'animation'), None)
    if record is None:
        raise ProjectError('World clip is absent or unsupported in the source catalog')
    retail, current, slot, disc_hash, _ = verify(project, scene)
    spans = animation_record_ranges(retail)
    if index >= len(spans):
        raise ProjectError('World clip is absent from its native bank')
    start, end = spans[index]
    source = record['source_record']
    if (source['disc_sha256'] != disc_hash or source['animation_slot'] != slot
            or source['byte_offset'] != start or source['byte_length'] != end-start
            or source['sha256'] != sha256(retail[start:end]).hexdigest()):
        raise ProjectError('World clip catalog differs from native source bytes')
    for bank in (retail, current):
        decoded = decode_animation_record(bank[start:end])
        if decoded['frame_count'] != record['frame_count'] or decoded['bone_count'] != record['channel_count']:
            raise ProjectError('World clip layout differs from its source catalog')
    result = dict(schema_version='legaia.world-animation-channels-inspection.v1',
                  project_path=str(project.root), source_key=source_key, animation_id=animation_id,
                  record=deepcopy(record), binding=deepcopy(project.overrides.get(owner(scene), {}).get(COMPONENT)),
                  retail_bank_base64=b64encode(retail).decode('ascii'), current_bank_base64=b64encode(current).decode('ascii'),
                  retail_bank_sha256=sha256(retail).hexdigest(), current_bank_sha256=sha256(current).hexdigest(),
                  current_record_sha256=sha256(current[start:end]).hexdigest(),
                  read_only=True, project_changed=False, gameplay_verified=False,
                  timing='unresolved', runtime_state='not_observed')
    _fresh(project, source_key)
    return result

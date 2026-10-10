"""Fresh native Retail restoration, including allocated World model layouts."""
from copy import deepcopy
from hashlib import sha256
import json
import struct
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner, source


def review(project, request):
    fields = {'asset_id', 'source_key', 'member_sha256', 'effective_sha256'}
    if (not isinstance(request, dict) or set(request) != fields or project.mode != 'edit'
            or not owner(request['asset_id']) or request['source_key'] != state_key(project)):
        raise ProjectError('World Retail restoration requires the inspected Current Edit source')
    original, native = source(project, request['asset_id'])
    binding = deepcopy(project.model_overrides.get(request['asset_id']))
    current = project.read_model_replacement(request['asset_id'], binding) if binding else original
    if sha256(original).hexdigest() != request['member_sha256'] or sha256(current).hexdigest() != request['effective_sha256']:
        raise ProjectError('World model changed; inspect Current before restoring Retail')
    count = struct.unpack_from('<I', original, 8)[0]
    if struct.unpack_from('<I', current, 8)[0] != count:
        raise ProjectError('World restoration has unsupported native object identity changes')
    objects = [dict(object_index=i,
        current_vertices=struct.unpack_from('<I', current, 16+i*28)[0],
        retail_vertices=struct.unpack_from('<I', original, 16+i*28)[0],
        current_normals=struct.unpack_from('<I', current, 24+i*28)[0],
        retail_normals=struct.unpack_from('<I', original, 24+i*28)[0]) for i in range(count)]
    report = dict(schema_version='legaia.worldmap-model-restoration.v1', project_path=str(project.root),
        request=deepcopy(request), source_record=native, current_binding=binding,
        current_byte_length=len(current), retail_byte_length=len(original), objects=objects,
        proposed_sha256=sha256(original).hexdigest(), changed=binding is not None,
        native_content_changed=current != original, retained_inputs_changed=False,
        read_only=True, project_changed=False, gameplay_verified=False,
        scope='remove-selected-World-model-binding-and-restore-native-Retail')
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > 8*1024*1024:
        raise ProjectError('World restoration Review exceeds its metadata budget')
    report['review_key'] = digest(report)
    if project.mode != 'edit' or state_key(project) != request['source_key']:
        raise ProjectError('World source changed during Retail restoration Review')
    return report


def apply(project, request, review_key):
    report = review(project, request)
    if report['review_key'] != review_key:
        raise ProjectError('World Retail restoration requires its exact fresh Review')
    if report['changed']:
        project.command(dict(type='clear_model_replacement', asset_id=request['asset_id']))
    return report

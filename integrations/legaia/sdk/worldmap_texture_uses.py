"""Compare static Retail and Current material address candidates for one World TIM."""
from copy import deepcopy
import json
import re
from .project import ProjectError
from .worldmap_authoring import state_key
from .worldmap_texture_authoring import scene_for, _inspected_current
from .worldmap_current_textures import compose
from importer.worldmap_geometry import load_worldmap_geometry


def inspect(project, request):
    fields = {'texture_id', 'source_key', 'member_sha256', 'effective_sha256'}
    if (not isinstance(request, dict) or set(request) != fields or project.mode != 'edit'
            or request['source_key'] != state_key(project) or not scene_for(request['texture_id'])):
        raise ProjectError('World material comparison requires the exact current Edit texture source')
    if any(not isinstance(request[k], str) or not re.fullmatch('[0-9a-f]{64}', request[k])
           for k in ('member_sha256', 'effective_sha256')):
        raise ProjectError('World material comparison requires inspected TIM hashes')
    ctx, _, _ = _inspected_current(project, request)
    scene = scene_for(request['texture_id'])
    retail = load_worldmap_geometry(project.disc_path, scene)
    if retail['source_record']['disc_sha256'] != ctx._source(request['texture_id'])['disc']['sha256']:
        raise ProjectError('World texture and geometry source discs differ')
    current = compose(project, deepcopy(retail))
    assets = retail['scene_graph']['assets']
    if len(assets) > 256:
        raise ProjectError('World material comparison exceeds its asset budget')
    rows = []
    def association(value):
        return dict(status=value['status'], source_ids=sorted(value.get('source_ids', [])),
                    reason=value.get('reason'))
    for original, authored in zip(assets, current['scene_graph']['assets'], strict=True):
        preview = original['preview']; changed = authored['preview']; matches = []
        if len(preview['materials']) > 256:
            raise ProjectError('World material comparison exceeds its material budget')
        for index, (material, before, after) in enumerate(zip(preview['materials'], preview['textures'], changed['textures'], strict=True)):
            if request['texture_id'] not in before.get('source_ids', []) and request['texture_id'] not in after.get('source_ids', []):
                continue
            matches.append(dict(material_index=index, material=deepcopy(material),
                                retail=association(before), current=association(after)))
        if matches:
            members=sorted(e['entity_id'] for e in retail['scene_graph']['entities'] if e['asset_id']==original['asset_id'])
            rows.append(dict(asset_id=original['asset_id'], source_instance_ids=members, materials=matches))
    result = dict(schema_version='legaia.worldmap-texture-uses.v1', project_path=str(project.root),
                  request=dict(request), source_record=deepcopy(retail['source_record']), assets=rows,
                  evidence='static_vram_addresses_not_runtime_residency', read_only=True,
                  project_changed=False, gameplay_verified=False)
    if len(json.dumps(result).encode('utf-8')) > 4*1024*1024:
        raise ProjectError('World material comparison exceeds its response budget')
    if project.mode != 'edit' or request['source_key'] != state_key(project):
        raise ProjectError('World material comparison source changed during inspection')
    return result

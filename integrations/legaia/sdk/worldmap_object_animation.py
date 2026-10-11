"""Qualified Current model plus retail World object-bind/ANM frame preview."""
from importer.pipeline import _disc_context, _bounded_scene_range
from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from importer.worldmap_object_animation import resolve_object_animation
from .project import ProjectError
from .worldmap_object_bind import inspect as inspect_bind
from .worldmap_current_placements import inspect as inspect_current
from .worldmap_placement_allocation import _fresh
import json


def inspect(project, scene, key, entity_id, frame_index):
    if type(frame_index) is not int or not 0 <= frame_index < 512:
        raise ProjectError('World animation frame requires an integer0..511')
    binding = inspect_bind(project,scene,key,entity_id)
    if not binding['bind']['encoded_animation_selector']:
        raise ProjectError('Selected World object has no nonzero source animation bind')
    current = inspect_current(project,scene,key)
    entity = next((e for e in current['scene_graph']['entities'] if e['entity_id']==entity_id),None)
    if not entity or entity.get('source_layer')!='placed':
        raise ProjectError('World animation requires a resolved Current placed model')
    asset = next(a for a in current['scene_graph']['assets'] if a['asset_id']==entity['asset_id'])
    with _disc_context(project.disc_path) as (_, digest, mapping, archive):
        start,end = _bounded_scene_range(archive,mapping,scene)
        base = KINGDOM_BASES[scene]
        if digest != binding['man_source']['disc_sha256'] or start!=base-2 or not start<=base<base+1<end:
            raise ProjectError('World animation bank differs from the selected source kingdom')
        _,index,offset,bundle,carrier = _kingdom_table(archive,base)
        bank,source = _slot(bundle,carrier,4)
        if source['descriptor_type']!=5 or index!=binding['man_source']['entry_index'] or offset!=binding['man_source']['table_offset']:
            raise ProjectError('World animation requires the same native type-5 carrier')
    result = dict(schema_version='legaia.worldmap-object-animation.v1',
        project_path=str(project.root),scene=scene,source_key=key,entity_id=entity_id,
        model_asset_id=asset['asset_id'],model_source=asset['source_record'],
        binding=binding,animation_source=source,
        preview=resolve_object_animation(binding['bind'],bank,asset['preview'],frame_index),
        representation='current-model-retail-object-animation',read_only=True,
        project_changed=False,gameplay_verified=False)
    if len(json.dumps(result,allow_nan=False).encode('utf-8')) > 40*1024*1024:
        raise ProjectError('World object pose exceeds its private response budget')
    _fresh(project,key)
    return result

"""Global world-map asset identities and recorded ownership, never field residency."""
from copy import copy, deepcopy
from hashlib import sha256
import re

from .project import AssetDatabase, ProjectError
from .project_assets import source_key, _metadata, _budget
from .worldmap_placements import SCENES, owner, context, values


def inspect(project, expected_key):
    """Build a detached metadata graph from all three qualified kingdom sources."""
    if not isinstance(expected_key, str) or not re.fullmatch('[0-9a-f]{64}', expected_key) or expected_key != source_key(project):
        raise ProjectError('Global world-map asset source changed; refresh project resources')
    view = copy(project)
    for name, value in vars(project).items():
        if name != 'assets':
            setattr(view, name, deepcopy(value))
    view.assets = AssetDatabase()
    if source_key(view) != expected_key:
        raise ProjectError('Global world-map inputs changed while taking their snapshot')
    assets, references, roots, identities = [], [], [], set()

    def add(record):
        if record['id'] in identities:
            raise ProjectError('Global world-map asset identities are ambiguous')
        identities.add(record['id'])
        record.update(kind='worldmap', asset_kind='worldmap', semantic_id=record['id'],
                      scene_id=None, scope='global-worldmap-placements')
        assets.append(record)

    for scene in SCENES:
        _, provenance, records, _, _, binding, current, _ = context(view, scene)
        if provenance.get('scene') != scene or any(not isinstance(provenance.get(k), str) or not re.fullmatch('[0-9a-f]{64}', provenance[k]) for k in ('source_disc_sha256','source_map_sha256','source_floor_lut_sha256')) or not isinstance(records, dict) or not 1 <= len(records) <= 512:
            raise ProjectError('Global world-map index requires qualified kingdom provenance')
        root = owner(scene)
        roots.append(root)
        native_ids, seed_ids = [], []
        for key, row in sorted(records.items()):
            index = row.get('object_record_index')
            members = row.get('placements')
            if not re.fullmatch('[0-9]{4}', key) or type(index) is not int or index != int(key) or not 0 <= index < 512 or row.get('record_id') != key or not isinstance(row.get('source_record_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', row['source_record_sha256']) or type(row.get('writable')) is not bool or type(row.get('source_cell_count')) is not int or not 1 <= row['source_cell_count'] <= 16384 or not isinstance(members, list) or not 1 <= len(members) <= 512 or len(members) > row['source_cell_count'] or row['writable'] and len(members) != row['source_cell_count']:
                raise ProjectError('Global world-map source-record ownership is invalid')
            retail, current_values = values(row.get('retail_values')), values(row.get('current_values'))
            authored = row.get('authored_values')
            if authored is not None:
                authored = values(authored)
            if current_values != (authored or retail):
                raise ProjectError('Global world-map Current transform differs from its source layers')
            record_id = root + '/records/' + key
            native_ids.append(record_id)
            owned = []
            for seed in members:
                cell = seed.get('source_cell')
                identifier = seed.get('entity_id')
                if type(cell) is not int or not 0 <= cell < 16384 or identifier != f'scene://{scene}/worldmap/placements/{cell:04x}' or seed.get('object_record_index') != index or seed.get('source_record_sha256') != row['source_record_sha256']:
                    raise ProjectError('Global world-map seed differs from its native record owner')
                owned.append(identifier)
                seed_ids.append(identifier)
                add(dict(id=identifier, name=f'{scene} source seed {cell:04x}', resource_role='source_seed', source_scene=scene,
                         owner_id=record_id, source_cell=cell, source_record_sha256=row['source_record_sha256'],
                         membership='global_worldmap_source', runtime_state='not_observed'))
                references.append(dict(source_id=record_id, target_id=identifier, kind='owns_source_seed', layer='derived',
                                       source_record_sha256=row['source_record_sha256']))
            add(dict(id=record_id, name=f'{scene} source record {key}', resource_role='native_source_record', source_scene=scene,
                     owner_id=root, record_id=key, object_record_index=index, source_record_sha256=row['source_record_sha256'],
                     source_byte_offset=index*32, source_byte_length=32, byte_coordinate_space='retail_worldmap_MAP',
                     source_cell_count=row['source_cell_count'], qualified_seed_ids=owned, complete_ownership=row['writable'],
                     retail_values=retail, current_values=current_values, authored_values=authored,
                     runtime_state='not_observed'))
            references.append(dict(source_id=root, target_id=record_id, kind='owns_native_source_record', layer='derived',
                                   source_record_sha256=row['source_record_sha256']))
        if len(seed_ids) > 512:
            raise ProjectError('Global world-map seed inventory exceeds the qualified budget')
        add(dict(id=root, name=f'{scene} source placements', resource_role='kingdom_placements', source_scene=scene,
                 source_record=deepcopy(provenance), current_map_sha256=sha256(current).hexdigest(),
                 native_record_ids=native_ids, qualified_seed_ids=seed_ids,
                 authored_component=deepcopy(binding), runtime_state='not_observed'))
    result = dict(schema_version='legaia.worldmap-assets.v1', source_key=expected_key, project_path=str(project.root),
                  metadata_only=True, read_only=True, project_changed=False, gameplay_verified=False,
                  roots=roots, assets=sorted(assets, key=lambda r:r['id']),
                  references=sorted(references, key=lambda r:(r['source_id'],r['target_id'])),
                  coverage=dict(kingdom_count=len(roots), asset_count=len(assets), reference_count=len(references),
                                native_record_count=sum(r['resource_role']=='native_source_record' for r in assets),
                                qualified_seed_count=sum(r['resource_role']=='source_seed' for r in assets)),
                  limitations=['Global kingdom roots and native owners have no imported field-scene membership.',
                               'Seed scene URI identities identify world-map source geometry; they do not establish field actor residency.',
                               'Ownership describes recorded native source cells, not runtime visibility, resting position or gameplay reachability.',
                               'Incomplete native record ownership stays explicit and does not grant authoring permission.'])
    _metadata(result)
    _budget(result)
    if expected_key != source_key(project) or expected_key != source_key(view):
        raise ProjectError('Global world-map source changed during inventory')
    return deepcopy(result)


def references(project, identifier, expected_key):
    """A qualified global neighborhood with its complete recorded ownership graph."""
    if not isinstance(identifier, str) or not re.fullmatch(
            r'(?:worldmap://map0[123]/placements(?:/records/[0-9]{4})?|scene://map0[123]/worldmap/placements/[0-9a-f]{4})', identifier):
        raise ProjectError('Global asset references require a world-map source identity')
    graph = inspect(project, expected_key)
    if not any(node['id'] == identifier for node in graph['assets']):
        raise ProjectError('Global asset is absent from the qualified ownership graph')
    result = dict(schema_version='legaia.global-asset-references.v1', asset_id=identifier,
                  source_key=expected_key, read_only=True, global_worldmap_index=graph,
                  incoming=[edge for edge in graph['references'] if edge['target_id'] == identifier],
                  outgoing=[edge for edge in graph['references'] if edge['source_id'] == identifier])
    _metadata(result)
    _budget(result)
    if source_key(project) != expected_key:
        raise ProjectError('Global reference source changed during qualification')
    return deepcopy(result)

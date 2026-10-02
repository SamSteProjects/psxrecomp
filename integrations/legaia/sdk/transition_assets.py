"""Source transition assets expose encoded arrivals, never runtime routes."""
from copy import deepcopy
import hashlib
import itertools
import re

from importer.core import ImportError as RetailImportError, validate_metadata_only
from importer.transition_authoring import ENTRY_FIELDS, reference_entry_interpretation
from .project import ProjectError
from .transitions import build_transition_graph

MAX_TRANSITION_ASSETS = 4096
MAX_TRANSITION_REFERENCES = 16384
MAX_SOURCE_BYTES = 4 * 1024 * 1024
_SCRIPT = re.compile(r'script://([a-z0-9_]+)/(actors/man-p1|scripts/man-p2)/(\d{4})')
_SCENE = re.compile(r'scene://[a-z0-9_]+')
_HASH = re.compile(r'[0-9a-f]{64}')
_COVERAGE = {'script_count', 'partial_script_count', 'unavailable_script_count'}
_EDGE_FIELDS = {'id', 'source', 'target', 'script_id', 'script_name', 'owner_id', 'partition',
                'script_status', 'script_stop_count', 'source_record', 'reference', 'reachability', 'entry_layers'}
_ASSET_FIELDS = _EDGE_FIELDS | {'semantic_id', 'asset_kind', 'read_only', 'name', 'coverage',
                              'limitations', 'arrival_layers', 'trigger_position', 'runtime_verified'}
_WRAPPER_FIELDS = {'kind', 'layer', 'scene_id'}
_REFERENCE_FIELDS = {'pc', 'byte_offset', 'mnemonic', 'extended_target', 'target_scene_name',
                     'target_in_scene_index', 'status', 'name_byte_length', 'name_sha256',
                     *ENTRY_FIELDS, 'reachability'}


def _reject(reason):
    raise ProjectError('Invalid transition asset: ' + reason)


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _text(value, maximum=8192):
    return isinstance(value, str) and 0 < len(value) <= maximum


def _metadata(value):
    try:
        validate_metadata_only(value)
    except (RetailImportError, AttributeError) as exc:
        raise ProjectError('Invalid transition asset metadata') from exc
    if isinstance(value, dict):
        forbidden = {'text', 'raw_hex', 'encoded_hex', 'tokens', 'scene_name_bytes_hex', 'rgba', 'stp'}
        if any(not isinstance(key, str) or key.lower() in forbidden for key in value):
            _reject('contains payload fields')
        for child in value.values():
            _metadata(child)
    elif isinstance(value, list):
        for child in value:
            _metadata(child)


def _coverage(value):
    if not isinstance(value, dict) or set(value) != _COVERAGE:
        _reject('coverage shape')
    if any(not _integer(value[key], 0, 1024) for key in _COVERAGE):
        _reject('coverage bounds')
    if value['partial_script_count'] + value['unavailable_script_count'] > value['script_count']:
        _reject('coverage counts')


def _entry(value, partial=False):
    if (not isinstance(value, dict) or (set(value) - set(ENTRY_FIELDS) if partial else set(value) != set(ENTRY_FIELDS)) or
            any(not _integer(byte, 0, 255) for byte in value.values())):
        _reject('encoded entry bytes')


def _stop_count(script):
    stops = script.get('stops')
    count = script.get('stop_count', len(stops) if isinstance(stops, list) else None)
    if (not _integer(count, 0, MAX_TRANSITION_REFERENCES) or
            'stops' in script and (not isinstance(stops, list) or len(stops) != count)):
        _reject('source script stop count')
    return count


def _arrival(value, encoded):
    expected = reference_entry_interpretation(encoded)
    if (not isinstance(value, dict) or set(value) != set(expected) or
            any(type(value[key]) is not type(expected[key]) or value[key] != expected[key] for key in expected)):
        _reject('static arrival differs from encoded bytes')


def validate_transition_asset(record):
    """Validate adapter/registered metadata and return the unchanged record."""
    if (not isinstance(record, dict) or not _ASSET_FIELDS <= set(record) or
            set(record) - _ASSET_FIELDS - _WRAPPER_FIELDS):
        _reject('record shape')
    if (record['asset_kind'] != 'transition' or record['read_only'] is not True or
            record['runtime_verified'] is not False or record['trigger_position'] is not None or
            record['reachability'] != 'not_evaluated' or not _text(record['name'])):
        _reject('runtime route or asset metadata')
    script = _SCRIPT.fullmatch(record['script_id']) if isinstance(record['script_id'], str) else None
    if script is None:
        _reject('source script identity')
    scene, path, index_text = script.groups()
    partition = 1 if path == 'actors/man-p1' else 2
    source_id = 'scene://' + scene
    if (record['source'] != source_id or record['owner_id'] != record['script_id'].replace('script://', 'scene://', 1) or
            type(record['partition']) is not int or record['partition'] != partition or
            not _text(record['script_name']) or record['script_status'] not in ('decoded_supported_paths', 'partial') or
            not _integer(record['script_stop_count'], 0, MAX_TRANSITION_REFERENCES)):
        _reject('source owner or status')
    if (record.get('kind', 'transition') != 'transition' or record.get('layer', 'derived') != 'derived' or
            record.get('scene_id', source_id) != source_id):
        _reject('registered identity')
    source = record['source_record']
    if (not isinstance(source, dict) or type(source.get('partition')) is not int or source['partition'] != partition or
            type(source.get('record_index')) is not int or source['record_index'] != int(index_text) or
            not _integer(source.get('byte_offset'), 0, MAX_SOURCE_BYTES) or
            not _integer(source.get('byte_length'), 1, MAX_SOURCE_BYTES) or
            source['byte_offset'] + source['byte_length'] > MAX_SOURCE_BYTES or
            not _text(source.get('byte_coordinate_space'), 128) or
            not isinstance(source.get('sha256'), str) or not _HASH.fullmatch(source['sha256'])):
        _reject('source locator or hash')
    ref = record['reference']
    if not isinstance(ref, dict) or set(ref) != _REFERENCE_FIELDS:
        _reject('reference shape')
    pc, target = ref['pc'], ref['extended_target']
    if (not _integer(pc, 0, MAX_SOURCE_BYTES) or pc >= source['byte_length'] or
            type(ref['byte_offset']) is not int or ref['byte_offset'] != source['byte_offset'] + pc or
            ref['mnemonic'] != 'SCENE_CHANGE' or ref['reachability'] != 'not_evaluated' or
            target is not None and not _integer(target, 0, 255)):
        _reject('source instruction PC or dispatch context')
    identity = record['script_id'].replace('script://', 'transition://', 1) + f'/{pc:04x}'
    if record['id'] != identity or record['semantic_id'] != identity:
        _reject('transition identity')
    name = ref['target_scene_name']
    if not _integer(ref['name_byte_length'], 0, 255) or not isinstance(ref['name_sha256'], str) or not _HASH.fullmatch(ref['name_sha256']):
        _reject('destination name evidence')
    if name is None:
        if (record['target'] != identity + '/unresolved-target' or ref['target_in_scene_index'] is not None or
                ref['status'] != 'unsupported_name_encoding'):
            _reject('unresolved destination identity')
    else:
        if (not isinstance(name, str) or not re.fullmatch('[a-z0-9]{1,12}', name) or
                ref['name_byte_length'] != len(name) or ref['name_sha256'] != hashlib.sha256(name.encode('ascii')).hexdigest() or
                type(ref['target_in_scene_index']) is not bool or ref['status'] != 'encoded_named_reference' or
                record['target'] != 'scene://' + name):
            _reject('named destination identity')
    if pc + (2 if target is not None else 1) + 6 + ref['name_byte_length'] > source['byte_length']:
        _reject('instruction exceeds source record')
    imported = {field: ref[field] for field in ENTRY_FIELDS}
    _entry(imported)
    layers = record['entry_layers']
    if (not isinstance(layers, dict) or set(layers) != {'imported', 'authored', 'effective', 'validation', 'transition_id'} or
            layers['transition_id'] != record['script_id'] + f'/transition/{pc:04x}'):
        _reject('entry layer identity')
    _entry(layers['imported'])
    _entry(layers['authored'], partial=True)
    _entry(layers['effective'])
    if layers['imported'] != imported or layers['effective'] != dict(imported, **layers['authored']):
        _reject('entry layers differ from imported/authored bytes')
    if layers['validation'] != ('reverified_on_build' if layers['authored'] else 'imported_reference'):
        _reject('entry validation marker')
    if layers['authored'] and (name is None or record['script_stop_count']):
        _reject('unknown or stopped transition cannot be authored')
    arrival = record['arrival_layers']
    if not isinstance(arrival, dict) or set(arrival) != {'imported', 'effective'}:
        _reject('arrival layer shape')
    _arrival(arrival['imported'], layers['imported'])
    _arrival(arrival['effective'], layers['effective'])
    _coverage(record['coverage'])
    if (not isinstance(record['limitations'], list) or len(record['limitations']) > 256 or
            any(not _text(row) for row in record['limitations'])):
        _reject('limitations')
    _metadata(record)
    return record


def build_transition_assets(catalog, imported_scenes, overrides=None):
    """Adapt the existing source graph without reading or decoding more bytes."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get('assets'), list):
        _reject('catalog shape')
    assets = catalog['assets']
    if any(not isinstance(asset, dict) for asset in assets):
        _reject('catalog record shape')
    if 'transition_count' not in catalog and not any('transitions' in asset for asset in assets):
        return []
    if len(assets) > 8192 or not isinstance(catalog.get('scene'), str) or not re.fullmatch('[a-z0-9_]+', catalog['scene']):
        _reject('catalog count or scene identity')
    if isinstance(imported_scenes, (str, bytes)):
        _reject('imported scene identities')
    try:
        imported = list(itertools.islice(iter(imported_scenes), 65))
    except TypeError as exc:
        raise ProjectError('Invalid transition asset imported scenes') from exc
    if len(imported) > 64 or any(not isinstance(scene, str) or not _SCENE.fullmatch(scene) for scene in imported):
        _reject('imported scene identities or count')
    _coverage({key: catalog.get(key) for key in _COVERAGE})
    scripts = [asset for asset in assets if asset.get('asset_kind') == 'script']
    if catalog['script_count'] != len(scripts):
        _reject('catalog script count')
    reference_count, source_stops = 0, {}
    for script in scripts:
        identifier = script.get('semantic_id')
        parsed = _SCRIPT.fullmatch(identifier) if isinstance(identifier, str) else None
        if (parsed is None or parsed.group(1) != catalog['scene'] or
                (script.get('owner_semantic_id') or script.get('actor_semantic_id')) != identifier.replace('script://', 'scene://', 1) or
                not _text(script.get('name')) or not isinstance(script.get('source_record'), dict) or
                script.get('status') not in ('decoded_supported_paths', 'partial', 'unavailable') or
                not isinstance(script.get('transitions'), list)):
            _reject('source script contract')
        if identifier in source_stops:
            _reject('duplicate source script identity')
        source_stops[identifier] = _stop_count(script)
        reference_count += len(script['transitions'])
        if reference_count > MAX_TRANSITION_REFERENCES:
            _reject('reference count exceeds discovery bounds')
    if (catalog['partial_script_count'] != sum(script['status'] == 'partial' for script in scripts) or
            catalog['unavailable_script_count'] != sum(script['status'] == 'unavailable' for script in scripts) or
            ('transition_count' in catalog and (type(catalog['transition_count']) is not int or catalog['transition_count'] != reference_count))):
        _reject('catalog coverage counts')
    if overrides is not None and not isinstance(overrides, dict):
        _reject('authored owner map')
    requested = set()
    for owner, components in (overrides or {}).items():
        if not isinstance(owner, str):
            _reject('authored owner identity')
        if not owner.startswith('scene://' + catalog['scene'] + '/'):
            continue
        if not isinstance(components, dict):
            _reject('authored component map')
        if 'Transitions' not in components:
            continue
        component = components['Transitions']
        if (not isinstance(component, dict) or set(component) != {'entries'} or
                not isinstance(component['entries'], dict) or len(component['entries']) > 1024):
            _reject('authored transition entries')
        for identifier, value in component['entries'].items():
            if (not isinstance(identifier, str) or not identifier.startswith(owner.replace('scene://', 'script://', 1) + '/transition/') or
                    not isinstance(value, dict) or not value):
                _reject('authored transition identity')
            _entry(value, partial=True)
            requested.add(identifier)
    try:
        graph = build_transition_graph(catalog, imported, overrides)
    except (KeyError, TypeError, IndexError, AttributeError, ValueError) as exc:
        raise ProjectError('Invalid transition asset source graph contract') from exc
    if len(graph['edges']) > MAX_TRANSITION_ASSETS:
        _reject('asset count exceeds discovery bounds')
    records, seen, consumed = [], set(), set()
    for edge in graph['edges']:
        record = deepcopy(edge)
        layers = record['entry_layers']
        try:
            arrival = {layer: reference_entry_interpretation(layers[layer]) for layer in ('imported', 'effective')}
        except (RetailImportError, TypeError, AttributeError) as exc:
            raise ProjectError('Invalid transition asset encoded entry interpretation') from exc
        destination = edge['reference']['target_scene_name'] or 'unresolved destination'
        record.update(semantic_id=edge['id'], asset_kind='transition', read_only=True,
                      script_stop_count=source_stops[edge['script_id']],
                      name=f"{edge['script_name']} · {edge['reference']['pc']:04x} → {destination}",
                      coverage=deepcopy(graph['coverage']), limitations=list(graph['limitations']),
                      arrival_layers=arrival, trigger_position=None, runtime_verified=False)
        validate_transition_asset(record)
        if record['id'] in seen:
            _reject('duplicate source transition identity')
        seen.add(record['id'])
        if layers['authored']:
            consumed.add(layers['transition_id'])
        records.append(record)
    if requested != consumed:
        _reject('authored transition is absent from decoded source references')
    return sorted(records, key=lambda record: record['id'])

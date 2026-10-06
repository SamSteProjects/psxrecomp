"""Read-only source-qualified project Asset Database with scene variants.

Shared structural identities can have different recorded bindings in different
scenes. Discovery retains those records separately and never changes editor
navigation, imported evidence, authored state or the active resource caches.
"""
from copy import copy, deepcopy
from pathlib import Path
import re

from importer.core import ImportError as RetailImportError, validate_metadata_only
from .project import AssetDatabase, ProjectError, canonical, digest

MAX_SCENES = 64
MAX_METADATA_BYTES = 32 * 1024 * 1024
MAX_ASSETS = 16384
MAX_MEMBERSHIPS = 65536
KINDS = {'scene', 'actor', 'model', 'texture', 'animation', 'script', 'dialogue',
         'collision', 'trigger', 'region', 'worldmap', 'flag', 'transition'}
STATUSES = {'available', 'partial', 'unavailable'}
LIMITATIONS = [
    'The index covers imported source scenes and their bounded verified resource loaders; unsupported or unavailable coverage remains explicit.',
    'Shared IDs retain a separate source record for each imported scene; memberships do not establish runtime residency or gameplay reachability.',
    'NPC draft entries are authored project metadata: the owning import hash identifies scene context, not a retail origin for the draft. Donor references retain imported actor identities.',
    'Authored state participates in freshness; records are metadata, not executable payloads or a complete format inventory.',
]


def _metadata(value):
    try:
        validate_metadata_only(value)
        return canonical(value)
    except (RetailImportError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        raise ProjectError('Project Asset Database requires bounded metadata-only records: ' + str(exc)) from exc


def _budget(value):
    try:
        encoded = canonical(value)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ProjectError('Project Asset Database metadata cannot be serialized') from exc
    if len(encoded) > MAX_METADATA_BYTES:
        raise ProjectError('Project Asset Database metadata exceeds the 32 MiB budget')
    return encoded


def _imports(project):
    imports = project.imports
    if not isinstance(imports, dict) or not 1 <= len(imports) <= MAX_SCENES:
        raise ProjectError('Project Asset Database requires from 1 through 64 imported scenes')
    for scene, document in imports.items():
        if (not isinstance(scene, str) or not scene.startswith('scene://') or len(scene) > 1024 or
                not isinstance(document, dict) or not isinstance(document.get('scene'), dict) or
                document['scene'].get('semantic_id') != scene or
                not isinstance(document['scene'].get('name'), str) or not document['scene']['name'] or
                len(document['scene']['name']) > 256 or any(ord(c) < 32 for c in document['scene']['name']) or
                not isinstance(document.get('actors'), list) or not isinstance(document.get('assets'), dict) or
                not isinstance(document['assets'].get('models', []), list)):
            raise ProjectError('Project Asset Database imports require coherent source scene identities')
    _metadata(imports)
    _budget(imports)
    return imports


def source_key(project) -> str:
    """Navigation-independent freshness for imported and authored project inputs."""
    imports = _imports(project)
    disc_path = str(Path(project.disc_path).resolve()) if project.disc_path else None
    stamp = None
    if disc_path is not None:
        try:
            stat = Path(disc_path).stat()
            stamp = [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]
        except OSError:
            pass
    value = dict(project_path=str(project.root), disc_path=disc_path, disc_stat=stamp,
                 imports={scene: digest(document) for scene, document in sorted(imports.items())},
                 overrides=project.overrides, drafts=project.actor_drafts,
                 model_overrides=project.model_overrides, texture_overrides=project.texture_overrides)
    _budget(dict(imports=imports, authored={key: value[key] for key in
                                          ('overrides', 'drafts', 'model_overrides', 'texture_overrides')}))
    return digest(value)


def _limitations(value):
    if (not isinstance(value, list) or len(value) > 256 or
            any(not isinstance(item, str) or not item or len(item) > 8192 for item in value)):
        raise ProjectError('Project Asset Database limitations exceed their bounded metadata format')
    return list(dict.fromkeys(value))


def _record(record, scene, kind=None):
    if not isinstance(record, dict):
        raise ProjectError('Project Asset Database source record must be metadata')
    _metadata(record)
    identifier = record.get('semantic_id', record.get('id'))
    actual_kind = record.get('asset_kind', record.get('kind', kind))
    source_model_kind = kind == 'model' and actual_kind == 'tmd_model'
    if source_model_kind:
        # Existing retail imports name the encoded family tmd_model. Browser
        # categories use model; retain the original family as source metadata.
        actual_kind = 'model'
    if (not isinstance(identifier, str) or not identifier or len(identifier) > 1024 or
            '://' not in identifier or any(ord(c) <= 32 or ord(c) >= 127 for c in identifier) or
            not isinstance(actual_kind, str) or actual_kind not in KINDS or kind is not None and actual_kind != kind or
            record.get('id', identifier) != identifier or record.get('semantic_id', identifier) != identifier or
            record.get('kind', actual_kind) != actual_kind or
            record.get('asset_kind', actual_kind) != ('tmd_model' if source_model_kind else actual_kind) or
            record.get('scene_id', scene) != scene):
        raise ProjectError('Project Asset Database record has conflicting identity, kind or scene membership')
    name = record.get('name')
    if name is not None and (not isinstance(name, str) or len(name) > 8192):
        raise ProjectError('Project Asset Database source name exceeds its metadata format')
    # Preserve structural names when printable and bounded. A missing or unsafe
    # display name gets an ID-derived label, never invented source semantics.
    if not name or len(name) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in name):
        name = actual_kind.capitalize() + ' ' + identifier.rsplit('/', 1)[-1][:240]
    result = deepcopy(record)
    result.update(id=identifier, semantic_id=identifier, kind=actual_kind,
                  asset_kind=actual_kind, name=name)
    if source_model_kind:
        if record.get('source_asset_kind', 'tmd_model') != 'tmd_model':
            raise ProjectError('Project Asset Database model source family conflicts with its imported kind')
        result['source_asset_kind'] = 'tmd_model'
    return result


def _enriched(base, derived):
    # Select a complete decoded record, rather than guessing a merged source.
    # Wrapper/display additions may differ; every baseline structural field
    # remains present and equal, including the complete source_record.
    ignored = {'id', 'semantic_id', 'kind', 'asset_kind', 'name', 'layer', 'scene_id'}
    return (base['kind'] == derived['kind'] and
            ('source_record' in base) == ('source_record' in derived) and
            all(key in derived and derived[key] == value for key, value in base.items() if key not in ignored))


def _scene_coverage(scene, import_hash, catalog, supplied):
    if not isinstance(supplied, dict) or set(supplied) - {'status', 'reason', 'limitations', 'source_import_sha256', 'source_catalog_key'}:
        raise ProjectError('Project Asset Database scene coverage has invalid fields')
    catalog_key = catalog['source_key'] if catalog is not None else None
    if (supplied.get('source_import_sha256', import_hash) != import_hash or
            supplied.get('source_catalog_key', catalog_key) != catalog_key):
        raise ProjectError('Project Asset Database scene coverage differs from source provenance')
    limitations = _limitations((catalog or {}).get('limitations', []))
    limitations += _limitations(supplied.get('limitations', []))
    explicit = supplied.get('status', (catalog or {}).get('status'))
    if explicit is None:
        explicit = 'unavailable' if catalog is None else 'partial' if limitations else 'available'
    if (not isinstance(explicit, str) or explicit not in STATUSES or
            (catalog is None and explicit != 'unavailable') or (catalog is not None and explicit == 'unavailable')):
        raise ProjectError('Project Asset Database scene availability conflicts with its decoded evidence')
    reason = supplied.get('reason')
    if reason is not None and (not isinstance(reason, str) or not reason or len(reason) > 8192):
        raise ProjectError('Project Asset Database unavailable reason exceeds its metadata format')
    if reason is not None and explicit != 'unavailable':
        raise ProjectError('Available project Asset Database scene cannot carry an unavailable reason')
    if explicit == 'unavailable':
        limitations.append('Derived resources unavailable: ' + (reason or 'No source-qualified resource catalog was supplied.'))
    return explicit, list(dict.fromkeys(limitations))


def assemble(project, catalogs, coverage=None) -> dict:
    """Adapt already verified source products, retaining every scene variant."""
    imports = _imports(project)
    if not isinstance(catalogs, dict) or set(catalogs) - set(imports):
        raise ProjectError('Project Asset Database catalogs must belong to imported scenes')
    supplied = {} if coverage is None else coverage
    if not isinstance(supplied, dict) or set(supplied) - set(imports):
        raise ProjectError('Project Asset Database coverage must belong to imported scenes')
    _metadata(dict(catalogs=catalogs, coverage=supplied))
    _budget(dict(imports=imports, catalogs=catalogs, coverage=supplied))
    key = source_key(project)
    draft_models={row['source_id']:row for row in project.model_references() if row['kind']=='draft_initial_model_assignment'}
    drafts = {}
    for identifier, draft in sorted(project.actor_drafts.items()):
        project._validate_actor_draft(identifier, draft)
        drafts.setdefault(draft['scene_id'], []).append(dict(
            id=identifier, kind='actor', layer='authored', draft=True, name=draft['name'],
            scene_id=draft['scene_id'], donor_entity_id=draft['donor_entity_id'], authored=deepcopy(draft),
            model_reference=deepcopy(draft_models.get(identifier))))
    indexed, scenes, membership_count = {}, [], 0
    for scene, document in sorted(imports.items()):
        import_hash = digest(document)
        catalog = catalogs.get(scene)
        if catalog is not None:
            if (not isinstance(catalog, dict) or catalog.get('scene_id') != scene or
                    not isinstance(catalog.get('source_key'), str) or
                    re.fullmatch(r'[0-9a-f]{64}', catalog['source_key']) is None or
                    not isinstance(catalog.get('records'), list)):
                raise ProjectError('Project Asset Database catalog requires its exact scene and source key')
        status, limitations = _scene_coverage(scene, import_hash, catalog, supplied.get(scene, {}))
        local = {}

        def add(record, catalog_key=None, base_kind=None, authored=False):
            nonlocal membership_count
            normalized = _record(record, scene, base_kind)
            if authored:
                # Validated project names retain their exact authored value;
                # source-record structural display fallback does not rename them.
                normalized['name'] = record['name']
            identifier = normalized['id']
            if not authored and (identifier.startswith('authored-actor://') or normalized['kind'] == 'actor' and 'draft' in normalized):
                raise ProjectError('NPC draft identities require validated authored project records')
            variant = dict(scene_id=scene, source_import_sha256=import_hash,
                           source_catalog_key=catalog_key, record=normalized)
            previous = local.get(identifier)
            if previous is not None:
                if previous['record'] == normalized:
                    if catalog_key is not None:
                        local[identifier] = variant
                    return
                if previous['source_catalog_key'] is None and catalog_key is not None and _enriched(previous['record'], normalized):
                    local[identifier] = variant
                    return
                raise ProjectError('Project Asset Database has conflicting same-scene duplicate records: ' + identifier)
            if identifier in indexed and indexed[identifier]['kind'] != normalized['kind']:
                raise ProjectError('Project Asset Database shared identity has conflicting kinds: ' + identifier)
            if identifier not in indexed:
                indexed[identifier] = dict(id=identifier, kind=normalized['kind'], label=normalized['name'], scene_ids=[], variants=[])
                if len(indexed) > MAX_ASSETS:
                    raise ProjectError('Project Asset Database exceeds the 16384 unique asset budget')
            local[identifier] = variant
            membership_count += 1
            if membership_count > MAX_MEMBERSHIPS:
                raise ProjectError('Project Asset Database exceeds the 65536 scene membership budget')

        add(document['scene'], base_kind='scene')
        for record in document['actors']:
            add(record, base_kind='actor')
        for record in document['assets'].get('models', []):
            add(record, base_kind='model')
        if catalog is not None:
            for record in catalog['records']:
                add(record, catalog['source_key'])
        for record in drafts.get(scene, []):
            add(record, base_kind='actor', authored=True)
        for identifier, variant in sorted(local.items()):
            indexed[identifier]['variants'].append(variant)
            indexed[identifier]['scene_ids'].append(scene)
            # The first deterministic scene variant supplies the summary label.
            if len(indexed[identifier]['variants']) == 1:
                indexed[identifier]['label'] = variant['record']['name']
        scenes.append(dict(id=scene, name=document['scene']['name'], import_sha256=import_hash,
                           status=status, record_count=len(local), limitations=limitations))
    counts = {status: sum(row['status'] == status for row in scenes) for status in STATUSES}
    result = dict(schema_version='legaia.project-assets.v1', source_key=key, project_path=str(project.root),
                  metadata_only=True, read_only=True, scenes=scenes,
                  assets=[indexed[identifier] for identifier in sorted(indexed)],
                  coverage=dict(imported_scene_count=len(scenes), available_scene_count=counts['available'],
                                partial_scene_count=counts['partial'], unavailable_scene_count=counts['unavailable'],
                                asset_count=len(indexed), membership_count=membership_count),
                  limitations=list(LIMITATIONS))
    _metadata(result)
    _budget(result)
    if key != source_key(project):
        raise ProjectError('Project Asset Database source changed during assembly')
    return deepcopy(result)


def inspect(project) -> dict:
    """Verify all imports before decoding on a fully detached project copy."""
    from importer.pipeline import _disc_context
    from .resources import _verify, refresh_resource_catalog
    if not project.disc_path:
        raise ProjectError('Project Asset Database discovery requires the user-owned source disc')
    key = source_key(project)
    view = copy(project)
    for name, value in vars(project).items():
        if name != 'assets':
            setattr(view, name, deepcopy(value))
    view.assets = AssetDatabase()
    if key != source_key(view):
        raise ProjectError('Project Asset Database source changed while taking its snapshot')
    catalogs, coverage = {}, {}
    with _disc_context(view.disc_path):
        for scene, document in sorted(view.imports.items()):
            try:
                _verify(view, document)
            except RetailImportError as exc:
                coverage[scene] = dict(status='unavailable', reason=str(exc))
        for scene in sorted(view.imports):
            if scene in coverage:
                continue
            view.active_scene = scene
            try:
                catalogs[scene] = refresh_resource_catalog(view)
            except RetailImportError as exc:
                coverage[scene] = dict(status='unavailable', reason=str(exc))
            _budget(dict(imports=view.imports, catalogs=catalogs, coverage=coverage))
    if key != source_key(project) or key != source_key(view):
        raise ProjectError('Project Asset Database source changed during discovery')
    result = assemble(view, catalogs, coverage)
    if key != source_key(project):
        raise ProjectError('Project Asset Database source changed during discovery')
    return result

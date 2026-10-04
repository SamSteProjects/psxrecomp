"""Persistent donor snapshots for independently allocated rigid clips."""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record, append_animation_record_payloads
from importer.animation_authoring import patch_animation_channels
from importer.pipeline import _disc_context, import_scene
from importer.scene_animation import load_scene_actor_animation_catalog
from .project import ProjectError, canonical, digest

SCHEMA = 'legaia.animation-record-ledger.v1'
ENTRY_KEYS = {'record_id', 'entity_id', 'channel_owner_entity_id', 'model_source_entity_id',
              'donor_animation_id', 'donor_asset_id', 'donor_record_sha256',
              'effective_donor_record_sha256', 'donor_frame_count', 'object_count',
              'donor_edits', 'source_frame_indices', 'edits', 'record_sha256'}


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _identity(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    return parsed is not None and parsed.version == 4 and str(parsed) == value


def _edits(rows, frames, objects):
    if not isinstance(rows, list) or len(rows) > 4096:
        raise ProjectError('Animation ledger axis edits exceed bounds')
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row)-{'frame_index','object_index','translation','rotation_psx'} or
                not {'frame_index','object_index'} <= set(row) or
                not set(row) & {'translation','rotation_psx'}):
            raise ProjectError('Animation ledger requires exact channel axes')
        frame, obj = row['frame_index'], row['object_index']
        if type(frame) is not int or type(obj) is not int or not 0 <= frame < frames or not 0 <= obj < objects:
            raise ProjectError('Animation ledger channel index exceeds bounds')
        if (frame,obj) in seen:
            raise ProjectError('Duplicate animation ledger channel edit')
        seen.add((frame,obj))
        for field in ('translation','rotation_psx'):
            if field not in row:
                continue
            axes = row[field]
            if not isinstance(axes,dict) or not axes or set(axes)-set('xyz'):
                raise ProjectError('Animation ledger requires nonempty XYZ axes')
            for value in axes.values():
                if (type(value) is not int or
                        (field == 'translation' and not -2048 <= value <= 2047) or
                        (field == 'rotation_psx' and (not 0 <= value <= 4080 or value % 16))):
                    raise ProjectError('Animation ledger axis value exceeds source bounds')


def validate(project, scene_id, value, *, verify_disc=False):
    document = project.imports.get(scene_id)
    if (document is None or not isinstance(value,dict) or set(value) != {
            'schema_version','source_scene_id','source_bank_sha256','revision','records','removed_record_ids'} or
            value['schema_version'] != SCHEMA or value['source_scene_id'] != scene_id or
            not _hash(value['source_bank_sha256']) or type(value['revision']) is not int or
            not 1 <= value['revision'] <= 64 or not isinstance(value['records'],list) or
            not 1 <= len(value['records']) <= 64 or not isinstance(value['removed_record_ids'],list)):
        raise ProjectError('Animation record ledger has invalid source/schema/budgets')
    if len(canonical(value)) > 2*1024*1024:
        raise ProjectError('Animation record ledger exceeds 2 MiB metadata')
    actors = {a['semantic_id']:a for a in document['actors']}
    identities, total = set(), 0
    prefix = f"animation://{document['scene']['name']}/scene-anm/"
    for entry in value['records']:
        if not isinstance(entry,dict) or set(entry) != ENTRY_KEYS or not _identity(entry['record_id']):
            raise ProjectError('Allocated animation entry has invalid fields/identity')
        identity = entry['record_id']
        if identity in identities:
            raise ProjectError('Duplicate allocated animation identity')
        identities.add(identity)
        if any(not isinstance(entry[key],str) or entry[key] not in actors
               for key in ('entity_id','channel_owner_entity_id','model_source_entity_id')):
            raise ProjectError('Allocated animation witnesses must be imported actors in its scene')
        donor = actors[entry['channel_owner_entity_id']]
        clip = entry['donor_animation_id']
        if (not isinstance(clip,str) or not clip.startswith(prefix) or
                len(clip[len(prefix):]) != 4 or not clip[len(prefix):].isascii() or
                not clip[len(prefix):].isdigit() or int(clip[len(prefix):]) >= 4096 or
                donor['placement_fields'].get('animation_id') != int(clip[len(prefix):])+1 or
                entry['donor_asset_id'] != donor['model_reference'].get('asset_semantic_id') or
                any(not _hash(entry[key]) for key in ('donor_record_sha256','effective_donor_record_sha256','record_sha256'))):
            raise ProjectError('Allocated animation donor provenance differs from imported binding')
        frames, objects = entry['donor_frame_count'], entry['object_count']
        sequence = entry['source_frame_indices']
        if (type(frames) is not int or not 1 <= frames <= 512 or type(objects) is not int or not 1 <= objects <= 64 or
                not isinstance(sequence,list) or not 1 <= len(sequence) <= 512 or
                any(type(frame) is not int or not 0 <= frame < frames for frame in sequence)):
            raise ProjectError('Allocated animation donor/sequence counts exceed bounds')
        total += len(sequence)*objects
        if total > 4096:
            raise ProjectError('Animation ledger exceeds its cumulative 4096-channel budget')
        _edits(entry['donor_edits'],frames,objects)
        _edits(entry['edits'],len(sequence),objects)
    removed = value['removed_record_ids']
    if (len(removed) > len(identities) or any(not _identity(item) or item not in identities for item in removed) or
            len(set(removed)) != len(removed)):
        raise ProjectError('Animation ledger tombstones must name distinct retained identities')
    if verify_disc:
        source, catalog = verified_source(project,scene_id)
        verify_witnesses(value,catalog)
        reconstruct(source,value)
    return deepcopy(value)


def verified_source(project, scene_id):
    document = project.imports.get(scene_id)
    if document is None or not project.disc_path:
        raise ProjectError('Allocated animations require imported scene and user-owned disc')
    with _disc_context(project.disc_path):
        if digest(import_scene(project.disc_path,document['scene']['name'])) != digest(document):
            raise ProjectError('Allocated animation source differs from imported evidence')
        catalog = load_scene_actor_animation_catalog(project.disc_path,document['scene']['name'])
        source, _ = catalog.source_bank()
    return source, catalog


def reconstruct(source, ledger):
    """Rebuild captured records against Retail; later shared edits cannot alter them."""
    if sha256(source).hexdigest() != ledger['source_bank_sha256']:
        raise ProjectError('Animation ledger bank preimage differs from Retail')
    ranges = animation_record_ranges(source)
    payloads = []
    removed = set(ledger['removed_record_ids'])
    for entry in ledger['records']:
        index = int(entry['donor_animation_id'].rsplit('/',1)[1])
        if not 0 <= index < len(ranges):
            raise ProjectError('Allocated animation donor record is outside Retail bank')
        start,end = ranges[index]
        donor = source[start:end]
        decoded = decode_animation_record(donor)
        if decoded['frame_count'] != entry['donor_frame_count'] or decoded['bone_count'] != entry['object_count']:
            raise ProjectError('Allocated animation donor counts differ from Retail')
        effective, _ = patch_animation_channels(donor,entry['donor_record_sha256'],entry['donor_edits'])
        if sha256(effective).hexdigest() != entry['effective_donor_record_sha256']:
            raise ProjectError('Allocated animation captured donor hash differs')
        record, _ = allocate_animation_record(effective,entry['effective_donor_record_sha256'],
                                              entry['source_frame_indices'],entry['edits'])
        if sha256(record).hexdigest() != entry['record_sha256']:
            raise ProjectError('Allocated animation record hash differs from its ledger')
        if entry['record_id'] not in removed:
            payloads.append(dict(record_id=entry['record_id'],record=record))
    return payloads


def verify_witnesses(ledger, catalog):
    bindings = {row['actor_semantic_id']:row for row in catalog.referenced_animation_metadata()['bindings']}
    for entry in ledger['records']:
        binding = bindings.get(entry['channel_owner_entity_id'])
        if (binding is None or binding['semantic_id'] != entry['donor_animation_id'] or
                binding['asset_semantic_id'] != entry['donor_asset_id'] or
                binding['source_record']['record_sha256'] != entry['donor_record_sha256']):
            raise ProjectError('Allocated animation donor/model witness is not supported by Retail')


def compose(project, scene_id, *, ledger=None):
    value = ledger if ledger is not None else project.overrides.get(scene_id,{}).get('AnimationRecords')
    source, catalog = verified_source(project,scene_id)
    document = project.imports[scene_id]
    owners = {a['semantic_id']:deepcopy(project.overrides[a['semantic_id']]['AnimationChannels'])
              for a in document['actors'] if 'AnimationChannels' in project.overrides.get(a['semantic_id'],{})}
    effective, _ = catalog.authored_bank(owners)
    if value is None:
        return effective, None
    validate(project,scene_id,value)
    verify_witnesses(value,catalog)
    payloads = reconstruct(source,value)
    return append_animation_record_payloads(effective,sha256(effective).hexdigest(),payloads)


def publish(project, scene_id, ledger):
    before = deepcopy(project.overrides.get(scene_id))
    after = deepcopy(before or {})
    after['AnimationRecords'] = deepcopy(ledger)
    if before != after:
        project.overrides[scene_id] = after
        project.undo_stack.append(dict(entity_id=scene_id,before=before,after=deepcopy(after)))
        project.redo_stack.clear()

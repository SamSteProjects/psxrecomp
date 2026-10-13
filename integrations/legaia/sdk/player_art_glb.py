"""Immutable physical-art import inputs and independently replayed baselines."""
from copy import deepcopy
from base64 import b64decode, b64encode
from hashlib import sha256
import re
from importer.core import ImportError as NativeError
from importer.player_art_authoring import compose, _source
from importer.player_art_glb import import_player_art_glb
from importer.player_battle import _sources, assemble_tmd
from .project import ProjectError, atomic_write, digest

MAX_BYTES = 4 * 1024 * 1024
SLOT_BYTES = 0x10800
MAX_PROJECT_BYTES = 64 * 1024 * 1024
KEYS = {'schema_version', 'stream_id', 'archive_id', 'source_record',
        'glb_sha256', 'glb_byte_length', 'baseline_slot_sha256',
        'baseline_slot_byte_length', 'baseline_owners', 'model_source_sha256',
        'equipped', 'object_part_indices', 'fps', 'animation_index',
        'object_node_indices', 'import_digest'}


def _path(project, key, kind):
    if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
        raise ProjectError('Art input identity requires an exact SHA-256')
    if kind not in ('glb', 'bin'):
        raise ProjectError('Art input kind changed')
    folder = 'ArtInputs' if kind == 'glb' else 'ArtBaselines'
    path = project.root / 'Authored' / 'PLAYER' / folder / (key + '.' + kind)
    if not path.resolve().is_relative_to(project.root.resolve()):
        raise ProjectError('Art input path escapes the project root')
    return path


def _bytes(project, key, size, kind):
    limit = MAX_BYTES if kind == 'glb' else SLOT_BYTES
    if type(size) is not int or not 1 <= size <= limit:
        raise ProjectError('Art retained input size exceeds its bounds')
    path = _path(project, key, kind)
    if not path.is_file() or path.stat().st_size != size:
        raise ProjectError('Art retained input is missing or changed size')
    content = path.read_bytes()
    if sha256(content).hexdigest() != key:
        raise ProjectError('Art retained input hash changed')
    return content


def _convert(project, original, catalog, archive_id, stream_id, current,
             baseline_owners, content, equipped, fps, animation_index,
             object_node_indices):
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_BYTES:
        raise ProjectError('Art motion GLB must be at most 4 MiB')
    try:
        stream, _ = _source(original, catalog, archive_id, stream_id)
        # Complete slot equality proves fixed headers, unused capacity and tail,
        # while permitting legitimate authored neighboring streams.
        if compose(original, catalog, archive_id, baseline_owners) != current:
            raise ProjectError('Art retained baseline differs from canonical owners')
        disc_hash, files = _sources(project.disc_path)
        if disc_hash != catalog['source_disc_sha256']:
            raise ProjectError('Art retained model belongs to another source disc')
        model = files[stream['player_index']][3]
        _, assembly, _ = assemble_tmd(model, equipped)
        parts = assembly['animation_part_indices']
        candidate, report = import_player_art_glb(
            original, catalog, archive_id, stream_id, current,
            sha256(current).hexdigest(), parts, content, fps=fps,
            animation_index=animation_index, object_node_indices=object_node_indices)
    except (NativeError, KeyError, TypeError, ValueError, IndexError) as error:
        raise ProjectError('Art retained import cannot replay its source and assembly') from error
    return stream, sha256(model).hexdigest(), parts, candidate, report


def prepare_input(project, original, catalog, archive_id, stream_id, current,
                  baseline_owners, content, *, equipped, fps,
                  animation_index=None, object_node_indices=None):
    """Qualify without writing; preserve Current-relative conversion evidence."""
    stream, model_hash, parts, candidate, report = _convert(
        project, original, catalog, archive_id, stream_id, current,
        baseline_owners, content, equipped, fps, animation_index, object_node_indices)
    evidence = dict(schema_version='legaia.player-art-glb-input.v1',
                    stream_id=stream_id, archive_id=archive_id,
                    source_record=deepcopy(stream['source_record']),
                    glb_sha256=sha256(content).hexdigest(), glb_byte_length=len(content),
                    baseline_slot_sha256=sha256(current).hexdigest(),
                    baseline_slot_byte_length=len(current),
                    baseline_owners=deepcopy(baseline_owners),
                    model_source_sha256=model_hash, equipped=deepcopy(equipped),
                    object_part_indices=deepcopy(parts), fps=fps,
                    animation_index=animation_index,
                    object_node_indices=deepcopy(object_node_indices),
                    import_digest=digest(report))
    return candidate, report, evidence


def validate_input(project, original, catalog, value):
    """Replay historical input independently of later numeric Current edits."""
    if (not isinstance(value, dict) or set(value) != KEYS or
            value['schema_version'] != 'legaia.player-art-glb-input.v1' or
            type(value['baseline_slot_byte_length']) is not int or
            value['baseline_slot_byte_length'] != SLOT_BYTES):
        raise ProjectError('Art retained input metadata changed')
    content = _bytes(project, value['glb_sha256'], value['glb_byte_length'], 'glb')
    current = _bytes(project, value['baseline_slot_sha256'], SLOT_BYTES, 'bin')
    candidate, report, expected = prepare_input(
        project, original, catalog, value['archive_id'], value['stream_id'],
        current, value['baseline_owners'], content, equipped=value['equipped'],
        fps=value['fps'], animation_index=value['animation_index'],
        object_node_indices=value['object_node_indices'])
    if value != expected:
        raise ProjectError('Art retained input source, assembly or receipt changed')
    return candidate, report


def check_budget(project, evidence_values):
    if not isinstance(evidence_values, (list, tuple)) or len(evidence_values) > 88:
        raise ProjectError('Art retained inputs exceed the source stream catalogue')
    files = {}
    for evidence in evidence_values:
        if not isinstance(evidence, dict) or set(evidence) != KEYS or evidence['schema_version'] != 'legaia.player-art-glb-input.v1':
            raise ProjectError('Art retained budget metadata changed')
        for key, size, kind in [(evidence['glb_sha256'], evidence['glb_byte_length'], 'glb'),
                                (evidence['baseline_slot_sha256'], evidence['baseline_slot_byte_length'], 'bin')]:
            path = _path(project, key, kind)
            limit = MAX_BYTES if kind == 'glb' else SLOT_BYTES
            if (type(size) is not int or not 1 <= size <= limit or
                    (kind == 'bin' and size != SLOT_BYTES) or
                    (path in files and files[path] != size)):
                raise ProjectError('Art retained budget sizes changed')
            files[path] = size
    if sum(files.values()) > MAX_PROJECT_BYTES:
        raise ProjectError('Art retained inputs exceed the 64 MiB project budget')


def retain_inputs(project, value, current, content, *, active_inputs=()):
    """Preflight all active sizes and existing files before creating either file.

    Caller must use fresh prepare_input evidence. This helper never changes a
    project owner or history. Budget counts unique content-addressed files.
    """
    if not isinstance(value, dict) or set(value) != KEYS or value['schema_version'] != 'legaia.player-art-glb-input.v1':
        raise ProjectError('Art retained input metadata changed')
    proposed = ((value['glb_sha256'], value['glb_byte_length'], 'glb', content),
                (value['baseline_slot_sha256'], value['baseline_slot_byte_length'], 'bin', current))
    for key, size, kind, raw in proposed:
        limit = MAX_BYTES if kind == 'glb' else SLOT_BYTES
        if (type(size) is not int or not 1 <= size <= limit or
                (kind == 'bin' and size != SLOT_BYTES) or not isinstance(raw, bytes) or
                len(raw) != size or sha256(raw).hexdigest() != key):
            raise ProjectError('Art bytes differ from prepared retained input')
    if not isinstance(active_inputs, (list, tuple)) or len(active_inputs) > 87:
        raise ProjectError('Art retained inputs exceed the source stream catalogue')
    check_budget(project, [*active_inputs, value])
    for evidence in active_inputs:
        _bytes(project, evidence['glb_sha256'], evidence['glb_byte_length'], 'glb')
        _bytes(project, evidence['baseline_slot_sha256'], evidence['baseline_slot_byte_length'], 'bin')
    targets = [(_path(project, key, kind), raw) for key, _, kind, raw in proposed]
    for path, raw in targets:
        if path.exists() and (not path.is_file() or path.read_bytes() != raw):
            raise ProjectError('Art retained content-addressed file changed')
    created = []
    try:
        for path, raw in targets:
            if not path.exists():
                created.append(path)
                atomic_write(path, raw)
    except Exception:
        for path in reversed(created):
            if path.is_file():
                path.unlink()
        raise
    return tuple(created)


def _decode(value):
    if not isinstance(value,str) or not 1<=len(value)<=MAX_BYTES*4//3+4:
        raise ProjectError('Art GLB requires at most 4 MiB of exact base64 bytes')
    try:content=b64decode(value,validate=True)
    except (ValueError,TypeError) as error:raise ProjectError('Art GLB requires exact base64 bytes') from error
    if not 1<=len(content)<=MAX_BYTES:raise ProjectError('Art GLB requires at most 4 MiB')
    return content


def prepare_review(project,frame_index,part_index,expected_current_slot_sha256,
                   glb_base64,fps,animation_index,object_node_indices,**context):
    from .player_art_authoring import inspect,_edit
    from .player_art_store import context as sources,numeric_values,composed_slots
    from .battle_character_resources import _fresh
    from importer.me_archive import entries
    from importer.player_battle import decode_part
    from importer.player_art_authoring import owner
    inspection=inspect(project,frame_index,part_index,**context)
    if inspection['current_slot_sha256']!=expected_current_slot_sha256:
        raise ProjectError('Art GLB Current slot changed; inspect again')
    content=_decode(glb_base64);base=inspection['base_playback'];stream=base['stream']
    original=b64decode(base['source_slot_base64']);current=b64decode(inspection['current_slot_base64'])
    raw,catalog,_=sources(project)
    candidate,analysis,evidence=prepare_input(project,original,catalog,stream['archive_asset_id'],stream['semantic_id'],
        current,numeric_values(inspection['owners']),content,equipped=context['equipped'],fps=fps,
        animation_index=animation_index,object_node_indices=object_node_indices)
    if evidence['object_part_indices']!=base['base_inspection']['assembly']['animation_part_indices']:
        raise ProjectError('Art GLB assembly mapping changed')
    if not analysis['edits'] or candidate==current:raise ProjectError('Art GLB Review requires changed Current motion')
    retail=entries(original)[stream['stream_index']]['decoded'];decoded=entries(candidate)[stream['stream_index']]['decoded']
    rows=[]
    for frame in range(stream['frame_count']):
        for part in range(stream['part_count']):
            at=2+(frame*stream['part_count']+part)*9
            if decoded[at:at+9]!=retail[at:at+9]:
                rows.append(dict(frame_index=frame,part_index=part,**decode_part(decoded[at:at+9])))
    after=deepcopy(project.player_art_overrides);identifier=stream['semantic_id']
    try:
        if rows:
            after[identifier]=owner(original,catalog,stream['archive_asset_id'],identifier,rows)
            after[identifier]['glb_import']=deepcopy(evidence)
        else:after.pop(identifier,None)
    except NativeError as error:raise ProjectError(str(error)) from error
    canonical=composed_slots(raw,catalog,numeric_values(after)).get(stream['archive_asset_id'],original)
    source=stream['source_record'];at=source['byte_offset']-source['slot_offset'];end=at+source['byte_length']
    # Conversion preserves Current unused body bytes; final native ownership
    # always encodes on Retail. Verify semantic equality and all outside bytes,
    # then use the canonical body so shortening/restoration cannot retain stale
    # compressed bytes from an earlier owner.
    if (canonical[:at]!=candidate[:at] or canonical[end:]!=candidate[end:] or
            entries(canonical)[stream['stream_index']]['decoded']!=decoded):
        raise ProjectError('Art GLB differs from canonical final owner composition')
    canonicalized_bytes=sum(a!=b for a,b in zip(canonical,candidate));candidate=canonical
    active=[v['glb_import'] for v in after.values() if 'glb_import' in v]
    check_budget(project,active)
    value=dict(schema_version='legaia.player-art-glb-review.v1',inspection=inspection,frame_index=frame_index,part_index=part_index,
        glb_import=analysis,retained_input=evidence,ownership_after=deepcopy(after.get(identifier)),
        candidate_slot_base64=b64encode(candidate).decode(),candidate_slot_sha256=sha256(candidate).hexdigest(),
        candidate_body_sha256=sha256(candidate[at:end]).hexdigest(),candidate_decoded_base64=b64encode(decoded).decode(),
        projection=dict(byte_change_count=sum(a!=b for a,b in zip(current,candidate)),changed_current_part_frames=len(analysis['edits']),retail_relative_part_frames=len(rows),
            native_body_policy='retail_relative_canonical_owner',canonicalized_body_bytes=canonicalized_bytes),
        capacity=dict(original_body_size=source['byte_length'],decoded_byte_count=len(decoded),growth=False),
        motion_layer='proposed',geometry_layer=context['layer'],persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)
    value['review_key']=digest(value);_edit(project);_fresh(project,context['expected_project_path'],context['expected_source_key'])
    return current,content,after,value


def review(project,**args):return prepare_review(project,**args)[3]


def proposed_pose(project,review_key,**args):
    from .player_art_animation import frame_geometry
    value=review(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Art GLB Proposed requires exact fresh Review')
    base=value['inspection']['base_playback'];stream=base['stream'];frame=args['frame_index']
    current,ct=frame_geometry(base['base_inspection'],stream,b64decode(value['inspection']['current_decoded_base64']),frame)
    proposed,pt=frame_geometry(base['base_inspection'],stream,b64decode(value['candidate_decoded_base64']),frame)
    return dict(schema_version='legaia.player-art-glb-pose.v1',review=value,review_key=review_key,
        current_pose=dict(geometry=current,object_transforms=ct,frame_index=frame),
        proposed_pose=dict(geometry=proposed,object_transforms=pt,frame_index=frame),
        motion_layer='proposed',geometry_layer=args['layer'],persistence='not_applied',read_only=True,project_changed=False,gameplay_verified=False)


def apply(project,review_key,**args):
    from .player_art_store import validate
    from .player_art_authoring import _edit
    from .battle_character_resources import _fresh
    current,content,after,value=prepare_review(project,**args)
    if value['review_key']!=review_key:raise ProjectError('Art GLB Apply requires exact fresh Review')
    before=deepcopy(project.player_art_overrides);created=()
    try:
        if value['ownership_after'] is not None:
            active=[v['glb_import'] for k,v in after.items() if k!=args['stream_id'] and 'glb_import' in v]
            created=retain_inputs(project,value['retained_input'],current,content,active_inputs=active)
        after=validate(project,after);_edit(project);_fresh(project,args['expected_project_path'],args['expected_source_key'])
    except Exception:
        for path in reversed(created):path.unlink(missing_ok=True)
        raise
    project.player_art_overrides=after
    project.undo_stack.append(dict(target='player_art_overrides',before=before,after=deepcopy(after),label='PLAYER Art GLB'))
    project.redo_stack.clear()
    return dict(schema_version='legaia.player-art-glb-apply.v1',history_steps=1,project_changed=True,
        stream_id=args['stream_id'],current_slot_sha256=value['candidate_slot_sha256'],
        retained_input=deepcopy(value['retained_input']) if value['ownership_after'] is not None else None,gameplay_verified=False)


def input_records(project,catalog):
    """Register active historical inputs separately from final Current channels."""
    from .player_art_store import context,composed_slots
    values=getattr(project,'player_art_overrides',{})
    if not isinstance(values,dict):raise ProjectError('Art retained input ownership changed')
    if not any(isinstance(v,dict) and 'glb_import' in v for v in values.values()):return []
    raw,verified,_=context(project)
    if catalog!=verified:raise ProjectError('Art retained input catalogue changed')
    composed_slots(raw,catalog,values,project=project)
    streams={s['semantic_id']:s for s in catalog['streams']};records=[]
    for identifier,binding in sorted(values.items()):
        evidence=binding.get('glb_import')
        if evidence is None:continue
        stream=streams[identifier];player=stream['player_index'];role=stream['archive_role'];index=stream['stream_index'];key=evidence['glb_sha256']
        records.append(dict(semantic_id=f'retained-animation://legaia/player-art/{player:04d}/{role}/{index:04d}/glb/{key}',
            asset_kind='retained_player_art_glb',name=f'PLAYER {player} {role.title()} Art Stream {index} GLB Input',
            model_asset_id=stream['model_asset_id'],stream_asset_id=identifier,player_index=player,archive_role=role,stream_index=index,
            layer='retained_authored_input',source_record=deepcopy(evidence),retail_source=deepcopy(stream['source_record']),
            references=[stream['model_asset_id'],identifier],current_body_sha256=binding['current_body_sha256'],current_decoded_sha256=binding['decoded_sha256'],
            relationship='historical_import_input_not_final_current_art',read_only=True,gameplay_verified=False))
    return records


def export_input(project,expected_project_path,expected_source_key,asset_id):
    from .player_art_animation import resources
    from .battle_character_resources import _fresh
    report=resources(project,expected_project_path,expected_source_key)
    record=next((r for r in report['retained_art_inputs'] if r['semantic_id']==asset_id),None)
    if record is None:raise ProjectError('Art GLB input is no longer registered; refresh Project assets')
    evidence=record['source_record'];content=_bytes(project,evidence['glb_sha256'],evidence['glb_byte_length'],'glb')
    _fresh(project,expected_project_path,expected_source_key)
    return dict(schema_version='legaia.player-art-input-export.v1',project_path=str(project.root),project_source_key=expected_source_key,
        record=record,filename=f'player-art-input-{record["player_index"]}-{record["archive_role"]}-{record["stream_index"]}-{evidence["glb_sha256"]}.glb',
        glb_base64=b64encode(content).decode(),read_only=True,project_changed=False,gameplay_verified=False)

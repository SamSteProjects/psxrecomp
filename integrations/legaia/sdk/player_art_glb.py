"""Immutable physical-art import inputs; not yet registered in owner/API schemas."""
from copy import deepcopy
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
    files = {}
    for evidence in [*active_inputs, value]:
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

"""Persistent source-qualified SEQ operands and raw native PROT delivery."""
from copy import deepcopy
from hashlib import sha256
from importer.audio_catalog import read_audio_sequence, decode_audio_entry
from importer.audio_sequence import inspect_sequence
from importer.audio_sequence_authoring import replace_audio_entry_sequence, MAX_EDITS
from importer.pipeline import _disc_context
from .project import ProjectError, digest

COMMANDS = {'set_audio_sequence_operands', 'clear_audio_sequence_operands'}
MAX_ASSETS = 128


def _hash(body):
    return sha256(body).hexdigest()


def _inspection(body):
    report = inspect_sequence(body)
    report['limitations'][-1] = ('SDK projects can author reached fixed-width channel/tempo operands; '
                                'synthesis, bank assignment and game playback remain unverified.')
    return report


def source_key(project):
    return digest(dict(root=str(project.root), mode=project.mode, document=project._document()))


def _source(project, asset_id, entry_sha256, scene_id):
    from .resources import _verify
    if not isinstance(scene_id, str):
        raise ProjectError('Audio source scene must be an imported identity')
    document = project.imports.get(scene_id)
    if not project.disc_path or document is None:
        raise ProjectError('Audio edits require a verified imported scene and retail disc')
    with _disc_context(project.disc_path) as (image, _, _, archive):
        _verify(project, document)
        sequence, record = read_audio_sequence(project.disc_path, asset_id, entry_sha256)
        body = image.read_user(archive.node.extent_lba, record['entry_byte_offset'],
                               record['entry_size_bytes'], archive.node.size)
        if _hash(body) != entry_sha256:
            raise ProjectError('Audio entry changed during source qualification')
    return body, sequence, record


def read(project, asset_id, binding):
    """Reconstruct and qualify saved metadata against fresh native source."""
    if (not isinstance(binding, dict) or set(binding) != {'format', 'source_scene_id', 'source_record', 'edits'}
            or binding['format'] != 'seq-operands-v1' or not isinstance(binding['source_record'], dict)):
        raise ProjectError('Invalid source-qualified audio operand binding')
    body, sequence, record = _source(project, asset_id, binding['source_record'].get('entry_sha256'),
                                      binding['source_scene_id'])
    if record != binding['source_record']:
        raise ProjectError('Saved audio source ownership differs from retail readback')
    output, audit = replace_audio_entry_sequence(body, body,
        expected_source_sha256=_hash(body), expected_current_sha256=_hash(body), edits=binding['edits'])
    canonical = _normalise(inspect_sequence(sequence), binding['edits'])
    if not canonical or canonical != binding['edits']:
        raise ProjectError('Audio bindings require sorted unique nonretail operand edits')
    return body, output, record, audit


def validate_collection(project):
    if not isinstance(project.audio_overrides, dict) or len(project.audio_overrides) > MAX_ASSETS:
        raise ProjectError('Audio overrides must be a bounded resource mapping')
    for identifier, binding in project.audio_overrides.items():
        read(project, identifier, binding)


def _normalise(source, edits):
    rows = {event['offset']: event for event in source['events']}
    # The native codec validates exact shapes, legal values and unique offsets
    # before this normalization is called.
    return [deepcopy(edit) for edit in sorted(edits, key=lambda e: e['event_offset'])
            if edit['values'] != rows[edit['event_offset']]['values']]


def _current(project, asset_id, entry_sha256):
    body, sequence, record = _source(project, asset_id, entry_sha256, project.active_scene)
    binding = project.audio_overrides.get(asset_id)
    current = body
    if binding is not None:
        bound_source, current, bound_record, _ = read(project, asset_id, binding)
        if bound_source != body or bound_record != record:
            raise ProjectError('Audio override no longer refers to the same global source entry')
    return body, current, sequence, record, binding


def options(project, asset_id, expected_entry_sha256, expected_source_key):
    from .scene_preview import source_key as resource_key
    if expected_source_key != resource_key(project):
        raise ProjectError('Audio resource source changed; refresh resources')
    key = source_key(project)
    body, current, sequence, record, binding = _current(project, asset_id, expected_entry_sha256)
    start, size = record['sequence_offset'], record['sequence_size_bytes']
    source_report = _inspection(sequence)
    current_report = _inspection(current[start:start+size])
    if source_key(project) != key:
        raise ProjectError('Audio authored state changed during inspection')
    return dict(schema_version='legaia.audio-sequence-authoring.v1', asset_id=asset_id,
                authoring_key=key, source_key=expected_source_key, scene_id=project.active_scene,
                source_record=record, current_entry_sha256=_hash(current),
                current_sequence_sha256=_hash(current[start:start+size]),
                binding_source_scene_id=binding['source_scene_id'] if binding else project.active_scene,
                authored_edits=deepcopy(binding['edits']) if binding else [],
                retail=source_report, current=current_report, max_edits=MAX_EDITS,
                project_changed=False, runtime_state='not_observed')


def review(project, asset_id, expected_entry_sha256, expected_authoring_key, edits):
    if project.mode != 'edit' or expected_authoring_key != source_key(project):
        raise ProjectError('Audio authored state changed or is not in Edit mode; inspect again')
    body, current, sequence, record, binding = _current(project, asset_id, expected_entry_sha256)
    candidate, audit = replace_audio_entry_sequence(body, current,
        expected_source_sha256=_hash(body), expected_current_sha256=_hash(current), edits=edits)
    merged = {e['event_offset']: deepcopy(e) for e in (binding['edits'] if binding else [])}
    merged.update({e['event_offset']: deepcopy(e) for e in edits})
    final_edits = _normalise(inspect_sequence(sequence), list(merged.values()))
    if len(final_edits) > MAX_EDITS:
        raise ProjectError('Audio entry exceeds 256 authored source events')
    after = (dict(format='seq-operands-v1', source_scene_id=binding['source_scene_id'] if binding else project.active_scene,
                  source_record=record, edits=final_edits) if final_edits else None)
    if after:
        _, reconstructed, _, _ = read(project, asset_id, after)
        if reconstructed != candidate:
            raise ProjectError('Composed audio operands differ from their native reconstruction')
    elif candidate != body:
        raise ProjectError('Cleared audio operands do not restore retail bytes')
    if source_key(project) != expected_authoring_key:
        raise ProjectError('Audio state changed while reviewing operands')
    report = dict(schema_version='legaia.audio-sequence-review.v1', asset_id=asset_id,
                  authoring_key=expected_authoring_key, source_record=record,
                  proposed_binding=after, native_audit=audit, no_change=current==candidate,
                  project_changed=False, runtime_state='not_observed')
    report['review_key'] = digest(report)
    return report


def command(project, value):
    kind = value.get('type')
    fields = {'type', 'asset_id', 'expected_entry_sha256', 'expected_authoring_key'}
    if kind == 'set_audio_sequence_operands':
        fields |= {'edits', 'review_key'}
    elif kind != 'clear_audio_sequence_operands':
        raise ProjectError('Unsupported audio operand command')
    if set(value) != fields:
        raise ProjectError('Audio commands require exact resource and freshness fields')
    identifier = value['asset_id']
    before = deepcopy(project.audio_overrides.get(identifier)) if isinstance(identifier, str) else None
    if kind == 'set_audio_sequence_operands':
        report = review(project, identifier, value['expected_entry_sha256'], value['expected_authoring_key'], value['edits'])
        if report['review_key'] != value['review_key']:
            raise ProjectError('Audio operands differ from the reviewed proposal')
        after = report['proposed_binding']
    else:
        if project.mode != 'edit' or value['expected_authoring_key'] != source_key(project):
            raise ProjectError('Audio state changed; inspect again before clearing')
        _current(project, identifier, value['expected_entry_sha256'])
        if value['expected_authoring_key'] != source_key(project):
            raise ProjectError('Audio state changed while clearing operands')
        after = None
    if before == after:
        return
    if after is not None and before is None and len(project.audio_overrides) >= MAX_ASSETS:
        raise ProjectError('Audio resource override budget reached')
    if after is None:
        project.audio_overrides.pop(identifier, None)
    else:
        project.audio_overrides[identifier] = deepcopy(after)
    project.undo_stack.append(dict(target='audio_overrides', asset_id=identifier, before=before, after=deepcopy(after)))
    project.redo_stack.clear()


def prepare_overlays(project, image, archive):
    """Independently encode only requested operands and bind native disc extents."""
    validate_collection(project)
    overlays, changes = [], []
    for identifier, binding in sorted(project.audio_overrides.items()):
        body, candidate, record, _ = read(project, identifier, binding)
        start = record['sequence_offset']
        source_events = {e['offset']: e for e in inspect_sequence(body[start:start+record['sequence_size_bytes']])['events']}
        expected = bytearray(body)
        for edit in binding['edits']:
            event = source_events[edit['event_offset']]
            tempo = event['kind'] == 'set_tempo'
            encoded = edit['values'][0].to_bytes(3,'big') if tempo else bytes(edit['values'])
            position = start + event['end_offset'] - len(encoded)
            expected[position:position+len(encoded)] = encoded
            changes.append(dict(scene='global-audio', semantic_id=identifier,
                field='audio.sequence.'+event['kind'], scope='audio-SEQ-fixed-operands-only',
                event_offset=event['offset'], entry_byte_offset=position, byte_length=len(encoded),
                before_value=list(event['values']), after_value=list(edit['values']),
                source_entry_sha256=_hash(body), candidate_entry_sha256=_hash(candidate)))
        if candidate != bytes(expected) or len(candidate) != len(body):
            raise ProjectError('Native audio serializer changed bytes outside requested operand spans')
        decode_audio_entry(candidate)
        offset = archive.node.extent_lba*2048 + record['entry_byte_offset']
        if image.read_user(0, offset, len(body), image.size//2352*2048) != body:
            raise ProjectError('Audio PROT entry failed physical disc extent binding')
        overlays.append(dict(scene='global-audio', source_kind='raw_PROT_SEQ', iso_file='PROT.DAT',
            prot_entry_index=record['prot_entry_index'], entry_byte_offset=record['entry_byte_offset'],
            offset=offset, size=len(candidate), file=f"assets/audio-seq-{record['prot_entry_index']:04d}.bin",
            payload=candidate, sha256=_hash(candidate), expected_sha256=_hash(body)))
    return overlays, changes

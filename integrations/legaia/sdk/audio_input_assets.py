"""Content identities for retained WAV blobs and their historical target receipts."""
from copy import deepcopy
import re

from .audio_sample_sources import read_source, validate_collection
from .project import ProjectError, digest

PREFIX = 'audio-input://legaia/wav/'


def inventory(project):
    """Qualify project files, without decoding native banks or changing the project."""
    rows = deepcopy(project.audio_sample_sources)
    validate_collection(rows)
    expected = digest(rows)
    assets, receipts, memberships = {}, {}, {}
    for receipt_key, row in sorted(rows.items()):
        scene = row['source_scene_id']
        imported = project.imports.get(scene)
        if not isinstance(imported, dict):
            raise ProjectError('WAV asset capture scene is absent from imported project sources')
        if imported.get('source', {}).get('disc_identity') != 'sha256:' + row['source_record']['disc_sha256']:
            raise ProjectError('WAV asset capture disc differs from its imported scene')
        # The existing reader qualifies exact bytes, mono PCM layout, frame count
        # and rate against this receipt; an ID alone never qualifies a file.
        read_source(project, row)
        identifier = PREFIX + row['wav_sha256']
        record = dict(id=identifier, semantic_id=identifier, kind='audio', asset_kind='audio',
            name='WAV input ' + row['wav_sha256'][:12], layer='authored_input',
            source_kind='retained_wav_input', format='pcm-wav',
            source_record=dict(kind='project_wav_input', sha256=row['wav_sha256'],
                byte_length=row['byte_length'], relative_path='Authored/Audio/Sources/' + row['wav_sha256'] + '.wav'),
            audio_input=dict(schema_version='legaia.audio-input-asset.v1',
                wav_sha256=row['wav_sha256'], byte_length=row['byte_length'],
                input_wav_rate=row['input_wav_rate'], decoded_frames=row['decoded_frames'],
                channels=1, bits_per_sample=16))
        if identifier in assets and assets[identifier] != record:
            raise ProjectError('Shared WAV content has conflicting retained file metadata')
        assets[identifier] = record
        memberships.setdefault(scene, set()).add(identifier)
        receipts.setdefault(identifier, []).append(deepcopy(row))
    if expected != digest(project.audio_sample_sources):
        raise ProjectError('Retained WAV assets changed during file qualification')
    return dict(records_by_scene={scene: [deepcopy(assets[key]) for key in sorted(keys)]
                                 for scene, keys in sorted(memberships.items())},
                assets=deepcopy(assets), receipts=deepcopy(receipts))


def inspect(project, identifier, expected_source_key, *, include_wav=False):
    """Return one qualified local source asset, not a runtime/native sample."""
    from .project_assets import source_key
    if not isinstance(identifier, str) or re.fullmatch(re.escape(PREFIX) + r'[a-f0-9]{64}', identifier) is None:
        raise ProjectError('Choose a retained WAV asset identity')
    if type(include_wav) is not bool:
        raise ProjectError('WAV download selection must be Boolean')
    if source_key(project) != expected_source_key:
        raise ProjectError('Project WAV asset sources changed')
    snapshot = inventory(project)
    if identifier not in snapshot['assets']:
        raise ProjectError('WAV asset has no retained receipt in Current')
    result = dict(schema_version='legaia.audio-input-inspection.v1', asset_id=identifier,
        source_key=expected_source_key, project_path=str(project.root),
        record=deepcopy(snapshot['assets'][identifier]), receipts=deepcopy(snapshot['receipts'][identifier]),
        historical_inputs=True, read_only=True, project_changed=False,
        runtime_binding='not_asserted', gameplay_verified=False)
    if include_wav:
        import base64
        result['wav_base64'] = base64.b64encode(read_source(project, result['receipts'][0])).decode('ascii')
    # Requalify files before publication, including changes that do not alter the
    # saved document's metadata identity.
    if inventory(project) != snapshot or source_key(project) != expected_source_key:
        raise ProjectError('Project WAV asset sources changed during inspection')
    return deepcopy(result)

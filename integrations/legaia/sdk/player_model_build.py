"""Deliver replayed PLAYER Current files within adjacent physical TOC bounds."""
from hashlib import sha256
from importer.player_battle import DATA_BASE, table
from .player_model_store import effective, validate
from .project import ProjectError


def prepare(project, archive, disc_hash):
    values = getattr(project, 'player_model_overrides', {})
    validate(project, values)
    overlays, changes = [], []
    for identifier, binding in sorted(values.items()):
        index = 863 + int(identifier[-1])
        entry, following = archive.entry(index), archive.entry(index + 1)
        length = (following.start_lba - entry.start_lba) * archive.SECTOR
        if not DATA_BASE < length <= 4 * 1024 * 1024:
            raise ProjectError('PLAYER Build physical boundary is unsupported')
        original = archive.image.read_user(archive.node.extent_lba,
            entry.start_lba * archive.SECTOR, length, archive.node.size)
        rows = table(original)
        source = dict(disc=dict(sha256=disc_hash, serial='SCUS-94254'),
            iso_file='PROT.DAT', prot_entry_index=index,
            record_kind='adjacent_toc_bounded_player_file',
            start_lba=entry.start_lba, next_start_lba=following.start_lba,
            byte_length=length, sha256=sha256(original).hexdigest(),
            boundary_evidence='adjacent_PROT_start_and_complete_descriptor_chain')
        current = effective(project, dict(semantic_id=identifier, source_record=source), original)
        if len(current) != length or table(current) != rows or current[:DATA_BASE] != original[:DATA_BASE]:
            raise ProjectError('PLAYER Build changed record0, descriptors or physical footprint')
        if current == original:
            continue
        offset = (archive.node.extent_lba + entry.start_lba) * archive.SECTOR
        overlays.append(dict(scene='player-battle', offset=offset, size=length,
            file=f'assets/player-{index - 863}-native.bin', payload=current,
            sha256=sha256(current).hexdigest(), expected_sha256=source['sha256'],
            source_kind='adjacent_toc_bounded_player_file', source_record=source,
            retained_input_sha256=[i['sha256'] for i in binding['inputs']],
            retained_input_replay=True))
        changes.append(dict(scene='player-battle', semantic_id=identifier,
            field='model.shape', scope='PLAYER-native-model-pools-only',
            before_sha256=source['sha256'], after_sha256=sha256(current).hexdigest(),
            prot_entry_index=index, byte_length=length,
            retained_input_count=len(binding['inputs']),
            changed_byte_count=sum(a != b for a, b in zip(original, current))))
    return overlays, changes

"""Deliver replayed PLAYER Current files within adjacent physical TOC bounds."""
from hashlib import sha256
from importer.player_battle import DATA_BASE, table
from .player_model_store import effective, validate
from .project import ProjectError


def prepare(project, archive, disc_hash):
    values = getattr(project, 'player_model_overrides', {})
    validate(project, values)
    from .player_action_store import validate as validate_actions, effective as effective_actions
    action_values = getattr(project, 'player_action_overrides', {})
    validate_actions(project, action_values)
    overlays, changes = [], []
    for identifier in sorted(set(values) | set(action_values)):
        binding = values.get(identifier)
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
        record = dict(semantic_id=identifier, source_record=source)
        model_current = effective(project, record, original)
        if len(model_current) != length or table(model_current) != rows or model_current[:DATA_BASE] != original[:DATA_BASE]:
            raise ProjectError('PLAYER Build changed record0, descriptors or physical footprint')
        action_current, action_reports = effective_actions(project, record, original)
        descriptor_offset = rows[0]['descriptor_offset']
        if action_current[:16] != original[:16] or action_current[descriptor_offset:] != original[descriptor_offset:]:
            raise ProjectError('PLAYER action Build changed model-owned bytes')
        current = model_current[:16] + action_current[16:descriptor_offset] + model_current[descriptor_offset:]
        if current == original:
            continue
        offset = (archive.node.extent_lba + entry.start_lba) * archive.SECTOR
        overlays.append(dict(scene='player-battle', offset=offset, size=length,
            file=f'assets/player-{index - 863}-native.bin', payload=current,
            sha256=sha256(current).hexdigest(), expected_sha256=source['sha256'],
            source_kind='adjacent_toc_bounded_player_file', source_record=source,
            retained_input_sha256=[i['sha256'] for i in binding['inputs']] if binding else [],
            retained_input_replay=True, action_ledger_replay=bool(action_reports)))
        if model_current != original:changes.append(dict(scene='player-battle', semantic_id=identifier,
            field='model.shape', scope='PLAYER-native-model-pools-only',
            before_sha256=source['sha256'], after_sha256=sha256(model_current).hexdigest(),
            prot_entry_index=index, byte_length=length,
            retained_input_count=len(binding['inputs']),
            changed_byte_count=sum(a != b for a, b in zip(original, model_current))))
        for report in action_reports:
            for channel in report['channels']:
                changes.append(dict(channel,scene='player-battle',semantic_id=identifier,
                    animation_id=f'animation://legaia/player-battle/{index-863:04d}/action/{report["action_slot"]:04d}',
                    action_slot=report['action_slot'],scope='PLAYER-action-channel-content-only',
                    source_bank_sha256=report['source_bank_sha256'],proposed_bank_sha256=report['proposed_bank_sha256']))
    return overlays, changes

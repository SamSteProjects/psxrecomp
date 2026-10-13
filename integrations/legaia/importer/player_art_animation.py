"""PLAYER art records and separate resident ME archive source references.

The bank's rate_alt byte is retained as a source-role hint. Runtime resident
archive selection is not observed; a preview must select its archive explicitly.
"""
from hashlib import sha256
import struct
from .core import ImportError, validate_metadata_only
from .pipeline import _disc_context, REFERENCE_COMMIT
from .player_battle import _sources, actions
from .me_archive import entries


def bank_records(raw, player_index, disc_sha256):
    _, bank = actions(raw, player_index, disc_sha256)
    start = struct.unpack_from('<I', bank, 0x58)[0]
    count = struct.unpack_from('<I', bank, start)[0]
    boundary = struct.unpack_from('<I', raw, 4)[0]
    if not 1 <= count <= 64 or start + 4 + count * 0xd0 > boundary:
        raise ImportError('PLAYER art bank exceeds its decoded record0 source region')
    result = []
    for index in range(count):
        at = start + 4 + index * 0xd0
        body = bank[at:at + 0xd0]
        combo = list(body[:10].split(b'\0', 1)[0])
        name = body[0x10:0x24].split(b'\0', 1)[0]
        if any(v not in (1, 2, 3, 4) for v in combo) or any(not 32 <= v < 127 for v in name):
            raise ImportError('PLAYER art combo or inline name is unsupported')
        source = dict(disc=dict(sha256=disc_sha256, serial='SCUS-94254'), prot_entry_index=863 + player_index,
                      source_entry_sha256=sha256(raw).hexdigest(), containing_sha256=sha256(bank).hexdigest(),
                      containing_size=len(bank), byte_coordinate_space='decoded_player_record0',
                      record_kind='player_art_bank_record', byte_offset=at, byte_length=0xd0,
                      sha256=sha256(body).hexdigest(), bank_offset=start, bank_record_count=count)
        result.append(dict(semantic_id=f'art-record://legaia/player-battle/{player_index:04d}/{index:04d}',
                           asset_kind='player_art_record', player_index=player_index, record_index=index,
                           staged_animation_id=0x10 + index, name=name.decode('ascii'), combo=combo,
                           stream_source=body[0x0a], entry_tag=body[0x24], attach_key=body[0x9b],
                           rate_byte=body[0x9c], rate_alt_byte=body[0xa8],
                           reference_archive_role='base' if body[0xa8] == 255 else 'main', source_record=source,
                           reference_commit=REFERENCE_COMMIT))
    return result


def discover(disc):
    digest, players = _sources(disc)
    with _disc_context(disc) as (_, current_digest, _, archive):
        raw = archive.read_entry(archive.entry(894))
    if current_digest != digest or len(raw) != 78 * 0x10800:
        raise ImportError('PLAYER art archive disc or fixed entry footprint changed')
    archive_hash = sha256(raw).hexdigest()
    archives, streams, records = [], [], []
    for player, item in enumerate(players):
        owned = bank_records(item[3], player, digest)
        for role in ('main', 'base'):
            slot = player * 3 + (1 if role == 'main' else 2)
            body = raw[slot * 0x10800:(slot + 1) * 0x10800]
            parsed = entries(body)
            expected = [17, 18, 19, 1][player] if role == 'main' else 8
            if len(parsed) != expected:
                raise ImportError('PLAYER art ME archive differs from its qualified source entry count')
            archive_id = f'archive://legaia/player-art/894/{slot:04d}'
            archives.append(dict(semantic_id=archive_id, player_index=player, role=role, slot_index=slot,
                                 entry_count=len(parsed), slot_sha256=sha256(body).hexdigest()))
            for entry in parsed:
                data = entry['decoded']
                if data[0] != [15, 16, 15, 17][player]:
                    raise ImportError('PLAYER art stream part count differs from the qualified character source rig')
                index = entry['entry_index']
                source = dict(disc=dict(sha256=digest, serial='SCUS-94254'), iso_file='PROT.DAT', prot_entry_index=894,
                              entry_sha256=archive_hash, entry_byte_length=len(raw), slot_index=slot,
                              slot_offset=slot * 0x10800, slot_byte_length=0x10800, slot_sha256=sha256(body).hexdigest(),
                              record_kind='player_art_me_stream', byte_coordinate_space='raw_prot_entry',
                              byte_offset=slot * 0x10800 + entry['byte_offset'], byte_length=entry['byte_length'],
                              size_word=entry['size_word'], compressed=entry['compressed'],
                              sha256=sha256(body[entry['byte_offset']:entry['byte_offset'] + entry['byte_length']]).hexdigest(),
                              decoded_sha256=sha256(data).hexdigest(), decoded_byte_length=len(data))
                streams.append(dict(semantic_id=f'animation://legaia/player-art/{player:04d}/{role}/{index:04d}',
                                    asset_kind='animation', name=f'PLAYER {player} {role.title()} Art Stream {index}',
                                    model_asset_id=f'asset://legaia/models/player-battle/{player:04d}',
                                    player_index=player, archive_role=role, archive_asset_id=archive_id,
                                    stream_index=index, part_count=data[0], frame_count=data[1], source_record=source,
                                    reference_commit=REFERENCE_COMMIT, timing='not_observed', runtime_state='not_observed'))
        for record in owned:
            eligible = [s['semantic_id'] for s in streams if s['player_index'] == player and s['stream_index'] == record['stream_source']]
            preferred = f"animation://legaia/player-art/{player:04d}/{record['reference_archive_role']}/{record['stream_source']:04d}"
            if preferred not in eligible:
                raise ImportError('PLAYER art bank source index lies outside its reference archive role')
            record.update(eligible_stream_ids=eligible, reference_stream_id=preferred,
                          relationship='static_bank_reference_runtime_resident_archive_not_observed')
        records.extend(owned)
    file_hashes = [sha256(item[3]).hexdigest() for item in players]
    key = sha256(('player-art-v1:' + digest + ':' + archive_hash + ':' + ':'.join(file_hashes)).encode()).hexdigest()
    result = dict(schema_version='legaia.player-art-catalog.v1', source_disc_sha256=digest, source_entry_sha256=archive_hash,
                  source_key=key, player_file_sha256=file_hashes, archives=archives, streams=streams, records=records,
                  reference_commit=REFERENCE_COMMIT, read_only=True, project_changed=False, gameplay_verified=False,
                  limitations=['Runtime archive residency, activation, cadence and interpolation are unobserved.',
                               'Art records may share streams; record identity and physical source identity remain distinct.',
                               'Source decoding does not establish writable capacity or native animation authoring.'])
    validate_metadata_only(result)
    return result


def load_stream(disc, stream_id, expected_source_key):
    catalog = discover(disc)
    if expected_source_key != catalog['source_key']:
        raise ImportError('PLAYER art source changed; refresh discovery')
    record = next((r for r in catalog['streams'] if r['semantic_id'] == stream_id), None)
    if record is None:
        raise ImportError('Choose an existing physical PLAYER art stream')
    with _disc_context(disc) as (_, digest, _, archive):
        raw = archive.read_entry(archive.entry(894))
    source = record['source_record']
    if digest != catalog['source_disc_sha256'] or sha256(raw).hexdigest() != source['entry_sha256']:
        raise ImportError('PLAYER art entry identity changed')
    slot = raw[source['slot_offset']:source['slot_offset'] + source['slot_byte_length']]
    if sha256(slot).hexdigest() != source['slot_sha256']:
        raise ImportError('PLAYER art slot identity changed')
    parsed = entries(slot)[record['stream_index']]
    if parsed['byte_length'] != source['byte_length'] or source['slot_offset'] + parsed['byte_offset'] != source['byte_offset'] or sha256(parsed['decoded']).hexdigest() != source['decoded_sha256']:
        raise ImportError('PLAYER art decoded source span changed')
    return catalog, record, slot, parsed['decoded']

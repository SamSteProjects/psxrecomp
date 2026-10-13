"""Fixed-slot battle sideband sources; object-local geometry, not native assembly."""
from hashlib import sha256
import struct
from importer.core import ImportError, TMD_MAGIC, validate_metadata_only
from importer.assets import decode_tmd
from importer.pipeline import REFERENCE_COMMIT

SLOT_BYTES = 0x10800
ENTRIES = {893: 103, 894: 78}
LIMITATIONS = [
    'Object-local sources only; native assembly and animation are unresolved.',
    'Source CLUT words only; live upload, residency and STP forcing are unobserved.',
    'Fixed source envelopes are not writable allocation or scene membership.',
]


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def model_extent(body):
    geometry = decode_tmd(body)
    end = 12 + 28 * len(geometry['objects'])
    for i in range(len(geometry['objects'])):
        vertex, count, normal, normals, _, _, _ = struct.unpack_from('<7I', body, 12 + i * 28)
        end = max(end, 12 + vertex + count * 8, 12 + normal + normals * 8)
    if end > len(body) or decode_tmd(body[:end]) != geometry:
        raise ImportError('Compact side-band model does not preserve its complete referenced geometry')
    return end, geometry


def decode_catalog(entries, disc_sha256):
    if type(entries) is not dict or not _hash(disc_sha256) or set(entries) != set(ENTRIES):
        raise ImportError('Battle side-band discovery requires both fixed entries and an immutable disc hash')
    banks = []
    models, textures, slots = [], [], []
    for entry, count in ENTRIES.items():
        content = entries[entry]
        if not isinstance(content, bytes) or len(content) != count * SLOT_BYTES:
            raise ImportError('Battle side-band entry differs from the qualified fixed-slot footprint')
        bank_hash = sha256(content).hexdigest()
        banks.append(dict(prot_entry_index=entry, byte_length=len(content), sha256=bank_hash, slot_count=count))
        for index in range(count):
            start = index * SLOT_BYTES
            body = content[start:start + SLOT_BYTES]
            header = struct.unpack_from('<3I', body)
            source = dict(disc=dict(sha256=disc_sha256, serial='SCUS-94254'), iso_file='PROT.DAT',
                          prot_entry_index=entry, entry_sha256=bank_hash, entry_byte_length=len(content),
                          slot_index=index, slot_offset=start, slot_byte_length=SLOT_BYTES,
                          slot_sha256=sha256(body).hexdigest(), byte_coordinate_space='raw_prot_entry')
            row = dict(prot_entry_index=entry, slot_index=index, kind='opaque', source_record=source)
            if header[0] in (0, 1, 2):
                mode = header[0]
                clut_rows = 2 if mode == 1 else 1
                image_offset = 4 + clut_rows * 512
                width_words = 64 if mode == 0 else 128
                length = image_offset + width_words * 2 * 256
                if length > SLOT_BYTES:
                    raise ImportError('Battle side-band texture exceeds its fixed slot')
                record = dict(semantic_id=f'texture://legaia/battle-sideband/{entry}/{index:04d}',
                              asset_kind='texture', name=f'Battle Sideband {entry} Texture Slot {index}',
                              mode=mode, width=width_words * 4, height=256, bpp=4,
                              palette_count=clut_rows * 16, clut_rows=clut_rows,
                              image_offset=image_offset, image_byte_length=width_words * 2 * 256,
                              source_record=dict(source, record_kind='sideband_clut_page', byte_offset=start,
                                                 byte_length=length, sha256=sha256(body[:length]).hexdigest()),
                              preview_supported=True, reference_commit=REFERENCE_COMMIT)
                textures.append(record)
                row.update(kind='texture', asset_id=record['semantic_id'])
            else:
                name, model, pool = header
                if 0x4c <= name < model < pool < SLOT_BYTES and model + 12 <= SLOT_BYTES and struct.unpack_from('<I', body, model)[0] == TMD_MAGIC:
                    row.update(kind='actor_record', name_offset=name, model_offset=model, texture_pool_offset=pool,
                               part_count=body[0x4a], preview_supported=False)
                    try:
                        if not 1 <= row['part_count'] <= 16 or 0x4c + row['part_count'] * 4 > name:
                            raise ImportError('Battle side-band actor part table exceeds its source header')
                        end, geometry = model_extent(body[model:])
                        record = dict(semantic_id=f'asset://legaia/models/battle-sideband/{entry}/{index:04d}',
                                      asset_kind='tmd_model', name=f'Battle Sideband {entry} Actor Slot {index}',
                                      source_record=dict(source, record_kind='sideband_actor_tmd', byte_offset=start + model,
                                                         byte_length=end, sha256=sha256(body[model:model + end]).hexdigest()),
                                      source_model_offset=model, source_texture_pool_offset=pool,
                                      references_beyond_texture_pool=end > pool - model,
                                      preview_summary=dict(objects=len(geometry['objects']), vertices=len(geometry['vertices']),
                                                           triangles=len(geometry['triangles'])),
                                      preview_supported=True, reference_commit=REFERENCE_COMMIT)
                        models.append(record)
                        row.update(asset_id=record['semantic_id'], preview_supported=True)
                    except ImportError as error:
                        row['diagnostic'] = str(error)
            slots.append(row)
    key = sha256(('battle-sideband-v1:' + disc_sha256 + ':' + ':'.join(b['sha256'] for b in banks)).encode()).hexdigest()
    result = dict(schema_version='legaia.battle-sideband-catalog.v1', source_disc_sha256=disc_sha256,
                  source_key=key, banks=banks, models=models, textures=textures, slots=slots,
                  reference_commit=REFERENCE_COMMIT, limitations=LIMITATIONS.copy(),
                  read_only=True, project_changed=False, gameplay_verified=False)
    validate_metadata_only(result)
    return result


def texture_preview(content, record, palette_index):
    if type(palette_index) is not int or not 0 <= palette_index < record['palette_count']:
        raise ImportError('Choose an existing local side-band CLUT palette')
    source = record['source_record']
    body = content[source['byte_offset']:source['byte_offset'] + source['byte_length']]
    if sha256(body).hexdigest() != source['sha256']:
        raise ImportError('Battle side-band texture source changed')
    words = struct.unpack_from('<16H', body, 4 + palette_index * 32)
    palette = []
    for word in words:
        channels = [(word >> shift) & 31 for shift in (0, 5, 10)]
        palette.append(bytes([(v << 3) | (v >> 2) for v in channels] + [0 if word == 0 else 255]))
    raw = body[record['image_offset']:]
    rgba, stp = bytearray(len(raw) * 8), bytearray(len(raw) * 2)
    for i, byte in enumerate(raw):
        for j, index in enumerate((byte & 15, byte >> 4)):
            pixel = i * 2 + j
            rgba[pixel * 4:pixel * 4 + 4] = palette[index]
            stp[pixel] = (words[index] >> 15) & 1
    return dict(width=record['width'], height=256, palette_index=palette_index,
                words=list(words), rgba=bytes(rgba), stp=bytes(stp), stp_forcing='not_applied_source_words_only')


def load_sources(disc):
    from .pipeline import _disc_context
    with _disc_context(disc) as (_, digest, _, archive):
        entries = {i: archive.read_entry(archive.entry(i)) for i in ENTRIES}
    return decode_catalog(entries, digest), entries


def discover(disc):
    return load_sources(disc)[0]

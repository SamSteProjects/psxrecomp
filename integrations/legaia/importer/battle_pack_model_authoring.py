"""Tagged fixed-layout pack TMD interchange, separate from PLAYER assembly."""
from copy import deepcopy
from hashlib import sha256
import struct
from .core import ImportError
from .assets import decode_tmd
from .battle_character_catalog import material_textures
from .model_glb import export_model_glb, import_model_glb
from .model_authoring import replace_model_content


def source(original, record, catalog, current_tmd=None):
    if (not isinstance(original, bytes) or not isinstance(record, dict)
            or not isinstance(catalog, dict) or record not in catalog.get('models', [])
            or catalog.get('source_entry_index') != 1204
            or len(original) != catalog.get('source_entry_byte_length')
            or sha256(original).hexdigest() != catalog.get('source_entry_sha256')):
        raise ImportError('Pack model authoring requires its complete immutable Retail entry')
    native = record['source_record']; at = native['byte_offset']; size = native['byte_length']
    if (native['prot_entry_index'] != 1204 or native['record_kind'] != 'raw_prot_entry'
            or native['containing_sha256'] != catalog['source_entry_sha256']
            or native['containing_size'] != len(original) or native['stream_chunk_type'] != 9
            or native['stream_header_offset'] != at-4 or at < 4 or size < 12
            or at+size > len(original) or struct.unpack_from('<I', original, at-4)[0] != (9 << 24) | size):
        raise ImportError('Pack native model stream header or source extent changed')
    retail = original[at:at+size]
    if sha256(retail).hexdigest() != native['sha256']:
        raise ImportError('Pack Retail TMD differs from its source record')
    tmd = retail if current_tmd is None else current_tmd
    if not isinstance(tmd, bytes) or len(tmd) != size:
        raise ImportError('Pack Current model must preserve the exact native span')
    replace_model_content(retail, native['sha256'], tmd, allow_normal_references=True)
    geometry = decode_tmd(tmd)
    geometry.update(semantic_id=record['semantic_id'], source_record=deepcopy(native),
                    representation='retail-reference-pack-not-player-assembly')
    geometry['textures'] = material_textures(original, catalog, geometry)
    return tmd, geometry


def export(original, record, catalog, current_tmd=None):
    tmd, geometry = source(original, record, catalog, current_tmd)
    content, profile = export_model_glb(tmd, geometry)
    binding = dict(schema_version='legaia.battle-pack-model-glb-binding.v1',
        asset_id=record['semantic_id'], source_record=deepcopy(record['source_record']),
        current_tmd_sha256=sha256(tmd).hexdigest(), profile=profile)
    return content, binding


def convert(original, record, catalog, binding, content, current_tmd=None):
    current, _ = source(original, record, catalog, current_tmd)
    _, fresh = export(original, record, catalog, current)
    if binding != fresh:
        raise ImportError('Pack model GLB binding changed; export the selected Current model again')
    candidate, analysis = import_model_glb(current, content, binding['profile'])
    candidate, changes = replace_model_content(current, sha256(current).hexdigest(), candidate,
                                               allow_normal_references=True)
    _, geometry = source(original, record, catalog, candidate)
    at = record['source_record']['byte_offset']; end = at+len(candidate)
    entry = original[:at]+candidate+original[end:]
    if len(entry) != len(original) or entry[:at] != original[:at] or entry[end:] != original[end:]:
        raise ImportError('Pack model projection changed neighboring models, textures or stream headers')
    return candidate, dict(schema_version='legaia.battle-pack-model-projection.v1',
        source_tmd_sha256=sha256(current).hexdigest(), candidate_tmd_sha256=sha256(candidate).hexdigest(),
        source_entry_sha256=sha256(original).hexdigest(), candidate_entry_sha256=sha256(entry).hexdigest(),
        entry_scope='retail_entry_with_selected_model_only',
        byte_length=len(candidate), changes=changes, glb_analysis=analysis, geometry=geometry,
        source_span=deepcopy(record['source_record']), read_only=True,
        project_changed=False, gameplay_verified=False)

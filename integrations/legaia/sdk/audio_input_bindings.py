"""Current authored WAV dependencies, qualified against composed native bytes."""
from copy import deepcopy
from hashlib import sha256

from .project import ProjectError, digest
from .audio_input_assets import PREFIX


def current(project, inputs, identifier=None):
    bindings = deepcopy(project.audio_sample_overrides)
    if not isinstance(bindings, dict) or len(bindings) > 32:
        raise ProjectError('Current WAV bindings require a bounded native resource mapping')
    from .audio_sample_authoring import read, _sample
    from .audio_composition import read_entry
    from importer.audio_bank import bank_from_entry
    results = []
    count = 0
    for native_id, binding in sorted(bindings.items()):
        # Fully qualify persisted bindings; never infer usage from a receipt alone.
        retail, _, source, _ = read(project, native_id, binding)
        composed = read_entry(project, native_id, retail)
        _, retail_pieces, retail_carrier = bank_from_entry(retail)
        bank, pieces, carrier = bank_from_entry(composed)
        if retail_pieces != source['pieces'] or retail_carrier != source['carrier'] or carrier!=retail_carrier:
            raise ProjectError('Current WAV sample ownership differs from retail pieces')
        scene = binding['source_scene_id']
        if scene not in project.imports:
            raise ProjectError('Current WAV binding scene is not imported')
        for sample in binding['samples']:
            count += 1
            if count > 32:
                raise ProjectError('Current WAV bindings exceed 32 native samples')
            receipt = project.audio_sample_sources.get(sample['receipt_key'])
            wav_id = PREFIX + receipt['wav_sha256']
            if wav_id not in inputs['assets'] or receipt not in inputs['receipts'][wav_id]:
                raise ProjectError('Current native sample lacks a qualified retained WAV asset')
            row, offset, _ = _sample(bank, pieces, sample['sample_index'])
            sample_hash = sha256(composed[offset:offset + row['size_bytes']]).hexdigest()
            if sample_hash != receipt['candidate_sample_sha256']:
                raise ProjectError('Current composed sample differs from its retained WAV candidate')
            if identifier is not None and wav_id != identifier:
                continue
            results.append(dict(native_asset_id=native_id, wav_asset_id=wav_id,
                binding_scene_id=scene, capture_scene_id=receipt['source_scene_id'],
                sample_index=sample['sample_index'], receipt_key=receipt['receipt_key'],
                binding_sha256=digest(binding), retail_entry_sha256=source['entry_sha256'],
                current_entry_sha256=sha256(composed).hexdigest(), current_sample_sha256=sample_hash,
                sample_entry_byte_offset=offset, sample_size_bytes=row['size_bytes']))
    if bindings != project.audio_sample_overrides:
        raise ProjectError('Current WAV bindings changed during native qualification')
    return deepcopy(results)

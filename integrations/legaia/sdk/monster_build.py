"""One guarded native overlay per composed monster slot."""
from hashlib import sha256
import struct
from .project import ProjectError
from .monster_models import validate as validate_models,compose as compose_models
from .monster_palettes import validate as validate_palettes,compose as compose_palettes
from .monster_motions import validate as validate_motion,compose as compose_motion
from importer.monster_archive import decode_catalog,block
from importer.serialization import serialize_lzs_decoded
from importer.core import ImportError as NativeError


def prepare(project,archive,disc_hash):
    palettes=getattr(project,'monster_palette_overrides',{});models=getattr(project,'monster_model_overrides',{})
    motions=getattr(project,'monster_motion_overrides',{})
    validate_palettes(project,palettes);validate_models(project,models);validate_motion(project,motions)
    if not palettes and not models and not motions:return [],[]
    raw=archive.read_entry(archive.entry(867));catalog=decode_catalog(raw,disc_hash);overlays=[];changes=[]
    slots={r['monster_id'] for r in catalog['textures'] if r['semantic_id'] in palettes}|{r['monster_id'] for r in catalog['models'] if r['semantic_id'] in models}
    slots|={r['monster_id'] for r in catalog['animations'] if r['semantic_id'] in motions}
    for identifier in sorted(slots):
        texture=next((r for r in catalog['textures'] if r['monster_id']==identifier),None);model=next((r for r in catalog['models'] if r['monster_id']==identifier),None);owner=model if model and model['semantic_id'] in models or texture is None else texture
        original,used=block(raw,identifier);current=original;binding=palettes.get(texture['semantic_id']) if texture else None
        if binding:current=compose_palettes(original,texture,binding,project)
        current=compose_models(project,original,catalog,identifier,current);start=owner['source_record']['compressed_stream_offset']
        current=compose_motion(original,catalog,identifier,motions,current)
        try:payload,capacity=serialize_lzs_decoded(raw[start:start+used],len(original),current,'monster-slot')
        except NativeError as e:raise ProjectError(str(e)) from e
        offset=(archive.node.extent_lba+archive.entry(867).start_lba)*archive.SECTOR+start
        has_model=model and model['semantic_id'] in models;has_motion=any(c['monster_id']==identifier and c['semantic_id'] in motions for c in catalog['animations'])
        overlays.append(dict(scene='monster-archive',offset=offset,size=used,file=f'assets/monster-{identifier}-'+('slot.bin' if has_model or has_motion else 'palette.bin'),payload=payload,sha256=sha256(payload).hexdigest(),expected_sha256=sha256(raw[start:start+used]).hexdigest(),source_kind='fixed_span_monster_slot' if has_model or has_motion else 'fixed_span_monster_palette',source_record=owner['source_record'],capacity=capacity,decoded_before_sha256=sha256(original).hexdigest(),decoded_after_sha256=sha256(current).hexdigest()))
        for c in catalog['animations']:
            if c['monster_id']==identifier and c['semantic_id'] in motions:
                for edit in motions[c['semantic_id']]['edits']:changes.append(dict(edit,scene='monster-archive',semantic_id=c['semantic_id'],field='motion.part_frame',scope='monster-existing-part-frame-channels',byte_offset=c['source_record']['byte_offset']+2+(edit['frame_index']*c['part_count']+edit['part_index'])*9,byte_length=9))
        if has_model:
            record=models[model['semantic_id']];changes.append(dict(scene='monster-archive',semantic_id=model['semantic_id'],field='model.native_tmd',scope='monster-fixed-layout-model-only',byte_offset=model['source_record']['byte_offset'],byte_length=record['byte_length'],before_sha256=model['source_record']['sha256'],after_sha256=record['current_tmd_sha256'],byte_change_count=len(record['edits'])))
        if binding:
            pool_at=texture['source_record']['byte_offset']
            if 'image_override' in binding:changes.append(dict(scene='monster-archive',semantic_id=texture['semantic_id'],field='texture.image_indices',scope='monster-native-image-indices-only',byte_offset=pool_at+480,byte_length=len(current)-pool_at-480,before_sha256=sha256(original[pool_at+480:]).hexdigest(),after_sha256=sha256(current[pool_at+480:]).hexdigest()))
            for edit in binding['edits']:
                at=pool_at+edit['palette_index']*32+edit['entry_index']*2;changes.append(dict(edit,scene='monster-archive',semantic_id=texture['semantic_id'],field='palette.word',scope='monster-native-palette-words-only',byte_offset=at,before_word=struct.unpack_from('<H',original,at)[0],after_word=edit['word']))
    return overlays,changes

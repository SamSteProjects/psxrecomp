"""Exact raw TMD overlays inside existing PROT1204 model spans."""
from hashlib import sha256
from .battle_pack_models import validate,effective
from importer.battle_character_catalog import decode_catalog


def prepare(project,archive,disc_hash):
    values=getattr(project,'battle_pack_model_overrides',{});validate(project,values)
    if not values:return [],[]
    entry=archive.entry(1204);original=archive.read_entry(entry);catalog=decode_catalog(original,disc_hash)
    overlays=[];changes=[]
    for record in catalog['models']:
        owner=values.get(record['semantic_id'])
        if owner is None:continue
        source=record['source_record'];at=source['byte_offset'];size=source['byte_length']
        payload=effective(project,original,catalog,record,owner)
        offset=(archive.node.extent_lba+entry.start_lba)*archive.SECTOR+at
        overlays.append(dict(scene='battle-character-pack',offset=offset,size=size,
            file=f'assets/battle-pack-{record["pool_index"]}-model.bin',payload=payload,
            sha256=sha256(payload).hexdigest(),expected_sha256=source['sha256'],
            source_kind='fixed_span_battle_pack_model',source_record=source,retained_input_replay=True))
        changes.append(dict(scene='battle-character-pack',semantic_id=record['semantic_id'],
            field='model.native_tmd',scope='battle-pack-existing-TMD-content-only',byte_offset=at,
            byte_length=size,before_sha256=source['sha256'],after_sha256=sha256(payload).hexdigest(),
            byte_change_count=len(owner['edits']),retained_input_count=len(owner['inputs'])))
    return overlays,changes

"""Read-only World vector allocation and complete native carrier qualification.

No binding is published. Archive relocation, Apply and editor authoring remain
separate integration work; a qualified carrier is not playable output.
"""
import base64
import json
import re
from copy import deepcopy
from hashlib import sha256
from importer.pipeline import _disc_context
from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from importer.worldmap_placements import _pack_spans
from importer.model_face_ledger import create_face_ledger, append_vector_ledger
from importer.model_vector_allocation import append_model_vectors
from importer.model_pack_growth import grow_scene_model_pack
from importer.core import parse_scene_assets, decompress_lzs
from importer.assets import decode_tmd
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner, source


def prepare(project, request):
    fields = {'asset_id', 'source_key', 'member_sha256', 'effective_sha256', 'requests'}
    if (not isinstance(request, dict) or set(request) != fields or project.mode != 'edit'
            or request['source_key'] != state_key(project) or not owner(request['asset_id'])):
        raise ProjectError('World vector allocation requires the exact Current Edit source')
    if any(not isinstance(request[k], str) or not re.fullmatch('[0-9a-f]{64}', request[k])
           for k in ('member_sha256', 'effective_sha256')):
        raise ProjectError('World allocation requires native and effective model hashes')
    if len(json.dumps(request, allow_nan=False).encode('utf-8')) > 128*1024:
        raise ProjectError('World vector allocation request exceeds its metadata budget')
    identifier = request['asset_id']; scene = identifier.split('/')[2]
    original, native = source(project, identifier)
    binding = project.model_overrides.get(identifier)
    effective = project.read_model_replacement(identifier, binding) if binding else original
    if (sha256(original).hexdigest() != request['member_sha256']
            or sha256(effective).hexdigest() != request['effective_sha256']):
        raise ProjectError('World allocation source changed; inspect Current again')
    candidate, ledger, topology = append_vector_ledger(effective, create_face_ledger(effective), request['requests'])
    independent, allocation = append_model_vectors(effective, request['effective_sha256'], request['requests'])
    if independent != candidate:
        raise ProjectError('World vector candidate differs from complete ledger replay')
    with _disc_context(project.disc_path) as (_, disc_hash, _, archive):
        _, entry, offset, bundle, raw = _kingdom_table(archive, KINGDOM_BASES[scene])
        pack, _ = _slot(bundle, raw, 1); spans = _pack_spans(pack)
        if (disc_hash != native['disc_sha256'] or entry != native['prot_entry_index']
                or offset != 0 or bundle.table_offset != 0 or native['slot_index'] != 1):
            raise ProjectError('World allocation native carrier ownership changed')
        replacements = []; expected = {}; composed = []
        bindings = dict(project.model_overrides); bindings.setdefault(identifier, None)
        for asset_id, current_binding in sorted(bindings.items()):
            if owner(asset_id) != owner(identifier):
                continue
            retail, record = (original, native) if asset_id == identifier else source(project, asset_id)
            slot = record['pack_slot']
            if (record['disc_sha256'] != disc_hash or record['prot_entry_index'] != entry
                    or record['slot_index'] != 1 or not 0 <= slot < len(spans)
                    or spans[slot] != (record['decoded_member_offset'], record['decoded_member_span_end'])
                    or pack[spans[slot][0]:spans[slot][1]] != retail):
                raise ProjectError('World allocation member differs from its exact Retail slot')
            current = effective if asset_id == identifier else project.read_model_replacement(asset_id, current_binding)
            replay = ledger if asset_id == identifier else create_face_ledger(current)
            replacements.append(dict(slot_index=slot, source_model_byte_length=len(retail),
                base_binding=deepcopy(current_binding), base_payload=current if current_binding else None, ledger=replay))
            expected[slot] = candidate if asset_id == identifier else current
            composed.append(dict(asset_id=asset_id, slot_index=slot, current_sha256=sha256(current).hexdigest(),
                                 proposed_sha256=sha256(expected[slot]).hexdigest()))
        carrier, carrier_audit = grow_scene_model_pack(raw, sha256(raw).hexdigest(), 1,
            sha256(pack).hexdigest(), replacements, allow_growth=True)
        descriptor = parse_scene_assets(carrier, entry).descriptors[1]
        reopened, _ = decompress_lzs(carrier[descriptor.data_offset:], descriptor.size)
        moved = _pack_spans(reopened)
        if len(moved) != len(spans):
            raise ProjectError('World allocation changed native pack slot count')
        for slot, (start, stop) in enumerate(moved):
            before_start, before_stop = spans[slot]
            wanted = expected.get(slot, pack[before_start:before_stop])
            if reopened[start:stop] != wanted:
                raise ProjectError('World allocation changed a model member or unselected neighbor')
    report = dict(schema_version='legaia.worldmap-model-vector-allocation-review.v1',
        project_path=str(project.root), request=deepcopy(request), source_record=deepcopy(native),
        proposed_sha256=sha256(candidate).hexdigest(), proposed_model_base64=base64.b64encode(candidate).decode('ascii'),
        source_byte_length=len(original), current_byte_length=len(effective), proposed_byte_length=len(candidate),
        ledger=deepcopy(ledger), topology=topology, allocation=allocation,
        current_preview=decode_tmd(effective), proposed_preview=decode_tmd(candidate),
        composed_models=composed, carrier=carrier_audit,
        read_only=True, project_changed=False, gameplay_verified=False, build_ready=False,
        scope='native-vector-allocation-and-carrier-review-only')
    if len(json.dumps(report, allow_nan=False).encode('utf-8')) > 16*1024*1024:
        raise ProjectError('World allocation Review exceeds its metadata budget')
    report['review_key'] = digest(report)
    if project.mode != 'edit' or request['source_key'] != state_key(project):
        raise ProjectError('World source changed during allocation Review')
    return candidate, ledger, report


def review(project, request):
    return prepare(project, request)[2]

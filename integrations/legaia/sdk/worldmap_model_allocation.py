"""Source-bound World vector allocation, retained ledger and native carrier Review."""
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
from importer.worldmap_model_ledger import FACE_FORMAT
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_model_binding import owner, source


FORMAT = 'world-tmd-vector-allocation-v1'
CONTENT_FORMAT = 'world-tmd-vector-content-v1'
FORMATS = (FORMAT, CONTENT_FORMAT, FACE_FORMAT)


def retained(project, identifier, original, binding, effective):
    """Return the independently qualified base and replay record for a pack member."""
    if binding and binding.get('format') in FORMATS:
        from .model_face_addition import base_content
        return base_content(project, identifier, original, binding), deepcopy(binding['base_binding']), deepcopy(binding['ledger'])
    return effective, deepcopy(binding), create_face_ledger(effective)


def validate_ledger(binding):
    if binding.get('format') == FACE_FORMAT:
        from importer.worldmap_model_ledger import validate_face_ledger
        validate_face_ledger(binding.get('ledger'))
        return
    from importer.model_face_ledger import VECTOR_SCHEMA
    ledger = binding.get('ledger')
    if (not isinstance(ledger, dict) or ledger.get('schema_version') != VECTOR_SCHEMA
            or not isinstance(ledger.get('operations'), list) or not ledger['operations']
            or not any(isinstance(op,dict) and op.get('kind')=='allocate_vectors' for op in ledger['operations'])
            or any(not isinstance(op,dict) or op.get('kind') not in (('allocate_vectors','edit_content') if binding['format']==CONTENT_FORMAT else ('allocate_vectors',)) for op in ledger['operations'])
            or binding['format']==CONTENT_FORMAT and not any(op.get('kind')=='edit_content' for op in ledger['operations'])):
        raise ProjectError('World vector-only binding requires allocation replay' if binding.get('format')==FORMAT else 'World allocated content binding requires vector/content replay')



def qualify_carrier(project, identifier, original, native, effective, candidate, base_binding, ledger):
    """Compose a proposed native member and prove every remaining pack member."""
    with _disc_context(project.disc_path) as (_, disc_hash, _, archive):
        _, entry, offset, bundle, raw = _kingdom_table(archive, KINGDOM_BASES[identifier.split('/')[2]])
        pack, _ = _slot(bundle, raw, 1); spans = _pack_spans(pack)
        if (disc_hash != native['disc_sha256'] or entry != native['prot_entry_index']
                or offset != 0 or bundle.table_offset != 0 or native['slot_index'] != 1):
            raise ProjectError('World model carrier native carrier ownership changed')
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
                raise ProjectError('World model carrier member differs from its exact Retail slot')
            current = effective if asset_id == identifier else project.read_model_replacement(asset_id, current_binding)
            _, retained_binding, replay = retained(project, asset_id, retail, current_binding, current)
            if asset_id == identifier:
                retained_binding, replay = base_binding, ledger
            retained_payload = project.read_model_replacement(asset_id, retained_binding) if retained_binding else None
            replacements.append(dict(slot_index=slot, source_model_byte_length=len(retail),
                base_binding=retained_binding, base_payload=retained_payload, ledger=replay))
            expected[slot] = candidate if asset_id == identifier else current
            composed.append(dict(asset_id=asset_id, slot_index=slot, current_sha256=sha256(current).hexdigest(),
                                 proposed_sha256=sha256(expected[slot]).hexdigest()))
        carrier, carrier_audit = grow_scene_model_pack(raw, sha256(raw).hexdigest(), 1,
            sha256(pack).hexdigest(), replacements, allow_growth=True)
        descriptor = parse_scene_assets(carrier, entry).descriptors[1]
        reopened, _ = decompress_lzs(carrier[descriptor.data_offset:], descriptor.size)
        moved = _pack_spans(reopened)
        if len(moved) != len(spans):
            raise ProjectError('World model carrier changed native pack slot count')
        for slot, (start, stop) in enumerate(moved):
            before_start, before_stop = spans[slot]
            wanted = expected.get(slot, pack[before_start:before_stop])
            if reopened[start:stop] != wanted:
                raise ProjectError('World model carrier changed a model member or unselected neighbor')
    return composed, carrier_audit

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
    identifier = request['asset_id']
    original, native = source(project, identifier)
    binding = project.model_overrides.get(identifier)
    effective = project.read_model_replacement(identifier, binding) if binding else original
    if (sha256(original).hexdigest() != request['member_sha256']
            or sha256(effective).hexdigest() != request['effective_sha256']):
        raise ProjectError('World allocation source changed; inspect Current again')
    base, base_binding, previous_ledger = retained(project, identifier, original, binding, effective)
    candidate, ledger, topology = append_vector_ledger(base, previous_ledger, request['requests'])
    proposed_binding = dict(format=binding['format'] if binding and binding['format'] in FORMATS else FORMAT, source_scene_id=owner(identifier),
        source_sha256=sha256(original).hexdigest(), asset_sha256=sha256(candidate).hexdigest(),
        byte_length=len(candidate), base_binding=base_binding, ledger=deepcopy(ledger))
    independent, allocation = append_model_vectors(effective, request['effective_sha256'], request['requests'])
    if independent != candidate:
        raise ProjectError('World vector candidate differs from complete ledger replay')
    composed, carrier_audit = qualify_carrier(project, identifier, original, native, effective, candidate, base_binding, ledger)
    report = dict(schema_version='legaia.worldmap-model-vector-allocation-review.v2',
        project_path=str(project.root), request=deepcopy(request), source_record=deepcopy(native),
        proposed_sha256=sha256(candidate).hexdigest(), proposed_model_base64=base64.b64encode(candidate).decode('ascii'),
        source_byte_length=len(original), current_byte_length=len(effective), proposed_byte_length=len(candidate),
        binding=deepcopy(proposed_binding), ledger=deepcopy(ledger), topology=topology, allocation=allocation,
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


def apply(project, request, review_key):
    candidate, _, report = prepare(project, request)
    if review_key != report['review_key']:
        raise ProjectError('World vector allocation differs from its fresh reviewed candidate')
    project._publish_model_ledger(request['asset_id'], candidate, report['binding'],
                                  request['source_key'], 'World vector allocation')

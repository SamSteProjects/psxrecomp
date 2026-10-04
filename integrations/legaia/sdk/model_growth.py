"""Gather all authored members of packs requiring topology relocation.

Produces source-bound archive requests; normal package output is not connected yet.
"""
from copy import deepcopy
from hashlib import sha256

from importer.core import parse_scene_assets, decompress_lzs, _pack_ranges
from importer.model_face_ledger import create_face_ledger
from importer.model_pack_growth import grow_scene_model_pack
from importer.pipeline import import_scene
from importer.prot_layout import locate_physical_span
from .build import authored_state_key
from .project import ProjectError, digest


def prepare_model_growth(project, archive):
    key = authored_state_key(project)
    groups, documents = {}, set()
    for identifier, binding in sorted(project.model_overrides.items()):
        scene = binding['source_scene_id']
        document = project.imports.get(scene)
        if document is None:
            raise ProjectError('Model growth requires its imported source scene')
        if scene not in documents:
            if digest(import_scene(project.disc_path, document['scene']['name'])) != digest(document):
                raise ProjectError('Model growth source metadata differs from Retail')
            documents.add(scene)
        asset = next((a for a in document['assets']['models'] if a['semantic_id'] == identifier), None)
        if asset is None:
            raise ProjectError('Model growth requires an imported model identity')
        source = asset['source_record']
        identity = (source['prot_entry_index'], source.get('container_section'))
        groups.setdefault(identity, []).append((identifier, binding, source))
    requests, reports, deferred = [], [], []
    for (entry_index, section_index), members in sorted(groups.items(), key=lambda row:str(row[0])):
        if not any(binding['format'] == 'tmd-face-addition-v1' for _, binding, _ in members):
            continue
        if type(section_index) is not int:
            raise ProjectError('Model growth carrier is not yet a qualified packed resource')
        entry = archive.entry(entry_index)
        span = locate_physical_span(archive, entry.start_lba*2048)
        if span['entry_index'] != entry_index or span['offset_within_span'] != 0:
            raise ProjectError('Model growth carrier lacks unique physical ownership')
        raw = archive.image.read_user(archive.node.extent_lba, span['byte_offset'], span['byte_length'], archive.node.size)
        table = parse_scene_assets(raw, entry_index)
        if table is None or not 0 <= section_index < len(table.descriptors):
            raise ProjectError('Model growth resource descriptor is missing')
        descriptor = table.descriptors[section_index]
        if descriptor.type_byte != 2:
            raise ProjectError('Model growth requires an explicit TMD pack resource')
        end = min([d.data_offset for d in table.descriptors if d.data_offset > descriptor.data_offset]+[len(raw)])
        pack, _ = decompress_lzs(raw[descriptor.data_offset:end], descriptor.size)
        ranges = _pack_ranges(pack)
        replacements, expected = [], {}
        for identifier, binding, source in members:
            if (source['record_kind'] not in ('decoded_lzs_section', 'decoded_tmd_pack_slot')
                    or source.get('compressed_stream_offset') != descriptor.data_offset
                    or source['containing_size'] != len(pack)):
                raise ProjectError('Model growth imported resource locator changed')
            slots = [slot for slot,(start,stop) in enumerate(ranges)
                     if start == source['byte_offset'] and 0 < source['byte_length'] <= stop-start]
            if len(slots) != 1 or 'pack_slot' in source and source['pack_slot'] != slots[0]:
                raise ProjectError('Model growth source is not an exact directory slot')
            slot = slots[0];start, _ = ranges[slot]
            original = project._model_source(identifier, binding['source_scene_id'])
            if original != pack[start:start+source['byte_length']]:
                raise ProjectError('Model growth imported model differs from its physical carrier')
            payload = project.read_model_replacement(identifier, binding)
            if binding['format'] == 'tmd-face-addition-v1':
                base_binding = deepcopy(binding['base_binding'])
                base_payload = project.read_model_replacement(identifier, base_binding) if base_binding else None
                ledger = deepcopy(binding['ledger'])
            else:
                base_binding, base_payload = deepcopy(binding), payload
                ledger = create_face_ledger(payload)
            replacements.append(dict(slot_index=slot, source_model_byte_length=len(original),
                base_binding=base_binding, base_payload=base_payload, ledger=ledger))
            expected[slot] = (identifier, payload)
            deferred.append(identifier)
        candidate, audit = grow_scene_model_pack(raw, sha256(raw).hexdigest(), section_index,
            sha256(pack).hexdigest(), replacements, allow_growth=True)
        updated = parse_scene_assets(candidate, entry_index).descriptors[section_index]
        reopened, _ = decompress_lzs(candidate[updated.data_offset:], updated.size)
        for slot,(start,_) in enumerate(_pack_ranges(reopened)):
            if slot in expected:
                identifier, payload = expected[slot]
                if reopened[start:start+len(payload)] != payload:
                    raise ProjectError('Model growth emitted bytes differ from the saved model binding')
        requests.append(dict(entry_index=entry_index, descriptor_index=section_index,
            expected_pack_sha256=sha256(pack).hexdigest(), replacements=replacements))
        reports.append(dict(entry_index=entry_index, descriptor_index=section_index,
            authored_models=sorted(identifier for identifier,_,_ in members), carrier=audit))
    if authored_state_key(project) != key:
        raise ProjectError('Project changed while preparing model growth')
    return requests, dict(schema_version='legaia.model-growth-preparation.v1', authored_state_key=key,
        deferred_model_ids=sorted(deferred), carriers=reports, build_ready=False, gameplay_verified=False)

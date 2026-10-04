"""Collect complete, source-qualified packs for saved image allocations."""
from hashlib import sha256

from importer.core import ImportError
from importer.prot_layout import locate_physical_span
from importer.texture_authoring import _validate, texture_payload_changes
from importer.texture_layout_allocation import validate_tim_allocation
from importer.texture_pack_allocation import allocate_texture_pack


def prepare(project, bindings, replacements, context, archive, *, scene_id=None):
    from .texture_slots import group
    from importer.texture_slot_allocation import append_texture_pack
    scene_id = scene_id or getattr(project, 'active_scene', None)
    slot_groups = group(project, scene_id, context, archive)
    groups = {}
    added_rows = [row for rows in slot_groups.values() for row in rows]
    if len(replacements) + len(added_rows) > 128 or sum(map(len, replacements.values())) + sum(len(row[2]) for row in added_rows) > 16 * 1024 * 1024:
        raise ImportError('Texture allocation exceeds the authoring edit budget')
    for identifier in replacements:
        source = context._item(identifier)[1]
        groups.setdefault((source['prot_entry_index'], source.get('descriptor_index', -1)), []).append(identifier)
    allocated = {key for key, ids in groups.items()
                 if any(bindings[i]['format'] == 'tim-image-layout-v1' for i in ids)}
    allocated.update(slot_groups)
    for key in slot_groups:
        groups.setdefault(key, [])
    ordinary = {i: value for i, value in replacements.items()
                if not any(i in groups[key] for key in allocated)}
    overlays, audit, requests = context.build_patch(ordinary)
    budget = sum(len(row['payload']) for row in overlays) + sum(len(row.get('pack', b'')) for row in requests)
    for key in sorted(allocated):
        ids = groups[key]
        added = slot_groups.get(key, [])
        anchor = ids[0] if ids else added[0][1]['anchor_asset_id']
        carrier = context._carrier(archive, context._item(anchor)[1])
        pack = carrier['decoded']
        raw = key[1] == -1
        if raw:
            entry = archive.entry(key[0])
            span = locate_physical_span(archive, entry.start_lba * 2048)
            if span['entry_index'] != key[0] or span['offset_within_span']:
                raise ImportError('Resized texture pack requires unique physical ownership')
            pack = archive.image.read_user(archive.node.extent_lba, span['byte_offset'], span['byte_length'], archive.node.size)
        edits, changes = [], []
        for identifier in sorted(ids):
            original = context._original(identifier, carrier)
            value = replacements[identifier]
            project.validate_effective_texture(identifier, value, context=context)
            layout = bindings[identifier]['format'] == 'tim-image-layout-v1'
            info = validate_tim_allocation(original, value) if layout else _validate(original, value)
            if original == value:
                continue
            edits.append(dict(slot_index=context._item(identifier)[1]['pack_slot'],
                              source_tim_sha256=sha256(original).hexdigest(), tim=value))
            changes.append(dict(semantic_id=identifier, source_record=context._source(identifier),
                scope='TIM-image-allocation-fixed-mode-and-VRAM-origin' if layout else 'TIM-image-and-palette-payload-only',
                before_sha256=sha256(original).hexdigest(), after_sha256=sha256(value).hexdigest(),
                byte_length=len(value), carrier_relocation_required=True,
                **({'allocation': info} if layout else {'payload_changes': texture_payload_changes(original, value)})))
        if not edits and not added:
            continue
        additions = [row[2] for row in added]
        if added:
            proposed, _ = append_texture_pack(pack, sha256(pack).hexdigest(), additions, edits=edits, standalone=raw)
            changes.extend(dict(semantic_id=identifier,scope='TIM-new-slot-upload',before_sha256=None,
                after_sha256=sha256(content).hexdigest(),byte_length=len(content),slot_index=binding['slot_index'],
                anchor_asset_id=binding['anchor_asset_id'],source_pack_sha256=binding['source_pack_sha256'],
                carrier_relocation_required=True) for identifier,binding,content in added)
        else:
            proposed, _ = allocate_texture_pack(pack, sha256(pack).hexdigest(), edits, standalone=raw)
        budget += len(proposed)
        if budget > 32 * 1024 * 1024:
            raise ImportError('Texture allocation exceeds the output pack budget')
        if raw:
            requests.append(dict(kind='texture-addition-raw' if added else 'texture-layout-raw', entry_index=key[0],
                                 expected_pack_sha256=sha256(pack).hexdigest(), edits=edits,
                                 **({'slot_additions': additions} if added else {})))
        else:
            requests.append(dict(kind='texture-addition-pack' if added else 'texture-layout-pack', entry_index=key[0], table_offset=0,
                descriptor_index=key[1], expected_pack_sha256=sha256(pack).hexdigest(),
                pack=proposed, layout_edits=edits,**({'slot_additions': additions} if added else {})))
        audit.extend(changes)
    return overlays, audit, requests

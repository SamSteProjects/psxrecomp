"""Source-only GLB material tuples, interpreted by the qualified semantic writer."""
from hashlib import sha256

from .core import ImportError
from .model_materials import (_catalog, _material_field_locations, patch_model_materials,
                              CLUT_MASK, TPAGE_MASK, MAX_MATERIAL_EDITS)


def material_bindings(data, inspection):
    bindings = {}
    for obj in _catalog(data, inspection)['objects']:
        for group in obj['groups']:
            for row in group['primitives']:
                bindings[obj['object_index'], row['primitive_index']] = (
                    row['clut'] if row['textured'] else -1,
                    row['tpage'] if row['textured'] else -1,
                    int(group['semi_transparent']))
    return bindings


def apply_material_values(data, inspection, bindings, primitive_values, group_values):
    edits = []
    for (obj, primitive), words in primitive_values.items():
        clut, tpage, _abe = bindings[obj, primitive]
        new_clut, new_tpage = words
        if clut == -1:
            continue
        if (clut ^ new_clut) & (0xffff ^ CLUT_MASK):
            raise ImportError('Model GLB source CLUT reserved bits must remain unchanged')
        if (tpage ^ new_tpage) & (0xffff ^ TPAGE_MASK):
            raise ImportError('Model GLB source TPage ABR and reserved bits must remain unchanged')
        values = {}
        for name, mask, shift in (('page_column', 15, 0), ('page_row', 16, 4)):
            if (tpage ^ new_tpage) & mask:
                values[name] = (new_tpage & mask) >> shift
        if (tpage ^ new_tpage) & 0x180:
            depth = (new_tpage >> 7) & 3
            if depth == 3:
                raise ImportError('Model GLB material target depth must be supported')
            values['texture_bpp'] = (4, 8, 16)[depth]
        for name, mask, shift in (('clut_column', 63, 0), ('clut_row', 0x7fc0, 6)):
            if (clut ^ new_clut) & mask:
                values[name] = (new_clut & mask) >> shift
        if values:
            edits.append(dict(kind='primitive', object_index=obj, primitive_index=primitive, values=values))
    for (obj, group), abe in group_values.items():
        source_rows = [row for row in inspection['objects'][obj]['primitives'] if row['group_index'] == group]
        if abe != bindings[obj, source_rows[0]['primitive_index']][2]:
            edits.append(dict(kind='group', object_index=obj, group_index=group,
                              values={'semi_transparent': bool(abe)}))
    # Each batch is independently bounded by the existing semantic authoring API.
    patched = data
    for start in range(0, len(edits), MAX_MATERIAL_EDITS):
        patched, _audit = patch_model_materials(patched, sha256(patched).hexdigest(), edits[start:start + MAX_MATERIAL_EDITS])
    # Return only qualified material spans, allowing the caller to compose normal,
    # reference, RGB and position changes without weakening the writer contract.
    return [(field['byte_offset'], patched[field['byte_offset']:field['byte_offset'] + width])
            for field, width, _mask in _material_field_locations(data, inspection)]

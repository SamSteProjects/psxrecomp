"""Read-only retail MAN bind at a qualified Current placed-object anchor."""
from hashlib import sha256
from base64 import b64encode

from importer.field_map import load_field_map_catalog
from importer.pipeline import _disc_context, _bounded_scene_range
from importer.worldmap_geometry import KINGDOM_BASES, _kingdom_table, _slot
from importer.worldmap_object_binds import resolve_object_bind
from .project import ProjectError
from .worldmap_footprint import inspect as inspect_footprint
from .worldmap_placement_allocation import _fresh


def inspect(project, scene, key, entity_id):
    footprint = inspect_footprint(project, scene, key, entity_id)
    with _disc_context(project.disc_path) as (_, disc_hash, mapping, archive):
        if disc_hash != footprint['source_record']['source_disc_sha256']:
            raise ProjectError('Object bind source differs from the qualified placement disc')
        start, end = _bounded_scene_range(archive, mapping, scene)
        base = KINGDOM_BASES[scene]
        if start != base-2 or not start <= base < base+1 < end:
            raise ProjectError('Object bind carrier is outside the qualified kingdom range')
        physical, index, offset, bundle, carrier = _kingdom_table(archive, base)
        man, slot = _slot(bundle, carrier, 2)
        entry = archive.entry(start)
        raw_map = archive.read_entry(entry, extended=True)
        if sha256(raw_map).hexdigest() != footprint['source_record']['source_map_sha256']:
            raise ProjectError('Object bind MAP differs from its qualified retail placement')
        blocks = [dict(table_source='primary', bytes_base64=b64encode(raw_map[0x10000:0x12000]).decode('ascii'))]
        if start+1 < end:
            following = archive.entry(start+1)
            if following.start_lba == entry.start_lba+36 and following.size_sectors >= 4:
                fallback = archive.image.read_user(archive.node.extent_lba, following.start_lba*archive.SECTOR, 0x2000, archive.node.size)
                blocks.append(dict(table_source='fallback', bytes_base64=b64encode(fallback).decode('ascii')))
        source = dict(disc_sha256=disc_hash, entry_index=index, table_offset=offset,
                      physical_table_offset=physical, carrier_sha256=sha256(carrier).hexdigest(),
                      slot=slot)
    catalog = load_field_map_catalog(project.disc_path, scene)
    if catalog['disc_sha256'] != disc_hash:
        raise ProjectError('Object bind MAP catalog belongs to another disc')
    anchor = footprint['anchor']
    bind = resolve_object_bind(catalog, man, anchor['col'], anchor['row'])
    result = dict(schema_version='legaia.worldmap-object-bind-inspection.v1',
        project_path=str(project.root), scene=scene, source_key=key, entity_id=entity_id,
        placement=footprint, man_source=source, bind=bind,
        source_witness=dict(man_base64=b64encode(man).decode('ascii'), trigger_blocks=blocks),
        representation='retail-bind-at-current-anchor', read_only=True,
        project_changed=False, gameplay_verified=False)
    _fresh(project, key)
    return result

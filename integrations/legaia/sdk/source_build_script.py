"""Read-only retail versus emitted script record comparison for imported owners."""
from hashlib import sha256
import re
import zipfile

from .project import ProjectError
from .project_copy import source_key
from .script_branches import state_key
from .build_history import verify_build, _load, _path
from .npc_build_script import emitted_prot
from .build_inventory import MAX_RELOCATION
from importer.pipeline import _bounded_scene_range, _disc_context
from importer.model_pack_archive import _archive
from importer.man_source import read_man_source
from importer.man_layout import read_man_layout
from importer.script_inspection import inspect_record, MAX_RECORD_BYTES, REFERENCE_COMMIT
from importer.trigger_scripts import _p2_entry


def record_at(man, partition, index):
    layout = read_man_layout(man)
    rows = [r for r in layout['records'] if r['partition'] == partition and r['record_index'] == index]
    if len(rows) != 1:
        raise ProjectError('Emitted script owner is absent or ambiguous')
    row = rows[0]; start = row['byte_offset']; length = row['byte_length']
    if start < layout['data_region_offset'] or not 0 < length <= MAX_RECORD_BYTES or sum(r['byte_offset'] == start for r in layout['records']) != 1:
        raise ProjectError('Emitted script record exceeds bounds or aliases another owner')
    if any(start < s['byte_offset'] + s['byte_length'] and s['byte_offset'] < start + length for s in layout['sections']):
        raise ProjectError('Emitted script record overlaps a MAN section')
    data = man[start:start + length]
    entry = _p2_entry(data)[0] if partition == 2 else 1 + data[0] * 2 + 4
    if entry > length:
        raise ProjectError('Emitted actor script header exceeds its record')
    return start, data, entry


def describe(offset, data, entry, owner):
    identity = 'script://' + owner.removeprefix('scene://')
    return dict(byte_offset=offset, byte_length=len(data), script_offset=entry,
                sha256=sha256(data).hexdigest(), raw_hex=data.hex(),
                inspection=dict(inspect_record(data, entry, semantic_id=identity, base_offset=offset), semantic_id=identity))


def inspect(project, owner, build_id):
    match = re.fullmatch(r'scene://([A-Za-z0-9_-]{1,128})/(actors/man-p1|scripts/man-p2|controllers/man-p1)/([0-9]{4})', owner) if isinstance(owner, str) else None
    controller = bool(match and match[2] == 'controllers/man-p1')
    if not match or 'scene://' + match[1] != project.active_scene or controller and match[3] != '0000':
        raise ProjectError('Choose an imported script owner in the active scene')
    if not project.disc_path:
        raise ProjectError('Saved script comparison requires the retail disc')
    key = state_key(project); provenance_key = source_key(project)
    if controller:
        from .resources import _verify
        from importer.controller_system_flags import load_controller_record_source
        with _disc_context(project.disc_path):
            _verify(project, project.imports[project.active_scene])
            context = load_controller_record_source(project.disc_path, match[1])
    else:
        context = project._dialogue_context(owner)
    source_offset, retail, retail_entry = context.verified_record(owner)
    verified = verify_build(project, build_id)
    if not verified['matches_current_inputs']:
        raise ProjectError('Saved Build differs from current inputs; Build the current project first')
    receipt, audit = _load(project, build_id)
    scene = project.imports[project.active_scene]['scene']['name']
    with _disc_context(project.disc_path) as (_, disc_hash, mapping, source_archive):
        if disc_hash != receipt['source_disc_sha256'] or project.imports[project.active_scene]['source']['disc_identity'] != 'sha256:' + disc_hash:
            raise ProjectError('Saved Build source disc differs from the project')
        if not 0 < source_archive.node.size <= MAX_RELOCATION:
            raise ProjectError('Source PROT exceeds the inspection budget')
        source = source_archive.image.read_user(source_archive.node.extent_lba, 0, source_archive.node.size, source_archive.node.size)
        with zipfile.ZipFile(_path(project, build_id, receipt['archive_file'])) as package:
            prot, delivery = emitted_prot(source, source_archive.node.extent_lba * 2048, package, audit)
        if not 0 < len(prot) <= MAX_RELOCATION:
            raise ProjectError('Emitted PROT exceeds the inspection budget')
        archive = _archive(prot)
        carrier = read_man_source(archive, *_bounded_scene_range(archive, mapping, scene), scene)
        if controller:
            from importer.scene_controller import controller_record
            offset, generated, entry = controller_record(carrier.payload, scene)
        else:
            offset, generated, entry = record_at(carrier.payload, 2 if match[2] == 'scripts/man-p2' else 1, int(match[3]))
        if len(generated) != len(retail) or entry != retail_entry:
            raise ProjectError('Emitted source owner changed record layout; comparison is unsupported')
        changes = [dict(pc=i, retail=a, generated=b) for i, (a, b) in enumerate(zip(retail, generated)) if a != b]
        result = dict(schema_version='legaia.source-build-script.v1', owner_id=owner, scene_id=project.active_scene,
                      state_key=key, project_source_key=provenance_key, read_only=True, gameplay_verified=False,
                      reference_commit=REFERENCE_COMMIT, representation='saved_build', runtime_binding='not_asserted',
                      build=dict(id=build_id, archive_sha256=receipt['archive_sha256'], integrity='verified', matches_current_inputs=True,
                                 source_disc_sha256=disc_hash, source_disc_integrity='verified', delivery=delivery),
                      source=describe(source_offset, retail, retail_entry, owner),
                      generated=describe(offset, generated, entry, owner), changed_bytes=changes,
                      generated_man_sha256=sha256(carrier.payload).hexdigest(),
                      limitations=['Record PCs are comparable; decoded MAN offsets may move when records are allocated.',
                                   'Changed bytes may include record header fields. Decoder stops and opaque regions remain unresolved.',
                                   'Package delivery does not prove script execution, effect targets, story state or gameplay.'])
    if state_key(project) != key or source_key(project) != provenance_key or verify_build(project, build_id)['receipt'] != receipt:
        raise ProjectError('Project or saved Build changed during script comparison')
    return result

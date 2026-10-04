"""Persistent, reviewed authored TIM slots; Retail identities remain immutable."""
from copy import deepcopy
from hashlib import sha256
from uuid import UUID, uuid4

from importer.texture_slot_allocation import append_texture_pack, validate_added_tim
from importer.textures import _pack_members, parse_tim
from importer.prot_layout import locate_physical_span
from .project import ProjectError, atomic_write, digest
from .scene_preview import source_key
from .texture_resize import _area, image_layout


def native_pack(context, archive, anchor):
    locator = context._item(anchor)[1]
    carrier = context._carrier(archive, locator)
    key = (locator['prot_entry_index'], locator.get('descriptor_index', -1))
    pack = carrier['decoded']
    if key[1] == -1:
        entry = archive.entry(key[0])
        span = locate_physical_span(archive, entry.start_lba * 2048)
        if span['entry_index'] != key[0] or span['offset_within_span']:
            raise ProjectError('Texture slot allocation requires unique physical pack ownership')
        pack = archive.image.read_user(archive.node.extent_lba, span['byte_offset'], span['byte_length'], archive.node.size)
    return key, pack


def validate_binding(project, identifier, binding):
    fields = {'format', 'source_scene_id', 'anchor_asset_id', 'source_pack_sha256',
              'source_slot_count', 'slot_index', 'asset_sha256', 'byte_length', 'label',
              'accept_potential_overlap', 'pack_entry_index', 'pack_descriptor_index'}
    if not isinstance(binding, dict) or set(binding) != fields or binding['format'] != 'tim-slot-v1':
        raise ProjectError('Invalid authored TIM slot binding')
    try:
        if not isinstance(identifier, str) or not identifier.startswith('texture-new://'):
            raise ValueError()
        if str(UUID(identifier[14:])) != identifier[14:]:
            raise ValueError()
    except (ValueError, AttributeError):
        raise ProjectError('Authored texture requires a canonical persistent UUID') from None
    scene = project.imports.get(binding['source_scene_id']) if isinstance(binding['source_scene_id'], str) else None
    anchor = binding['anchor_asset_id']
    if (scene is None or not isinstance(anchor, str) or len(anchor) > 512 or
            not anchor.startswith('texture://' + scene['scene']['name'] + '/') or
            any(not isinstance(binding[k], str) or len(binding[k]) != 64 or
                any(c not in '0123456789abcdef' for c in binding[k]) for k in ('asset_sha256', 'source_pack_sha256')) or
            type(binding['byte_length']) is not int or not 1 <= binding['byte_length'] <= 1024 * 1024 or
            type(binding['source_slot_count']) is not int or not 1 <= binding['source_slot_count'] <= 1023 or
            type(binding['slot_index']) is not int or not binding['source_slot_count'] <= binding['slot_index'] < 1024 or
            type(binding['pack_entry_index']) is not int or binding['pack_entry_index'] < 0 or
            type(binding['pack_descriptor_index']) is not int or binding['pack_descriptor_index'] < -1 or
            type(binding['accept_potential_overlap']) is not bool or
            not isinstance(binding['label'], str) or not 1 <= len(binding['label']) <= 128 or
            not binding['label'].strip() or any(ord(c) < 32 for c in binding['label'])):
        raise ProjectError('Authored texture slot identity, allocation or receipt is malformed')


def read(project, identifier, binding):
    validate_binding(project, identifier, binding)
    path = project.root / 'Authored' / 'Textures' / (binding['asset_sha256'] + '.tim')
    if not path.resolve().is_relative_to(project.root) or not path.is_file() or path.stat().st_size != binding['byte_length']:
        raise ProjectError('Authored texture slot content is missing or has changed size')
    content = path.read_bytes()
    if sha256(content).hexdigest() != binding['asset_sha256']:
        raise ProjectError('Authored texture slot content hash changed')
    validate_added_tim(content)
    return content


def validate_collection(project):
    slots = project.texture_additions
    if not isinstance(slots, dict) or len(slots) > 128:
        raise ProjectError('Authored texture slots require a bounded mapping')
    total = 0
    groups = {}
    for identifier, binding in slots.items():
        total += len(read(project, identifier, binding))
        key = (binding['source_scene_id'], binding['pack_entry_index'], binding['pack_descriptor_index'])
        groups.setdefault(key, []).append(binding)
    for bindings in groups.values():
        source = {(b['source_pack_sha256'], b['source_slot_count']) for b in bindings}
        count = bindings[0]['source_slot_count']
        if len(source) != 1 or sorted(b['slot_index'] for b in bindings) != list(range(count, count + len(bindings))):
            raise ProjectError('Saved texture slots contain conflicting packs, gaps or duplicate indices')
    if total > 16 * 1024 * 1024:
        raise ProjectError('Authored texture slot input exceeds 16 MiB')


def group(project, scene_id, context, archive):
    """Freshly qualify source packs, slot continuity and immutable file receipts."""
    groups = {}
    for identifier, binding in sorted(getattr(project, 'texture_additions', {}).items()):
        validate_binding(project, identifier, binding)
        if binding['source_scene_id'] != scene_id:
            continue
        key, pack = native_pack(context, archive, binding['anchor_asset_id'])
        count = len(_pack_members(pack, key[1] == -1))
        if (key != (binding['pack_entry_index'], binding['pack_descriptor_index']) or
                sha256(pack).hexdigest() != binding['source_pack_sha256'] or count != binding['source_slot_count']):
            raise ProjectError('Authored texture slot Retail pack changed')
        groups.setdefault(key, []).append((identifier, binding, read(project, identifier, binding)))
    for rows in groups.values():
        rows.sort(key=lambda row: row[1]['slot_index'])
        count = rows[0][1]['source_slot_count']
        if [b['slot_index'] for _, b, _ in rows] != list(range(count, count + len(rows))):
            raise ProjectError('Authored texture slots must append without gaps or duplicate indices')
    return groups


def current_items(project, scene_id=None):
    """Requalify authored uploads against their native Retail pack before display."""
    validate_collection(project)
    scene_id=scene_id or project.active_scene
    selected=[(i,b) for i,b in project.texture_additions.items() if b['source_scene_id']==scene_id]
    if not selected:return []
    from importer.texture_authoring import load_texture_authoring_context
    from importer.pipeline import _disc_context,import_scene
    document=project.imports.get(scene_id)
    if document is None or not project.disc_path:raise ProjectError('New texture inspection requires its imported scene')
    with _disc_context(project.disc_path):
        if import_scene(project.disc_path,document['scene']['name'])!=document:
            raise ProjectError('New texture source differs from fresh imported evidence')
        context=load_texture_authoring_context(project.disc_path,document['scene']['name'])
        with context._archive() as archive:
            groups=group(project,scene_id,context,archive)
    return [row for key in sorted(groups) for row in groups[key]]


def metadata(identifier,binding,content):
    tim=validate_added_tim(content)
    palettes=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp in (4,8) and tim.clut else 0
    return dict(semantic_id=identifier,asset_kind='texture',name=binding['label'],
        source_record=dict(semantic_id=identifier,authored=True,anchor_asset_id=binding['anchor_asset_id'],
                           prot_entry_index=binding['pack_entry_index'],descriptor_index=binding['pack_descriptor_index'],
                           pack_slot=binding['slot_index'],source_pack_sha256=binding['source_pack_sha256'],
                           asset_sha256=binding['asset_sha256']),
        width=tim.width,height=tim.image.height,dimensions=dict(width=tim.width,height=tim.image.height),
        bpp=tim.bpp,palette_count=palettes,
        preview_supported=tim.bpp>=16 or palettes>0,image=tim.image.metadata(),clut=tim.clut.metadata() if tim.clut else None,
        authored_slot=True,limitations=['Current authored upload; no Retail texture counterpart.',
        'Static upload addresses do not establish runtime residency or upload order.'])


def _footprint(project, context, candidate, *, exclude_asset_id=None):
    new = validate_added_tim(candidate)
    proposed = [('image', (new.image.x, new.image.y, new.image.width_words, new.image.height))]
    if new.clut:
        proposed.append(('flattened-clut', (new.clut.x, new.clut.y, new.clut.width_words * new.clut.height, 1)))
    uploads = []
    for tim, locator in context._catalog.textures:
        owner = locator['semantic_id']
        if owner in project.texture_overrides:
            content = project.read_texture_replacement(project.texture_overrides[owner])
            project.validate_effective_texture(owner, content, context=context)
            tim = parse_tim(content)
        uploads.append((owner, tim))
    uploads.extend((identifier, parse_tim(read(project, identifier, binding)))
                   for identifier, binding in project.texture_additions.items()
                   if binding['source_scene_id'] == project.active_scene and identifier!=exclude_asset_id)
    rectangles = []
    for owner, tim in uploads:
        rectangles.append((owner, 'image', (tim.image.x, tim.image.y, tim.image.width_words, tim.image.height)))
        if tim.clut:
            rectangles.append((owner, 'flattened-clut', (tim.clut.x, tim.clut.y, tim.clut.width_words * tim.clut.height, 1)))
    rectangles.extend((None, 'boot-upload', (b.x, b.y, b.width_words, b.height)) for b, _ in context._catalog.boot_uploads)
    if new.clut:
        rectangles.append((None, 'proposed-clut', proposed[1][1]))
    rows = []
    count = 0
    for proposed_kind, rect in proposed:
        for owner, kind, other in rectangles:
            if proposed_kind == 'flattened-clut' and kind == 'proposed-clut':
                continue
            overlap = _area(rect, other)
            if overlap:
                count += 1
                if len(rows) < 64:
                    rows.append(dict(asset_id=owner, kind=kind, proposed_kind=proposed_kind, overlap_words=overlap,
                                     rectangle=dict(x=other[0], y=other[1], width_words=other[2], height=other[3])))
    return dict(potential_overlap_count=count, rows=rows, rows_truncated=count > len(rows),
                coverage='known-static-scene-authored-and-boot-uploads', runtime_residency_verified=False)


def review(project, anchor, content, expected_source_key, label, accept_potential_overlap=False):
    if project.mode != 'edit' or type(accept_potential_overlap) is not bool:
        raise ProjectError('Texture slot review requires Edit mode and an explicit overlap choice')
    key = source_key(project)
    if not key or key != expected_source_key:
        raise ProjectError('Texture slot source context changed; review again')
    if not isinstance(label, str) or not label.strip() or len(label) > 128 or any(ord(c) < 32 for c in label):
        raise ProjectError('Texture label must contain one to 128 printable characters')
    validate_added_tim(content)
    validate_collection(project)
    if len(project.texture_additions) >= 128 or sum(b['byte_length'] for b in project.texture_additions.values()) + len(content) > 16 * 1024 * 1024:
        raise ProjectError('Authored texture slot input budget exhausted')
    context = project._texture_context(anchor)
    with context._archive() as archive:
        pack_key, pack = native_pack(context, archive, anchor)
        existing = group(project, project.active_scene, context, archive).get(pack_key, [])
        edits = []
        for identifier, binding in project.texture_overrides.items():
            if binding['source_scene_id'] != project.active_scene:
                continue
            locator = context._item(identifier)[1]
            if (locator['prot_entry_index'], locator.get('descriptor_index', -1)) != pack_key:
                continue
            effective = project.read_texture_replacement(binding)
            project.validate_effective_texture(identifier, effective, context=context)
            original = context.original_tim(identifier)
            if original != effective:
                edits.append(dict(slot_index=locator['pack_slot'], source_tim_sha256=sha256(original).hexdigest(), tim=effective))
    count = len(_pack_members(pack, pack_key[1] == -1))
    # Construct the complete pack during review, before any project mutation.
    proposed, allocation = append_texture_pack(pack, sha256(pack).hexdigest(), [r[2] for r in existing] + [content], edits=edits, standalone=pack_key[1] == -1)
    if pack_key[1] != -1 and len(proposed) > 4 * 1024 * 1024:
        raise ProjectError('Added texture pack exceeds the native descriptor decoder budget')
    footprint = _footprint(project, context, content)
    report = dict(schema_version='legaia.texture-slot-review.v1', project_source_key=key,
                  source_scene_id=project.active_scene, anchor_asset_id=anchor,
                  source_pack_sha256=sha256(pack).hexdigest(), source_slot_count=count,
                  pack_entry_index=pack_key[0], pack_descriptor_index=pack_key[1],
                  slot_index=count + len(existing), proposed_sha256=sha256(content).hexdigest(),
                  byte_length=len(content), label=label, image_layout=image_layout(content),
                  allocation=allocation, footprint=footprint, accept_potential_overlap=accept_potential_overlap,
                  can_apply=not footprint['potential_overlap_count'] or accept_potential_overlap,
                  project_changed=False, gameplay_verified=False)
    tim=validate_added_tim(content)
    report['palette_count']=len(tim.clut.data)//((1<<tim.bpp)*2) if tim.bpp in (4,8) and tim.clut else 0
    report['review_key'] = digest(report)
    if source_key(project) != key:
        raise ProjectError('Texture slot source changed during review')
    return report


def pixels(project, anchor, content, expected_source_key, label, accept_potential_overlap, review_key, palette_index):
    import base64
    from importer.texture_png import export_texture_png
    report=review(project,anchor,content,expected_source_key,label,accept_potential_overlap)
    if report['review_key']!=review_key:
        raise ProjectError('Texture slot pixel inspection requires the current review')
    if type(palette_index) is not int or not 0<=palette_index<max(1,report['palette_count']):
        raise ProjectError('Texture slot pixel inspection requires an existing palette')
    png,_,_=export_texture_png(content,palette_index)
    if len(png)>8*1024*1024:
        raise ProjectError('New texture pixel PNG exceeds the inspection budget')
    if source_key(project)!=expected_source_key:
        raise ProjectError('Texture slot source changed during pixel inspection')
    return dict(report=report,palette_index=palette_index,proposed_png_base64=base64.b64encode(png).decode('ascii'))


def apply(project, anchor, content, expected_source_key, label, accept_potential_overlap, review_key):
    report = review(project, anchor, content, expected_source_key, label, accept_potential_overlap)
    if report['review_key'] != review_key or not report['can_apply']:
        raise ProjectError('Texture slot Apply requires the current applicable review')
    identifier = 'texture-new://' + str(uuid4())
    binding = {k: report[k] for k in ('source_scene_id', 'anchor_asset_id', 'source_pack_sha256',
               'source_slot_count', 'slot_index', 'byte_length', 'label', 'accept_potential_overlap',
               'pack_entry_index', 'pack_descriptor_index')}
    binding.update(format='tim-slot-v1', asset_sha256=report['proposed_sha256'])
    validate_binding(project, identifier, binding)
    path = project.root / 'Authored' / 'Textures' / (binding['asset_sha256'] + '.tim')
    if not path.resolve().is_relative_to(project.root):
        raise ProjectError('Authored texture slot path escapes the project')
    if path.exists():
        read(project, identifier, binding)
    else:
        atomic_write(path, content)
    project.texture_additions[identifier] = binding
    project.undo_stack.append(dict(target='texture_additions', asset_id=identifier, before=None, after=deepcopy(binding)))
    project.redo_stack.clear()
    return dict(report, asset_id=identifier, project_changed=True)

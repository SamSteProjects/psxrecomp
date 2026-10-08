"""Qualified NPC script-body preview before allocation, never emitted/live code."""
from copy import copy, deepcopy
from hashlib import sha256
from importer.script_inspection import inspect_record
from .project import ProjectError, digest
from .project_copy import source_key
from .npc_donor_script import inspect as inspect_donor
from .npc_branches import branch_context, effective_man


def proposed_inspection(project, entity_id, proposed):
    """Use the same serializers on a detached draft map; no command or history."""
    detached=copy(project)
    detached.actor_drafts=deepcopy(project.actor_drafts)
    detached.actor_drafts[entity_id]=deepcopy(proposed)
    return inspect(detached,entity_id)['inspection']


def inspect(project, entity_id):
    donor = inspect_donor(project, entity_id)
    key = donor['project_source_key']; draft = donor['draft']; owner = draft['donor_entity_id']
    context = branch_context(project, draft)
    source = context._source
    offset, original, entry = source.verified_record(owner)
    retail = donor['inspection']
    record = retail['record']
    if (offset != record['byte_offset'] or len(original) != record['byte_length']
            or entry != record['script_offset'] or original.hex() != record['raw_hex']
            or sha256(original).hexdigest() != record['sha256']):
        raise ProjectError('Current NPC script differs from its freshly inspected Retail donor')
    candidate = effective_man(project, draft, context)
    if 'effect_colors' in draft:
        adapter = project._effect_color_context(owner)
        if adapter._man != context._man:
            raise ProjectError('NPC effect preview source snapshots differ')
        changed, _ = adapter.patch(draft['effect_colors']['entries'])
        working = bytearray(candidate)
        for at, (before, after) in enumerate(zip(context._man, changed)):
            if before != after:
                if candidate[at] != before:
                    raise ProjectError('NPC effect preview overlaps another authored operand')
                working[at] = after
        candidate = bytes(working)
    if 'branches' in draft:
        candidate, _ = context.patch_composed(candidate, draft['branches']['entries'])
        decoded = context.inspect_owner(owner, candidate)
        for family in ('instructions','dialogues','unvisited_instructions','unvisited_dialogues'):
            for row in decoded.get(family, []):
                row['byte_offset'] = offset + row['pc']
                if 'dialogues' in family:
                    row['semantic_id'] = retail['semantic_id'] + f"/dialogue/{row['pc']:04x}"
        for row in decoded.get('opaque_regions', []):row['byte_offset'] = offset + row['pc']
    else:
        decoded = inspect_record(candidate[offset:offset+len(original)], entry,
                                 semantic_id=retail['semantic_id'], base_offset=offset)
    current = candidate[offset:offset+len(original)]
    # The preview retains the donor header; appearance/placement and allocation
    # are qualified by Build, not silently represented as generated source.
    if current[:entry] != original[:entry]:
        raise ProjectError('Current NPC script preview changed its donor header')
    result = deepcopy(retail)
    result.update(decoded)
    result['record'].update(raw_hex=current.hex(), sha256=sha256(current).hexdigest())
    if source_key(project) != key:
        raise ProjectError('Project changed during Current NPC script preview')
    return dict(schema_version='legaia.npc-current-script.v1', project_source_key=key,
        entity_id=entity_id, scene_id=donor['scene_id'], draft=deepcopy(draft),
        donor=donor, inspection=result, representation='npc_authored_script_source',
        state_key=digest(dict(entity_id=entity_id, draft=draft, source_record_sha256=record['sha256'],
                             current_record_sha256=result['record']['sha256'])),
        changed_byte_count=sum(a != b for a,b in zip(original,current)),
        generated_code=False, runtime_binding='not_asserted', gameplay_verified=False,
        limitations=['Script-body preview at Retail donor offsets; no generated allocation.',
                    'Initial appearance, placement, spawning and scheduling are not previewed.',
                    'Hypothetical simulation is not native execution or observed game state.'])

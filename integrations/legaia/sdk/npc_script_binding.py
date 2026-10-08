"""Editor-facing NPC script ownership metadata, independent of retail decoding."""
from .project import digest

FAMILIES = ('dialogue', 'waits', 'movement', 'facing', 'flags', 'system_flags', 'branches', 'model_selectors', 'effect_colors')


def snapshots(project):
    result = {}
    for identifier, draft in sorted(project.actor_drafts.items()):
        project._validate_actor_draft(identifier, draft)
        result[identifier] = dict(schema_version='legaia.npc-script-binding.v1',
            entity_id=identifier, scene_id=draft['scene_id'], donor_entity_id=draft['donor_entity_id'],
            source_script_id='script://' + draft['donor_entity_id'].removeprefix('scene://'),
            authored_draft_sha256=digest(draft),
            authored_counts={family:len(draft.get(family, {}).get('runs' if family=='dialogue' else 'entries', {})) for family in FAMILIES},
            source_qualification='inspect_retail_donor_script', generated_qualification='inspect_saved_build_script',
            runtime_binding='not_asserted')
    return result

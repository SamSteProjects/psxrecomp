"""Read-only serialization review for saved NPC candidates, without a disc writer."""
from copy import deepcopy
from hashlib import sha256
import json
import re

from .build import authored_state_key
from .project import ProjectError
from .npc_build import NORMAL_BUILD_SCOPE_NOTE

_HASH = re.compile(r'[0-9a-f]{64}\Z')
MAX_REPORT_BYTES = 4 * 1024 * 1024


def review(project, expected_key):
    from .draft_build import prepare_draft_archive
    if project.mode != 'edit':
        raise ProjectError('NPC output review requires Edit mode')
    if not isinstance(expected_key, str) or not _HASH.fullmatch(expected_key):
        raise ProjectError('NPC output review requires the current project input key')
    key = authored_state_key(project)
    if expected_key != key:
        raise ProjectError('NPC output inputs changed; review the current project again')
    if not project.actor_drafts:
        raise ProjectError('Create or open a saved NPC draft before reviewing its output')
    archive, audit = prepare_draft_archive(project)
    if (project.mode != 'edit' or authored_state_key(project) != key or
            audit.get('authored_state_key') != key):
        raise ProjectError('NPC output inputs changed during serialization review')
    if sha256(archive).hexdigest() != audit.get('result_prot_sha256'):
        raise ProjectError('NPC output review candidate differs from the verified archive')
    summaries = []
    scene_audits = audit.get('scenes') or {audit['scene_id']: audit}
    for scene_id, scene in sorted(scene_audits.items()):
        summaries.append(dict(scene_id=scene_id, draft_count=sum(
            item['scene_id'] == scene_id for item in project.actor_drafts.values()),
            final_man_sha256=scene['final_man_sha256'],
            actor_pool_evidence=deepcopy(scene.get('actor_pool_evidence')),
            facing_changes=deepcopy(scene.get('facing_changes', [])),
            other_change_counts={name: len(scene.get(name) or []) for name in (
                'existing_actor_placement_changes', 'existing_actor_appearance_changes',
                'existing_actor_dialogue_changes', 'movement_changes', 'flag_changes',
                'wait_changes', 'model_selector_changes', 'branch_changes', 'transition_changes')}))
    result = dict(schema_version='legaia.draft-output-review.v1', project_source_key=key,
        source_disc_sha256=audit['source_disc_sha256'],
        source_prot_sha256=audit['source_prot_sha256'],
        result_prot_sha256=audit['result_prot_sha256'], archive_bytes=len(archive),
        draft_count=len(project.actor_drafts), scenes=summaries,
        allocation=deepcopy(audit['container']), experimental=True,
        normal_build_ready=False, normal_build_assessment='not_assessed_here', output_written=False, gameplay_verified=False,
        limitations=[
            'This is an experimental serialized NPC candidate, not gameplay or spawn acceptance.',
            'Existing source facing edits affect their original owner; appended donor copies retain retail facing.',
            'Facing operands are source script sectors, not initial or live Transform heading.',
            NORMAL_BUILD_SCOPE_NOTE,
            'This experimental archive review does not assess normal Build readiness. The legacy normal_build_ready=false field grants no readiness claim; use Review Build for that assessment.',
            'Appended NPCs qualify the retail actor-pool lower bound before repacking. Scenery and intervening scripts leave total demand unverified.',
            'Review writes no project, package or disc output and does not launch the game.',
        ])
    try:
        encoded = json.dumps(result, allow_nan=False, ensure_ascii=False).encode('utf-8')
    except (TypeError, ValueError, OverflowError) as error:
        raise ProjectError('NPC output review requires finite metadata') from error
    if len(encoded) > MAX_REPORT_BYTES:
        raise ProjectError('NPC output review exceeds its 4 MiB metadata budget')
    return result

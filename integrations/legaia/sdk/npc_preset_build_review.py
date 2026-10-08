"""Assess the complete supported project with one reviewed preset instance."""
from .project import ProjectError
from .project_copy import source_key
from .npc_presets import review as preset_review, proposal_view
from .build import authored_state_key
from .build_review import review as build_review


def review(project, request):
    fields = {'template_id', 'name', 'position', 'expected_source_key'}
    if not isinstance(request, dict) or set(request) != fields | {'review_key'}:
        raise ProjectError('NPC preset Build review requires exact reviewed fields')
    preset = preset_review(project, {key: request[key] for key in fields})
    if request['review_key'] != preset['review_key']:
        raise ProjectError('NPC preset changed since review')
    view = proposal_view(project, preset)
    key = authored_state_key(view)
    assessment = build_review(view)
    count = len(project.actor_drafts) + 1
    if assessment['source_key'] != key or assessment['included_npc_draft_count'] != count or assessment['read_only'] is not True:
        raise ProjectError('NPC preset Build assessment differs from its isolated inputs')
    if source_key(project) != preset['project_source_key']:
        raise ProjectError('Project changed during NPC preset Build review')
    return dict(schema_version='legaia.npc-preset-build-review.v1', review=preset,
                prospective_build_source_key=key, build_review=assessment,
                existing_npc_draft_count=len(project.actor_drafts), proposed_npc_draft_count=count,
                read_only=True, project_changed=False, output_written=False, gameplay_verified=False,
                assessment_scope='complete_supported_project_with_one_preset_instance')

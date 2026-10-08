"""Read-only normal-Build assessment with one prospective, unsaved NPC."""
from .project import ProjectError
from .project_copy import source_key
from .npc_creation_preview import review as creation_review, proposal_view
from .build import authored_state_key
from .build_review import review as build_review


def review(project, request):
    creation=creation_review(project,request)
    view=proposal_view(project,creation)
    key=authored_state_key(view)
    assessment=build_review(view)
    expected_count=len(project.actor_drafts)+1
    if assessment['source_key']!=key or assessment['included_npc_draft_count']!=expected_count or assessment['read_only'] is not True:
        raise ProjectError('Prospective NPC Build review differs from its isolated authored inputs')
    if source_key(project)!=creation['project_source_key']:
        raise ProjectError('Project changed during prospective NPC Build review')
    return dict(schema_version='legaia.npc-creation-build-review.v1',review=creation,
                prospective_build_source_key=key,build_review=assessment,
                existing_npc_draft_count=len(project.actor_drafts),proposed_npc_draft_count=expected_count,
                read_only=True,project_changed=False,output_written=False,gameplay_verified=False,
                assessment_scope='complete_supported_project_with_one_prospective_npc')

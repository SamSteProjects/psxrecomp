"""Read-only normal-Build serialization assessment of current authored inputs."""
from copy import deepcopy
from importer.core import ImportError as RetailImportError
from .project import ProjectError,canonical
from .build import BuildError,_build_project,authored_state_key

def review(project):
    if not project.disc_path or not 1<=len(project.imports)<=64:raise ProjectError('Build review requires a user-owned disc and1–64 imported scenes')
    key=authored_state_key(project);snapshot=deepcopy(project)
    blockers=[dict(kind='npc_draft',owner_id=identifier,message='NPC draft is not supported by normal playable Build; retained in project.') for identifier in sorted(snapshot.actor_drafts)]
    snapshot.actor_drafts={}
    assessment=None
    try:
        assessment=_build_project(snapshot,None,review_only=True)
        if len(canonical(assessment))>8*1024*1024:raise BuildError('Build review metadata exceeds8 MiB; full review could not be returned')
    except (BuildError,ProjectError,RetailImportError,OSError) as error:
        assessment=None;blockers.append(dict(kind='serialization',owner_id=None,message=str(error)[:8192]))
    if key!=authored_state_key(project):raise ProjectError('Authored inputs changed during Build review; reopen the review')
    return dict(schema_version='legaia.build-review.v1',source_key=key,read_only=True,
                status='blocked' if blockers else 'ready_for_build',normal_build_ready=not blockers,
                blockers=blockers,excluded_npc_draft_count=len(project.actor_drafts),assessment=assessment,
                assessment_scope='existing_imported_content_and_supported_overrides_excluding_npc_drafts',
                limitations=['This review serializes supported existing content without writing package files. NPC drafts are explicitly excluded from the assessment and remain normal-Build blockers.',
                             'An assessment failure stops serialization; later changes are not claimed to have passed.',
                             'Archive packing, filesystem write capacity/permissions, installation and interactive gameplay are not tested here.',
                             'Passing serialization does not prove script behavior, runtime actor identity, collision or animation suitability. Gameplay verification remains deferred.'])

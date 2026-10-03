"""Read-only normal-Build serialization assessment of current authored inputs."""
from copy import deepcopy
from importer.core import ImportError as RetailImportError
from .project import ProjectError,canonical
from .build import BuildError,_build_project,authored_state_key

def review(project):
    if not project.disc_path or not 1<=len(project.imports)<=64:raise ProjectError('Build review requires a user-owned disc and1–64 imported scenes')
    key=authored_state_key(project);snapshot=deepcopy(project)
    blockers=[]
    assessment=None
    try:
        assessment=_build_project(snapshot,None,review_only=True)
        if len(canonical(assessment))>8*1024*1024:raise BuildError('Build review metadata exceeds8 MiB; full review could not be returned')
    except (BuildError,ProjectError,RetailImportError,OSError) as error:
        assessment=None;blockers.append(dict(kind='serialization',owner_id=None,message=str(error)[:8192]))
    if key!=authored_state_key(project):raise ProjectError('Authored inputs changed during Build review; reopen the review')
    return dict(schema_version='legaia.build-review.v2',source_key=key,read_only=True,
                status='blocked' if blockers else 'ready_for_build',normal_build_ready=not blockers,
                blockers=blockers,excluded_npc_draft_count=0,included_npc_draft_count=len(project.actor_drafts),assessment=assessment,
                assessment_scope='all_supported_authored_content_including_source_qualified_npc_drafts',
                npc_build_scope='fixed_span_compressed_man_source_candidates',npc_gameplay_verified=False,
                limitations=['This review serializes all supported authored inputs without writing package files. NPC candidates require compressed MAN data that fits the original consumed source span; streaming or oversized candidates are rejected.',
                             'An assessment failure stops serialization; later changes are not claimed to have passed.',
                             'Archive packing, filesystem write capacity/permissions, installation and interactive gameplay are not tested here.',
                             'NPC candidates qualify the retail 143-slot actor pool and reject unavoidable initial-placement overflow. Scenery and two later setup allocations share the pool; intervening scripts and other channels remain unverified, so remaining slots are not a safe NPC budget.',
                             'Passing serialization proves package fit only. Native NPC allocation, spawning, scheduling and opaque script references remain unverified.',
                             'Script behavior, runtime actor identity, collision and animation suitability require deferred gameplay verification.'])

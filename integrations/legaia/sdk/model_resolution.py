"""Fresh native initial-model diagnostics; unresolved indices have no guessed asset."""
from copy import deepcopy
from .project import ProjectError,digest,canonical
from .asset_references import source_key
from .resources import _verify
from importer.pipeline import _disc_context

def inspect(project,scene_id,expected_source_key):
    key=source_key(project)
    if key!=expected_source_key or scene_id!=project.active_scene or scene_id not in project.imports:
        raise ProjectError('Model resolution sources changed; reopen inspection')
    document=project.imports[scene_id]
    with _disc_context(project.disc_path):_verify(project,document)
    models=document['assets']['models'];actors={a['semantic_id']:a for a in document['actors']}
    counts={pool:sum(m['model_pool']==pool for m in models) for pool in ('scene_tmd','global_special')}
    def layer(actor):
        reference=actor['model_reference'];index=reference['model_index'];pool='global_special' if index>=240 else 'scene_tmd';slot=index-240 if index>=240 else index
        matches=[m for m in models if m['model_pool']==pool and m['normalized_pool_index']==slot]
        if len(matches)>1:raise ProjectError('Model resolution has ambiguous native slot ownership')
        asset=matches[0]['semantic_id'] if matches else None
        if (reference['model_pool']!=pool or reference['normalized_pool_index']!=slot or reference['asset_semantic_id']!=asset or reference['resolution_status']!=('resolved' if asset else 'pool_index_out_of_bounds')):
            raise ProjectError('Model resolution differs from imported slot evidence')
        return dict(source_actor_id=actor['semantic_id'],model_index=index,model_pool=pool,slot_index=slot,asset_id=asset,status='resolved' if asset else 'unresolved',source_record=deepcopy(actor['source_record']))
    rows=[];retail_unresolved=current_unresolved=0;source_count=draft_count=0
    def collect(identity,kind,retail,effective):
        nonlocal retail_unresolved,current_unresolved
        missing_retail=retail is not None and retail['status']=='unresolved';missing_current=effective['status']=='unresolved'
        retail_unresolved+=bool(missing_retail);current_unresolved+=bool(missing_current)
        if missing_retail or missing_current:rows.append(dict(entity_id=identity,kind=kind,retail=retail,current=effective))
    for identity,actor in sorted(actors.items()):
        source_count+=1;collect(identity,'actor',layer(actor),layer(project.appearance_source_actor(identity)))
    for identity,draft in sorted(project.actor_drafts.items()):
        if draft['scene_id']!=scene_id:continue
        project._validate_actor_draft(identity,draft);draft_count+=1
        donor=actors[draft.get('appearance',{}).get('donor_entity_id',draft['donor_entity_id'])]
        collect(identity,'npc',None,layer(donor))
    if source_count+draft_count>8192 or source_key(project)!=key:
        raise ProjectError('Model resolution exceeds source bounds or changed during inspection')
    result=dict(schema_version='legaia.model-resolution.v1',scene_id=scene_id,source_key=key,source_import_sha256=digest(document),disc_identity=document['source']['disc_identity'],read_only=True,runtime_binding='not_asserted',rows=rows,counts=dict(source_actors=source_count,npc_drafts=draft_count,retail_unresolved=retail_unresolved,current_unresolved=current_unresolved,**counts),coverage='initial_model_references_only',gameplay_verified=False)
    if len(canonical(result))>4*1024*1024:raise ProjectError('Model resolution exceeds metadata response bound')
    return result

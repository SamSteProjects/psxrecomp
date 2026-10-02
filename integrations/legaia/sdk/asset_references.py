"""Recorded asset relationships, never runtime residency or gameplay reachability."""
from copy import deepcopy
from .project import ProjectError,digest

def source_key(project):
    return digest(dict(project_root=str(project.root),active_scene=project.active_scene,
                       imports={key:digest(doc) for key,doc in sorted(project.imports.items())},
                       overrides=project.overrides,drafts=project.actor_drafts))

def assemble(project,catalog,identifier):
    """Adapt explicit imported/derived references; callers verify retail sources first."""
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    nodes={};edges={};unresolved=0
    def node(identifier,kind,scene,label=None,available=True):
        if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
        value=dict(id=identifier,kind=kind,scene_id=scene,label=label or identifier,available=available)
        if identifier in nodes:
            if nodes[identifier]['kind']!=kind:raise ProjectError('Conflicting asset reference type')
            if available:nodes[identifier]['available']=True
        else:nodes[identifier]=value
        if len(nodes)>16384:raise ProjectError('Asset reference node limit exceeded')
    def edge(source,target,kind,scene,layer='imported',pc=None):
        if source not in nodes or target not in nodes:raise ProjectError('Asset reference has an unavailable structural endpoint')
        value=dict(source_id=source,target_id=target,kind=kind,scene_id=scene,layer=layer,runtime_binding='not_asserted')
        if pc is not None:value['pc']=pc
        value['source_import_sha256']=digest(project.imports[scene])
        if layer=='decoded':value['source_catalog_key']=catalog['source_key']
        value['id']=digest(value);edges[value['id']]=value
        if len(edges)>32768:raise ProjectError('Asset reference edge limit exceeded')
    for scene,document in sorted(project.imports.items()):
        node(scene,'scene',scene,document['scene']['name'])
        for actor in document['actors']:
            node(actor['semantic_id'],'actor',scene,'Actor '+actor['semantic_id'].rsplit('/',1)[-1]);edge(scene,actor['semantic_id'],'scene_actor',scene)
        for model in document['assets'].get('models',[]):
            node(model['semantic_id'],'model',scene,model.get('name') or 'Model '+model['semantic_id'].rsplit('/',1)[-1]);edge(scene,model['semantic_id'],'scene_model_catalog',scene)
    for identifier_draft,draft in sorted(project.actor_drafts.items()):
        node(identifier_draft,'actor',draft['scene_id'],draft['name']);edge(identifier_draft,draft['donor_entity_id'],'draft_donor',draft['scene_id'],'authored')
    for ref in project.model_references():
        if ref['target_id'] not in nodes:unresolved+=1;continue
        if ref['imported']:edge(ref['source_id'],ref['target_id'],'initial_model',ref['scene_id'])
        if ref['effective']:edge(ref['source_id'],ref['target_id'],'effective_initial_model',ref['scene_id'],'effective')
    scene=project.active_scene
    for record in catalog['records']:node(record['id'],record['kind'],scene,record.get('name'))
    for record in catalog['records']:
        identity=record['id'];kind=record['kind']
        if kind=='script':
            actor=record.get('actor_semantic_id')
            if actor in nodes:edge(actor,identity,'actor_script_record',scene,'decoded')
            elif actor is not None:unresolved+=1
            for transition in record.get('transitions',[]):
                name=transition.get('target_scene_name')
                if name:
                    target='scene://'+name;node(target,'scene',target,name,target in project.imports);edge(identity,target,'encoded_scene_change',scene,'decoded',transition['pc'])
                else:unresolved+=1
            # Model pool selectors explicitly have unresolved runtime pool bases.
            unresolved+=len(record.get('model_selection_references',[]))
        elif kind=='dialogue':
            target=record.get('script_id')
            if target in nodes:edge(target,identity,'script_dialogue_segment',scene,'decoded',record.get('pc'))
            else:unresolved+=1
        elif kind=='animation':
            for binding in record.get('bindings',[]):
                actor=binding.get('actor_semantic_id');model=binding.get('model_asset_semantic_id')
                if actor in nodes:edge(actor,identity,'initial_animation_binding',scene,'decoded')
                else:unresolved+=1
                if model in nodes:edge(identity,model,'recorded_model_clip_binding',scene,'decoded')
                else:unresolved+=1
        elif kind in ('trigger','region'):
            target=record.get('collision_id')
            if target in nodes:edge(identity,target,'field_map_table_source',scene,'decoded')
            else:unresolved+=1
            if record.get('script_reference'):unresolved+=1
        elif kind=='worldmap':
            name=record.get('destination_source_label')
            if name:
                target='scene://'+name;node(target,'scene',target,name,target in project.imports);edge(identity,target,'landmark_destination_source',scene,'decoded')
            else:unresolved+=1
    if identifier not in nodes:raise ProjectError('Asset is outside imported project records and the active resource catalog')
    incoming=sorted((e for e in edges.values() if e['target_id']==identifier),key=lambda e:(e['kind'],e['source_id'],e.get('pc',-1)))
    outgoing=sorted((e for e in edges.values() if e['source_id']==identifier),key=lambda e:(e['kind'],e['target_id'],e.get('pc',-1)))
    if len(incoming)+len(outgoing)>4096:raise ProjectError('Asset reference neighborhood exceeds4096 edges')
    neighbors={identifier}|{e['source_id'] for e in incoming}|{e['target_id'] for e in outgoing}
    return deepcopy(dict(schema_version='legaia.asset-references.v1',asset_id=identifier,source_key=source_key(project),read_only=True,
                         nodes=[nodes[key] for key in sorted(neighbors)],incoming=incoming,outgoing=outgoing,
                         coverage=dict(verified_scene_ids=sorted(project.imports),resource_scene_id=scene,unresolved_reference_count=unresolved),
                         limitations=['Imported scene/model membership and initial assignments are project-wide. Derived resources cover the active scene only.',
                                      'Script model pools, field trigger dispatch, texture/material dependencies and effective animation donor bindings are not resolved here.',
                                      'Edges describe recorded references, not runtime residency, successful scheduling or gameplay reachability.',*catalog.get('limitations',[])]))

def inspect(project,identifier):
    from importer.pipeline import _disc_context
    from .resources import _verify,refresh_resource_catalog
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    if not project.disc_path or not project.active_scene or not 1<=len(project.imports)<=64:raise ProjectError('Asset references require an active scene, user-owned disc and at most64 imported scenes')
    key=source_key(project)
    with _disc_context(project.disc_path):
        for document in project.imports.values():_verify(project,document)
        catalog=refresh_resource_catalog(project);result=assemble(project,catalog,identifier)
    if key!=source_key(project):raise ProjectError('Asset reference source changed during discovery')
    return result

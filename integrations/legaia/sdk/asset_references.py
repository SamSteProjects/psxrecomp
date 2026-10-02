"""Recorded asset relationships, never runtime residency or gameplay reachability."""
from copy import deepcopy
from .project import ProjectError,digest

def source_key(project):
    return digest(dict(project_root=str(project.root),active_scene=project.active_scene,disc_path=project.disc_path,
                       imports={key:digest(doc) for key,doc in sorted(project.imports.items())},
                       overrides=project.overrides,drafts=project.actor_drafts))

def assemble(project,catalog,identifier,materials=None,*,_full_graph=False):
    """Adapt explicit imported/derived references; callers verify retail sources first."""
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    nodes={};edges={};unresolved=0;memberships={};navigation={}
    import_digests={scene:digest(document) for scene,document in project.imports.items()}
    def node(identifier,kind,scene,label=None,available=True):
        if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
        value=dict(id=identifier,kind=kind,scene_id=scene,label=label or identifier,available=available)
        memberships.setdefault(identifier,set()).add(scene)
        if available and scene in project.imports:navigation.setdefault(identifier,set()).add(scene)
        if identifier in nodes:
            if nodes[identifier]['kind']!=kind:raise ProjectError('Conflicting asset reference type')
            if available:nodes[identifier]['available']=True
        else:nodes[identifier]=value
        if len(nodes)>16384:raise ProjectError('Asset reference node limit exceeded')
    def edge(source,target,kind,scene,layer='imported',pc=None,evidence=None,animation_evidence=None):
        if source not in nodes or target not in nodes:raise ProjectError('Asset reference has an unavailable structural endpoint')
        value=dict(source_id=source,target_id=target,kind=kind,scene_id=scene,layer=layer,runtime_binding='not_asserted')
        if pc is not None:value['pc']=pc
        value['source_import_sha256']=import_digests[scene]
        if layer=='decoded':value['source_catalog_key']=catalog['source_key']
        if evidence is not None:value['material_evidence']=deepcopy(evidence)
        if animation_evidence is not None:
            value['effective_animation_evidence']=deepcopy(animation_evidence)
            value['source_catalog_key']=catalog['source_key']
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
    for actor_id,components in sorted(project.overrides.items()):
        donor=components.get('ActorAppearance',{}).get('donor_entity_id')
        if donor and donor!=actor_id:
            if actor_id in nodes and donor in nodes:edge(actor_id,donor,'appearance_donor',nodes[actor_id]['scene_id'],'authored')
            else:unresolved+=1
    model_references=project.model_references()
    effective_bindings={}
    for ref in model_references:
        if ref['effective']:
            effective_bindings.setdefault((ref['scene_id'],ref['effective_donor_id'],ref['target_id']),[]).append(ref)
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
                for ref in effective_bindings.get((scene,actor,model),[]):
                    draft=ref['kind']=='draft_initial_model_assignment'
                    edge(ref['source_id'],identity,'draft_initial_animation_binding' if draft else 'effective_initial_animation_binding',scene,'authored' if draft else 'effective',
                         animation_evidence=dict(donor_entity_id=actor,model_id=model,initial_animation_id=binding['initial_animation_id']))
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
    if materials is not None:
        unresolved+=materials['unresolved_reference_count']
        for model in materials['models']:
            for material in model['materials']:
                if material['status']!='address_match':continue
                evidence={key:deepcopy(material[key]) for key in ('material_index','tpage','clut','uv_bounds','evidence')}
                evidence['model_source_sha256']=model['source_sha256']
                for target in material['source_ids']:
                    node(target,'texture',scene,available=target in nodes)
                    edge(model['model_id'],target,'static_material_texture_source',scene,'decoded',evidence=evidence)
    if _full_graph:
        for identity,value in nodes.items():
            value['scene_ids']=sorted(memberships[identity]);value['_navigation_scene_ids']=sorted(navigation.get(identity,set()))
        return dict(nodes=nodes,edges=edges,unresolved_reference_count=unresolved)
    if identifier not in nodes:raise ProjectError('Asset is outside imported project records and the active resource catalog')
    incoming=sorted((e for e in edges.values() if e['target_id']==identifier),key=lambda e:(e['kind'],e['source_id'],e.get('pc',-1)))
    outgoing=sorted((e for e in edges.values() if e['source_id']==identifier),key=lambda e:(e['kind'],e['target_id'],e.get('pc',-1)))
    if len(incoming)+len(outgoing)>4096:raise ProjectError('Asset reference neighborhood exceeds4096 edges')
    neighbors={identifier}|{e['source_id'] for e in incoming}|{e['target_id'] for e in outgoing}
    return deepcopy(dict(schema_version='legaia.asset-references.v1',asset_id=identifier,source_key=source_key(project),read_only=True,
                         nodes=[nodes[key] for key in sorted(neighbors)],incoming=incoming,outgoing=outgoing,
                         coverage=dict(verified_scene_ids=sorted(project.imports),resource_scene_id=scene,unresolved_reference_count=unresolved),
                         material_diagnostics=deepcopy(next((row for row in (materials or {}).get('models',[]) if row['model_id']==identifier),None)),
                         limitations=['Imported scene/model membership and initial assignments are project-wide. Derived resources cover the active scene only.',
                                      'Script model pools, field trigger dispatch and live animation state are not resolved here.',
                                      'Edges describe recorded references, not runtime residency, successful scheduling or gameplay reachability.',*(materials or {}).get('limitations',['Material source relationships were not requested.']),*catalog.get('limitations',[])]))

def inspect(project,identifier):
    from importer.pipeline import _disc_context
    from .resources import _verify,refresh_resource_catalog
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:raise ProjectError('Invalid asset reference identity')
    if not project.disc_path or not project.active_scene or not 1<=len(project.imports)<=64:raise ProjectError('Asset references require an active scene, user-owned disc and at most64 imported scenes')
    key=source_key(project)
    with _disc_context(project.disc_path):
        for document in project.imports.values():_verify(project,document)
        from .material_references import verified_catalog
        catalog=refresh_resource_catalog(project);materials=verified_catalog(project);result=assemble(project,catalog,identifier,materials)
    if key!=source_key(project):raise ProjectError('Asset reference source changed during discovery')
    return result


def _reference_limitations(rows):
    if not isinstance(rows,list) or len(rows)>256 or any(not isinstance(row,str) or len(row)>8192 for row in rows):
        raise ProjectError('Asset reference limitations exceed the bounded metadata format')
    return rows


def _project_graph(project,catalog,identifier,materials=None):
    try:
        graph=assemble(project,catalog,identifier,materials,_full_graph=True)
        from .project import canonical
        if len(canonical(graph))>8*1024*1024:raise ProjectError('Asset reference scene graph exceeds8 MiB')
        return graph
    except (KeyError,TypeError,IndexError) as error:
        raise ProjectError('Invalid project reference decoded metadata') from error


def assemble_project(project,catalogs,identifier,materials_by_scene=None,scene_coverage=None):
    """Merge complete scene graphs before selecting a project-wide neighborhood."""
    from copy import copy
    from .project import canonical
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:
        raise ProjectError('Invalid asset reference identity')
    if not isinstance(catalogs,dict) or not 1<=len(project.imports)<=64 or project.active_scene not in project.imports:
        raise ProjectError('Project references require an active imported scene and at most64 imported scenes')
    if set(catalogs)-set(project.imports):raise ProjectError('Resource catalog is outside imported project scenes')
    materials_by_scene={} if materials_by_scene is None else materials_by_scene
    if not isinstance(materials_by_scene,dict) or set(materials_by_scene)-set(catalogs):
        raise ProjectError('Material catalog is outside verified resource scenes')
    if len(canonical(dict(catalogs=catalogs,materials=materials_by_scene)))>32*1024*1024:
        raise ProjectError('Project reference decoded metadata exceeds32 MiB')
    supplied={} if scene_coverage is None else scene_coverage
    if not isinstance(supplied,dict) or set(supplied)-set(project.imports):raise ProjectError('Invalid project reference coverage')
    nodes={};edges={};memberships={};navigation={};unresolved=0;coverage=[];limitations=[]
    # A placeholder is only a graph adapter for imported membership, never evidence
    # that an unavailable scene has decoded resources.
    for scene in sorted(project.imports):
        catalog=catalogs.get(scene)
        if catalog is not None:
            if not isinstance(catalog,dict) or not isinstance(catalog.get('source_key'),str) or len(catalog['source_key'])!=64 or any(c not in '0123456789abcdef' for c in catalog['source_key']):
                raise ProjectError('Invalid project reference resource source key')
            if catalog.get('scene_id',scene)!=scene or not isinstance(catalog.get('records'),list):
                raise ProjectError('Invalid project reference resource catalog')
            for record in catalog['records']:
                if not isinstance(record,dict) or record.get('kind') not in ('texture','animation','script','dialogue','collision','trigger','region','worldmap'):
                    raise ProjectError('Invalid project reference resource type')
                if record.get('name') is not None and (not isinstance(record['name'],str) or len(record['name'])>8192):
                    raise ProjectError('Invalid project reference resource label')
        status='available' if catalog is not None else 'unavailable'
        details=supplied.get(scene,{})
        if not isinstance(details,dict) or details.get('status',status)!=status:
            raise ProjectError('Project reference coverage differs from resource evidence')
        expected_key=catalog['source_key'] if catalog else None
        if details.get('source_import_sha256',digest(project.imports[scene]))!=digest(project.imports[scene]) or details.get('resource_source_key',expected_key)!=expected_key:
            raise ProjectError('Project reference coverage differs from source provenance')
        if status=='available' and details.get('reason') is not None:
            raise ProjectError('Available resource scene cannot have an unavailable reason')
        reason=details.get('reason') if status=='unavailable' else None
        if status=='unavailable' and (not isinstance(reason,str) or not reason or len(reason)>8192):
            raise ProjectError('Unavailable resource scene requires an explicit reason')
        local_limitations=_reference_limitations((catalog or {}).get('limitations',[]))
        coverage.append(dict(scene_id=scene,source_import_sha256=digest(project.imports[scene]),status=status,
                             resource_source_key=catalog['source_key'] if catalog else None,reason=reason,limitations=local_limitations))
        limitations.extend(scene+': '+row for row in local_limitations)
        if reason:limitations.append(scene+': Derived resources unavailable: '+reason)
        view=copy(project);view.active_scene=scene
        graph=_project_graph(view,catalog or dict(source_key=None,records=[],limitations=[]),identifier,materials_by_scene.get(scene))
        # Imported/effective edges are repeated by every adapter; exact edge IDs
        # deduplicate them. Unresolved imported references likewise count once.
        imported_graph=_project_graph(view,dict(source_key=None,records=[],limitations=[]),identifier)
        unresolved+=graph['unresolved_reference_count']-imported_graph['unresolved_reference_count']
        if scene==sorted(project.imports)[0]:unresolved+=imported_graph['unresolved_reference_count']
        for identity,value in graph['nodes'].items():
            memberships.setdefault(identity,set()).update(value.pop('scene_ids'))
            navigation.setdefault(identity,set()).update(value.pop('_navigation_scene_ids'))
            if identity in nodes:
                if nodes[identity]['kind']!=value['kind']:raise ProjectError('Conflicting asset reference type')
                nodes[identity]['available']=nodes[identity]['available'] or value['available']
            else:nodes[identity]=value
        edges.update(graph['edges'])
        if len(nodes)>16384:raise ProjectError('Asset reference node limit exceeded')
        if len(edges)>32768:raise ProjectError('Asset reference edge limit exceeded')
        if len(canonical(dict(nodes=nodes,edges=edges)))>32*1024*1024:
            raise ProjectError('Project reference graph exceeds32 MiB')
    if identifier not in nodes:raise ProjectError('Asset is outside imported project records and verified resource catalogs')
    for identity,value in nodes.items():
        if len(memberships[identity])>64:raise ProjectError('Asset reference scene membership limit exceeded')
        value['scene_ids']=sorted(memberships[identity])
        value['navigable_scene_ids']=sorted(navigation[identity])
        value['available']=bool(navigation[identity])
        value['scene_id']=min(navigation[identity] or memberships[identity])
    incoming=sorted((e for e in edges.values() if e['target_id']==identifier),key=lambda e:(e['kind'],e['scene_id'],e['source_id'],e.get('pc',-1),e['id']))
    outgoing=sorted((e for e in edges.values() if e['source_id']==identifier),key=lambda e:(e['kind'],e['scene_id'],e['target_id'],e.get('pc',-1),e['id']))
    if len(incoming)+len(outgoing)>4096:raise ProjectError('Asset reference neighborhood exceeds4096 edges')
    neighbors={identifier}|{e['source_id'] for e in incoming}|{e['target_id'] for e in outgoing}
    diagnostics=next((row for scene in sorted(materials_by_scene) for row in materials_by_scene[scene].get('models',[]) if row['model_id']==identifier),None)
    for scene,materials in sorted(materials_by_scene.items()):
        limitations.extend(scene+': '+row for row in _reference_limitations(materials.get('limitations',[])))
    result=dict(schema_version='legaia.project-asset-references.v1',asset_id=identifier,source_key=source_key(project),read_only=True,
                nodes=[nodes[key] for key in sorted(neighbors)],incoming=incoming,outgoing=outgoing,
                coverage=dict(verified_scene_ids=sorted(project.imports),resource_scene_id=project.active_scene,
                              unresolved_reference_count=unresolved,scenes=coverage),material_diagnostics=deepcopy(diagnostics),
                limitations=['Derived resource discovery covers every imported scene with explicit per-scene availability.',
                             'Edges describe recorded references, not runtime residency, successful scheduling or gameplay reachability.',
                             'Script model pools, field trigger dispatch and live animation state are not resolved here.',*list(dict.fromkeys(limitations))])
    _reference_limitations(result['limitations'])
    if len(canonical(result))>8*1024*1024:raise ProjectError('Project reference response exceeds8 MiB')
    return deepcopy(result)


def inspect_project(project,identifier):
    """Fresh verified discovery using detached project state and private catalogs."""
    from importer.pipeline import _disc_context
    from importer.core import ImportError as RetailImportError
    from .resources import _verify,refresh_resource_catalog
    from .material_references import verified_catalog
    from .project import AssetDatabase
    if not isinstance(identifier,str) or not identifier or len(identifier)>1024:
        raise ProjectError('Invalid asset reference identity')
    if not project.disc_path or project.active_scene not in project.imports or not 1<=len(project.imports)<=64:
        raise ProjectError('Project references require an active scene, user-owned disc and at most64 imported scenes')
    key=source_key(project)
    from copy import copy
    active_scene=project.active_scene
    view=copy(project)
    for name,value in vars(project).items():
        if name!='assets':setattr(view,name,deepcopy(value))
    view.assets=AssetDatabase()
    catalogs={};materials={};coverage={};metadata_bytes=0
    with _disc_context(view.disc_path):
        # Verify the complete snapshot before any derived decoding or reuse.
        for scene in sorted(view.imports):_verify(view,view.imports[scene])
        for scene in sorted(view.imports):
            view.active_scene=scene
            try:
                catalog=refresh_resource_catalog(view)
                material=verified_catalog(view)
            except RetailImportError as error:
                coverage[scene]=dict(status='unavailable',reason=str(error))
                continue
            from .project import canonical
            metadata_bytes+=len(canonical(dict(catalog=catalog,materials=material)))
            if metadata_bytes>32*1024*1024:raise ProjectError('Project reference decoded metadata exceeds32 MiB')
            catalogs[scene]=catalog;materials[scene]=material
    view.active_scene=active_scene
    if key!=source_key(project) or key!=source_key(view):raise ProjectError('Asset reference source changed during discovery')
    result=assemble_project(view,catalogs,identifier,materials,coverage)
    if key!=source_key(project):raise ProjectError('Asset reference source changed during discovery')
    return result

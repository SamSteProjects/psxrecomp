"""Request-scoped central AssetDatabase registration for World source behavior."""
from copy import copy,deepcopy
from .project import AssetDatabase,ProjectError
from .worldmap_authoring import state_key
from .project_assets import _metadata,_budget
from importer.pipeline import _disc_context
from importer.worldmap_behavior_catalog import load_worldmap_behavior_catalog,LIMITATIONS


def inspect(project,key):
    if project.mode!='edit' or not project.disc_path or key!=state_key(project):
        raise ProjectError('World behavior discovery requires fresh Edit project inputs')
    view=copy(project)
    for name,value in vars(project).items():
        if name!='assets':setattr(view,name,deepcopy(value))
    view.assets=AssetDatabase();assets=[];kingdoms=[]
    with _disc_context(view.disc_path):
        for scene in ('map01','map02','map03'):
            catalog=load_worldmap_behavior_catalog(view.disc_path,scene)
            registered=view.assets.register_resources('worldmap://'+scene+'/behavior-resources',key,catalog['assets'],catalog['limitations'])
            for row in registered['records']:
                row.update(scene_id=None,asset_registration='verified_world_behavior_catalog');assets.append(row)
            kingdoms.append(dict(scene=scene,consumer=catalog['consumer'],unbound=catalog['unbound'],
                unsupported_animation_bindings=catalog['unsupported_animation_bindings'],
                script_asset_count=sum(r['kind']=='script' for r in catalog['assets']),
                animation_asset_count=sum(r['kind']=='animation' for r in catalog['assets'])))
    if len({r['id'] for r in assets})!=len(assets):raise ProjectError('World behavior resource identities conflict')
    result=dict(schema_version='legaia.worldmap-behavior-resources.v1',project_path=str(project.root),source_key=key,
        assets=sorted(assets,key=lambda r:r['id']),kingdoms=kingdoms,metadata_only=True,read_only=True,
        project_changed=False,gameplay_verified=False,limitations=list(LIMITATIONS))
    _metadata(result);_budget(result)
    if key!=state_key(project) or key!=state_key(view):raise ProjectError('World behavior resources changed during discovery')
    return result

"""Reviewed persistent controller selector overrides, separate from actors."""
from .controller_components import CONTROLLER_COMPONENTS
from copy import deepcopy
import re
from hashlib import sha256
from .project import ProjectError, digest
from importer.core import ImportError as RetailImportError
from importer.controller_system_flags import load_controller_system_flag_context
from importer.system_flag_authoring import validate_system_flag_values

COMPONENT='ControllerSystemFlags'
SCHEMA='legaia.controller-system-flags.v1'


def scene_document(project, owner):
    match=re.fullmatch(r'scene://([A-Za-z0-9_-]+)/controllers/man-p1/0000',owner) if isinstance(owner,str) else None
    document=project.imports.get('scene://'+match[1]) if match else None
    if document is None:
        raise ProjectError('Controller selector owner requires an imported scene controller')
    return document


def validate(project, owner, value):
    scene_document(project,owner)
    if not isinstance(value,dict) or set(value)!={'source_record_sha256','entries'} or not isinstance(value['source_record_sha256'],str) or re.fullmatch(r'[a-f0-9]{64}',value['source_record_sha256']) is None or not isinstance(value['entries'],dict) or not 1<=len(value['entries'])<=1024:
        raise ProjectError('Controller selectors require a source record hash and bounded entries')
    prefix=owner.replace('scene://','script://',1)+'/system-flag/'
    for identity,fields in value['entries'].items():
        if not isinstance(identity,str) or re.fullmatch(re.escape(prefix)+r'[a-f0-9]{4}',identity) is None:
            raise ProjectError('Controller selector operand belongs to another source owner')
        try:validate_system_flag_values(fields)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    return deepcopy(value)


def validate_components(project,owner,components):
    if not isinstance(components,dict) or not components or set(components)-CONTROLLER_COMPONENTS:
        raise ProjectError('Controller overrides cannot contain actor components')
    hashes=set()
    for family,value in components.items():
        if family==COMPONENT:checked=validate(project,owner,value)
        elif family=='ControllerBranches':
            from .controller_branches import validate as validate_branches
            checked=validate_branches(project,owner,value)
        elif family=='ControllerTileRects':
            from .controller_tile_rects import validate as validate_tiles
            checked=validate_tiles(project,owner,value)
        elif family=='ControllerFades':
            from .controller_fades import validate as validate_fades
            checked=validate_fades(project,owner,value)
        elif family=='ControllerTableCopies':
            from .controller_tables import validate as validate_tables
            checked=validate_tables(project,owner,value)
        elif family=='ControllerWordTriplets':
            from .controller_word_triplets import validate as validate_triplets
            checked=validate_triplets(project,owner,value)
        elif family=='ControllerSceneBytes':
            from .controller_scene_bytes import validate as validate_scene_bytes
            checked=validate_scene_bytes(project,owner,value)
        else:
            from .controller_three_words import validate as validate_three_words
            checked=validate_three_words(project,owner,value)
        hashes.add(checked['source_record_sha256'])
    if len(hashes)!=1:raise ProjectError('Controller components require the same Retail source hash')
    return deepcopy(components)


def compose(context,owner,components):
    selectors=components.get(COMPONENT,{}).get('entries',{})
    current,_=context.patch(selectors)
    if 'ControllerBranches' in components:
        from importer.controller_branches import ControllerBranchAuthoringContext
        branches=ControllerBranchAuthoringContext(context._source,system_selectors=selectors)
        current,_=branches.patch_composed(current,components['ControllerBranches']['entries'])
    if 'ControllerTileRects' in components:
        from .controller_tile_rects import compose as compose_tiles
        current=compose_tiles(context._source,current,components['ControllerTileRects']['entries'])
    if 'ControllerFades' in components:
        from .controller_fades import compose as compose_fades
        current=compose_fades(context._source,current,components['ControllerFades']['entries'])
    if 'ControllerTableCopies' in components:
        from .controller_tables import compose as compose_tables
        current=compose_tables(context._source,current,components['ControllerTableCopies']['entries'])
    if 'ControllerWordTriplets' in components:
        from .controller_word_triplets import compose as compose_triplets
        current=compose_triplets(context._source,current,components['ControllerWordTriplets']['entries'])
    if 'ControllerThreeWords' in components:
        from .controller_three_words import compose as compose_three_words
        current=compose_three_words(context._source,current,components['ControllerThreeWords']['entries'])
    if 'ControllerSceneBytes' in components:
        from .controller_scene_bytes import compose as compose_scene_bytes
        current=compose_scene_bytes(context._source,current,components['ControllerSceneBytes']['entries'])
    return current


def state_key(project):
    from .script_branches import state_key as script_key
    return digest({'project_path':str(project.root),'source_state':script_key(project)})


def prepare(project,owner):
    from .resources import _verify
    from importer.pipeline import _disc_context
    document=scene_document(project,owner)
    if project.mode!='edit' or project.active_scene!=document['scene']['semantic_id']:
        raise ProjectError('Controller selector editing requires the active imported scene in Edit mode')
    key=state_key(project)
    try:
        with _disc_context(project.disc_path):
            _verify(project,document)
            context=load_controller_system_flag_context(project.disc_path,document['scene']['name'])
        offset,record,entry=context._source.verified_record(owner)
        components=deepcopy(project.overrides.get(owner,{}))
        if components:validate_components(project,owner,components)
        for family in components.values():
            if family['source_record_sha256']!=sha256(record).hexdigest():raise ProjectError('Controller source record changed')
        current=compose(context,owner,components)
        options=context.options(owner)
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    if key!=state_key(project):raise ProjectError('Controller selector source changed during inspection')
    return key,context,offset,record,entry,components,current,options


def snapshot(project,owner):
    key,context,offset,record,entry,components,current,options=prepare(project,owner)
    from importer.script_inspection import inspect_record
    current_report=inspect_record(current[offset:offset+len(record)],entry,semantic_id=owner.replace('scene://','script://',1),base_offset=offset)
    entries=components.get(COMPONENT,{}).get('entries',{})
    targets=[]
    for target in options['targets']:
        pc=target['pc'];at=offset+pc
        targets.append(dict(target,authored_values=deepcopy(entries.get(target['semantic_id'])),current_index=((current[at]&15)<<8)|current[at+1]))
    return dict(schema_version=SCHEMA,owner_id=owner,state_key=key,source_record_sha256=sha256(record).hexdigest(),current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),targets=targets,current_report=current_report,supported=bool(targets),reason=options['reason'],limitations=options['limitations'],gameplay_verified=False)


def review(project,owner,operand,value):
    if value is not None:
        try:validate_system_flag_values(value)
        except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    key,context,offset,record,entry,components,current,options=prepare(project,owner)
    target=next((t for t in options['targets'] if t['semantic_id']==operand),None)
    if target is None:raise ProjectError('Choose a source-qualified controller selector')
    entries=deepcopy(components.get(COMPONENT,{}).get('entries',{}))
    if value is None:entries.pop(operand,None)
    else:entries[operand]=deepcopy(value)
    proposed=deepcopy(components)
    if entries:proposed[COMPONENT]=validate(project,owner,{'source_record_sha256':sha256(record).hexdigest(),'entries':entries})
    else:proposed.pop(COMPONENT,None)
    try:candidate=compose(context,owner,proposed)
    except RetailImportError as exc:raise ProjectError(str(exc)) from exc
    differences=[i for i,(a,b) in enumerate(zip(current,candidate)) if a!=b]
    if any(i not in (offset+target['pc'],offset+target['pc']+1) for i in differences):raise ProjectError('Controller selector Review changed an unrelated byte')
    from importer.script_inspection import inspect_record
    current_report=inspect_record(current[offset:offset+len(record)],entry,semantic_id=owner.replace('scene://','script://',1),base_offset=offset)
    proposed_report=inspect_record(candidate[offset:offset+len(record)],entry,semantic_id=owner.replace('scene://','script://',1),base_offset=offset)
    proof=dict(owner_id=owner,operand_id=operand,value=deepcopy(value),state_key=key,source_record_sha256=sha256(record).hexdigest(),current_record_sha256=sha256(current[offset:offset+len(record)]).hexdigest(),proposed_record_sha256=sha256(candidate[offset:offset+len(record)]).hexdigest(),proposed=proposed)
    if key!=state_key(project):raise ProjectError('Controller selector source changed during Review')
    return dict(schema_version=SCHEMA,**proof,review_key=digest(proof),current_report=current_report,proposed_report=proposed_report,changed_decoded_byte_offsets=differences,no_op=components==proposed,native_bytes_changed=current!=candidate,project_changed=False,gameplay_verified=False)


def apply(project,command):
    if set(command)!={'type','entity_id','operand_id','value','review_key'}:raise ProjectError('Controller selector Apply requires exact reviewed inputs')
    result=review(project,command['entity_id'],command['operand_id'],command['value'])
    if result['review_key']!=command['review_key']:raise ProjectError('Controller selector inputs changed; review again')
    if result['no_op']:raise ProjectError('Controller selector has no authored state change')
    owner=command['entity_id'];before=deepcopy(project.overrides.get(owner));after=result['proposed'] or None
    if after is None:project.overrides.pop(owner,None)
    else:project.overrides[owner]=deepcopy(after)
    project.undo_stack.append(dict(entity_id=owner,before=before,after=deepcopy(after)));project.redo_stack.clear()

"""Atomic rectangular source wall edits, using the existing MAP bit serializer."""
from copy import deepcopy
from hashlib import sha256
from .project import ProjectError,digest
from .project_copy import source_key
from importer.collision_authoring import patch_collision_walls

def review(project,scene,rectangle,cell_edits=None):
    if project.mode!='edit' or not isinstance(scene,str) or scene not in project.imports:raise ProjectError('Wall rectangle requires an imported scene in Edit mode')
    fields={'row_start','row_end','column_start','column_end','quadrant','blocked'}
    if not isinstance(rectangle,dict) or set(rectangle)!=fields:raise ProjectError('Wall rectangle requires inclusive row/column bounds, quadrant and blocked only')
    for key,low,high in [('row_start',1,127),('row_end',1,127),('column_start',0,127),('column_end',0,127)]:
        if type(rectangle[key]) is not int or not low<=rectangle[key]<=high:raise ProjectError('Wall rectangle bounds are outside the canonical grid')
    q=rectangle['quadrant']
    if not (q=='all' or type(q) is int and 0<=q<=3) or not (type(rectangle['blocked']) is bool or rectangle['blocked'] in ('retail','current')):raise ProjectError('Invalid rectangle quadrant or blocked value')
    if rectangle['row_start']>rectangle['row_end'] or rectangle['column_start']>rectangle['column_end']:raise ProjectError('Wall rectangle bounds must be ordered')
    quadrants=range(4) if q=='all' else [q]
    count=(rectangle['row_end']-rectangle['row_start']+1)*(rectangle['column_end']-rectangle['column_start']+1)*len(quadrants)
    if count>4096:raise ProjectError('Wall rectangle exceeds 4096 wall bits')
    patterned=cell_edits is not None or rectangle['blocked']=='current'
    cells=[] if cell_edits is None else deepcopy(cell_edits);targets={}
    if not isinstance(cells,list) or len(cells)>4096:raise ProjectError('Wall paint accepts at most 4096 quadrant edits')
    for cell in cells:
        if not isinstance(cell,dict) or set(cell)!={'row','column','quadrant','blocked'}:raise ProjectError('Wall paint requires row, column, quadrant and blocked only')
        if any(type(cell[k]) is not int for k in ('row','column','quadrant')) or not rectangle['row_start']<=cell['row']<=rectangle['row_end'] or not rectangle['column_start']<=cell['column']<=rectangle['column_end'] or cell['quadrant'] not in quadrants:raise ProjectError('Wall paint escapes the selected rectangle or quadrant')
        if not (type(cell['blocked']) is bool or cell['blocked']=='retail'):raise ProjectError('Wall paint operation must be blocked, unblocked or retail')
        identity=(cell['row'],cell['column'],cell['quadrant'])
        if identity in targets:raise ProjectError('Duplicate wall paint quadrant')
        targets[identity]=cell['blocked']
    cells=sorted(cells,key=lambda c:(c['row'],c['column'],c['quadrant']))
    before=source_key(project);original=project._environment_source(scene);source_hash=sha256(original).hexdigest()
    authored=deepcopy(project.overrides.get(scene,{}).get('Collision'))
    effective=patch_collision_walls(original,authored['source_sha256'],authored['edits'])[0] if authored else original
    merged={(e['row'],e['column'],e['quadrant']):deepcopy(e) for e in (authored or {}).get('edits',[])};rows=[]
    for row in range(rectangle['row_start'],rectangle['row_end']+1):
        for column in range(rectangle['column_start'],rectangle['column_end']+1):
            offset=0x4000+row*128+column
            for quadrant in quadrants:
                retail=bool(original[offset]&(16<<quadrant));current=bool(effective[offset]&(16<<quadrant));key=(row,column,quadrant)
                operation=targets.get(key,rectangle['blocked']);blocked=retail if operation=='retail' else current if operation=='current' else operation
                if blocked==retail:merged.pop(key,None)
                else:merged[key]=dict(row=row,column=column,quadrant=quadrant,blocked=blocked)
                rows.append(dict(row=row,column=column,quadrant=quadrant,retail=retail,effective=current,proposed=blocked))
    edits=[merged[key] for key in sorted(merged)]
    if len(edits)>4096:raise ProjectError('Combined wall override exceeds 4096 wall bits')
    _,audit=patch_collision_walls(original,source_hash,edits)
    if source_key(project)!=before:raise ProjectError('Project changed while reviewing wall rectangle')
    key=digest(dict(project_source_key=before,scene=scene,source_sha256=source_hash,rectangle=rectangle,**({'cell_edits':cells} if patterned else {})))
    return dict(**({'cell_edits':cells} if patterned else {}),schema_version='legaia.collision-rectangle-review.v2' if patterned else 'legaia.collision-rectangle-review.v1',project_source_key=before,scene_id=scene,
                source_sha256=source_hash,review_key=key,rectangle=deepcopy(rectangle),rows=rows,wall_bit_count=count,
                effective_change_count=sum(row['effective']!=row['proposed'] for row in rows),
                project_change=authored!=(dict(source_sha256=source_hash,edits=edits) if edits else None),
                authored_bit_count=len(edits),audited_bit_count=len(audit),value=dict(source_sha256=source_hash,edits=edits),
                scope='source-MAP-wall-bits-only',gameplay_verified=False)

def apply(project,command):
    if set(command) not in ({'type','entity_id','rectangle','review_key'},{'type','entity_id','rectangle','review_key','cell_edits'}):raise ProjectError('Wall rectangle Apply requires owner, rectangle and current review key only')
    if 'cell_edits' in command and not isinstance(command['cell_edits'],list):raise ProjectError('Wall paint Apply requires a quadrant edit list')
    result=review(project,command['entity_id'],command['rectangle'],command.get('cell_edits'))
    if result['review_key']!=command['review_key']:raise ProjectError('Wall rectangle inputs changed since review')
    project.command(dict(type='set_collision_walls',entity_id=command['entity_id'],value=result['value']) if result['value']['edits'] else dict(type='clear_collision_walls',entity_id=command['entity_id']))

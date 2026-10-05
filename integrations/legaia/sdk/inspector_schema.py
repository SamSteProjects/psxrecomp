"""Editor property contracts; authoring validation still belongs to ProjectService."""

def inspector_schema():
    schema = {'schema_version':'legaia.inspector-schema.v1','components':{
        'Transform':{'label':'Transform','units':'Scene units','layout':'layered-number',
            'layers':['imported','authored','effective'],
            'properties':[{'id':axis,'label':axis.upper(),'path':['position',axis],
                'type':'number','nullable':True,'authoring':{'minimum':-32767,'maximum':32767,'step':'any','set_command':'set_transform','clear_command':'clear_transform'},
                'retail_status':'unresolved' if axis=='y' else 'imported',
                'build':{'supported':axis!='y',**({'minimum':64,'maximum':16384,'step':64} if axis!='y' else {}),
                         'note':'Project-only height; clear before Build' if axis=='y' else 'Build requires a representable64-unit retail placement'}} for axis in ('x','y','z')],
            'notes':['Empty authored fields inherit imported values. Authoring bounds and Build encoding bounds are separate.',
                     'Unknown heights use source terrain for preview when available, otherwise the ground plane. Display axes use the SDK conversion.']},
        'ActorAppearance':{'label':'Actor appearance','units':'Inherited model + default clip','layout':'layered-properties',
            'actions':[{'id':'choose-appearance','label':'Choose donor appearance…','capability':'actor_appearance','requires_edit':True},{'id':'clear-appearance','label':'Clear appearance override','capability':'actor_appearance','requires_edit':True,'when':['authored','donor_entity_id']},{'id':'preview-appearance','label':'Preview authored appearance','capability':'actor_appearance','when':['authored','donor_entity_id']}],
            'layers':[{'id':'imported','label':'Imported'},{'id':'authored','label':'Authored override'},{'id':'effective','label':'Appearance default'}],
            'properties':[{'id':'asset_id','label':'Model','path':['asset_id'],'type':'asset-reference','layers':['imported','effective'],'state':'read-only-reference'},
                          {'id':'animation_id','label':'Animation ID','path':['animation_id'],'type':'integer','layers':['imported','effective'],'state':'read-only-reference'},
                          {'id':'donor_entity_id','label':'Donor actor','path':['donor_entity_id'],'type':'entity-reference','layers':['authored'],'empty_label':'None · inherit imported appearance','state':'authored-through-donor-review'}],
            'notes':['Assign a verified donor pair to this existing actor. Script behavior and gameplay compatibility are not established by a matching model and animation.']},
        'RuntimeCorrelation':{'label':'Runtime observation','units':'Read only · sampled','layout':'read-only-properties',
            'properties':[{'id':'status','label':'Correlation','path':['status'],'fallback_paths':[['state']],'empty_label':'Unresolved','type':'string','state':'live-observed'},
                          {'id':'binding_confirmed','label':'Binding confirmed','path':['binding_confirmed'],'type':'boolean','state':'live-observed'}],
            'notes':['Candidate associations preserve ambiguity. They do not replace imported or authored values.'],
            'details':[{'label':'Epoch, candidates and evidence','path':[]}]},
        'RetailMetadata':{'label':'Retail metadata','units':'Read only','layout':'read-only-properties',
            'properties':[{'id':'source','label':'Source','path':['source_record','prot_entry_name'],'fallback_paths':[['source_record','scene'],['source_record','kind']],'empty_label':'Imported record','type':'string','state':'read-only-retail'}],
            'details':[{'label':'Source, evidence and unresolved fields','path':[]}]},
        'ModelRenderer':{'label':'Model renderer','layout':'read-only-properties',
            'actions':[{'id':'inspect-model','label':'Inspect model objects','capability':'model_preview','when':['asset_id']},{'id':'preview-reference-animation','label':'Preview reference animation','capability':'animation_preview','when':['reference_animation','supported']}],
            'properties':[{'id':'asset_id','label':'Asset','path':['asset_id'],'type':'asset-reference','state':'read-only-retail'},
                          {'id':'resolution_status','label':'Resolution','path':['resolution_status'],'type':'string','state':'derived'}]},
        'Dialogue':{'label':'Script and dialogue','units':'Inspect source','layout':'read-only-properties','properties':[],
            'notes':['Inspect decoded dialogue and supported instruction paths; source capacity and unknown instructions remain explicit.'],
            'actions':[{'id':'inspect-script','label':'Inspect script and dialogue','capability':'actor_script_preview'},{'id':'inspect-actor-candidate','label':'Inspect NPC creation candidate','capability':'actor_candidate_inspection'}]},
        'ScriptBranches':{'label':'Script branch destinations','layout':'read-only-properties','properties':[],
            'actions':[{'id':'inspect-script','label':'Inspect and review script flow','capability':'actor_script_preview'}],
            'details':[{'label':'Authored destination entries','path':['entries']}],
            'notes':['Source-qualified destinations preserve encoded conditions and record layout. Runtime execution remains unverified.']},
        'ScriptFacing':{'label':'Script facing operands','units':'Source instruction sectors0–7','layout':'read-only-properties','properties':[],
            'actions':[{'id':'inspect-script','label':'Inspect facing instructions','capability':'actor_script_preview'}],
            'notes':['Source-qualified facing instructions preserve separate retail, authored and effective operands.',
                     'Script branches determine runtime facing. Initial and live actor heading are not established.'],
            'details':[{'label':'Authored instruction entries','path':['entries']}]},
        'ActorPresets':{'label':'Actor presets','units':'Position, appearance and initial clip','layout':'read-only-properties','properties':[],
            'notes':['Capture authored position, appearance or initial-animation presets for this existing actor.',
                     'Clip presets preserve their exact imported witness; complete proposed components are verified before Apply.'],
            'actions':[{'id':'inspect-templates','label':'Open actor templates…','capability':'authored_transform_templates'}]},
        'ActorAnimation':{'label':'Initial animation assignment','layout':'layered-properties',
            'layers':[{'id':'imported','label':'Imported'},{'id':'base','label':'Appearance default'},
                      {'id':'authored','label':'Authored override'},{'id':'effective','label':'Effective'}],
            'properties':[{'id':'animation_asset_id','label':'Clip','path':['animation_asset_id'],'type':'asset-reference',
                           'layers':['imported','base','authored','effective'],'empty_label':'Unknown or inherited'},
                          {'id':'initial_animation_id','label':'MAN animation ID','path':['initial_animation_id'],'type':'integer','layers':['imported','base','effective']},
                          {'id':'donor_entity_id','label':'Binding witness','path':['donor_entity_id'],'type':'entity-reference','layers':['authored','effective']}],
            'actions':[{'id':'choose-initial-animation','label':'Choose initial animation…','capability':'actor_animation_assignment','requires_edit':True},
                       {'id':'preview-initial-animation','label':'Preview assigned initial animation','capability':'actor_animation_assignment','when':['authored','animation_asset_id']}],
            'notes':['Only observed same-model scene clips accepted by the MAN serializer can be assigned.',
                     'Clearing inherits the appearance default. Existing channel edits remain attached to their imported clip.',
                     'Scripts may replace this initial clip; timing and gameplay suitability remain unverified.']},
        'ActorAllocatedAnimation':{'label':'Allocated initial animation','units':'Retained native clip','layout':'read-only-properties',
            'properties':[{'id':'record_id','label':'Retained clip','path':['authored','record_id'],'type':'string','empty_label':'Inherited/imported','state':'authored-through-review'},
                          {'id':'record_sha256','label':'Record SHA-256','path':['authored','record_sha256'],'type':'string','empty_label':'None','state':'derived'},
                          {'id':'model_asset_id','label':'Captured model','path':['authored','model_asset_id'],'type':'asset-reference','empty_label':'None','state':'read-only-reference'},
                          {'id':'initial_selection','label':'Selector identity','path':['initial_selection'],'type':'string','empty_label':'Inherited/imported','state':'derived'},
                          {'id':'gameplay_verified','label':'Gameplay verified','path':['gameplay_verified'],'type':'boolean','empty_label':'Unknown','state':'evidence-status'}],
            'actions':[{'id':'manage-allocated-clips','label':'Manage allocated clips','capability':'actor_animation_assignment','requires_edit':True},
                       {'id':'preview-allocated-initial-animation','label':'Preview allocated initial animation','capability':'actor_animation_assignment','when':['authored','record_id']}],
            'details':[{'label':'Retained assignment witness','path':['authored']}],
            'notes':['Manage retained clips to review replacement, content edits or clear the assignment. The native selector resolves during Review and Build.',
                     'Imported source remains separate. Scripts may replace the initial clip; gameplay and playback timing remain unverified.']},
        'Animation':{'label':'Animation channels','layout':'read-only-properties',
            'actions':[{'id':'preview-scene-animation','label':'Preview imported scene animation','capability':'actor_animation_preview','when':['preview_support','supported']},{'id':'author-animation-channels','label':'Author animation channels','capability':'actor_animation_authoring','requires_edit':True,'when':['preview_support','supported']}],
            'properties':[{'id':'imported_id','label':'Imported ID','path':['imported_id'],'type':'integer','state':'read-only-retail'}],
            'notes':['Timing, live animation state and retargeting are not inferred from an imported association.']}
    },'unknown_component_policy':'read-only-details','live_writes':False}

    for identifier, label, action, note in (
        ('ScriptMovement', 'Authored script movement', 'Inspect movement instructions', 'Encoded X/Z and move-selector overrides do not establish executed paths, height or movement behavior.'),
        ('ScriptFlags', 'Authored script flag operands', 'Inspect flag instructions', 'Encoded flag operands do not establish live variable values, story meaning or executed paths.'),
        ('ScriptWaits', 'Authored script waits', 'Inspect wait instructions', 'Encoded wait operands do not establish runtime cadence or wall-clock durations.'),
        ('ScriptModelSelectors', 'Authored script model selectors', 'Inspect model-selector instructions', 'Encoded model selectors do not establish runtime rebinding, animation compatibility or executed paths.'),
    ):
        schema['components'][identifier] = {
            'label': label, 'units': 'Authored source operands', 'layout': 'read-only-properties',
            'properties': [{'id': 'authored_instruction_count', 'label': 'Authored instructions',
                            'path': ['authored_instruction_count'], 'type': 'integer', 'state': 'authored-through-source-editor'}],
            'actions': [{'id': 'inspect-script', 'label': action, 'capability': 'actor_script_preview'},
                        {'id': 'reset-script-component', 'label': 'Review component reset', 'capability': 'project_navigation', 'requires_edit': True}],
            'details': [{'label': 'Authored entries by source instruction PC', 'path': ['entries']}],
            'notes': ['Open the source editor for separate retail, authored and effective operands. Existing qualified commands own Apply/Clear, history and Build.', note],
        }

    for identifier in ('ScriptFacing', 'ScriptBranches'):
        definition = schema['components'][identifier]
        definition['properties'] = [{'id': 'authored_instruction_count', 'label': 'Authored instructions',
                                     'path': ['authored_instruction_count'], 'type': 'integer',
                                     'state': 'authored-through-source-editor'}]
        definition['actions'].append({'id': 'reset-script-component', 'label': 'Review component reset',
                                      'capability': 'project_navigation', 'requires_edit': True,
                                      'when': ['authored_instruction_count']})

    # Asset inspector groups describe SDK catalog records, not entity components.
    tools = {
        'actor': ('AssetActor', 'Actor record', 'project_navigation', 'select-asset-actor', 'Select actor in scene'),
        'scene': ('AssetScene', 'Imported scene', 'project_navigation', 'open-asset-scene', 'Open imported scene'),
        'template': ('AssetTemplate', 'Actor preset', 'authored_transform_templates', 'open-asset-template', 'Open preset library'),
        'worldmap': ('AssetWorldmap', 'World-map landmark', 'worldmap_source_navigation', 'open-asset-worldmap', 'Open world-map landmarks'),
        'model': ('AssetModel', 'Model asset', 'model_preview', 'inspect-asset-model', 'Inspect model'),
        'texture': ('AssetTexture', 'Texture asset', 'texture_preview', 'inspect-asset-texture', 'Inspect texture'),
        'animation': ('AssetAnimation', 'Animation resource', 'animation_preview', 'inspect-asset-animation', 'Inspect animation bindings'),
        'script': ('AssetScript', 'Script resource', 'actor_script_preview', 'inspect-asset-script', 'Inspect script'),
        'dialogue': ('AssetDialogue', 'Dialogue resource', 'actor_script_preview', 'inspect-asset-script', 'Inspect dialogue'),
        'transition': ('AssetTransition', 'Transition source reference', 'scene_transitions', 'inspect-asset-transition', 'Inspect transition entry and source'),
        'flag': ('AssetFlag', 'Flag reference group', 'scene_flags', 'inspect-asset-flag', 'Inspect flag reference sites'),
        'collision': ('AssetCollision', 'Collision resource', 'field_map_preview', 'inspect-asset-field', 'Inspect collision'),
        'trigger': ('AssetTrigger', 'Trigger resource', 'field_map_preview', 'inspect-asset-field', 'Inspect trigger'),
        'region': ('AssetRegion', 'Region resource', 'field_map_preview', 'inspect-asset-field', 'Inspect region'),
    }
    schema['asset_inspectors'] = {}
    for kind, (identifier, label, capability, action, action_label) in tools.items():
        schema['asset_inspectors'][kind] = identifier
        schema['components'][identifier] = {
            'label': label, 'layout': 'read-only-properties',
            'properties': [
                {'id': 'id', 'label': 'Stable ID', 'path': ['id'], 'type': 'asset-reference', 'state': 'derived'},
                {'id': 'type', 'label': 'Record type', 'path': ['type'], 'type': 'string', 'state': 'derived'},
                {'id': 'source', 'label': 'Source', 'path': ['source'], 'type': 'string', 'state': 'read-only-retail'},
            ],
            'notes': ['Catalog identity and provenance do not establish runtime use. Supported edits remain in the source-verified tool.'],
            'actions': [{'id': action, 'label': action_label, 'capability': capability}],
        }
    schema['components']['AssetTrigger']['actions'].append({'id': 'inspect-asset-trigger-cells', 'label': 'Edit trigger cell', 'capability': 'field_trigger_authoring'})
    schema['components']['AssetTrigger']['notes'].append('Primary source cell coordinates can be reviewed and built. Payloads remain unchanged; moving a cell may change first-match shadowing. Contact, height and activation are unverified.')
    schema['components']['AssetRegion']['actions'].append({'id': 'inspect-asset-region-bounds', 'label': 'Edit region bounds', 'capability': 'field_region_authoring'})
    schema['components']['AssetRegion']['notes'].append('Primary source corners can be reviewed, undone and built; region type, height and activation remain read-only or unknown.')
    transition=schema['components']['AssetTransition']
    transition['properties'] += [
        {'id':'script','label':'Source script','path':['data','script_id'],'type':'asset-reference','state':'read-only-retail'},
        {'id':'destination','label':'Named destination','path':['data','reference','target_scene_name'],'empty_label':'Unresolved name encoding','type':'string','state':'read-only-retail'},
        {'id':'pc','label':'Source PC','path':['data','reference','pc'],'type':'integer','state':'read-only-retail'},
        {'id':'arrival_x','label':'Effective arrival X','path':['data','arrival_layers','effective','x'],'type':'integer','state':'derived'},
        {'id':'arrival_z','label':'Effective arrival Z','path':['data','arrival_layers','effective','z'],'type':'integer','state':'derived'},
        {'id':'reachability','label':'Reachability','path':['data','reachability'],'type':'string','state':'unresolved'},
    ]
    transition['notes']=['One decoded scene-change instruction with immutable source identity and separately verified authored/effective entry bytes.',
                         'Arrival X/Z and facing are static retail interpretations in the destination scene. Source trigger position and gameplay reachability are unknown.',
                         'Coverage remains partial where bytes are unvisited. Unknown/conflicting path stops and unsupported names block edits; the source script tool qualifies individual entries.']
    flag=schema['components']['AssetFlag']
    flag['properties'] += [
        {'id':'script','label':'Source script','path':['data','script_id'],'type':'asset-reference','state':'read-only-retail'},
        {'id':'bank','label':'Encoded bank','path':['data','bank'],'type':'string','state':'read-only-retail'},
        {'id':'selector','label':'Retail selector','path':['data','index'],'type':'integer','state':'read-only-retail'},
        {'id':'scope','label':'Dispatch scope','path':['data','scope'],'type':'string','state':'read-only-retail'},
        {'id':'sites','label':'Decoded sites','path':['data','reference_count'],'type':'integer','state':'derived'},
        {'id':'authored_sites','label':'Authored operands','path':['data','authored_reference_count'],'type':'integer','state':'derived'},
        {'id':'runtime_binding','label':'Runtime binding','path':['data','runtime_binding'],'type':'string','state':'unresolved'},
    ]
    flag['notes']=['Groups retain one source script, dispatch context, bank and retail selector.',
                   'Authored and effective operands are shown at individual sites. Matching selectors across scripts do not prove one runtime variable.',
                   'Partial paths, unresolved bank widths and system selectors remain explicit. Current values and story names are unknown.']
    worldmap=schema['components']['AssetWorldmap']
    worldmap['properties'] += [
        {'id':'destination','label':'Destination source','path':['data','destination_source_label'],'fallback_paths':[['data','destination_scene_id']],'type':'string','state':'read-only-retail'},
        {'id':'menu_x','label':'Encoded menu X','path':['data','menu_position','x'],'type':'integer','state':'read-only-retail'},
        {'id':'menu_y','label':'Encoded menu Y','path':['data','menu_position','y'],'type':'integer','state':'read-only-retail'},
        {'id':'discovery_flag','label':'Discovery flag index','path':['data','discovery_flag_index'],'type':'integer','state':'read-only-retail'},
    ]
    worldmap['notes']=['X/Y have a reference menu-pixel interpretation; executing draw and travel consumers remain unverified. Name/discovery consumers are independently qualified. Current values and activation are unobserved.']
    worldmap['actions'].append({'id':'inspect-landmark-destination','label':'Inspect destination source','capability':'worldmap_source_navigation','when':['data','destination_source_label']})
    schema['components']['ProjectSettings']={
        'label':'Project settings','layout':'read-only-properties',
        'properties':[
            {'id':'name','label':'Name','path':['name'],'type':'string','state':'authored-through-command','authoring':{'minimum_length':1,'maximum_length':120,'set_command':'rename_project'}},
            {'id':'path','label':'Project folder','path':['path'],'type':'string','state':'read-only-project'},
            {'id':'disc_path','label':'Retail source','path':['disc_path'],'type':'string','state':'read-only-source'},
            {'id':'disc_identity','label':'Disc identity','path':['disc_identity'],'type':'string','state':'read-only-retail'},
            {'id':'imported_scene_count','label':'Imported scenes','path':['imported_scene_count'],'type':'integer','state':'derived'},
            {'id':'active_scene','label':'Active scene','path':['active_scene'],'type':'asset-reference','state':'derived'},
            {'id':'mode','label':'Mode','path':['mode'],'type':'string','state':'editor-state'},
        ],'actions':[{'id':'rename-project','label':'Rename project…','capability':'project_settings','requires_edit':True}],
        'notes':['Rename changes project metadata and future package identity. Save persists it; Undo restores the previous name. Imported content and authored assets retain their identities.']}
    return schema

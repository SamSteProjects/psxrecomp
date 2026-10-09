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
                       {'id':'preview-allocated-initial-animation','label':'Preview allocated initial animation','capability':'actor_animation_assignment','when':['authored','record_id']},
                       {'id':'edit-actor-animation-glb','label':'Edit assigned clip through GLB','capability':'actor_animation_authoring','requires_edit':True,'when':['authored','record_id']},
                       {'id':'duplicate-allocated-initial-animation','label':'Duplicate assigned clip...','capability':'actor_animation_assignment','requires_edit':True,'when':['authored','record_id']}],
            'details':[{'label':'Retained assignment witness','path':['authored']}],
            'notes':['Manage retained clips to review replacement, content edits or clear the assignment. The native selector resolves during Review and Build.',
                     'Imported source remains separate. Scripts may replace the initial clip; gameplay and playback timing remain unverified.']},
        'Animation':{'label':'Animation channels','layout':'read-only-properties',
            'actions':[{'id':'edit-actor-animation-glb','label':'Edit actor clip through GLB','capability':'actor_animation_authoring','requires_edit':True,'when':['preview_support','supported']},{'id':'preview-scene-animation','label':'Preview imported scene animation','capability':'actor_animation_preview','when':['preview_support','supported']},{'id':'author-animation-channels','label':'Author animation channels','capability':'actor_animation_authoring','requires_edit':True,'when':['preview_support','supported']}],
            'properties':[{'id':'imported_id','label':'Imported ID','path':['imported_id'],'type':'integer','state':'read-only-retail'}],
            'notes':['Timing, live animation state and retargeting are not inferred from an imported association.']}
    },'unknown_component_policy':'read-only-details','live_writes':False}

    for identifier, label, action, note in (
        ('ScriptMovement', 'Authored script movement', 'Inspect movement instructions', 'Encoded X/Z and move-selector overrides do not establish executed paths, height or movement behavior.'),
        ('ScriptFlags', 'Authored script flag operands', 'Inspect flag instructions', 'Encoded flag operands do not establish live variable values, story meaning or executed paths.'),
        ('ScriptWaits', 'Authored script waits', 'Inspect wait instructions', 'Encoded wait operands do not establish runtime cadence or wall-clock durations.'),
        ('ScriptEffectColors', 'Authored effect colors', 'Inspect color instructions', 'Encoded color/intensity operands do not establish host rendering or visual color space.'),
        ('ScriptAnimationOperands', 'Authored animation script operands', 'Inspect animation instructions', 'Encoded model/frame/tween and effect arguments do not resolve clip identities or establish playback.'),
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

    for identifier, label in (
        ('ControllerSystemFlags', 'Controller System Flag Selectors'),
        ('ControllerBranches', 'Controller Branches'),
        ('ControllerTileRects', 'Controller Tile Requests'),
        ('ControllerFades', 'Controller Fades'),
        ('ControllerTableCopies', 'Controller Table Copies'),
        ('ControllerWordTriplets', 'Controller Word Triplets'),
        ('ControllerThreeWords', 'Controller Three Words'),
        ('ControllerSceneBytes', 'Controller Scene-State Bytes'),
        ('ControllerFiveWords', 'Controller Five Words'),
        ('ControllerGlobalBytes', 'Controller Global Bytes'),
        ('ControllerPartySelectors', 'Controller Party Selectors'),
        ('ControllerFlagBits', 'Controller Flag Bits'),
    ):
        schema['components'][identifier] = {
            'label': label, 'layout': 'read-only-properties',
            'properties': [
                {'id': 'authored_instruction_count', 'label': 'Authored Entries', 'path': ['authored_instruction_count'], 'type': 'integer', 'state': 'authored-through-source-editor'},
                {'id': 'source_record_sha256', 'label': 'Retail Record SHA-256', 'path': ['source_record_sha256'], 'type': 'string', 'state': 'read-only-retail'},
            ],
            'actions': [{'id': 'inspect-controller-component', 'label': 'Inspect and Edit Component', 'capability': 'controller_workspace_snapshot', 'requires_edit': True}],
            'details': [{'label': 'Authored Entries by Source Instruction', 'path': ['entries']}],
            'notes': ['Open source controls for separate Retail, Current and Authored values, reviewed edits and component reset. History and native Build are supported; runtime execution and gameplay remain unverified.'],
        }

    flag_bits=schema['components']['ControllerFlagBits']
    flag_bits['actions'][0]['label']='Inspect Component Source'
    flag_bits['notes']=['Project Review/Apply, reset, history and persistence support qualified encoded bit indices. Source comparison is available; native Build delivers qualified bit indices; dedicated editing controls remain pending. Runtime values and gameplay remain unverified.']

    schema['components']['ScriptSystemFlags'] = {
        'label': 'Authored system selectors', 'units': 'Encoded selector indices', 'layout': 'read-only-properties',
        'properties': [{'id': 'authored_instruction_count', 'label': 'Authored instructions', 'path': ['authored_instruction_count'], 'type': 'integer', 'state': 'authored-through-review'}],
        'actions': [{'id': 'inspect-script', 'label': 'Inspect system selectors', 'capability': 'system_selector_authoring'}], 'details': [{'label': 'Reviewed source selector bindings', 'path': ['entries']}],
        'notes': ['Open the source editor for separate Retail/Current selectors and keyed Proposed Review/Apply. History and native Build are supported; no live story values or execution are inferred.'],
    }

    for identifier in ('ScriptFacing', 'ScriptBranches'):
        definition = schema['components'][identifier]
        definition['properties'] = [{'id': 'authored_instruction_count', 'label': 'Authored instructions',
                                     'path': ['authored_instruction_count'], 'type': 'integer',
                                     'state': 'authored-through-source-editor'}]
        definition['actions'].append({'id': 'reset-script-component', 'label': 'Review component reset',
                                      'capability': 'project_navigation', 'requires_edit': True,
                                      'when': ['authored_instruction_count']})

    schema['components']['Dialogue']['properties'] = [
        {'id': 'authored_run_count', 'label': 'Authored text runs', 'path': ['authored_run_count'],
         'type': 'integer', 'state': 'authored-through-source-editor'}]
    schema['components']['Dialogue']['actions'].append(
        {'id': 'reset-script-component', 'label': 'Review component reset',
         'capability': 'project_navigation', 'requires_edit': True, 'when': ['authored_run_count']})
    schema['components']['Transitions'] = {
        'label': 'Authored script transitions', 'units': 'Encoded entry operands', 'layout': 'read-only-properties',
        'properties': [{'id': 'authored_instruction_count', 'label': 'Authored entries',
                        'path': ['authored_instruction_count'], 'type': 'integer', 'state': 'authored-through-source-editor'}],
        'actions': [{'id': 'inspect-script', 'label': 'Inspect transition entries', 'capability': 'actor_script_preview'},
                    {'id': 'reset-script-component', 'label': 'Review component reset',
                     'capability': 'project_navigation', 'requires_edit': True}],
        'details': [{'label': 'Authored transition entries', 'path': ['entries']}],
        'notes': ['Open the qualified source editor for separate retail, authored and effective entry operands. Destination names stay fixed; runtime arrival and transition execution remain unverified.']}

    # Presentation states describe evidence/ownership, never authoring capabilities.
    schema['property_states'] = {
        'read-only-retail': {'label': 'Retail', 'note': 'Imported source value. Read only; authored changes stay separate.'},
        'read-only-source': {'label': 'Source', 'note': 'Bound source input. Read only.'},
        'read-only-project': {'label': 'Project', 'note': 'Project metadata displayed read only here.'},
        'read-only-reference': {'label': 'Reference', 'note': 'SDK reference. Navigation does not imply editing or runtime use.'},
        'derived': {'label': 'Derived', 'note': 'Calculated SDK metadata; not a live measurement.'},
        'effective': {'label': 'Effective', 'note': 'Resolved project value after inheritance and overrides; not a live measurement.'},
        'authored-through-command': {'label': 'Authored', 'note': 'Project value changed only through a supported command.'},
        'authored-through-review': {'label': 'Authored', 'note': 'Project value owned by a source-qualified review workflow.'},
        'authored-through-donor-review': {'label': 'Authored', 'note': 'Project reference owned by a verified donor review.'},
        'authored-through-source-editor': {'label': 'Authored', 'note': 'Project override owned by the qualified source editor.'},
        'live-observed': {'label': 'Live observed', 'note': 'Read-only observation/correlation metadata. Missing values and unconfirmed associations remain unresolved.'},
        'unresolved': {'label': 'Unresolved', 'note': 'This property has no established interpretation or binding. A displayed value does not resolve that uncertainty.'},
        'evidence-status': {'label': 'Evidence', 'note': 'Verification status reported by the SDK; false or unknown is not acceptance.'},
        'editor-state': {'label': 'Editor', 'note': 'Current editor session state; not retail content or an authored game property.'},
        'unsupported': {'label': 'Unsupported', 'note': 'This property has no supported Build representation.'},
    }
    schema['components']['Transform']['layer_states'] = {
        'imported': 'read-only-retail', 'authored': 'authored-through-command', 'effective': 'effective'}
    for identifier in ('ActorAppearance', 'ActorAnimation'):
        for layer in schema['components'][identifier]['layers']:
            layer['state'] = {'imported': 'read-only-retail', 'authored': 'authored-through-review',
                              'base': 'effective', 'effective': 'effective'}[layer['id']]

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
        'controller': ('AssetController', 'Scene Entry Controller', 'scene_controller_inspection', 'inspect-asset-controller', 'Inspect and Edit Controller'),
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
    schema['asset_inspectors']['audio'] = 'AssetAudio'
    controller = schema['components']['AssetController']
    controller['properties'] += [
        {'id':'owner','label':'Owning Scene','path':['data','owner_scene_id'],'type':'asset-reference','state':'read-only-retail'},
        {'id':'entry','label':'Entry PC','path':['data','entry_pc'],'type':'integer','state':'read-only-retail'},
        {'id':'status','label':'Decoder Status','path':['data','inspection_status'],'type':'string','state':'derived'},
        {'id':'flag_reference_count','label':'Encoded Flag References','path':['data','flag_reference_count'],'type':'integer','state':'derived'},
        {'id':'instruction_count','label':'Decoded Instructions','path':['data','decoded_instruction_count'],'type':'integer','state':'derived'}]
    controller['notes'] = ['Retail partition-1 record zero is the scene controller, not a placed actor. Qualified controller families support reviewed authoring, history and native Build. Runtime execution and gameplay remain unverified.']
    schema['components']['AssetAudio'] = {
        'label': 'Source audio resource', 'layout': 'read-only-properties',
        'properties': [
            {'id': 'id', 'label': 'Stable ID', 'path': ['id'], 'type': 'asset-reference', 'state': 'derived'},
            {'id': 'format', 'label': 'Source format', 'path': ['data','format'], 'type': 'string', 'state': 'read-only-retail'},
            {'id': 'programs', 'label': 'Declared programs', 'path': ['data','bank','program_count'], 'type': 'number', 'nullable': True, 'state': 'read-only-retail'},
            {'id': 'samples', 'label': 'Declared samples', 'path': ['data','bank','sample_count'], 'type': 'number', 'nullable': True, 'state': 'read-only-retail'},
            {'id': 'ppqn', 'label': 'Declared ticks per quarter', 'path': ['data','sequence','ppqn'], 'type': 'number', 'nullable': True, 'state': 'read-only-retail'},
            {'id': 'tempo', 'label': 'Initial microseconds per quarter', 'path': ['data','sequence','initial_tempo_us_per_quarter'], 'type': 'number', 'nullable': True, 'state': 'read-only-retail'},
            {'id': 'complete', 'label': 'Declared bank byte extent complete', 'path': ['data','declared_bank_complete'], 'type': 'boolean', 'nullable': True, 'state': 'derived'},
            {'id': 'container', 'label': 'Supported container validated', 'path': ['data','container_validated'], 'type': 'boolean', 'state': 'derived'},
            {'id': 'bank_tables', 'label': 'Bank table coverage', 'path': ['data','bank_inspection','status'], 'type': 'string', 'state': 'derived'},
            {'id': 'assignment', 'label': 'Playback assignment', 'path': ['data','playback_assignment'], 'type': 'string', 'state': 'derived'},
        ],
        'notes': ['Header/container evidence only. Scene membership does not establish playback. Events, samples, duration and runtime use remain unverified.'],
        'actions': [{'id':'inspect-midi-input','label':'Inspect retained MIDI input','capability':'resource_catalog'}, {'id':'inspect-audio-input','label':'Inspect retained WAV input','capability':'resource_catalog'}, {'id':'inspect-audio-bank','label':'Inspect bank tables','capability':'resource_catalog'}, {'id':'edit-sequence-replacement','label':'Edit sequence replacement','capability':'resource_catalog','when':['data','sequence']}, {'id':'inspect-audio-sequence','label':'Inspect sequence events','capability':'resource_catalog','when':['data','sequence']}],
    }
    schema['components']['AssetTrigger']['actions'].append({'id': 'inspect-asset-trigger-cells', 'label': 'Edit trigger cell', 'capability': 'field_trigger_authoring'})
    schema['components']['AssetTrigger']['actions'].append({'id': 'inspect-asset-trigger-scripts', 'label': 'Edit trigger script binding', 'capability': 'field_trigger_script_authoring'})
    schema['components']['AssetTrigger']['actions'].append({'id':'inspect-asset-trigger-group','label':'Move trigger cell group','capability':'field_trigger_authoring'})
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
    schema['components']['EnvironmentPlacement']={
        'label':'Environment placement','layout':'read-only-properties',
        'properties':[
            {'id':'identity','label':'Identity','path':['entity_id'],'type':'entity-reference','state':'read-only-retail'},
            {'id':'model','label':'Model','path':['asset_id'],'type':'asset-reference','state':'read-only-retail'},
            {'id':'renderable','label':'Renderable','path':['renderable'],'type':'boolean','state':'derived'},
            {'id':'pose','label':'Preview pose','path':['pose_kind'],'fallback_paths':[['reason']],'type':'string','state':'derived'},
            {'id':'authored','label':'Authored transform in preview','path':['authored_transform'],'type':'boolean','state':'effective'},
        ],'notes':['Source placement identities and preview poses do not establish runtime visibility or script-driven transforms.']}
    for identifier,label,path,state in (
            ('EnvironmentRetailTransform','Retail transform',['source_record','imported_transform'],'read-only-retail'),
            ('EnvironmentPreviewTransform','Current preview transform',['effective_transform'],'effective')):
        schema['components'][identifier]={
            'label':label,'units':'Scene coordinates / PSX angle units','layout':'read-only-properties',
            'properties':[
                {'id':field+'_'+axis,'label':('Position ' if field=='position' else 'Rotation ')+axis.upper(),
                 'path':path+[field,axis],'type':'number','nullable':True,'state':state}
                for field in ('position','rotation_psx') for axis in ('x','y','z')],
            'notes':['4096 PSX angle units equal one turn. These are SDK source/preview coordinates, not sampled runtime transforms.',
                     'Missing values remain unknown. A pending preview refresh leaves the last preview snapshot visible; no current-source acceptance is inferred.']}
    schema['components']['EnvironmentMetadata']={
        'label':'Source and bindings','layout':'read-only-properties',
        'properties':[
            {'id':'map_hash','label':'Imported MAP SHA256','path':['source_record','source_record','map_sha256'],'type':'string','state':'read-only-retail'},
            {'id':'record','label':'Placement record index','path':['source_record','object_record_index'],'type':'integer','state':'read-only-retail'},
            {'id':'grid_byte','label':'MAP grid byte offset','path':['source_record','source_record','grid_byte_offset'],'type':'integer','state':'read-only-retail'},
        ],'details':[{'label':'Placement source record','path':['source_record']},{'label':'Decoder evidence','path':['evidence']}],
        'notes':['Source indices and offsets retain their decoder coordinate spaces. Shared and individual edits remain in the source-qualified transform tools; collision is separate.']}
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
    schema['authored_asset_inspectors']={'npc_draft':'AssetNpcDraft'}
    schema['components']['AssetNpcDraft']={
        'label':'Authored NPC draft asset','units':'Project-local donor candidate','layout':'read-only-properties',
        'properties':[
            {'id':'id','label':'Authored identity','path':['id'],'type':'entity-reference','state':'read-only-project'},
            {'id':'name','label':'Name','path':['authoredRecord','name'],'type':'string','state':'authored-through-command'},
            {'id':'scene','label':'Project scene','path':['authoredRecord','scene_id'],'type':'asset-reference','state':'read-only-project'},
            {'id':'donor','label':'Retail donor binding','path':['authoredRecord','donor_entity_id'],'type':'entity-reference','state':'authored-through-command'},
            {'id':'appearance-witness','label':'Independent initial appearance','path':['authoredRecord','authored','appearance','donor_entity_id'],'type':'entity-reference','state':'authored-through-command','empty_label':'Script donor initial appearance'},
            {'id':'model','label':'Recorded donor model','path':['authoredRecord','model_reference','target_id'],'type':'asset-reference','state':'read-only-reference','empty_label':'Unresolved donor model'},
            *[{'id':axis,'label':'Authored '+axis.upper(),'path':['authoredRecord','authored','position',axis],
               'type':'number','state':'authored-through-command'} for axis in ('x','z')]],
        'actions':[{'id':'select-asset-actor','label':'Select NPC draft','capability':'project_navigation'},
                   {'id':'edit-npc-appearance','label':'Choose NPC initial appearance','capability':'actor_appearance',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-branches','label':'Edit NPC script branches','capability':'actor_branch_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-model-selectors','label':'Edit NPC script model selectors','capability':'actor_model_selector_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-flags','label':'Edit NPC script flags','capability':'actor_flag_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-facing','label':'Edit NPC script facing','capability':'actor_facing_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-movement','label':'Edit NPC script movement','capability':'actor_movement_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-waits','label':'Edit NPC wait targets','capability':'actor_wait_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'edit-npc-dialogue','label':'Edit NPC dialogue','capability':'actor_dialogue_authoring',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'inspect-npc-build-script','label':'Inspect saved Build script','capability':'actor_script_preview',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'inspect-npc-current-script','label':'Inspect Current NPC script','capability':'actor_script_preview',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'inspect-npc-donor-script','label':'Inspect retail donor script','capability':'actor_script_preview',
                    'when':['authoredRecord','donor_entity_id']},
                   {'id':'inspect-npc-donor-model','label':'Inspect recorded donor model','capability':'model_preview',
                    'when':['authoredRecord','model_reference','target_id']}],
        'notes':['This is authored project metadata, not an imported retail actor placement or a confirmed runtime identity.',
                 'The scene and donor references preserve their SDK identities. Preview/model/script behavior comes from separate qualified tools.',
                 'The recorded initial model assignment uses the script donor or a separately qualified retail appearance witness; imported actor overrides remain separate. It does not prove runtime residency or pose.',
                 'Use Review Build for the complete project candidate. A browsable draft does not establish runtime spawning, visibility or gameplay.']}
    schema['components']['NpcDraftIdentity']={
        'label':'NPC draft identity','layout':'read-only-properties',
        'properties':[
            {'id':'identity','label':'Authored identity','path':['entity_id'],'type':'entity-reference','state':'read-only-project'},
            {'id':'name','label':'Name','path':['draft','name'],'type':'string','state':'authored-through-command'},
            {'id':'scene','label':'Scene','path':['draft','scene_id'],'type':'asset-reference','state':'read-only-project'},
            {'id':'donor','label':'Retail donor binding','path':['draft','donor_entity_id'],'type':'entity-reference','state':'authored-through-command'}],
        'details':[{'label':'Donor retail metadata','path':['donor','components','RetailMetadata']}],
        'notes':['This project-local draft has no retail placement or established runtime identity. The donor source remains separate.',
                 'Preview uses the retail donor assignment; shared authored assets may affect appearance. Runtime creation and gameplay remain unverified.']}
    schema['components']['NpcDraftTransform']={
        'label':'Authored NPC draft placement','units':'Guest scene coordinates','layout':'read-only-properties',
        'properties':[{'id':axis,'label':'Authored '+axis.upper(),'path':['draft','position',axis],
                       'type':'number','state':'authored-through-command'} for axis in ('x','z')],
        'notes':['X/Z authoring uses supported project commands on the exact64-unit retail grid, from64 through16384.',
                 'This draft does not author Y. Sampled source terrain height is preview metadata, not authored or live placement.']}
    schema['components']['NpcDraftPreview']={
        'label':'NPC draft preview snapshot','units':'Guest coordinates / sampled source elevation','layout':'read-only-properties',
        'properties':[
            *[{'id':'position_'+axis,'label':'Snapshot '+axis.upper(),'path':['preview','position',axis],
               'type':'number','nullable':True,'state':'unresolved' if axis=='y' else 'effective'} for axis in ('x','y','z')],
            {'id':'surface_y','label':'Preview elevation Y','path':['preview','preview_position','y'],'type':'number','nullable':True,'state':'derived'},
            {'id':'height_status','label':'Height resolution','path':['preview','preview_height_status'],'type':'string','state':'derived'},
            {'id':'model','label':'Preview model','path':['preview','asset_id'],'type':'asset-reference','state':'effective'},
            {'id':'pose','label':'Preview pose kind','path':['preview','pose_kind'],'type':'string','state':'derived'},
            {'id':'renderable','label':'Geometry available','path':['preview','renderable'],'type':'boolean','state':'evidence-status'}],
        'details':[{'label':'Preview evidence','path':['preview','evidence']}],
        'notes':['Missing snapshot values remain unknown; authored position and donor metadata are not substituted.',
                 'A sampled pose does not establish an idle stance, runtime playback, spawning or collision.']}
    script_actions=[
        {'id':'edit-npc-'+suffix,'label':label,'capability':capability,'requires_edit':True,
         'when':['draft','donor_entity_id']}
        for suffix,label,capability in [
            ('dialogue','Edit NPC dialogue...','actor_dialogue_authoring'),
            ('facing','Edit NPC script facing...','actor_facing_authoring'),
            ('model-selectors','Edit NPC script model selectors...','actor_model_selector_authoring'),
            ('flags','Edit NPC script flags...','actor_flag_authoring'),
            ('system-flags','Edit NPC system selectors...','npc_system_selector_authoring'),
            ('branches','Edit NPC script branches...','actor_branch_authoring'),
            ('effect-colors','Edit NPC effect colors...','actor_effect_color_authoring'),
            ('animation-operands','Edit NPC Animation Arguments...','npc_animation_operand_authoring'),
            ('transitions','Edit NPC transition arrivals...','npc_transition_authoring'),
            ('waits','Edit NPC wait targets...','actor_wait_authoring'),
            ('movement','Edit NPC script movement...','actor_movement_authoring')]]
    script_actions += [
        {'id':'reset-npc-script','label':'Reset NPC-owned script edits...','capability':'npc_script_reset','requires_edit':True,'when':['draft','donor_entity_id']},
        {'id':'inspect-npc-build-script','label':'Inspect saved Build script...','capability':'actor_script_preview','when':['draft','donor_entity_id']},
        {'id':'inspect-npc-current-script','label':'Inspect Current NPC script...','capability':'actor_script_preview','when':['draft','donor_entity_id']},
        {'id':'inspect-npc-donor-script','label':'Inspect retail donor script...','capability':'actor_script_preview','when':['draft','donor_entity_id']}]
    from .npc_script_binding import FAMILIES
    schema['components']['NpcDraftScriptBinding']={
        'label':'NPC script ownership','layout':'read-only-properties',
        'properties':[
            {'id':'source-script','label':'Retail donor script identity','path':['scriptBinding','source_script_id'],'type':'asset-reference','state':'read-only-reference'},
            {'id':'authored-digest','label':'Authored NPC SHA-256','path':['scriptBinding','authored_draft_sha256'],'type':'string','state':'derived'},
            *[{'id':family,'label':'Own '+family.replace('_',' ')+' targets','path':['scriptBinding','authored_counts',family],
               'type':'integer','state':'authored-through-command'} for family in FAMILIES]],
        'actions':script_actions,
        'details':[{'label':'Authored '+family.replace('_',' ')+' bindings','path':['draft',family]} for family in FAMILIES],
        'notes':['Counts describe project-local NPC overrides; zero inherits the cloned donor span. Source instructions must be qualified in their dedicated tool.',
                 'Retail source identity, authored metadata and saved generated script are separate. No runtime identity, execution, visibility or effect is inferred.',
                 'Review each family before Apply. Use saved Build comparison for emitted bytes; clearing one family leaves other owned edits intact.']}
    asset_actions=schema['components']['AssetNpcDraft']['actions']
    asset_actions.append({'id':'edit-npc-animation-operands','label':'Edit NPC Animation Arguments','capability':'npc_animation_operand_authoring','when':['authoredRecord','donor_entity_id']})
    asset_actions.append({'id':'edit-npc-transitions','label':'Edit NPC Transition Arrivals','capability':'npc_transition_authoring','when':['authoredRecord','donor_entity_id']})
    asset_actions.insert(next(i for i,a in enumerate(asset_actions) if a['id']=='edit-npc-flags'),
        {'id':'edit-npc-effect-colors','label':'Edit NPC effect colors','capability':'actor_effect_color_authoring',
         'when':['authoredRecord','donor_entity_id']})
    asset_actions.append({'id':'edit-npc-system-flags','label':'Edit NPC system selectors','capability':'npc_system_selector_authoring','when':['authoredRecord','donor_entity_id']})
    asset_actions.append({'id':'reset-npc-script','label':'Reset NPC-owned script edits','capability':'npc_script_reset','when':['authoredRecord','donor_entity_id']})
    return schema

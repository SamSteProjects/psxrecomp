"""Editor property contracts; authoring validation still belongs to ProjectService."""

def inspector_schema():
    return {'schema_version':'legaia.inspector-schema.v1','components':{
        'Transform':{'label':'Transform','units':'Scene units','layout':'layered-number',
            'layers':['imported','authored','effective'],
            'properties':[{'id':axis,'label':axis.upper(),'path':['position',axis],
                'type':'number','nullable':True,'authoring':{'minimum':-32767,'maximum':32767,'step':'any','set_command':'set_transform','clear_command':'clear_transform'},
                'retail_status':'unresolved' if axis=='y' else 'imported',
                'build':{'supported':axis!='y',**({'minimum':64,'maximum':16384,'step':64} if axis!='y' else {}),
                         'note':'Project-only height; clear before Build' if axis=='y' else 'Build requires a representable64-unit retail placement'}} for axis in ('x','y','z')],
            'notes':['Empty authored fields inherit imported values. Authoring bounds and Build encoding bounds are separate.',
                     'Unknown heights use source terrain for preview when available, otherwise the ground plane. Display axes use the SDK conversion.']},
        'ModelRenderer':{'label':'Model renderer','layout':'read-only-properties',
            'properties':[{'id':'asset_id','label':'Asset','path':['asset_id'],'type':'asset-reference','state':'read-only-retail'},
                          {'id':'resolution_status','label':'Resolution','path':['resolution_status'],'type':'string','state':'derived'}]},
        'Animation':{'label':'Animation','layout':'read-only-properties',
            'properties':[{'id':'imported_id','label':'Imported ID','path':['imported_id'],'type':'integer','state':'read-only-retail'}],
            'notes':['Timing, live animation state and retargeting are not inferred from an imported association.']}
    },'unknown_component_policy':'read-only-details','live_writes':False}

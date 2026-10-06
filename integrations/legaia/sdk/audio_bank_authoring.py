"""Source-qualified VAB metadata, atomic commands and native bank delivery."""
from copy import deepcopy,copy
from hashlib import sha256
from importer.audio_bank import read_audio_bank,bank_from_entry,inspect_bank
from importer.audio_bank_authoring import replace_audio_bank_parameters,MAX_EDITS
from importer.pipeline import _disc_context
from .project import ProjectError,digest
from .audio_authoring import source_key

COMMANDS={'set_audio_bank_parameters','clear_audio_bank_parameters'}
MAX_ASSETS=128
# Independent explicit native reader/build spans, reviewed against the pinned
# parser; no offsets are accepted from command metadata.
SPANS={
 'header':{'master_volume':(24,1,False),'pan':(25,1,False),'attributes1':(26,1,False),'attributes2':(27,1,False)},
 'program':{'volume':(1,1,False),'priority':(2,1,False),'mode':(3,1,False),'pan':(4,1,False),'attributes':(6,2,False)},
 'tone':{'priority':(0,1,False),'mode':(1,1,False),'volume':(2,1,False),'pan':(3,1,False),
         'center':(4,1,False),'shift':(5,1,False),'minimum_key':(6,1,False),'maximum_key':(7,1,False),
         'vibrato_width':(8,1,False),'vibrato_time':(9,1,False),'portamento_width':(10,1,False),
         'portamento_time':(11,1,False),'pitch_bend_down':(12,1,False),'pitch_bend_up':(13,1,False),
         'adsr1':(16,2,False),'adsr2':(18,2,False),'program_operand':(20,2,True),'sample_operand':(22,2,True)}}


def _hash(body):return sha256(body).hexdigest()


def _source(project,identifier,entry_hash,scene_id):
    from .resources import _verify
    if not isinstance(scene_id,str) or scene_id not in project.imports or not project.disc_path:
        raise ProjectError('Bank edits require a verified imported source scene and retail disc')
    with _disc_context(project.disc_path) as (image,_,_,archive):
        _verify(project,project.imports[scene_id])
        report=read_audio_bank(project.disc_path,identifier,entry_hash)
        record=report['source_record']
        body=image.read_user(archive.node.extent_lba,record['entry_byte_offset'],record['entry_size_bytes'],archive.node.size)
        if _hash(body)!=entry_hash:raise ProjectError('Bank carrier changed during source qualification')
    bank,_,_=bank_from_entry(body)
    return body,bank,record


def _rows(bank):
    report=inspect_bank(bank);rows=[]
    for section,records in (('header',[dict(offset=0)]),('program',report['programs']),('tone',report['tones'])):
        for row in records:
            identity=({'slot':row['slot']} if section=='program' else {'page':row['page'],'index':row['index']} if section=='tone' else {})
            for field,(relative,width,signed) in SPANS[section].items():
                at=row['offset']+relative
                rows.append(dict(section=section,field=field,**identity,bank_byte_offset=at,byte_length=width,signed=signed,
                                 value=int.from_bytes(bank[at:at+width],'little',signed=signed)))
    return rows


def _identity(edit):return tuple(edit.get(k) for k in ('section','slot','page','index','field'))


def _normalise(bank,edits):
    rows={_identity(r):r for r in _rows(bank)}
    return [deepcopy(e) for e in sorted(edits,key=lambda e:rows[_identity(e)]['bank_byte_offset'])
            if e['value']!=rows[_identity(e)]['value']]


def _profile(bank):
    report=inspect_bank(bank)
    return dict(bank_sha256=_hash(bank),header=report['header'],sections=report['sections'],
                used_program_slots=report['used_program_slots'],sample_count=len(report['samples']),
                parameters=_rows(bank),limitations=[
                  'Integer ranges are encoded widths, not runtime enums or audible effect validation.',
                  'Program slots and packed tone pages are distinct; sample/program operands do not establish an instrument assignment.',
                  'Counts, sample bodies, reserved bytes and allocation remain source-owned.'])


def read(project,identifier,binding):
    if (not isinstance(binding,dict) or set(binding)!={'format','source_scene_id','source_record','edits'}
            or binding['format']!='vab-parameters-v1' or not isinstance(binding['source_record'],dict)):
        raise ProjectError('Invalid source-qualified VAB parameter binding')
    body,bank,record=_source(project,identifier,binding['source_record'].get('entry_sha256'),binding['source_scene_id'])
    if record!=binding['source_record']:raise ProjectError('Saved bank source ownership differs from retail')
    candidate,audit=replace_audio_bank_parameters(body,body,expected_source_sha256=_hash(body),
        expected_current_sha256=_hash(body),edits=binding['edits'])
    canonical=_normalise(bank,binding['edits'])
    if not canonical or canonical!=binding['edits']:raise ProjectError('Bank bindings require sorted unique nonretail parameters')
    return body,candidate,record,audit


def validate_collection(project):
    if not isinstance(project.audio_bank_overrides,dict) or len(project.audio_bank_overrides)>MAX_ASSETS:
        raise ProjectError('Bank overrides must be a bounded resource mapping')
    for identifier,binding in project.audio_bank_overrides.items():read(project,identifier,binding)


def _current(project,identifier,entry_hash):
    from .audio_composition import read_entry
    body,bank,record=_source(project,identifier,entry_hash,project.active_scene)
    current=read_entry(project,identifier,body)
    return body,current,bank,record,project.audio_bank_overrides.get(identifier)


def options(project,asset_id,expected_entry_sha256,expected_source_key):
    from .scene_preview import source_key as resource_key
    if expected_source_key!=resource_key(project):raise ProjectError('Bank resource source changed; refresh resources')
    key=source_key(project);body,current,bank,record,binding=_current(project,asset_id,expected_entry_sha256)
    effective,_,_=bank_from_entry(current)
    if key!=source_key(project):raise ProjectError('Bank authored state changed during inspection')
    return dict(schema_version='legaia.audio-bank-authoring.v1',asset_id=asset_id,scene_id=project.active_scene,
                source_key=expected_source_key,authoring_key=key,source_record=record,
                current_entry_sha256=_hash(current),binding_source_scene_id=binding['source_scene_id'] if binding else project.active_scene,
                sequence_authored=asset_id in project.audio_overrides,
                authored_edits=deepcopy(binding['edits']) if binding else [],retail=_profile(bank),current=_profile(effective),
                max_edits=MAX_EDITS,project_changed=False,runtime_state='not_observed')


def review(project,asset_id,expected_entry_sha256,expected_authoring_key,edits):
    if project.mode!='edit' or expected_authoring_key!=source_key(project):
        raise ProjectError('Bank inputs changed or are not in Edit mode; inspect again')
    body,current,bank,record,binding=_current(project,asset_id,expected_entry_sha256)
    effective,pieces,_=bank_from_entry(current)
    isolated=bytearray(body)
    for p in pieces:isolated[p['entry_offset']:p['entry_offset']+p['size_bytes']]=effective[p['bank_offset']:p['bank_offset']+p['size_bytes']]
    changed,audit=replace_audio_bank_parameters(body,bytes(isolated),expected_source_sha256=_hash(body),
        expected_current_sha256=_hash(bytes(isolated)),edits=edits)
    candidate=bytearray(current)
    for p in pieces:candidate[p['entry_offset']:p['entry_offset']+p['size_bytes']]=changed[p['entry_offset']:p['entry_offset']+p['size_bytes']]
    candidate=bytes(candidate);audit.update(before_entry_sha256=_hash(current),after_entry_sha256=_hash(candidate))
    merged={_identity(e):deepcopy(e) for e in (binding['edits'] if binding else [])}
    merged.update({_identity(e):deepcopy(e) for e in edits})
    final=_normalise(bank,list(merged.values()))
    if len(final)>MAX_EDITS:raise ProjectError('Bank exceeds 256 authored scalar parameters')
    after=(dict(format='vab-parameters-v1',source_scene_id=binding['source_scene_id'] if binding else project.active_scene,
                source_record=record,edits=final) if final else None)
    from .audio_composition import read_entry
    view=copy(project);view.audio_bank_overrides=deepcopy(project.audio_bank_overrides)
    if after:view.audio_bank_overrides[asset_id]=after
    else:view.audio_bank_overrides.pop(asset_id,None)
    if read_entry(view,asset_id,body)!=candidate:raise ProjectError('Proposed bank parameters differ from full audio reconstruction')
    if source_key(project)!=expected_authoring_key:raise ProjectError('Bank state changed during review')
    result=dict(schema_version='legaia.audio-bank-review.v1',asset_id=asset_id,authoring_key=expected_authoring_key,
                source_record=record,proposed_binding=after,native_audit=audit,no_change=current==candidate,
                project_changed=False,runtime_state='not_observed')
    result['review_key']=digest(result);return result


def command(project,value):
    kind=value.get('type');fields={'type','asset_id','expected_entry_sha256','expected_authoring_key'}
    if kind=='set_audio_bank_parameters':fields|={'edits','review_key'}
    elif kind!='clear_audio_bank_parameters':raise ProjectError('Unsupported bank parameter command')
    if set(value)!=fields:raise ProjectError('Bank commands require exact source and reviewed freshness fields')
    identifier=value['asset_id'];before=deepcopy(project.audio_bank_overrides.get(identifier)) if isinstance(identifier,str) else None
    if kind=='set_audio_bank_parameters':
        report=review(project,identifier,value['expected_entry_sha256'],value['expected_authoring_key'],value['edits'])
        if report['review_key']!=value['review_key']:raise ProjectError('Bank parameters differ from reviewed proposal')
        after=report['proposed_binding']
    else:
        if project.mode!='edit' or value['expected_authoring_key']!=source_key(project):raise ProjectError('Bank inputs changed; inspect before clearing')
        _current(project,identifier,value['expected_entry_sha256'])
        if value['expected_authoring_key']!=source_key(project):raise ProjectError('Bank state changed while clearing')
        after=None
    if before==after:return
    if after is not None and before is None and len(project.audio_bank_overrides)>=MAX_ASSETS:raise ProjectError('Bank override budget reached')
    if after is None:project.audio_bank_overrides.pop(identifier,None)
    else:project.audio_bank_overrides[identifier]=deepcopy(after)
    project.undo_stack.append(dict(target='audio_bank_overrides',asset_id=identifier,before=before,after=deepcopy(after)));project.redo_stack.clear()


def prepare_overlays(project,image,archive):
    validate_collection(project);overlays=[];changes=[]
    for identifier,binding in sorted(project.audio_bank_overrides.items()):
        body,candidate,record,_=read(project,identifier,binding)
        bank,pieces,_=bank_from_entry(body);rows={_identity(r):r for r in _rows(bank)};expected=bytearray(body)
        for edit in binding['edits']:
            row=rows[_identity(edit)];at=row['bank_byte_offset'];width=row['byte_length'];signed=row['signed']
            owners=[p for p in pieces if p['bank_offset']<=at and at+width<=p['bank_offset']+p['size_bytes']]
            if len(owners)!=1:raise ProjectError('Bank parameter has no unique native carrier owner')
            owner=owners[0];position=owner['entry_offset']+at-owner['bank_offset']
            expected[position:position+width]=edit['value'].to_bytes(width,'little',signed=signed)
            changes.append(dict(scene='global-audio',semantic_id=identifier,scope='audio-VAB-fixed-parameters-only',
                field='audio.vab.'+edit['section']+'.'+edit['field'],before_value=row['value'],after_value=edit['value'],
                bank_byte_offset=at,entry_byte_offset=position,byte_length=width,signed=signed,
                **{k:edit[k] for k in ('slot','page','index') if k in edit},
                source_entry_sha256=_hash(body),candidate_entry_sha256=_hash(candidate)))
        if candidate!=bytes(expected):raise ProjectError('Bank serializer changed bytes outside independently encoded parameters')
        offset=archive.node.extent_lba*2048+record['entry_byte_offset']
        if image.read_user(0,offset,len(body),image.size//2352*2048)!=body:raise ProjectError('Bank physical PROT/disc extent changed')
        overlays.append(dict(scene='global-audio',source_kind='raw_PROT_VAB',iso_file='PROT.DAT',
            prot_entry_index=record['prot_entry_index'],entry_byte_offset=record['entry_byte_offset'],offset=offset,size=len(candidate),
            file=f"assets/audio-bank-{record['prot_entry_index']:04d}.bin",payload=candidate,
            sha256=_hash(candidate),expected_sha256=_hash(body)))
    return overlays,changes

"""One native audio entry from independently qualified bank/SEQ operands."""
from hashlib import sha256
from .project import ProjectError


def _hash(body):return sha256(body).hexdigest()


def merge(original, candidates):
    """Check exact audited byte ownership before merging family replacements."""
    output=bytearray(original);occupied=set()
    for kind,candidate,audit in candidates:
        if (len(candidate)!=len(original) or audit['source_entry_sha256']!=_hash(original)
                or audit['before_entry_sha256']!=_hash(original) or audit['after_entry_sha256']!=_hash(candidate)):
            raise ProjectError('Audio family differs from its common retail entry')
        changed=[i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b]
        if changed!=audit['changed_entry_byte_offsets'] or occupied.intersection(changed):
            raise ProjectError('Audio family has unaudited or overlapping changed bytes')
        for i in changed:output[i]=candidate[i]
        occupied.update(changed)
    return bytes(output)


def read_entry(project, identifier, original=None):
    from .audio_authoring import read as read_sequence
    from .audio_bank_authoring import read as read_bank
    from .audio_sample_authoring import read as read_samples
    candidates=[];replacement_sequence=None
    if identifier in project.audio_sequence_replacements:
        from .sequence_replacement_authoring import read
        source,replacement_sequence,_=read(project,identifier,project.audio_sequence_replacements[identifier])
        if original is None:original=source
        elif original!=source:raise ProjectError('Replacement audio differs from its common retail carrier')
    allocated=project.audio_sample_overrides.get(identifier,{}).get('format')=='sample-wav-allocated-v1'
    if allocated:
        from .audio_sample_allocation import _qualified
        source=_qualified(project,identifier,project.audio_sample_overrides[identifier])[0]
        if original is None:original=source
        elif original!=source:raise ProjectError('Allocated audio differs from its common Retail carrier')
    for kind,collection,reader in (('sequence',project.audio_overrides,read_sequence),
                                   ('bank',project.audio_bank_overrides,read_bank),
                                   ('samples',project.audio_sample_overrides,read_samples)):
        binding=collection.get(identifier)
        if binding is None:continue
        if kind=='samples' and allocated:continue
        source,candidate,_,audit=reader(project,identifier,binding)
        if original is None:original=source
        elif original!=source:raise ProjectError('Audio families no longer share the same physical source entry')
        candidates.append((kind,candidate,audit))
    if original is None:raise ProjectError('Choose a source-qualified authored audio resource')
    output=merge(original,candidates)
    if allocated:
        from .audio_sample_allocation import compose
        output=compose(project,identifier,project.audio_sample_overrides[identifier],output)[1]
    if replacement_sequence is not None:
        from importer.audio_sequence_replacement import insert_sequence
        output=insert_sequence(output,replacement_sequence)
    return output


def prepare_overlays(project,image,archive):
    if any(v.get('format')=='sample-wav-allocated-v1' for v in project.audio_sample_overrides.values()):
        raise ProjectError('Allocated audio needs native resource preparation, not fixed-span overlays')
    from .audio_authoring import prepare_overlays as sequence_overlays
    from .audio_bank_authoring import prepare_overlays as bank_overlays
    seq,seq_changes=sequence_overlays(project,image,archive)
    banks,bank_changes=bank_overlays(project,image,archive)
    from .audio_sample_authoring import prepare_overlays as sample_overlays
    samples,sample_changes=sample_overlays(project,image,archive)
    groups={}
    for kind,items in (('sequence',seq),('bank',banks),('samples',samples)):
        for overlay in items:groups.setdefault(overlay['prot_entry_index'],[]).append((kind,overlay))
    result=[];changes=seq_changes+bank_changes+sample_changes
    for index,items in sorted(groups.items()):
        first=items[0][1];offset,size=first['offset'],first['size']
        original=image.read_user(0,offset,size,image.size//2352*2048)
        candidates=[]
        for kind,overlay in items:
            if (overlay['offset'],overlay['size'],overlay['expected_sha256'])!=(offset,size,_hash(original)):
                raise ProjectError('Audio overlay families have mismatched physical ownership')
            payload=overlay['payload']
            # Each family preparation already independently qualified every
            # field span. Recheck full entry bytes and common source here.
            candidates.append((kind,payload,dict(source_entry_sha256=_hash(original),
                before_entry_sha256=_hash(original),after_entry_sha256=overlay['sha256'],
                changed_entry_byte_offsets=[i for i,(a,b) in enumerate(zip(original,payload)) if a!=b])))
        candidate=merge(original,candidates)
        overlay=dict(first,payload=candidate,sha256=_hash(candidate))
        if len(items)>1:
            overlay.update(source_kind='raw_PROT_audio_operands',file=f'assets/audio-operands-{index:04d}.bin')
        result.append(overlay)
        if len(items)>1:
            for change in changes:
                if change['semantic_id']==f'audio://legaia/prot/{index:04d}':
                    change['candidate_entry_sha256']=_hash(candidate)
    return result,changes


def _prepare_native_base(project,image,archive):
    """Fixed families keep overlays; allocated owners deliver complete native resources."""
    from copy import copy,deepcopy
    import struct
    from .audio_sample_allocation import FORMAT,read,selected,_receipt
    from .audio_sample_authoring import _independent_pcm
    from importer.audio_bank import bank_from_entry,inspect_bank
    from importer.audio_sample_authoring import read_pcm_wav
    allocated={identifier:binding for identifier,binding in project.audio_sample_overrides.items() if binding['format']==FORMAT}
    if not allocated:
        overlays,changes=prepare_overlays(project,image,archive);return overlays,changes,[]
    view=copy(project);view.audio_sample_overrides={k:deepcopy(v) for k,v in project.audio_sample_overrides.items() if k not in allocated}
    overlays,changes=prepare_overlays(view,image,archive);requests=[]
    for identifier,binding in sorted(allocated.items()):
        body,_,record,audit=read(project,identifier,binding);candidate=read_entry(project,identifier,body)
        index=record['prot_entry_index'];owned=[row for row in overlays if row['prot_entry_index']==index]
        baseline=merge(body,[(row['source_kind'],row['payload'],dict(source_entry_sha256=_hash(body),before_entry_sha256=_hash(body),
            after_entry_sha256=row['sha256'],changed_entry_byte_offsets=[i for i,(a,b) in enumerate(zip(body,row['payload'])) if a!=b])) for row in owned])
        bank,pieces,kind=bank_from_entry(baseline);source_report=inspect_bank(bank);actual_bank,_,actual_kind=bank_from_entry(candidate)
        encoded_rows={};source_bank=bank_from_entry(body)[0]
        for row,proof in zip(binding['samples'],audit['samples']):
            sample_index=row['sample_index'];source,source_at,raw=selected(body,sample_index);current,current_at,encoded=selected(candidate,sample_index)
            receipt,wav=_receipt(project,identifier,sample_index,row['receipt_key'],record,source_bank)
            n=proof['sample'];blocks=n['encoded_blocks'];pcm,rate=read_pcm_wav(wav,blocks*28)
            targets=struct.unpack('<'+str(blocks*28)+'h',pcm);values=_independent_pcm(encoded,blocks);decoded=struct.pack('<'+str(len(values))+'h',*values)
            errors=[a-b for a,b in zip(targets,values)]
            if (_hash(encoded)!=receipt['candidate_sample_sha256'] or _hash(decoded)!=n['decoded_pcm_sha256']
                    or _hash(pcm)!=n['input_pcm_sha256'] or rate!=n['input_wav_rate']
                    or sum(v*v for v in errors)!=n['sum_squared_error'] or max(map(abs,errors))!=n['maximum_absolute_error']):
                raise ProjectError('Allocated native sample failed independent PCM, retained input or error qualification')
            if proof['allocation']:
                source_consumed=n['source_decoded_frames']//28*16;starts=n['preserved_start_blocks']
                flags=bytes(1 if i==blocks-1 else 4 if i in starts else 0 for i in range(blocks))
                if encoded[1:blocks*16:16]!=flags or encoded[blocks*16:]!=raw[source_consumed:]:
                    raise ProjectError('Allocated native sample changed qualified start/end flags or source tail')
            elif encoded[1:blocks*16:16]!=raw[1:blocks*16:16] or encoded[blocks*16:]!=raw[blocks*16:]:
                raise ProjectError('Fixed native sample changed its source flags or tail during allocation')
            encoded_rows[sample_index]=encoded
            changes.append(dict(scene='global-audio',semantic_id=identifier,scope='audio-SPU-sample-allocation',field='audio.sample.allocation',
                before_value=source['source_sha256'],after_value=_hash(encoded),sample_index=sample_index,
                source_sample_entry_byte_offset=source_at,sample_entry_byte_offset=current_at,source_sample_size_bytes=source['size_bytes'],
                sample_size_bytes=current['size_bytes'],decoded_frames=blocks*28,input_wav_rate=rate,
                maximum_absolute_error=n['maximum_absolute_error'],sum_squared_error=n['sum_squared_error'],
                wav_sha256=receipt['wav_sha256'],receipt_key=receipt['receipt_key'],source_entry_sha256=_hash(body),candidate_entry_sha256=_hash(candidate)))
        prefix=bytearray(bank[:source_report['sections']['sample_offset']]);pool=[]
        for row in source_report['samples']:
            raw=bank[row['offset']:row['offset']+row['size_bytes']];encoded=encoded_rows.get(row['index'],raw);pool.append(encoded)
            if row['index'] in encoded_rows:struct.pack_into('<H',prefix,source_report['sections']['sample_table_offset']+row['table_index']*2,len(encoded)//8)
        expected_bank=prefix+b''.join(pool)+bank[source_report['consumed_sample_end']:];struct.pack_into('<I',expected_bank,12,len(expected_bank))
        expected_bank=bytes(expected_bank);delta=len(expected_bank)-len(bank)
        if kind=='standalone-vab':expected=expected_bank+baseline[len(bank):]
        elif kind=='leading-contiguous-vab-chunk':expected=struct.pack('<I',int.from_bytes(baseline[:4],'little')+delta)+expected_bank+baseline[4+len(bank):]
        else:
            head=pieces[0]['size_bytes'];part=pieces[1]
            expected=baseline[:4]+expected_bank[:head]+struct.pack('<I',1<<24|(part['size_bytes']+delta))+expected_bank[head:]+baseline[part['entry_offset']+part['size_bytes']:]
        if actual_kind!=kind or actual_bank!=expected_bank or candidate!=expected:
            raise ProjectError('Allocated audio failed complete independently reconstructed bank/carrier qualification')
        offset=archive.node.extent_lba*2048+record['entry_byte_offset']
        if image.read_user(0,offset,len(body),image.size//2352*2048)!=body:raise ProjectError('Allocated audio physical source changed')
        requests.append(dict(kind='audio-sample-bank',entry_index=index,expected_entry_sha256=_hash(body),candidate=candidate))
        overlays=[row for row in overlays if row['prot_entry_index']!=index]
        for change in changes:
            if change['semantic_id']==identifier:change['candidate_entry_sha256']=_hash(candidate)
    return overlays,changes,requests


def prepare_native(project,image,archive):
    from copy import copy,deepcopy
    from .sequence_replacement_authoring import validate_collection,read
    validate_collection(project)
    if not project.audio_sequence_replacements:return _prepare_native_base(project,image,archive)
    view=copy(project);view.audio_sequence_replacements={}
    overlays,changes,requests=_prepare_native_base(view,image,archive)
    for identifier,binding in sorted(project.audio_sequence_replacements.items()):
        original,_,_=read(project,identifier,binding);candidate=read_entry(project,identifier,original)
        record=binding['source_record'];index=record['prot_entry_index'];offset=archive.node.extent_lba*2048+record['entry_byte_offset']
        if image.read_user(0,offset,len(original),image.size//2352*2048)!=original:raise ProjectError('Replacement physical source changed before Build')
        overlays=[r for r in overlays if r['prot_entry_index']!=index];requests=[r for r in requests if r['entry_index']!=index]
        requests.append(dict(kind='audio-sequence',entry_index=index,expected_entry_sha256=_hash(original),candidate=candidate))
        changes.append(dict(scene='global-audio',semantic_id=identifier,field='audio.sequence.replacement',scope='audio-SEQ-complete-replacement',source_entry_sha256=_hash(original),candidate_entry_sha256=_hash(candidate),midi_sha256=binding['midi_sha256']))
        for row in changes:
            if row['semantic_id']==identifier:row['candidate_entry_sha256']=_hash(candidate)
    return overlays,changes,requests

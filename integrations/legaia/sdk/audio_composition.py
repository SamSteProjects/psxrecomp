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
    candidates=[]
    for kind,collection,reader in (('sequence',project.audio_overrides,read_sequence),
                                   ('bank',project.audio_bank_overrides,read_bank),
                                   ('samples',project.audio_sample_overrides,read_samples)):
        binding=collection.get(identifier)
        if binding is None:continue
        source,candidate,_,audit=reader(project,identifier,binding)
        if original is None:original=source
        elif original!=source:raise ProjectError('Audio families no longer share the same physical source entry')
        candidates.append((kind,candidate,audit))
    if original is None:raise ProjectError('Choose a source-qualified authored audio resource')
    return merge(original,candidates)


def prepare_overlays(project,image,archive):
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

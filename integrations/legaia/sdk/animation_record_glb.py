"""GLB content interchange for a retained UUID, including explicit frame growth.

Only object-local rigid channels enter the retained content transaction. The
frozen donor supplies native flags, trailers and opaque channel nibbles; output
mapping and interchange rate are explicit and never inferred from file timing.
"""
from copy import deepcopy
from hashlib import sha256
import math

from importer.animation import animation_record_ranges,decode_animation_record
from importer.animation_allocation import allocate_animation_record
from importer.animation_authoring import patch_animation_channels
from importer.animation_glb import import_animation_glb
from .animation_record_ledger import verified_source
from .animation_record_edit import options,prepare as prepare_content
from .animation_allocation import pose_saved_record
from .scene_preview import source_key
from .project import ProjectError,digest


def _snapshot(project,scene_id,record_id,expected_source_key,fps):
    if type(fps) not in (int,float) or not 1<=fps<=120 or not math.isfinite(fps):
        raise ProjectError('Retained GLB requires an explicit interchange rate from 1 to 120 fps')
    entry=options(project,scene_id,record_id,expected_source_key)['entry']
    if entry['object_count']>64:raise ProjectError('Retained GLB supports at most 64 existing rigid objects')
    bank,_=verified_source(project,scene_id)
    index=int(entry['donor_animation_id'].rsplit('/',1)[1]);start,end=animation_record_ranges(bank)[index]
    captured,_=patch_animation_channels(bank[start:end],entry['donor_record_sha256'],entry['donor_edits'])
    if sha256(captured).hexdigest()!=entry['effective_donor_record_sha256']:
        raise ProjectError('Captured donor differs from retained GLB provenance')
    retained,_=allocate_animation_record(captured,entry['effective_donor_record_sha256'],entry['source_frame_indices'],entry['edits'])
    if sha256(retained).hexdigest()!=entry['record_sha256']:
        raise ProjectError('Retained GLB content differs from its saved hash')
    binding=dict(schema_version='legaia.animation-record-glb-binding.v1',scene_id=scene_id,
        record_id=record_id,record_sha256=entry['record_sha256'],asset_id=entry['donor_asset_id'],
        effective_donor_record_sha256=entry['effective_donor_record_sha256'],
        project_source_key=expected_source_key,frame_count=len(entry['source_frame_indices']),
        object_count=entry['object_count'],clip_fps=float(fps),
        coordinate_conversion='[x,-y,z]; rigid Rz*Ry*Rx',
        node_names=[f'object-{i}' for i in range(entry['object_count'])])
    if source_key(project)!=expected_source_key:raise ProjectError('Retained GLB source changed during capture verification')
    return entry,captured,binding


def export_binding(project,scene_id,record_id,expected_source_key,fps):
    return _snapshot(project,scene_id,record_id,expected_source_key,fps)[2]


def prepare_import(project,scene_id,record_id,source_frame_indices,expected_source_key,content,binding,*,animation_index=None):
    if not isinstance(binding,dict):raise ProjectError('Choose the retained clip export binding JSON sidecar')
    entry,captured,current=_snapshot(project,scene_id,record_id,expected_source_key,binding.get('clip_fps'))
    normalized=dict(binding,clip_fps=float(binding['clip_fps']))
    object_nodes=binding.get('external_object_nodes')
    sampling=binding.get('external_sampling')
    if 'external_sampling' in binding and sampling is None:raise ProjectError('External sampling cannot be null')
    if 'external_object_nodes' in binding and object_nodes is None:raise ProjectError('Explicit object mapping cannot be null')
    normalized.pop('external_object_nodes',None)
    normalized.pop('external_sampling',None)
    if digest(normalized)!=digest(current):
        raise ProjectError('Retained GLB binding differs from the current saved capture or scene; export again')
    # Same mapping uses current content as the source-biased angular baseline.
    # A changed mapping inherits captured frames, never guesses new opaque data.
    baseline_edits=entry['edits'] if source_frame_indices==entry['source_frame_indices'] else []
    baseline,_=allocate_animation_record(captured,entry['effective_donor_record_sha256'],source_frame_indices,baseline_edits)
    candidate,analysis=import_animation_glb(baseline,content,fps=current['clip_fps'],animation_index=animation_index,object_node_indices=object_nodes,external_sampling=sampling)
    inherited,_=allocate_animation_record(captured,entry['effective_donor_record_sha256'],source_frame_indices,[])
    desired=decode_animation_record(candidate);original=decode_animation_record(inherited);edits=[]
    for frame in desired['frames']:
        f=frame['frame_index']
        for channel in frame['object_transforms']:
            o=channel['object_index'];old=original['frames'][f]['object_transforms'][o]
            row=dict(frame_index=f,object_index=o)
            for field in ('translation','rotation_psx'):
                axes={a:v for a,v,prior in zip('xyz',channel[field],old[field]) if v!=prior}
                if axes:row[field]=axes
            if len(row)>2:edits.append(row)
    native_request=dict(scene_id=scene_id,record_id=record_id,source_frame_indices=deepcopy(source_frame_indices),
        edits=edits,expected_source_key=expected_source_key)
    view,native=prepare_content(project,**native_request)
    if native['candidate_record_sha256']!=sha256(candidate).hexdigest():
        raise ProjectError('Retained GLB channel replay differs from the reconstructed native record')
    if object_nodes is not None:current=dict(current,external_object_nodes=object_nodes)
    if sampling is not None:current=dict(current,external_sampling=analysis['external_sampling'])
    report=dict(schema_version='legaia.animation-record-glb-review.v1',scene_id=scene_id,record_id=record_id,
        project_source_key=expected_source_key,binding=current,glb_sha256=sha256(content).hexdigest(),
        analysis=analysis,content_review=native,content_request=native_request,
        project_change=native['project_change'],project_changed=False,gameplay_verified=False,
        limitations=['Only rigid animation channels are imported; mesh edits are ignored.',
                     'Constant unit-scale tracks are accepted; native scale animation is unsupported.',
                     'Rigid parent TRS and static matrices are baked to scene-space poses; skinning remains unsupported.',
            'The explicit captured-donor mapping determines output frame count and opaque channel data.',
            'The interchange rate does not establish Retail playback timing.',
            'All referring initial assignments receive the new content hash in one Undo entry.'])
    report['review_key']=digest(report)
    return view,report


def pose_import(project,scene_id,record_id,source_frame_indices,expected_source_key,content,binding,review_key,*,animation_index=None):
    view,report=prepare_import(project,scene_id,record_id,source_frame_indices,expected_source_key,content,binding,animation_index=animation_index)
    if review_key!=report['review_key']:raise ProjectError('Retained GLB or mapping changed after Review')
    animation,asset=pose_saved_record(view,scene_id,record_id,source_key(view))
    animation.update(representation='allocated_record_edit_preview',clip_id='allocated-record-edit-preview',
        label='Proposed retained GLB content',edit_proposal=report['content_review'],glb_import_proposal=report)
    if source_key(project)!=expected_source_key:raise ProjectError('Retained GLB source changed during pose Preview')
    return animation,asset,report


def apply_import(project,scene_id,record_id,source_frame_indices,expected_source_key,content,binding,review_key,*,animation_index=None):
    _,report=prepare_import(project,scene_id,record_id,source_frame_indices,expected_source_key,content,binding,animation_index=animation_index)
    if review_key!=report['review_key']:raise ProjectError('Retained GLB, binding or mapping changed after Review')
    command=dict(type='edit_animation_record',**report['content_request'],review_key=report['content_review']['review_key'])
    if report['project_change']:
        from .animation_sources import apply
        apply(project,command,content,kind='retained',target_id=record_id,binding=binding,
              animation_index=animation_index,source_frame_indices=source_frame_indices,
              candidate_sha256=report['analysis']['candidate_sha256'],review_key=report['review_key'])
    else:project.command(command)
    return report

"""Explicit external animation snapshot before existing morph/skin/node baking.

glTF 2.0 sections 3.11 and Appendix C define endpoint clamping, STEP,
LINEAR/shortest-arc rotation and CUBICSPLINE interpolation. No native animation.
"""
from copy import deepcopy
import math
from .core import ImportError
from .animation_glb import _Accessors,_sample,_unit_quaternion


def animation_pose_config(value):
    if value is None:return None
    if (not isinstance(value,dict) or set(value)!={'animation_index','time_seconds'}
            or type(value['animation_index']) is not int or not 0<=value['animation_index']<64
            or type(value['time_seconds']) not in (int,float)
            or not math.isfinite(value['time_seconds']) or not 0<=value['time_seconds']<=3600):
        raise ImportError('Mesh animation pose needs an explicit clip index and finite time from 0 through 3600 seconds')
    return dict(animation_index=value['animation_index'],time_seconds=float(value['time_seconds']))


def sample_mesh_document(doc,binary,value,selected):
    pose=animation_pose_config(value);animations=doc.get('animations',[])
    if pose is None or not isinstance(binary,(bytes,bytearray)):
        raise ImportError('Mesh pose sampling requires an explicit choice and embedded binary bytes')
    if (not isinstance(animations,list) or not 1<=len(animations)<=64
            or pose['animation_index']>=len(animations)):
        raise ImportError('Choose an existing animation clip for the mesh pose')
    animation=animations[pose['animation_index']]
    if not isinstance(animation,dict) or 'extensions' in animation:
        raise ImportError('Mesh pose animation extensions are unsupported')
    channels,samplers=(animation.get(k) for k in ('channels','samplers'))
    if any(not isinstance(rows,list) or not 1<=len(rows)<=256 for rows in (channels,samplers)):
        raise ImportError('Mesh animation pose exceeds its channel or sampler budget')
    result=deepcopy(doc);reader=_Accessors(doc,binary);seen=set();sampled=[];excluded=[]
    for channel in channels:
        if not isinstance(channel,dict) or 'extensions' in channel:raise ImportError('Invalid mesh pose animation channel')
        target=channel.get('target');si=channel.get('sampler')
        if (not isinstance(target,dict) or 'extensions' in target or type(target.get('node')) is not int
                or not 0<=target['node']<len(doc['nodes']) or target.get('path') not in ('translation','rotation','scale','weights')
                or type(si) is not int or not 0<=si<len(samplers)):
            raise ImportError('Mesh pose animation target or sampler ownership is invalid')
        node,path=target['node'],target['path']
        if (node,path) in seen:raise ImportError('Mesh pose clip contains duplicate target channels')
        seen.add((node,path))
        if node not in selected:excluded.append(dict(node_index=node,path=path));continue
        if 'matrix' in doc['nodes'][node]:raise ImportError('Animated mesh nodes cannot contain matrices')
        sampler=samplers[si]
        if not isinstance(sampler,dict) or 'extensions' in sampler:raise ImportError('Mesh pose sampler extensions are unsupported')
        mode=sampler.get('interpolation','LINEAR')
        if mode not in ('STEP','LINEAR','CUBICSPLINE'):raise ImportError('Mesh pose interpolation must be STEP, LINEAR or CUBICSPLINE')
        times=[row[0] for row in reader.read(sampler.get('input'),'SCALAR')]
        if times[0]<0 or times[-1]>3600 or any(a>=b for a,b in zip(times,times[1:])):
            raise ImportError('Mesh pose key times must increase strictly within 0 through 3600 seconds')
        if path=='weights':
            mesh_index=doc['nodes'][node].get('mesh');meshes=doc.get('meshes',[])
            if type(mesh_index) is not int or not 0<=mesh_index<len(meshes):raise ImportError('Animated weights require an existing mesh')
            if not isinstance(meshes[mesh_index],dict):raise ImportError('Animated weights require a qualified mesh')
            primitives=meshes[mesh_index].get('primitives',[])
            counts=[len(p.get('targets',[])) for p in primitives if isinstance(p,dict) and isinstance(p.get('targets',[]),list)]
            if not counts or len(counts)!=len(primitives) or not 1<=counts[0]<=8 or any(n!=counts[0] for n in counts):
                raise ImportError('Animated mesh weights require matching bounded morph target counts')
            values=[row[0] for row in reader.read(sampler.get('output'),'SCALAR')];width=counts[0]
            if len(values)%width:raise ImportError('Mesh pose morph weights have incomplete keys')
            values=[values[at:at+width] for at in range(0,len(values),width)]
        else:values=reader.read(sampler.get('output'),'VEC4' if path=='rotation' else 'VEC3')
        cubic=mode=='CUBICSPLINE'
        if len(values)!=len(times)*(3 if cubic else 1) or cubic and len(times)<2:
            raise ImportError('Mesh pose animation input/output key counts disagree')
        if path=='rotation':
            if cubic:
                for row in values[1::3]:_unit_quaternion(row,'mesh pose rotation key')
            else:values=[_unit_quaternion(row,'mesh pose rotation key') for row in values]
        evaluated=_sample((times,values,mode),pose['time_seconds'],path=='rotation')
        if any(not math.isfinite(n) for n in evaluated):raise ImportError('Mesh pose sampling produced nonfinite values')
        result['nodes'][node][path]=evaluated
        sampled.append(dict(node_index=node,path=path,key_count=len(times),interpolation=mode,start_time=times[0],end_time=times[-1]))
    return result,dict(**pose,sampled_channels=sampled,excluded_channels=excluded)

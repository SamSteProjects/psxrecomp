"""Bounded sparse FLOAT VEC3 deltas, isolated from fixed-layout GLB import."""
import math,struct
from .core import ImportError
from .model_glb import _Accessors,_integer,_object,MAX_COMPONENTS


def _location(reader,spec,count,width,size,label):
    spec=_object(spec,label)
    view_index=_integer(spec.get('bufferView'),0,len(reader.views)-1,label+' buffer view')
    view=_object(reader.views[view_index],label+' buffer view')
    if type(view.get('buffer')) is not int or view['buffer']!=0 or 'byteStride' in view or 'target' in view:
        raise ImportError('Sparse morph views require the embedded buffer without stride or target')
    origin=_integer(view.get('byteOffset',0),0,len(reader.binary),label+' view offset')
    length=_integer(view.get('byteLength'),1,len(reader.binary),label+' view length')
    relative=_integer(spec.get('byteOffset',0),0,length,label+' offset')
    if relative%size or (origin+relative)%size:
        raise ImportError('Sparse morph accessor alignment is invalid')
    if origin+length>len(reader.binary) or relative+count*width*size>length:
        raise ImportError('Sparse morph accessor exceeds its buffer view')
    return origin+relative


def morph_delta(reader,index,count):
    index=_integer(index,0,len(reader.accessors)-1,'morph accessor')
    a=_object(reader.accessors[index],'morph accessor')
    if 'sparse' not in a:return reader.read(index,3,'morph delta')
    key=('morph_sparse',index)
    if key in reader.cache:
        result=reader.cache[key]
        if len(result)!=count:raise ImportError('Sparse morph count differs from the base mesh')
        return result
    if (a.get('type')!='VEC3' or type(a.get('componentType')) is not int or a['componentType']!=5126
            or a.get('normalized',False) is not False or type(a.get('count')) is not int or a['count']!=count
            or not 1<=count<=8192):
        raise ImportError('Sparse morph requires matching FLOAT VEC3 counts within 8192 vertices')
    sparse=_object(a['sparse'],'sparse morph')
    if not {'count','indices','values'}<=set(sparse) or not set(sparse)<={'count','indices','values','extras'}:
        raise ImportError('Sparse morph fields are malformed')
    changed=_integer(sparse['count'],1,count,'sparse morph count')
    indices=_object(sparse['indices'],'sparse morph indices');values=_object(sparse['values'],'sparse morph values')
    if (not {'bufferView','componentType'}<=set(indices) or not set(indices)<={'bufferView','componentType','byteOffset','extras'}
            or 'bufferView' not in values or not set(values)<={'bufferView','byteOffset','extras'}):
        raise ImportError('Sparse morph index/value fields are malformed')
    component=indices['componentType']
    if type(component) is not int or component not in (5121,5123,5125):
        raise ImportError('Sparse morph indices require unsigned byte, short or integer components')
    fmt,size={5121:('B',1),5123:('H',2),5125:('I',4)}[component]
    reader.components+=count*3+changed*4
    if reader.components>MAX_COMPONENTS:raise ImportError('Model GLB decoded component budget exceeded')
    index_at=_location(reader,indices,changed,1,size,'sparse morph indices')
    value_at=_location(reader,values,changed,3,4,'sparse morph values')
    slots=struct.unpack_from('<'+str(changed)+fmt,reader.binary,index_at)
    if any(slot>=count or i and slot<=slots[i-1] for i,slot in enumerate(slots)):
        raise ImportError('Sparse morph indices must be strictly increasing and within the base count')
    replacements=[struct.unpack_from('<3f',reader.binary,value_at+i*12) for i in range(changed)]
    if any(not math.isfinite(v) for row in replacements for v in row):
        raise ImportError('Sparse morph values must be finite')
    if 'bufferView' in a:
        dense=dict(a);dense.pop('sparse')
        base=_Accessors(dict(accessors=[dense],bufferViews=reader.views),reader.binary).read(0,3,'morph initialization')
        result=list(base)
    else:
        if type(a.get('byteOffset',0)) is not int or a.get('byteOffset',0)!=0:
            raise ImportError('Sparse morph zero initialization cannot have a base byte offset')
        result=[(0.,0.,0.)]*count
    for slot,row in zip(slots,replacements):result[slot]=row
    reader.cache[key]=result
    return result

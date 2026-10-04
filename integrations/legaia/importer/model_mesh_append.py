"""Append standard GLB triangle geometry through explicit native donor ownership.

Only POSITION and triangle indices are imported. Other supported display
attributes are validated and reported as inherited from the native donor.
"""
from hashlib import sha256
import math
from .animation_glb import _read_glb
from .model_glb import _Accessors
from .core import ImportError
from .model_face_addition import MAX_NEW_FACES
from .model_vector_allocation import MAX_NEW_VECTORS


def decode_append_mesh(content):
    doc,binary=_read_glb(content)
    if doc.get('animations') or doc.get('skins'):
        raise ImportError('Mesh append requires static geometry without skinning or animation')
    nodes,meshes,scenes=(doc.get(key) for key in ('nodes','meshes','scenes'))
    if any(not isinstance(rows,list) or len(rows)!=1 for rows in (nodes,meshes,scenes)):
        raise ImportError('Mesh append requires one scene, one mesh and one mesh node')
    if (not isinstance(scenes[0],dict) or scenes[0].get('nodes')!=[0]
            or any(type(index) is not int for index in scenes[0].get('nodes',[]))
            or type(doc.get('scene',0)) is not int or doc.get('scene',0)!=0):
        raise ImportError('Mesh append requires the sole mesh in its default scene')
    node=nodes[0]
    if (not isinstance(node,dict) or type(node.get('mesh')) is not int or node['mesh']!=0
            or any(key in node for key in ('skin','weights','children','extensions'))):
        raise ImportError('Mesh append node must own one unskinned mesh without children')
    transforms={'translation':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1],
                'matrix':[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]}
    if 'matrix' in node and any(key in node for key in ('translation','rotation','scale')):
        raise ImportError('Mesh append cannot combine a matrix with TRS')
    for key,identity in transforms.items():
        if key in node and (not isinstance(node[key],list) or len(node[key])!=len(identity)
                or any(type(value) not in (int,float) or not math.isfinite(value) or value!=expected
                       for value,expected in zip(node[key],identity))):
            raise ImportError('Apply mesh object transforms before appending geometry')
    mesh=meshes[0]
    if not isinstance(mesh,dict) or any(key in mesh for key in ('weights','extensions')):
        raise ImportError('Mesh append cannot import morph weights or mesh extensions')
    primitives=mesh.get('primitives')
    if not isinstance(primitives,list) or not 1<=len(primitives)<=MAX_NEW_FACES:
        raise ImportError('Mesh append requires a bounded set of triangle primitives')
    reader=_Accessors(doc,binary)
    if any(not isinstance(view,dict) or type(view.get('buffer')) is not int or view['buffer']!=0 for view in reader.views):
        raise ImportError('Mesh append buffer views must own the embedded buffer')
    vertices=[];triangles=[];owners={};ignored=set();error=0.0
    for primitive in primitives:
        if (not isinstance(primitive,dict) or type(primitive.get('mode',4)) is not int
                or primitive.get('mode',4)!=4 or any(key in primitive for key in ('targets','extensions'))):
            raise ImportError('Mesh append supports triangle lists without morph targets or extensions')
        attrs=primitive.get('attributes')
        if (not isinstance(attrs,dict) or 'POSITION' not in attrs
                or not set(attrs)<={'POSITION','NORMAL','TEXCOORD_0','COLOR_0','TANGENT'}):
            raise ImportError('Mesh append requires standard POSITION with supported display attributes only')
        positions=reader.read(attrs['POSITION'],3,'append positions')
        for key,width in [('NORMAL',3),('TEXCOORD_0',2),('COLOR_0',None),('TANGENT',4)]:
            if key not in attrs:continue
            if key=='COLOR_0':
                index=attrs[key]
                if type(index) is not int or not 0<=index<len(reader.accessors):
                    raise ImportError('Mesh append color accessor is invalid')
                if not isinstance(reader.accessors[index],dict):raise ImportError('Mesh append color accessor is invalid')
                width={'VEC3':3,'VEC4':4}.get(reader.accessors[index].get('type'))
                if width is None:raise ImportError('Mesh append color requires VEC3 or VEC4')
            values=reader.read(attrs[key],width,'append '+key)
            if len(values)!=len(positions):raise ImportError('Mesh append attribute counts differ')
            ignored.add(key)
        if 'indices' in primitive:
            indices=[row[0] for row in reader.read(primitive['indices'],1,'append indices',indices=True)]
        else:indices=list(range(len(positions)))
        if not indices or len(indices)%3 or len(indices)//3+len(triangles)>MAX_NEW_FACES:
            raise ImportError('Mesh append exceeds the native face budget or has incomplete triangles')
        for begin in range(0,len(indices),3):
            current=[]
            # Reflect Y and reverse winding to preserve the SDK GLB convention.
            for index in (indices[begin],indices[begin+2],indices[begin+1]):
                if not 0<=index<len(positions):raise ImportError('Mesh append index exceeds POSITION count')
                owner=(attrs['POSITION'],index)
                if owner not in owners:
                    values=[positions[index][0],-positions[index][1],positions[index][2]]
                    quantized=[round(value) for value in values]
                    if any(not -32768<=value<=32767 for value in quantized):
                        raise ImportError('Mesh append positions exceed signed native coordinates')
                    error=max(error,max(abs(a-b) for a,b in zip(values,quantized)))
                    if len(vertices)>=MAX_NEW_VECTORS:raise ImportError('Mesh append exceeds the new-vector budget')
                    owners[owner]=len(vertices);vertices.append(quantized)
                current.append(owners[owner])
            a,b,c=(vertices[index] for index in current)
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            if not any(u[(i+1)%3]*v[(i+2)%3]-u[(i+2)%3]*v[(i+1)%3] for i in range(3)):
                raise ImportError('Mesh append contains a degenerate triangle after native quantization')
            triangles.append(current)
    return dict(schema_version='legaia.model-mesh-append-geometry.v1',glb_sha256=sha256(content).hexdigest(),
        vertices=vertices,triangles=triangles,vertex_max_error=error,
        ignored_attributes=sorted(ignored),coordinate_conversion='[x,-y,z]; reverse triangle winding')

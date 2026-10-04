"""Append standard GLB triangle geometry through explicit native donor ownership.

POSITION, triangle indices, UVs, colors and unit normals are decoded. Native packet
ownership determines whether corner normals can be imported.
"""
from hashlib import sha256
import math
from .animation_glb import _read_glb
from .model_glb import _Accessors
from .core import ImportError
from .model_face_addition import MAX_NEW_FACES
from .model_vector_allocation import MAX_NEW_VECTORS


def inspect_append_mesh(content):
    """Qualified file inventory; material names describe source slots, not bindings."""
    geometry=decode_append_mesh(content)
    doc,binary=_read_glb(content)
    materials=doc.get('materials',[])
    if not isinstance(materials,list) or len(materials)>128:
        raise ImportError('Mesh material inventory exceeds its bounded source slots')
    reader=_Accessors(doc,binary);rows=[]
    for index,primitive in enumerate(doc['meshes'][0]['primitives']):
        material=primitive.get('material');name=None
        if material is not None:
            if type(material) is not int or not 0<=material<len(materials) or not isinstance(materials[material],dict):
                raise ImportError('Mesh primitive material slot is missing')
            name=materials[material].get('name')
            if name is not None and (not isinstance(name,str) or len(name)>256 or any(ord(c)<32 for c in name)):
                raise ImportError('Mesh primitive material name is invalid')
        accessor=primitive.get('indices',primitive['attributes']['POSITION'])
        count=reader.accessors[accessor]['count'];mode=primitive.get('mode',4)
        rows.append(dict(primitive_index=index,triangle_count=count//3 if mode==4 else count-2,
            source_mode=mode,material_index=material,material_name=name))
    return dict(schema_version='legaia.model-mesh-file.v1',glb_sha256=geometry['glb_sha256'],
        primitives=rows,triangle_count=len(geometry['triangles']),read_only=True)


def decode_append_mesh(content, *, preserve_primitives=False, primitive_index=None):
    if type(preserve_primitives) is not bool:
        raise ImportError('Mesh primitive preservation must be boolean')
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
    if primitive_index is not None and (type(primitive_index) is not int or not 0<=primitive_index<len(primitives)):
        raise ImportError('Choose an existing GLB primitive index')
    selected=primitives if primitive_index is None else [primitives[primitive_index]]
    if preserve_primitives:
        from .model_group_allocation import MAX_NEW_GROUPS
        if len(selected)>MAX_NEW_GROUPS:
            raise ImportError('Mesh primitive groups exceed the native group budget')
    reader=_Accessors(doc,binary)
    if any(not isinstance(view,dict) or type(view.get('buffer')) is not int or view['buffer']!=0 for view in reader.views):
        raise ImportError('Mesh append buffer views must own the embedded buffer')
    vertices=[];triangles=[];triangle_normals=[];triangle_uvs=[];triangle_colors=[];owners={};ignored=set();error=0.0;normal_error=0.0
    primitive_ranges=[]
    for primitive_index,primitive in enumerate(selected):
        first_triangle=len(triangles)
        if (not isinstance(primitive,dict) or type(primitive.get('mode',4)) is not int
                or primitive.get('mode',4) not in (4,5,6) or any(key in primitive for key in ('targets','extensions'))):
            raise ImportError('Mesh append supports triangle lists, strips and fans without morph targets or extensions')
        attrs=primitive.get('attributes')
        if (not isinstance(attrs,dict) or 'POSITION' not in attrs
                or not set(attrs)<={'POSITION','NORMAL','TEXCOORD_0','COLOR_0','TANGENT'}):
            raise ImportError('Mesh append requires standard POSITION with supported display attributes only')
        positions=reader.read(attrs['POSITION'],3,'append positions');normals=None;uvs=None;colors=None
        for key,width in [('NORMAL',3),('TEXCOORD_0',2),('COLOR_0',None),('TANGENT',4)]:
            if key not in attrs:continue
            if key=='COLOR_0':
                index=attrs[key]
                if type(index) is not int or not 0<=index<len(reader.accessors):
                    raise ImportError('Mesh append color accessor is invalid')
                if not isinstance(reader.accessors[index],dict):raise ImportError('Mesh append color accessor is invalid')
                width={'VEC3':3,'VEC4':4}.get(reader.accessors[index].get('type'))
                if width is None:raise ImportError('Mesh append color requires VEC3 or VEC4')
            values=reader.read(attrs[key],width,'append '+key,normalized=(key=='COLOR_0' and reader.accessors[attrs[key]].get('normalized',False) is True))
            if len(values)!=len(positions):raise ImportError('Mesh append attribute counts differ')
            if key=='NORMAL':normals=values
            elif key=='TEXCOORD_0':uvs=values
            elif key=='COLOR_0':colors=values
            else:ignored.add(key)
        if 'indices' in primitive:
            indices=[row[0] for row in reader.read(primitive['indices'],1,'append indices',indices=True)]
        else:indices=list(range(len(positions)))
        mode=primitive.get('mode',4)
        face_count=len(indices)//3 if mode==4 else len(indices)-2
        if (len(indices)<3 or (mode==4 and len(indices)%3)
                or face_count+len(triangles)>MAX_NEW_FACES):
            raise ImportError('Mesh append exceeds the native face budget or has incomplete triangles')
        if any(not 0<=index<len(positions) for index in indices):
            raise ImportError('Mesh append index exceeds POSITION count')
        if mode==4:
            source_triangles=[indices[begin:begin+3] for begin in range(0,len(indices),3)]
        elif mode==5:
            # Strip parity changes source ordering before the coordinate reflection.
            source_triangles=[(indices[begin+(begin%2)],indices[begin+1-(begin%2)],indices[begin+2])
                              for begin in range(face_count)]
        else:
            source_triangles=[(indices[0],indices[begin+1],indices[begin+2]) for begin in range(face_count)]
        for triangle in source_triangles:
            current=[];directions=[];texture_points=[];color_points=[]
            # Reflect Y and reverse winding to preserve the SDK GLB convention.
            for index in (triangle[0],triangle[2],triangle[1]):
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
                if uvs is not None:texture_points.append(list(uvs[index]))
                if colors is not None:
                    if any(not 0<=value<=1 for value in colors[index]):raise ImportError('Mesh COLOR_0 must remain within the normalized 0..1 range')
                    color_points.append(list(colors[index]))
                if normals is not None:
                    direction=[normals[index][0],-normals[index][1],normals[index][2]]
                    length=math.hypot(*direction)
                    if length<=1e-12:raise ImportError('Mesh append requires nonzero referenced normals')
                    scaled=[value/length*4096 for value in direction]
                    quantized=[round(value) for value in scaled]
                    normal_error=max(normal_error,max(abs(a-b) for a,b in zip(scaled,quantized)))
                    directions.append(quantized)
            a,b,c=(vertices[index] for index in current)
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            if not any(u[(i+1)%3]*v[(i+2)%3]-u[(i+2)%3]*v[(i+1)%3] for i in range(3)):
                raise ImportError('Mesh append contains a degenerate triangle after native quantization')
            triangles.append(current);triangle_normals.append(directions if normals is not None else None);triangle_uvs.append(texture_points if uvs is not None else None);triangle_colors.append(color_points if colors is not None else None)
        primitive_ranges.append(dict(primitive_index=primitive_index,first_triangle=first_triangle,triangle_count=len(triangles)-first_triangle,source_mode=mode))
    result=dict(schema_version='legaia.model-mesh-append-geometry.v4',glb_sha256=sha256(content).hexdigest(),
        vertices=vertices,triangles=triangles,vertex_max_error=error,triangle_normals=triangle_normals,normal_max_error=normal_error,triangle_uvs=triangle_uvs,triangle_colors=triangle_colors,
        ignored_attributes=sorted(ignored),coordinate_conversion='[x,-y,z]; reverse triangle winding')
    if preserve_primitives:result.update(schema_version='legaia.model-mesh-append-geometry.v5',primitive_ranges=primitive_ranges)
    return result

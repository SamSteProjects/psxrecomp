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
from .model_mesh_material import color_factor
from .model_mesh_scene import scene_source
from .model_mesh_sources import mesh_sources,source_binding
from .model_mesh_transform import transform_point,transform_normal,IDENTITY


def mesh_source_scale(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 1e-6<=value<=1e6:
        raise ImportError('Native units per GLB unit must be finite and between 0.000001 and 1000000')
    return float(value)


def inspect_append_mesh(content,*,scene_index=None,source_scale=1):
    """Qualified file inventory; material names describe source slots, not bindings."""
    source_scale=mesh_source_scale(source_scale)
    doc,binary=_read_glb(content)
    sources,canonical,scope=mesh_sources(doc,scene_index,allow_empty=True,with_scope=True)
    selection=scene_source(doc,scene_index)
    if not sources:
        return dict(schema_version='legaia.model-mesh-file.v1',glb_sha256=sha256(content).hexdigest(),primitives=[],triangle_count=0,read_only=True,scene_source=selection,
                    **({'static_scope':scope} if scope else {}),**({'source_scale':source_scale} if source_scale!=1 else {}))
    geometry=decode_append_mesh(content,scene_index=scene_index,source_scale=source_scale)
    materials=doc.get('materials',[])
    if not isinstance(materials,list) or len(materials)>128:
        raise ImportError('Mesh material inventory exceeds its bounded source slots')
    reader=_Accessors(doc,binary);rows=[]
    sources,canonical=mesh_sources(doc,scene_index)
    for index,source in enumerate(sources):
        primitive=source['primitive']
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
        primitives=rows,triangle_count=len(geometry['triangles']),read_only=True,
        **({'source_scale':source_scale} if source_scale!=1 else {}),
        **({'static_scope':geometry['static_scope']} if 'static_scope' in geometry else {}),
        **({'uv_sets':[row['sets'] for row in geometry['uv_sources']]} if 'uv_sources' in geometry else {}),
        **({'scene_source':geometry['scene_source']} if 'scene_source' in geometry else {}),
        **({'node_transform':geometry['node_transform']} if 'node_transform' in geometry else {}),
        **({'node_sources':[source_binding(row) for row in sources]} if not canonical else {}))


def decode_append_mesh(content, *, preserve_primitives=False, primitive_index=None, material_colors=False,scene_index=None,uv_set=0,source_scale=1):
    source_scale=mesh_source_scale(source_scale)
    if type(preserve_primitives) is not bool or type(material_colors) is not bool:
        raise ImportError('Mesh primitive preservation and material RGB choices must be boolean')
    if type(uv_set) is not int or not 0<=uv_set<=7:raise ImportError('Choose a source UV set from 0 through 7')
    doc,binary=_read_glb(content)
    sources,canonical,scope=mesh_sources(doc,scene_index,with_scope=True)
    primitives=sources
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
    primitive_ranges=[];material_factors=[];source_triangle_colors=[];uv_sources=[]
    for primitive_index,source in enumerate(selected):
        primitive=source['primitive'];transform=source['node_transform']
        factor=color_factor(doc,primitive,source['primitive_index']) if material_colors else None
        if factor is not None:material_factors.append(factor)
        first_triangle=len(triangles)
        if (not isinstance(primitive,dict) or type(primitive.get('mode',4)) is not int
                or primitive.get('mode',4) not in (4,5,6) or any(key in primitive for key in ('targets','extensions'))):
            raise ImportError('Mesh append supports triangle lists, strips and fans without morph targets or extensions')
        attrs=primitive.get('attributes')
        if (not isinstance(attrs,dict) or 'POSITION' not in attrs
                or not set(attrs)<=({'POSITION','NORMAL','COLOR_0','TANGENT'}|{f'TEXCOORD_{i}' for i in range(8)})):
            raise ImportError('Mesh append requires standard POSITION with supported display attributes only')
        positions=reader.read(attrs['POSITION'],3,'append positions');normals=None;uvs=None;colors=None
        sets=[i for i in range(8) if f'TEXCOORD_{i}' in attrs]
        if sets!=list(range(len(sets))):raise ImportError('Source UV sets must be consecutive starting at TEXCOORD_0')
        uv_sources.append(dict(primitive_index=source['primitive_index'],sets=sets,first_triangle=first_triangle))
        for key,width in [('NORMAL',3)]+[(f'TEXCOORD_{i}',2) for i in sets]+[('COLOR_0',None),('TANGENT',4)]:
            if key not in attrs:continue
            if key=='COLOR_0':
                index=attrs[key]
                if type(index) is not int or not 0<=index<len(reader.accessors):
                    raise ImportError('Mesh append color accessor is invalid')
                if not isinstance(reader.accessors[index],dict):raise ImportError('Mesh append color accessor is invalid')
                width={'VEC3':3,'VEC4':4}.get(reader.accessors[index].get('type'))
                if width is None:raise ImportError('Mesh append color requires VEC3 or VEC4')
            uv_key=key.startswith('TEXCOORD_')
            if uv_key:
                accessor=attrs[key]
                if type(accessor) is not int or not 0<=accessor<len(reader.accessors) or not isinstance(reader.accessors[accessor],dict):raise ImportError('Mesh UV accessor is invalid')
                spec=reader.accessors[accessor]
                if spec.get('componentType')!=5126 and not (spec.get('componentType') in (5121,5123) and spec.get('normalized') is True):raise ImportError('Mesh UV sets require floats or normalized unsigned components')
            values=reader.read(attrs[key],width,'append '+key,normalized=((key=='COLOR_0' or uv_key) and reader.accessors[attrs[key]].get('normalized',False) is True))
            if len(values)!=len(positions):raise ImportError('Mesh append attribute counts differ')
            if key=='NORMAL':normals=values
            elif key==f'TEXCOORD_{uv_set}':uvs=values
            elif key=='COLOR_0':colors=values
            else:ignored.add(key)
        original_colors=colors
        if material_colors:
            colors=colors if colors is not None else [[1,1,1,1] for _ in positions]
            if any(any(not 0<=v<=1 for v in row) for row in colors):
                raise ImportError('Mesh COLOR_0 must remain within the normalized 0..1 range')
            if any(len(row)==4 and row[3]!=1 for row in colors):
                raise ImportError('Material RGB baking requires opaque vertex alpha')
            colors=[[row[i]*factor['base_color_factor'][i] for i in range(3)]+[1] for row in colors]
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
            current=[];directions=[];texture_points=[];color_points=[];source_colors=[]
            # Reflect Y and reverse winding to preserve the SDK GLB convention.
            for index in ((triangle[0],triangle[2],triangle[1]) if transform['winding_reversed'] else triangle):
                owner=(source['node_index'],attrs['POSITION'],index)
                if owner not in owners:
                    values=[value*source_scale for value in transform_point(transform,positions[index])];values[1]=-values[1]
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
                    if material_colors:source_colors.append(list(original_colors[index]) if original_colors is not None else [1,1,1,1])
                if normals is not None:
                    direction=transform_normal(transform,normals[index]);direction[1]=-direction[1]
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
            if material_colors:
                source_triangle_colors.append(source_colors)
        uv_sources[-1]['triangle_count']=len(triangles)-first_triangle
        if factor is not None:factor.update(first_triangle=first_triangle,triangle_count=len(triangles)-first_triangle)
        primitive_ranges.append(dict(primitive_index=primitive_index,first_triangle=first_triangle,triangle_count=len(triangles)-first_triangle,source_mode=mode))
    result=dict(schema_version='legaia.model-mesh-append-geometry.v4',glb_sha256=sha256(content).hexdigest(),
        vertices=vertices,triangles=triangles,vertex_max_error=error,triangle_normals=triangle_normals,normal_max_error=normal_error,triangle_uvs=triangle_uvs,triangle_colors=triangle_colors,
        ignored_attributes=sorted(ignored),coordinate_conversion='[x,-y,z]; reverse triangle winding')
    if uv_set or any(isinstance(row['primitive'],dict) and isinstance(row['primitive'].get('attributes'),dict) and 'TEXCOORD_1' in row['primitive']['attributes'] for row in sources):result.update(uv_set=uv_set,uv_sources=uv_sources)
    selection=scene_source(doc,scene_index)
    if scope:result['static_scope']=scope
    if source_scale!=1:result['source_scale']=source_scale
    if len(selection['scenes'])>1:result['scene_source']=selection
    if material_colors:result.update(material_colors=True,material_factors=material_factors,source_triangle_colors=source_triangle_colors)
    if preserve_primitives:result.update(schema_version='legaia.model-mesh-append-geometry.v5',primitive_ranges=primitive_ranges)
    if not canonical:
        result['node_sources']=[source_binding(row) for row in selected]
        result['coordinate_conversion']='bake node transforms; [x,-y,z]; preserve oriented triangle winding'
    elif transform['matrix']!=IDENTITY:
        result['node_transform']=transform
        result['coordinate_conversion']='bake node transform; [x,-y,z]; preserve oriented triangle winding'
    return result

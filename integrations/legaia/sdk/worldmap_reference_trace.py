"""Bounded global ownership paths over one detached SDK source graph."""
from copy import deepcopy
from .project import ProjectError, canonical
from .project_assets import source_key
from .worldmap_asset_index import references
from .asset_reference_trace import trace_paths, MAX_ROWS, MAX_EXPANDED


def edge_id(edge):
    target=edge['target_id']
    return (target.replace('worldmap://','worldmap-reference://',1) if edge['kind']=='owns_native_source_record'
            else target.replace('scene://','worldmap-reference://',1).replace('/worldmap/placements/','/seeds/'))


def assemble(graph, identifier, direction, depth):
    if direction not in ('incoming','outgoing') or type(depth) is not int or not 1<=depth<=4:
        raise ProjectError('Global trace requires incoming/outgoing and depth 1..4')
    nodes={n['id']:dict(available=True) for n in graph['assets']}
    if identifier not in nodes:raise ProjectError('Global trace root is absent from qualified sources')
    edges=[dict(deepcopy(e),id=edge_id(e)) for e in sorted(graph['references'],key=lambda e:(e['kind'],e['source_id'],e['target_id']))]
    expanded,rows,omitted=trace_paths(identifier,nodes,edges,direction,depth,'derived')
    result=dict(schema_version='legaia.global-reference-trace.v1',asset_id=identifier,source_key=graph['source_key'],
                read_only=True,direction=direction,depth=depth,layer='derived',global_worldmap_index=deepcopy(graph),
                expanded_ids=expanded,rows=rows,limits=dict(max_rows=MAX_ROWS,max_expanded=MAX_EXPANDED,omitted_adjacent_edges=omitted),
                limitations=['Recorded global ownership paths only; no imported field-scene membership, runtime residency or gameplay reachability is implied.',
                             'One canonical first path expands each source identity. Depth, row and expansion limits exclude further traversal.',
                             'The retained complete graph may include source nodes outside the bounded trace; excluded source cells and incomplete native ownership do not grant authoring permission.'])
    if len(canonical(result))>8*1024*1024:raise ProjectError('Global trace response exceeds 8 MiB')
    return result


def inspect(project,identifier,direction,depth,layer,expected_source_key):
    if direction not in ('incoming','outgoing') or type(depth) is not int or not 1<=depth<=4 or layer!='derived':
        raise ProjectError('Global trace requires incoming/outgoing, depth 1..4 and derived layer')
    graph=references(project,identifier,expected_source_key)['global_worldmap_index']
    result=assemble(graph,identifier,direction,depth)
    if source_key(project)!=expected_source_key:raise ProjectError('Global trace sources changed during discovery')
    return result

"""Bounded recorded relationship paths over one fresh project graph snapshot."""
from copy import deepcopy
from collections import deque
from .project import ProjectError,canonical
from .asset_references import inspect_project,source_key

MAX_ROWS=128
MAX_EXPANDED=32

def assemble_trace(graph,direction,depth,layer):
    if direction not in ('incoming','outgoing') or type(depth) is not int or not 1<=depth<=4 or layer not in ('all','imported','decoded','authored','effective'):
        raise ProjectError('Reference trace requires incoming/outgoing, depth1..4 and a recorded layer')
    root=graph['asset_id'];nodes={n['id']:n for n in graph['nodes']};edges={e['id']:e for e in graph['edges']}
    if root not in nodes:raise ProjectError('Reference trace root is unavailable')
    adjacent={};incoming={};outgoing={}
    for edge in sorted(edges.values(),key=lambda e:(e['kind'],e['scene_id'],e['source_id'],e['target_id'],e['id'])):
        incoming.setdefault(edge['target_id'],[]).append(edge);outgoing.setdefault(edge['source_id'],[]).append(edge)
        if layer=='all' or edge['layer']==layer:adjacent.setdefault(edge['source_id'] if direction=='outgoing' else edge['target_id'],[]).append(edge)
    reports=[];rows=[];seen={root};queue=deque([(root,[root],[])]);omitted_edges=0
    while queue:
        identity,path,prior=queue.popleft()
        if len(reports)>=MAX_EXPANDED:
            omitted_edges+=len(adjacent.get(identity,[]));continue
        ins,outs=incoming.get(identity,[]),outgoing.get(identity,[])
        if len(ins)+len(outs)>4096:raise ProjectError('Reference trace neighborhood exceeds4096 edges')
        ids={identity}|{e['source_id'] for e in ins}|{e['target_id'] for e in outs}
        reports.append({**{k:deepcopy(graph[k]) for k in ('schema_version','source_key','read_only','coverage','limitations')},'asset_id':identity,'nodes':[deepcopy(nodes[k]) for k in sorted(ids)],'incoming':deepcopy(ins),'outgoing':deepcopy(outs),'material_diagnostics':None,'current_material_diagnostics':None})
        for edge in adjacent.get(identity,[]):
            if len(rows)>=MAX_ROWS:omitted_edges+=1;continue
            target=edge['target_id'] if direction=='outgoing' else edge['source_id'];node_path=path+[target];edge_path=prior+[edge['id']]
            stop='already_seen' if target in seen else 'unavailable' if not nodes[target]['available'] else 'depth_limit' if len(edge_path)>=depth else 'expanded'
            rows.append(dict(node_ids=node_path,edge_ids=edge_path,stop=stop))
            if stop=='expanded':seen.add(target);queue.append((target,node_path,edge_path))
    expanded={r['asset_id'] for r in reports}
    for row in rows:
        if row['stop']=='expanded' and row['node_ids'][-1] not in expanded:row['stop']='node_limit'
    result=dict(schema_version='legaia.asset-reference-trace.v1',asset_id=root,source_key=graph['source_key'],read_only=True,direction=direction,depth=depth,layer=layer,rows=rows,reports=reports,limits=dict(max_rows=MAX_ROWS,max_expanded=MAX_EXPANDED,omitted_adjacent_edges=omitted_edges),limitations=['Recorded edge chains only; mixed layers are not a resolved Current dependency graph.','One canonical first path expands each identity; parallel edges, cycles and alternate arrivals remain rows.','Depth, row, expansion and unavailable-source limits exclude further discovery. Runtime use and gameplay reachability are not established.'])
    if len(canonical(result))>8*1024*1024:raise ProjectError('Reference trace response exceeds8 MiB')
    return result

def inspect(project,identifier,direction,depth,layer,expected_source_key):
    # Validate controls before costly discovery; all graph qualification remains upstream.
    if direction not in ('incoming','outgoing') or type(depth) is not int or not 1<=depth<=4 or layer not in ('all','imported','decoded','authored','effective'):
        raise ProjectError('Invalid reference trace controls')
    if expected_source_key!=source_key(project):raise ProjectError('Reference trace source changed; reopen references')
    graph=inspect_project(project,identifier,_full_graph=True)
    result=assemble_trace(graph,direction,depth,layer)
    if expected_source_key!=source_key(project) or result['source_key']!=expected_source_key:raise ProjectError('Reference trace source changed during discovery')
    return result

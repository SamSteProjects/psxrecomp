"""Compare verified saved audit records, never inferred gameplay state."""
import json
from .build import authored_state_key
from .build_history import verify_build, _load, MAX_METADATA
from .project import ProjectError


def _index(report):
    result={}
    for row in report['changes']:
        fields=('scene','owner_id','asset_id','field','scope')
        if any(not isinstance(row.get(k),str) or not row[k] or len(row[k])>2048 for k in fields):
            raise ProjectError('Saved audit has an unsupported change identity')
        for k in ('frame_index','object_index'):
            if row.get(k) is not None and (type(row[k]) is not int or row[k]<0):
                raise ProjectError('Saved audit has an invalid animation record identity')
        identity=tuple(row[k] for k in fields)+(row.get('frame_index'),row.get('object_index'))
        if identity in result:raise ProjectError('Saved audit has ambiguous duplicate change identities')
        result[identity]=row
    return result


def compare_builds(project,left_id,right_id):
    if left_id==right_id:raise ProjectError('Choose two different saved Builds')
    source_key=authored_state_key(project)
    left=verify_build(project,left_id);right=verify_build(project,right_id)
    if left['receipt']['source_disc_sha256']!=right['receipt']['source_disc_sha256']:
        raise ProjectError('Saved Builds refer to different retail disc identities')
    a,b=_index(left['report']),_index(right['report']);changes=[];unchanged=0
    for identity in sorted(a.keys()|b.keys(),key=lambda value:json.dumps(value)):
        l,r=a.get(identity),b.get(identity)
        # Include detailed bounded payload/vector deltas and contributor metadata,
        # even when headline before/after values happen to be equal.
        if json.dumps(l,sort_keys=True,ensure_ascii=False)==json.dumps(r,sort_keys=True,ensure_ascii=False):
            unchanged+=1
            continue
        template=l or r
        changes.append(dict(identity={k:template[k] for k in ('scene','owner_id','asset_id','field','scope')},
                            frame_index=template.get('frame_index'),object_index=template.get('object_index'),
                            status='only_left_audit' if r is None else 'only_right_audit' if l is None else 'different_audit',
                            left=l,right=r))
    result=dict(schema_version='legaia.build-comparison.v1',left_id=left_id,right_id=right_id,
                project_source_key=source_key,source_disc_sha256=left['receipt']['source_disc_sha256'],
                integrity='both_packages_verified',gameplay_verified=False,source_disc_integrity='not_checked',
                comparison_scope='saved_audit_records_only',unchanged_change_count=unchanged,
                difference_count=len(changes),differences=changes,
                packages={side:{k:item['receipt'][k] for k in ('audit_sha256','archive_sha256','authored_state_key')}
                          for side,item in [('left',left),('right',right)]},
                limitation='A record absent from an audit does not establish a runtime value, deletion or scene coverage.')
    if len(json.dumps(result,ensure_ascii=False).encode('utf-8'))>MAX_METADATA:
        raise ProjectError('Saved Build comparison exceeds the eight MiB metadata limit')
    if authored_state_key(project)!=source_key or _load(project,left_id)[0]!=left['receipt'] or _load(project,right_id)[0]!=right['receipt']:
        raise ProjectError('Project or saved receipt changed during comparison')
    return result

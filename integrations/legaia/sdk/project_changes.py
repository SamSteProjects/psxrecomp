"""Exact metadata changes since this service last saved/opened the project."""
from copy import deepcopy
from .project import ProjectError, canonical, digest

PAGE_SIZE = 50
MAX_BYTES = 8 * 1024 * 1024
COLLECTIONS = frozenset(('authored', 'actor_templates', 'actor_drafts', 'scene_views',
    'script_bookmarks', 'actor_selection_sets', 'scene_selection_sets', 'model_vertex_groups',
    'texture_overrides', 'texture_additions', 'model_overrides', 'model_sources',
    'animation_sources', 'audio_sample_sources', 'audio_sample_overrides',
    'audio_overrides', 'audio_bank_overrides'))


def _context(project):
    current = project._document()
    saved = project.saved_document
    if saved is not None and digest(saved) != project.saved_digest:
        raise ProjectError('Saved metadata snapshot no longer matches its identity')
    key = digest(dict(project=str(project.root), saved=project.saved_digest,
                      saved_present=saved is not None, current=digest(current)))
    return current, saved, key


def _changes(current, saved):
    saved = saved if saved is not None else {}
    rows = []
    for section in sorted(set(current) | set(saved)):
        if section in current and section in saved and digest(current[section]) == digest(saved[section]):
            continue
        if section in COLLECTIONS:
            old, new = saved.get(section, {}), current.get(section, {})
            start = len(rows)
            for owner in sorted(set(old) | set(new)):
                if owner not in old or owner not in new or digest(old[owner]) != digest(new[owner]):
                    rows.append((section, owner, owner in old, old.get(owner), owner in new, new.get(owner)))
            if len(rows) == start:
                rows.append((section, None, section in saved, saved.get(section), section in current, current.get(section)))
        else:
            rows.append((section, None, section in saved, saved.get(section), section in current, current.get(section)))
    return rows


def _summary(row):
    section, owner, old_present, old, new_present, new = row
    return dict(section=section, owner_id=owner,
                change='modified' if old_present and new_present else 'added' if new_present else 'removed',
                saved_present=old_present, current_present=new_present, record_key=digest(row))


def review(project, offset=0):
    if type(offset) is not int or offset < 0:
        raise ProjectError('Change review offset must be a nonnegative integer')
    current, saved, key = _context(project)
    rows = _changes(current, saved)
    if len(rows) > 16384 or offset > len(rows):
        raise ProjectError('Change review count or offset exceeds the current metadata bound')
    page = [_summary(row) for row in rows[offset:offset+PAGE_SIZE]]
    result = dict(schema_version='legaia.project-changes.v1', read_only=True,
                  source_key=key, saved_snapshot_present=saved is not None,
                  dirty=project.dirty, saved_document_sha256=project.saved_digest,
                  current_document_sha256=digest(current), total=len(rows), offset=offset,
                  page_size=PAGE_SIZE, records=page,
                  next_offset=offset+len(page) if offset+len(page)<len(rows) else None)
    if len(canonical(result)) > MAX_BYTES:
        raise ProjectError('Change review page exceeds 8 MiB')
    return result


def inspect(project, source_key, section, owner_id, record_key):
    current, saved, key = _context(project)
    if source_key != key:
        raise ProjectError('Project changes are stale; refresh the review')
    if not isinstance(section, str) or not (owner_id is None or isinstance(owner_id, str)):
        raise ProjectError('Invalid project change selector')
    row = next((row for row in _changes(current, saved) if row[0:2] == (section, owner_id)), None)
    if row is None or digest(row) != record_key:
        raise ProjectError('Project change record no longer matches')
    result = dict(schema_version='legaia.project-change-record.v1', read_only=True,
                  source_key=key, **_summary(row), saved=deepcopy(row[3]), current=deepcopy(row[5]))
    if len(canonical(result)) > MAX_BYTES:
        raise ProjectError('Project change record exceeds 8 MiB')
    return result


def save_reviewed(project, source_key):
    if _context(project)[2] != source_key:
        raise ProjectError('Project changed after review; refresh before saving')
    return project.save()

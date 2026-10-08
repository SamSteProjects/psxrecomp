"""Read-only inclusion check against recorded stability source evidence."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

_HASH = re.compile(r'[a-f0-9]{64}\Z')


def audit_stability_sources(root=None, manifest=None):
    root = Path(root or Path(__file__).resolve().parents[3]).resolve()
    if manifest is None:
        manifest = json.loads(Path(__file__).with_name('stability_sources_manifest.json').read_text(encoding='utf-8'))
    if not isinstance(manifest, dict):
        raise ValueError('Invalid stability source manifest')
    files = manifest.get('files')
    if manifest.get('schema_version') != 'legaia.stability-source-manifest.v1' or not isinstance(files, list) or not 1 <= len(files) <= 32:
        raise ValueError('Invalid stability source manifest')
    for key in ('basis_revision', 'release_reference_revision'):
        if not isinstance(manifest.get(key), str) or not re.fullmatch(r'[a-f0-9]{40}', manifest[key]):
            raise ValueError('Invalid stability evidence revision')
    if not isinstance(manifest.get('comparison_receipt_sha256'), str) or not _HASH.fullmatch(manifest['comparison_receipt_sha256']) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(manifest.get('execution_evidence_date'))):
        raise ValueError('Invalid stability evidence identity')
    seen, rows = set(), []
    for record in files:
        if not isinstance(record, dict) or set(record) != {'path', 'category', 'expected_sha256'}:
            raise ValueError('Invalid stability source record')
        name = record.get('path')
        if not isinstance(name, str) or not name or '\\' in name or ':' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or PurePosixPath(name).as_posix() != name or name in seen or record.get('category') not in ('source_sha256', 'fixture_sha256') or not isinstance(record.get('expected_sha256'), str) or not _HASH.fullmatch(record['expected_sha256']):
            raise ValueError('Invalid stability source path or identity')
        seen.add(name)
        row = {**record, 'actual_sha256': None, 'status': 'unreadable'}
        target = root / name
        try:
            resolved = target.resolve()
            if not resolved.is_relative_to(root):
                row['status'] = 'unsafe'
            elif not target.is_file():
                row['status'] = 'missing'
            else:
                before = target.stat()
                if before.st_size > 2 * 1024 * 1024:
                    row['status'] = 'oversized'
                else:
                    with target.open('rb') as source:
                        payload = source.read(2 * 1024 * 1024 + 1)
                    after = target.stat()
                    if len(payload) > 2 * 1024 * 1024 or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        row['status'] = 'unstable'
                    else:
                        row['actual_sha256'] = sha256(payload).hexdigest()
                        row['status'] = 'matched' if row['actual_sha256'] == record['expected_sha256'] else 'changed'
        except OSError:
            pass
        rows.append(row)
    return dict(schema_version='legaia.stability-source-audit.v1', read_only=True,
                scope='recorded_source_inclusion_only', checked_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                basis_revision=manifest['basis_revision'], execution_evidence_date=manifest['execution_evidence_date'],
                release_reference_revision=manifest['release_reference_revision'], comparison_receipt_sha256=manifest['comparison_receipt_sha256'],
                files=rows, all_matched=all(row['status'] == 'matched' for row in rows),
                execution_repeated=False, runtime_binary_verified=False, gameplay_verified=False)

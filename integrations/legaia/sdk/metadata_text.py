"""Bounded authored display text that can survive canonical UTF-8 persistence."""
from .project import ProjectError


def metadata_name(value, label, maximum=80):
    if not isinstance(value, str):
        raise ProjectError(f'{label} must be text')
    if (not 1 <= len(value.strip()) <= maximum or
            any(ord(char) < 32 or ord(char) == 127 or 0xD800 <= ord(char) <= 0xDFFF for char in value)):
        raise ProjectError(f'{label} requires 1..{maximum} printable Unicode characters without surrogates')
    return value.strip()

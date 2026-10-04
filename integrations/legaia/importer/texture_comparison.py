"""Payload deltas with an explicit resized Retail comparison baseline."""
from hashlib import sha256

from .texture_authoring import texture_payload_changes
from .texture_layout_allocation import resize_tim_image, validate_tim_allocation
from .textures import parse_tim


def compare_payloads(source, candidate):
    allocation = validate_tim_allocation(source, candidate)
    if not allocation['layout_changed']:
        return texture_payload_changes(source, candidate), None
    old, new = parse_tim(source), parse_tim(candidate)
    baseline, _ = resize_tim_image(source, sha256(source).hexdigest(), new.width, new.image.height, 0)
    shared = min(old.width, new.width) * min(old.image.height, new.image.height)
    report = dict(schema_version='legaia.texture-retail-comparison.v1',
        source_sha256=sha256(source).hexdigest(), baseline_sha256=sha256(baseline).hexdigest(),
        bpp=new.bpp, source_width=old.width, source_height=old.image.height,
        proposed_width=new.width, proposed_height=new.image.height,
        added_pixels=new.width * new.image.height - shared,
        removed_pixels=old.width * old.image.height - shared, fill_value=0,
        baseline='Retail-top-left-overlap-with-zero-filled-new-pixels')
    return texture_payload_changes(baseline, candidate), report

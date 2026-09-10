"""Source-qualified flag operands; no inferred runtime bank bindings."""
from copy import deepcopy


def build_flag_index(catalog: dict) -> dict:
    groups = {}
    for script in catalog["assets"]:
        if script["asset_kind"] != "script":
            continue
        for reference in script["flag_references"]:
            target = reference["extended_target"]
            context = "current" if target is None else f"extended-{target}"
            identity = (script["semantic_id"].replace("script://", "flag-reference://", 1)
                        + f"/{context}/{reference['bank']}/{reference['index']}")
            if identity not in groups:
                groups[identity] = {
                    "id": identity, "script_id": script["semantic_id"],
                    "script_name": script["name"],
                    "owner_id": script.get("owner_semantic_id") or script["actor_semantic_id"],
                    "partition": script["source_record"]["partition"],
                    "script_status": script["status"],
                    "source_record": deepcopy(script["source_record"]),
                    "bank": reference["bank"], "index": reference["index"],
                    "scope": reference["scope"], "extended_target": target,
                    "runtime_binding": "unresolved", "runtime_value": None,
                    "references": [],
                }
            groups[identity]["references"].append(deepcopy(reference))
    return {
        "schema_version": "legaia.flag-references.v1", "read_only": True,
        "scene_id": "scene://" + catalog["scene"], "groups": list(groups.values()),
        "reference_count": sum(len(group["references"]) for group in groups.values()),
        "coverage": {key: catalog[key] for key in
                     ("script_count", "partial_script_count", "unavailable_script_count")},
        "limitations": [
            "Identities group encoded operands within one source script, not proven runtime variables.",
            "Matching bank/index operands across scripts are not merged; dispatch context may differ.",
            "Extended targets, system selectors and local bank widths retain their source uncertainty.",
            "No current values, story names, runtime writes or unvisited script paths are inferred.",
        ],
    }

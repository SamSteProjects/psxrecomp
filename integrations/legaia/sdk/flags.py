"""Source-qualified flag operands; no inferred runtime bank bindings."""
from copy import deepcopy


def observed_node_flags(status: dict, scene_id: str) -> dict:
    """Describe an already guarded capture, never claim present-time values."""
    unavailable = {"available": False, "reason": "No matching guarded scene capture", "nodes": []}
    observation = status.get("observation") or {}
    epoch = observation.get("epoch") or {}
    if (not status.get("available") or status.get("state") != "observed"
            or not observation.get("snapshot_current_at_capture")
            or "scene://" + str(epoch.get("scene_name")) != scene_id
            or not epoch.get("epoch_id")):
        return unavailable
    nodes = []
    for node in (observation.get("actor_chain") or {}).get("nodes", []):
        identity = node.get("epoch_scoped_node_id", "")
        if not identity.startswith("runtime://" + epoch["epoch_id"] + "/field-node/"):
            return unavailable
        fields = [field for field in node.get("decoded_fields", []) if field.get("property") == "flags"]
        if len(fields) != 1:
            continue
        field = fields[0]
        value = field.get("raw_numeric_value")
        if (field.get("offset") != 16 or field.get("width") != 4
                or field.get("confidence") != "confirmed" or field.get("unresolved")
                or type(value) is not int or not 0 <= value <= 0xFFFFFFFF):
            continue
        nodes.append({"id": identity, "value_hex": f"0x{value:08X}",
                      "set_bits": [bit for bit in range(32) if value & (1 << bit)],
                      "evidence": deepcopy(field.get("evidence", []))})
    return {"available": True, "read_only": True, "freshness": "captured_snapshot",
            "epoch_id": epoch["epoch_id"], "frame": epoch.get("last_validated_frame"),
            "nodes": nodes, "source_binding": "unresolved",
            "note": "Captured node flag words only; no current value or script-owner binding is asserted."}


def build_flag_index(catalog: dict, authored: dict | None = None, qualifications: dict | None = None) -> dict:
    authored = authored or {}
    if qualifications is not None and (not isinstance(qualifications,dict) or set(qualifications)!=set(authored)):
        from .project import ProjectError
        raise ProjectError('Native flag qualifications differ from the requested authored operands')
    consumed = set()
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
            row = deepcopy(reference)
            supported = reference['mnemonic'] in tuple(f'{bank}_{op}' for bank in ('LFLAG','GFLAG','CFLAG') for op in ('SET','CLEAR','TEST'))
            system = reference['mnemonic'] in ('SYSFLAG_SET','SYSFLAG_CLEAR','SYSFLAG_TEST') and target is None and reference['index']<=4095
            key = script['semantic_id'] + f"/{'system-flag' if system else 'flag-bit'}/{reference['pc']:04x}" if supported or system else None
            row.update(retail_index=reference['index'], authored_index=None,
                       effective_index=reference['index'], flag_operand_id=key if supported or key in authored else None)
            if key in authored:
                from importer.flag_authoring import validate_flag_values
                from importer.system_flag_authoring import validate_system_flag_values
                from importer.core import ImportError
                bit = validate_system_flag_values(authored[key]) if system else validate_flag_values(authored[key])
                if not system and reference['mnemonic'] not in tuple(f'{bank}_{op}' for bank in ('LFLAG','GFLAG','CFLAG') for op in ('SET','CLEAR','TEST')):
                    raise ImportError('Authored flag reference is not a supported bit instruction')
                if system and (qualifications is None or key not in qualifications):
                    raise ImportError('Authored system selector requires independent native qualification')
                row.update(authored_index=bit,effective_index=bit)
                if qualifications is not None and key in qualifications:
                    from .flag_qualification import validate
                    row['authored_qualification']=validate(qualifications[key],groups[identity]['owner_id'],key,
                        script['source_record']['sha256'],reference['pc'],reference['mnemonic'],target,reference['index'],bit)
                consumed.add(key)
            groups[identity]["references"].append(row)
    if consumed != set(authored):
        from importer.core import ImportError
        raise ImportError('Authored flag operand is absent from the verified reference catalog')
    return {
        "authored_reference_count": len(consumed),
        "grouping_layer": "retail",
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

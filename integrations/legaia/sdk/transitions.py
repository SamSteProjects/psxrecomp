"""Scene relationships derived from decoded references, never runtime routes."""
from copy import deepcopy


def build_transition_graph(catalog: dict, imported_scenes, overrides=None) -> dict:
    scene = catalog["scene"]
    source_id = "scene://" + scene
    imported = set(imported_scenes)
    nodes = {source_id: {"id": source_id, "name": scene, "imported": source_id in imported,
                         "roles": ["source"], "in_scene_index": True}}
    edges = []
    for script in catalog["assets"]:
        if script["asset_kind"] != "script":
            continue
        for reference in script["transitions"]:
            edge_id = script["semantic_id"].replace("script://", "transition://", 1) + f"/{reference['pc']:04x}"
            name = reference["target_scene_name"]
            target_id = "scene://" + name if name is not None else edge_id + "/unresolved-target"
            if target_id not in nodes:
                nodes[target_id] = {"id": target_id, "name": name, "imported": target_id in imported,
                                    "roles": [], "in_scene_index": reference["target_in_scene_index"]}
            if "destination" not in nodes[target_id]["roles"]:
                nodes[target_id]["roles"].append("destination")
            edges.append({"id": edge_id, "source": source_id, "target": target_id,
                          "script_id": script["semantic_id"], "script_name": script["name"],
                          "owner_id": script.get("owner_semantic_id") or script["actor_semantic_id"],
                          "partition": script["source_record"]["partition"], "script_status": script["status"],
                          "source_record": deepcopy(script["source_record"]),
                          "reference": deepcopy(reference), "reachability": "not_evaluated"})
    for edge in edges:
        identifier = edge["script_id"] + f"/transition/{edge['reference']['pc']:04x}"
        authored = (overrides or {}).get(edge["owner_id"], {}).get("Transitions", {}).get("entries", {}).get(identifier, {})
        fields = ("entry_x_encoded", "entry_z_encoded", "direction_encoded")
        imported_entry = {field: edge["reference"].get(field) for field in fields}
        edge["entry_layers"] = {"imported": imported_entry, "authored": deepcopy(authored),
                                "effective": dict(imported_entry, **authored),
                                "validation": "reverified_on_build" if authored else "imported_reference",
                                "transition_id": identifier}
    return {"schema_version": "legaia.scene-transitions.v1", "read_only": True,
            "scene_id": source_id, "nodes": list(nodes.values()), "edges": edges,
            "coverage": {key: catalog[key] for key in ("script_count", "partial_script_count", "unavailable_script_count")},
            "limitations": ["Edges represent decoded scene-change instructions, not verified gameplay routes.",
                            "Unknown script paths, partition-zero controllers and runtime transitions are not covered.",
                            "Verified named entry operands have a static retail arrival interpretation; it is not a source trigger position or runtime-verified route."]}

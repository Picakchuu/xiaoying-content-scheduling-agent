"""Strict structured action boundary for untrusted model proposals."""
import json

SCHEMAS = {
    "search_materials": {"query": str},
    "generate_script": {"variant": str, "material_ids": list},
    "estimate_cost": {},
    "save_plan": {},
    "finish": {"reason": str},
}


def parse_action(raw):
    if isinstance(raw, str):
        if len(raw) > 20000:
            raise ValueError("action exceeds size limit")
        raw = json.loads(raw)
    if not isinstance(raw, dict) or set(raw) != {"action", "args", "why"}:
        raise ValueError("expected action, args and why")
    name, args, why = raw["action"], raw["args"], raw["why"]
    if not isinstance(name, str) or name not in SCHEMAS:
        raise ValueError("unknown action")
    if not isinstance(args, dict) or set(args) != set(SCHEMAS[name]):
        raise ValueError("unexpected action arguments")
    if not isinstance(why, str) or not why.strip() or len(why) > 500:
        raise ValueError("why must be a short non-empty rationale")
    for key, kind in SCHEMAS[name].items():
        value = args[key]
        if not isinstance(value, kind) or not value:
            raise ValueError(f"invalid {key}")
        if isinstance(value, list) and any(not isinstance(x, str) or not x for x in value):
            raise ValueError(f"invalid {key} items")
    return raw

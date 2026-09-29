"""Transparent rule-based personalization."""

DIET_RULES = {
    "vegetarian": {"non_vegetarian"},
    "vegan": {"non_vegan", "non_vegetarian"},
    "gluten_free": {"gluten"},
    "dairy_free": {"dairy"},
}
LEVEL_ORDER = {"info": 0, "note": 1, "check": 2, "alert": 3}


def default_profile():
    return {"allergies": [], "diet": [], "health": []}


def _max_level(a, b):
    return a if LEVEL_ORDER[a] >= LEVEL_ORDER[b] else b


def personalize(findings, profile):
    allergies = set(profile.get("allergies", []))
    diets = profile.get("diet", [])
    health = set(profile.get("health", []))
    non_trace_ids = {f["kb"]["id"] for f in findings if not f["trace"]}
    out = []
    for f in findings:
        kb = f["kb"]
        if f["trace"] and kb["id"] in non_trace_ids:
            continue
        reasons, level = [], "info"
        key = kb.get("allergen_key", "")
        # Rule 1: allergen match + user has that allergy -> alert
        if key and key in allergies:
            reasons.append({"type": "trace_allergy" if f["trace"] else "allergy",
                            "name_key": "allergy_" + key})
            level = "alert"
        # Rule 2: ingredient conflicts with selected diet -> check
        if not f["trace"]:
            for diet in diets:
                if DIET_RULES.get(diet, set()) & set(kb.get("diet_flags", [])):
                    reasons.append({"type": "diet", "name_key": "diet_" + diet})
                    level = _max_level(level, "check")
            # Rule 3: ingredient relevant to a selected health note -> note
            for h in health:
                if h in kb.get("health_flags", []):
                    reasons.append({"type": "health", "name_key": "health_" + h})
                    level = _max_level(level, "note")
        g = dict(f)
        g.update({"level": level, "reasons": reasons})
        out.append(g)
    out.sort(key=lambda x: -LEVEL_ORDER[x["level"]])
    return out


def overall_result(personal, unknown_count):
    levels = {p["level"] for p in personal}
    if "alert" in levels:
        overall = "alert"
    elif "check" in levels:
        overall = "check"
    else:
        overall = "ok"
    return {"overall": overall, "unknown_count": unknown_count}

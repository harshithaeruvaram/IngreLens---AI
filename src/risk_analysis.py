"""Turn raw matches into findings (one per knowledge-base entry)."""


def build_findings(matches, kb):
    merged = {}
    for m in matches:
        key = (m["kb_index"], m["trace"])
        if key not in merged:
            merged[key] = {"kb": kb[m["kb_index"]], "ingredient_texts": [m["ingredient_text"]],
                           "methods": [m["method"]], "needs_check": m["needs_check"],
                           "trace": m["trace"]}
        else:
            f = merged[key]
            if m["ingredient_text"] not in f["ingredient_texts"]:
                f["ingredient_texts"].append(m["ingredient_text"])
            f["methods"].append(m["method"])
            f["needs_check"] = f["needs_check"] and m["needs_check"]
    return list(merged.values())


def summarize_by_category(findings):
    counts = {}
    for f in findings:
        counts[f["kb"]["category"]] = counts.get(f["kb"]["category"], 0) + 1
    return counts

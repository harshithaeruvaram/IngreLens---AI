"""Build consumer-friendly explanations (English / Telugu)."""
from src.i18n import t

ICONS = {"alert": "🔴", "check": "🟡", "note": "ℹ️", "info": "⚪"}
CATEGORY_KEYS = {"allergen": "cat_allergen", "additive": "cat_additive",
                 "dietary": "cat_dietary", "general": "cat_general"}


def _pick(entry, field, lang):
    return entry.get(f"{field}_{lang}") or entry.get(f"{field}_en", "")


def _reason_text(reason, lang):
    name = t(reason["name_key"], lang)
    key = {"allergy": "reason_allergy", "trace_allergy": "reason_trace",
           "diet": "reason_diet", "health": "reason_health"}[reason["type"]]
    return t(key, lang, name=name)


def _result_text(pf, lang):
    level = pf["level"]
    if level == "alert":
        return t("res_trace" if pf["trace"] else "res_alert", lang)
    return t({"check": "res_diet", "note": "res_health", "info": "res_info"}[level], lang)


def build_explanation(pf, lang="en"):
    kb = pf["kb"]
    name = kb["ingredient_te"] if lang == "te" and kb.get("ingredient_te") else kb["ingredient"]
    reasons = [_reason_text(r, lang) for r in pf["reasons"]] or [t("reason_none", lang)]
    return {
        "detected": ", ".join(pf["ingredient_texts"]),
        "matched_entry": name,
        "category": t(CATEGORY_KEYS.get(kb["category"], "cat_general"), lang),
        "explanation": _pick(kb, "explanation", lang),
        "high_intake": _pick(kb, "high_intake", lang),
        "reasons": reasons,
        "result": _result_text(pf, lang),
        "level": pf["level"],
        "icon": ICONS[pf["level"]],
        "trace": pf["trace"],
        "fuzzy_note": t("fuzzy_note", lang) if pf["needs_check"] else "",
        "source": kb.get("source", ""),
        "source_url": kb.get("source_url", ""),
        "verified": bool(kb.get("reviewed", False)),
    }


def overall_text(overall, lang="en"):
    key = {"alert": "overall_alert", "check": "overall_check", "ok": "overall_ok"}[overall["overall"]]
    return t(key, lang)

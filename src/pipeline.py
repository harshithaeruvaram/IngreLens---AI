"""End-to-end pipeline used by Colab tests and the Streamlit app."""
import os
from src import nlp, matching, risk_analysis, personalization, explainability

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE, "data", "knowledge_base", "ingredient_kb.json")
_matcher = None


def get_matcher():
    global _matcher
    if _matcher is None:
        _matcher = matching.Matcher(matching.load_kb(KB_PATH))
    return _matcher


def analyze_text(raw_text, profile, lang="en"):
    parsed = nlp.process_text(raw_text)
    matcher = get_matcher()
    matches, unknown = matcher.match_all(parsed["ingredients"], parsed["traces"])
    findings = risk_analysis.build_findings(matches, matcher.kb)
    personal = personalization.personalize(findings, profile)
    overall = personalization.overall_result(personal, len(unknown))
    return {
        "parsed": parsed,
        "unknown": unknown,
        "personal": personal,
        "overall": overall,
        "explanations": [explainability.build_explanation(p, lang) for p in personal],
        "overall_text": explainability.overall_text(overall, lang),
    }


def analyze_image(img_bgr, profile, lang="en", mode="standard"):
    if img_bgr is None:
        raise ValueError("No image")
    from src import preprocessing, ocr
    prepped = preprocessing.preprocess(img_bgr, mode)
    o = ocr.run_ocr(prepped)
    result = analyze_text(o["text"], profile, lang)
    result.update({"ocr": o, "preprocessed": prepped})
    return result

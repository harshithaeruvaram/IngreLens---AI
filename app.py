import cv2
import numpy as np
import streamlit as st
from PIL import Image

from src import pipeline, preprocessing
from src.i18n import t

st.set_page_config(page_title="IngreLens AI", page_icon="🔍", layout="wide")

LANGS = {"English": "en", "తెలుగు": "te"}
ALLERGY_KEYS = ["milk", "wheat", "soy", "peanut", "tree_nuts", "sesame", "egg", "fish", "shellfish"]
DIET_KEYS = ["vegetarian", "vegan", "gluten_free", "dairy_free"]
HEALTH_KEYS = ["sugar", "salt"]

lang = LANGS[st.sidebar.selectbox("Language / భాష", list(LANGS.keys()), key="lang_choice")]

st.title("🔍 " + t("app_title", lang))
st.caption(t("subtitle", lang))

# ---------- Profile ----------
st.sidebar.header(t("profile_header", lang))
allergies = st.sidebar.multiselect(t("allergies_label", lang), ALLERGY_KEYS, key="allergies",
                                   format_func=lambda k: t("allergy_" + k, lang))
diet = st.sidebar.multiselect(t("diet_label", lang), DIET_KEYS, key="diet",
                              format_func=lambda k: t("diet_" + k, lang))
health = st.sidebar.multiselect(t("health_label", lang), HEALTH_KEYS, key="health",
                                format_func=lambda k: t("health_" + k, lang))
profile = {"allergies": allergies, "diet": diet, "health": health}

# ---------- Input ----------
mode = st.radio(t("input_mode", lang), ["photo", "text"], key="mode", horizontal=True,
                format_func=lambda k: t("mode_" + k, lang))

if mode == "photo":
    up = st.file_uploader(t("upload", lang), type=["jpg", "jpeg", "png"])
    if up is not None:
        pil = Image.open(up).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        prepped = preprocessing.preprocess(img_bgr, "standard")
        c1, c2 = st.columns(2)
        c1.image(pil, caption=t("your_image", lang))
        c2.image(prepped, caption=t("prepared_image", lang), clamp=True)
        if st.button(t("run_ocr", lang)):
            with st.spinner(t("reading", lang)):
                try:
                    from src import ocr
                    text = ocr.run_ocr(prepped)["text"]
                    st.session_state["raw_ocr"] = text
                    st.session_state["edit_text"] = text
                    st.session_state["analyzed"] = False
                except Exception:
                    st.error(t("err_ocr", lang))
    if st.session_state.get("raw_ocr"):
        st.text_area(t("raw_text", lang), value=st.session_state["raw_ocr"], disabled=True, height=120)
        st.caption(t("edit_hint", lang))
    st.text_area(t("cleaned_text", lang) + " / " + t("type_hint", lang), key="edit_text", height=150)
else:
    st.text_area(t("type_hint", lang), key="edit_text", height=150)

if st.button(t("analyze", lang), type="primary"):
    st.session_state["analyzed"] = True

# ---------- Result ----------
if st.session_state.get("analyzed"):
    text = st.session_state.get("edit_text", "")
    if not text.strip():
        st.warning(t("err_no_text", lang))
    else:
        res = pipeline.analyze_text(text, profile, lang)
        st.subheader(t("overall_header", lang))
        level = res["overall"]["overall"]
        {"alert": st.error, "check": st.warning, "ok": st.success}[level](res["overall_text"])
        if res["overall"]["unknown_count"]:
            st.info(t("unknown_warn", lang, n=res["overall"]["unknown_count"]))

        st.text_area(t("cleaned_text", lang), value=", ".join(res["parsed"]["ingredients"]),
                     disabled=True, height=100)

        for e in res["explanations"]:
            title = f"{e['icon']} {e['matched_entry']}"
            if e["trace"]:
                title += f"  ({t('traces_header', lang)})"
            with st.expander(title, expanded=e["level"] in ("alert", "check")):
                st.markdown(f"**{t('detected', lang)}:** {e['detected']}")
                st.markdown(f"**{t('matched', lang)}:** {e['matched_entry']}")
                st.markdown(f"**{t('category', lang)}:** {e['category']}")
                st.markdown(f"**{t('safety_card', lang)}:** {e['explanation']}")
                st.markdown(f"**{t('high_intake', lang)}:** {e['high_intake']}")
                st.markdown(f"**{t('why', lang)} / {t('for_you', lang)}:**")
                for r in e["reasons"]:
                    st.markdown(f"- {r}")
                st.markdown(f"**{t('result', lang)}:** {e['result']}")
                if e["fuzzy_note"]:
                    st.caption(e["fuzzy_note"])
                src = e["source"] if e["source"] else t("no_source", lang)
                st.caption(f"{t('source', lang)}: {src} {e['source_url']}")
                if not e["verified"]:
                    st.caption(t("not_verified", lang))

        if res["unknown"]:
            st.markdown(f"**{t('not_in_db_header', lang)}:** " + ", ".join(res["unknown"]))

st.divider()
st.info(t("disclaimer", lang))

---
title: IngreLens AI
emoji: 🔍
colorFrom: green
colorTo: blue
sdk: streamlit
app_file: app.py
pinned: false
---

# IngreLens AI
Explainable personalized food-label screening using OCR and NLP (English / Telugu).

**Disclaimer:** This system provides an AI-based food-label screening result for educational and
informational purposes. It does not replace medical advice or laboratory testing.

## Pipeline
Label image -> preprocessing -> OCR (EasyOCR) -> NLP cleaning -> ingredient splitting ->
knowledge-base matching -> allergen/diet/health-note rules -> personalized, explained result.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Limitations
- Rule-based screening only; not a laboratory toxicity detector and not medical advice.
- Knowledge-base entries are marked "not yet verified" until sources are added and reviewed.
- Multilingual label reading/translation is not implemented (Telugu covers app text and explanations).
- OCR / matching accuracy: Not yet evaluated.

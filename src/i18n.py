"""Language switching (English / Telugu)."""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "translations.json")
_cache = None


def load():
    global _cache
    if _cache is None:
        with open(_PATH, encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def t(key, lang="en", **kwargs):
    data = load()
    text = data.get(lang, {}).get(key) or data["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text

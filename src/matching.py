"""Match ingredients to the knowledge base (whole-word phrase match + careful spelling match)."""
import json
import re
from rapidfuzz.distance import Levenshtein
from src.nlp import normalize_unicode

SPLIT_PATTERN = re.compile(r"[\s,;:()\[\]{}/\\|\"'’.*·•\-&]+")
GENERIC_WORDS = {"raising", "agent", "emulsifier", "acidity", "regulator", "colour", "color",
                 "antioxidant", "preservative", "stabilizer", "stabiliser", "flavour", "flavor",
                 "flavouring", "flavoring", "thickener", "sweetener", "and", "of", "class",
                 "contains", "contain", "natural", "artificial", "identical", "permitted", "added"}
FUZZY_BLOCK = {"batter", "lactase", "sucrase", "butyl"}


def stem(token):
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text):
    text = normalize_unicode(text).casefold()
    return [stem(t) for t in SPLIT_PATTERN.split(text) if t]


def load_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_generic(text):
    tokens = tokenize(text)
    return bool(tokens) and all(t in GENERIC_WORDS for t in tokens)


class Matcher:
    def __init__(self, kb):
        self.kb = kb
        self.alias_index = {}
        self.excludes = {}
        self.max_len = 1
        self.fuzzy_aliases = []
        for idx, entry in enumerate(kb):
            for alias in entry.get("aliases", []):
                toks = tuple(tokenize(alias))
                if not toks:
                    continue
                self.alias_index.setdefault(toks, []).append(idx)
                self.max_len = max(self.max_len, len(toks))
                if (len(toks) == 1 and len(toks[0]) >= 6 and toks[0].isascii()
                        and toks[0].isalpha()):
                    self.fuzzy_aliases.append((toks[0], idx))
            self.excludes[idx] = [tuple(tokenize(p)) for p in entry.get("exclude_phrases", [])]

    def _excluded(self, idx, tokens):
        for phrase in self.excludes.get(idx, []):
            n = len(phrase)
            for i in range(len(tokens) - n + 1):
                if tuple(tokens[i:i + n]) == phrase:
                    return True
        return False

    def _fuzzy(self, token):
        if (len(token) < 6 or not token.isascii() or not token.isalpha()
                or token in FUZZY_BLOCK):
            return None
        best = None
        for alias, idx in self.fuzzy_aliases:
            if alias[0] != token[0]:
                continue
            d = Levenshtein.distance(token, alias)
            limit = 1 if len(alias) <= 8 else 2
            if 0 < d <= limit and (best is None or d < best[0]):
                best = (d, idx, alias)
        return best

    @staticmethod
    def _make(idx, method, alias, needs_check):
        return {"kb_index": idx, "method": method, "matched_alias": alias, "needs_check": needs_check}

    def match_ingredient(self, text):
        tokens = tokenize(text)
        matches, covered, i = [], set(), 0
        while i < len(tokens):
            hit = False
            for n in range(min(self.max_len, len(tokens) - i), 0, -1):
                key = tuple(tokens[i:i + n])
                if key in self.alias_index:
                    for idx in self.alias_index[key]:
                        if not self._excluded(idx, tokens):
                            matches.append(self._make(idx, "exact", " ".join(key), False))
                    covered.update(range(i, i + n))
                    i += n
                    hit = True
                    break
            if not hit:
                i += 1
        for pos, tok in enumerate(tokens):
            if pos in covered:
                continue
            found = self._fuzzy(tok)
            if found and not self._excluded(found[1], tokens):
                matches.append(self._make(found[1], "fuzzy", found[2], True))
        unique = {}
        for m in matches:
            k = m["kb_index"]
            if k not in unique or (unique[k]["method"] == "fuzzy" and m["method"] == "exact"):
                unique[k] = m
        return list(unique.values())

    def match_all(self, ingredients, traces=None):
        results, unknown = [], []
        for text in ingredients:
            ms = self.match_ingredient(text)
            if not ms and not is_generic(text):
                unknown.append(text)
            for m in ms:
                m.update({"ingredient_text": text, "trace": False})
                results.append(m)
        for text in traces or []:
            for m in self.match_ingredient(text):
                m.update({"ingredient_text": text, "trace": True})
                results.append(m)
        return results, unknown

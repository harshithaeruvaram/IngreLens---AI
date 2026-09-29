"""NLP: clean OCR text, find the ingredient section, split into ingredients."""
import re
import unicodedata

KEEP_PUNCT = set(",;:()[]{}%.-/&'’•·*\"")
OCR_DIGIT_MAP = {"o": "0", "l": "1", "i": "1", "|": "1", "s": "5"}
E_PATTERN = re.compile(r"\b(?:e|ins)\s?-?\s?([0-9oli|s]{3,4})([a-i])?\b(?:\s*\(\s*[ivx]+\s*\))?")
FREE_PATTERN = re.compile(r"\b(?:gluten|dairy|lactose|egg|nut|nuts|soy|soya|milk|sugar|peanut|wheat)[\s-]+free\b")
HEADER = re.compile(r"(?:ingred[il1]ents?|ingr[eé]dients?|ingredientes|ingredienti|zutaten)\s*[:;.\-]?")
STOP = re.compile(r"\b(?:nutrition|nutritional|nutrient|energy|allergen advice|allergy advice|best before|"
                  r"use by|storage|store in|manufactured|marketed|mfd|net weight|net wt|fssai|customer care|mrp)\b")
TRACE = re.compile(r"(?:may contain|might contain|contains traces of|traces of|produced in a facility|"
                   r"manufactured in a facility|made in a facility|processed in a facility)(.{0,200}?)(?:\.|$)")


def normalize_unicode(text):
    return unicodedata.normalize("NFKC", text)


def fix_line_breaks(text):
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s*\n\s*", " ", text)


def canonicalize_e_numbers(text):
    """Turn 'E 121', 'El21', 'INS 500(ii)' into 'e121', 'e121', 'e500'."""
    def repl(m):
        raw = m.group(1)
        if not any(c.isdigit() for c in raw):
            return m.group(0)
        digits = "".join(OCR_DIGIT_MAP.get(c, c) for c in raw)
        if not digits.isdigit() or int(digits) < 100:
            return m.group(0)
        return " e" + digits + (m.group(2) or "") + " "
    return E_PATTERN.sub(repl, text)


def remove_noise(text):
    """Keep letters (any language), marks, numbers, spaces and useful punctuation."""
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] in ("L", "M", "N") or ch.isspace() or ch in KEEP_PUNCT:
            out.append(ch)
        else:
            out.append(" ")
    return "".join(out)


def clean_item(text):
    text = text.strip(" .,;:-/'\"•·*&")
    text = re.sub(r"\s+", " ", text)
    if not text or re.fullmatch(r"[ivx]{1,4}", text) or re.fullmatch(r"[\d\s.,]+", text):
        return ""
    return text


def clean_ocr_text(text):
    if not text:
        return ""
    text = normalize_unicode(text)
    text = fix_line_breaks(text)
    text = text.casefold()
    text = canonicalize_e_numbers(text)
    text = remove_noise(text)
    text = FREE_PATTERN.sub(" ", text)
    text = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_traces(clean_text):
    traces = []

    def repl(m):
        chunk = m.group(1)
        s = STOP.search(chunk)
        if s:
            chunk = chunk[:s.start()]
        for part in re.split(r"[,;]| and | or ", chunk):
            part = clean_item(part)
            if part:
                traces.append(part)
        return " "
    return TRACE.sub(repl, clean_text), traces


def extract_ingredient_section(clean_text):
    m = HEADER.search(clean_text)
    section = clean_text[m.end():] if m else clean_text
    s = STOP.search(section)
    if s:
        section = section[:s.start()]
    return section.strip(" .,;:")


def split_top_level(text):
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch in ",;•·" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def flatten_ingredients(text):
    """'chocolate (sugar, cocoa)' -> ['chocolate', 'sugar', 'cocoa']"""
    result = []
    for item in split_top_level(text):
        positions = [item.find(c) for c in "([{" if item.find(c) != -1]
        open_pos = min(positions) if positions else -1
        if open_pos == -1:
            result.append(item)
            continue
        depth, close_pos = 0, -1
        for i in range(open_pos, len(item)):
            if item[i] in "([{":
                depth += 1
            elif item[i] in ")]}":
                depth -= 1
                if depth == 0:
                    close_pos = i
                    break
        result.append(item[:open_pos])
        if close_pos == -1:
            result.extend(flatten_ingredients(item[open_pos + 1:]))
        else:
            result.extend(flatten_ingredients(item[open_pos + 1:close_pos]))
            rest = item[close_pos + 1:]
            if rest.strip():
                result.extend(flatten_ingredients(rest))
    cleaned = [clean_item(x) for x in result]
    return [x for x in cleaned if x]


def process_text(raw_text):
    clean = clean_ocr_text(raw_text)
    without_traces, traces = split_traces(clean)
    section = extract_ingredient_section(without_traces)
    ingredients = flatten_ingredients(section)
    return {"clean_text": clean, "section": section, "ingredients": ingredients, "traces": traces}

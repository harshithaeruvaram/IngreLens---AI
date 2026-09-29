"""OCR with EasyOCR (CPU)."""
_reader = None


def get_reader(langs=("en",), gpu=False):
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(list(langs), gpu=gpu)
    return _reader


def run_ocr(image, min_conf=0.2):
    """Returns {'text', 'avg_conf', 'n_boxes'}; text is joined line by line."""
    results = get_reader().readtext(image)
    items = []
    for bbox, text, conf in results:
        if conf < min_conf or not text.strip():
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append({"text": text, "conf": float(conf), "x": min(xs),
                      "y": sum(ys) / len(ys), "h": max(ys) - min(ys)})
    items.sort(key=lambda d: (d["y"], d["x"]))
    lines, cur, cur_y = [], [], None
    for it in items:
        if cur_y is None or abs(it["y"] - cur_y) <= 0.6 * max(it["h"], 1):
            cur.append(it)
            cur_y = sum(c["y"] for c in cur) / len(cur)
        else:
            lines.append(cur)
            cur, cur_y = [it], it["y"]
    if cur:
        lines.append(cur)
    text = "\n".join(" ".join(c["text"] for c in sorted(line, key=lambda d: d["x"])) for line in lines)
    avg = sum(i["conf"] for i in items) / len(items) if items else 0.0
    return {"text": text, "avg_conf": avg, "n_boxes": len(items)}

"""Image preprocessing for OCR."""
import cv2
import numpy as np


def resize_for_ocr(img, target_width=1600):
    h, w = img.shape[:2]
    if 1000 <= w <= 2400:
        return img
    scale = target_width / w
    interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=interp)


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def enhance_contrast(gray):
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def denoise(gray):
    return cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)


def sharpen(gray):
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    return cv2.addWeighted(gray, 1.5, blur, -0.5, 0)


def binarize(gray):
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)


def preprocess(img, mode="standard"):
    """Modes: none, standard (gray+contrast), denoise, sharp, binary."""
    img = resize_for_ocr(img)
    gray = to_gray(img)
    if mode == "none":
        return gray
    gray = enhance_contrast(gray)
    if mode == "standard":
        return gray
    if mode == "denoise":
        return denoise(gray)
    if mode == "sharp":
        return sharpen(gray)
    if mode == "binary":
        return binarize(denoise(gray))
    raise ValueError(f"Unknown mode: {mode}")

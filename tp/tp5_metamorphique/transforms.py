"""Transformations d'images pour les tests métamorphiques (TP5).

Chaque fonction prend une image 8x8 (numpy, pixels entre 0 et 1) et renvoie une NOUVELLE
image de même forme, pixels ramenés entre 0 et 1. Le paramètre d'intensité est décrit
dans chaque docstring : c'est à vous de justifier la valeur choisie.
"""

import numpy as np
from PIL import Image


def _clip(img):
    return np.clip(img, 0.0, 1.0)


def brightness(img, delta):
    """Luminosité : ajoute delta à chaque pixel.
    delta = 0.05 : +5 % de l'échelle ; delta < 0 : image plus sombre."""
    return _clip(np.asarray(img, dtype=float) + delta)


def contrast(img, factor):
    """Contraste : écarte (factor > 1) ou rapproche (factor < 1) chaque pixel de la moyenne de l'image.
    factor = 1 : inchangé ; factor = 0 : image uniforme."""
    img = np.asarray(img, dtype=float)
    mean = img.mean()
    return _clip(mean + (img - mean) * factor)


def noise(img, sigma, seed=0):
    """Bruit gaussien additif d'écart-type sigma (0.05 : léger, 0.2 : fort).
    seed fixe : même bruit à chaque exécution (test reproductible)."""
    rng = np.random.default_rng(seed)
    img = np.asarray(img, dtype=float)
    return _clip(img + rng.normal(0.0, sigma, img.shape))


def translate(img, dx, dy=0):
    """Translation de dx pixels vers la droite et dy pixels vers le bas (entiers).
    1 pixel = 1/8 de la largeur de l'image ; les pixels qui entrent sont noirs."""
    img = np.asarray(img, dtype=float)
    out = np.zeros_like(img)
    h, w = img.shape
    out[max(dy, 0) : h + min(dy, 0), max(dx, 0) : w + min(dx, 0)] = img[
        max(-dy, 0) : h + min(-dy, 0), max(-dx, 0) : w + min(-dx, 0)
    ]
    return out


def rotate(img, angle):
    """Rotation de angle degrés, sens inverse des aiguilles d'une montre.
    Multiples de 90 : rotation exacte ; sinon interpolation bilinéaire (coins remplis de noir)."""
    img = np.asarray(img, dtype=float)
    if angle % 90 == 0:
        return np.rot90(img, k=int(angle // 90) % 4).copy()
    rotated = Image.fromarray(img.astype(np.float32)).rotate(angle, resample=Image.BILINEAR)
    return _clip(np.asarray(rotated, dtype=float))


def fog(img, alpha):
    """Brouillard : mélange avec un gris uniforme (0.5).
    alpha = 0 : inchangé ; alpha = 1 : image entièrement grise."""
    return _clip((1 - alpha) * np.asarray(img, dtype=float) + alpha * 0.5)

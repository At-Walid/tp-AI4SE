"""Petit classifieur de chiffres manuscrits (TP5).

Images 8x8 du jeu « digits » fourni avec scikit-learn (aucun téléchargement),
pixels entre 0 (noir) et 1 (blanc). Modèle : régression logistique, graine fixe.

    import model
    label, confidence = model.predict(img)      # img : tableau numpy 8x8
    images, labels = model.test_images()        # images jamais vues à l'entraînement
    images_de_6, _ = model.test_images(digit=6)

Le modèle est entraîné une fois puis enregistré (image Docker : /opt/lab/digits_model.pkl ;
ailleurs : tp/tp5_metamorphique/.cache/). python tp/tp5_metamorphique/model.py --train le réentraîne.
"""

import argparse
import os
import pickle
from pathlib import Path

import numpy as np

SEED = 0
MODEL_PATH = Path(os.environ.get("TP5_MODEL_PATH", "/opt/lab/digits_model.pkl"))
LOCAL_CACHE = Path(__file__).resolve().parent / ".cache" / "digits_model.pkl"

_model = None


def _split():
    from sklearn.datasets import load_digits
    from sklearn.model_selection import train_test_split

    digits = load_digits()
    images = digits.images / 16.0
    return train_test_split(images, digits.target, test_size=0.3, random_state=SEED, stratify=digits.target)


def train():
    from sklearn.linear_model import LogisticRegression

    x_train, _, y_train, _ = _split()
    classifier = LogisticRegression(max_iter=3000, random_state=SEED)
    return classifier.fit(x_train.reshape(len(x_train), -1), y_train)


def save(classifier, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(classifier, f)


def get_model():
    """Charge le modèle enregistré (ou l'entraîne et l'enregistre la première fois)."""
    global _model
    if _model is None:
        for path in (MODEL_PATH, LOCAL_CACHE):
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        _model = pickle.load(f)
                    break
                except Exception:  # fichier abîmé ou autre version de scikit-learn
                    pass
        else:
            _model = train()
            save(_model, LOCAL_CACHE)
    return _model


def predict_proba(img):
    """Probabilité de chacune des 10 classes pour une image 8x8."""
    flat = np.asarray(img, dtype=float).reshape(1, -1)
    return get_model().predict_proba(flat)[0]


def predict(img):
    """Renvoie (classe prédite, confiance) pour une image 8x8 de pixels entre 0 et 1."""
    proba = predict_proba(img)
    label = int(np.argmax(proba))
    return label, float(proba[label])


def predict_many(images):
    """Classes prédites pour une liste d'images (plus rapide qu'une boucle sur predict)."""
    flat = np.asarray(images, dtype=float).reshape(len(images), -1)
    return [int(c) for c in get_model().predict(flat)]


def test_images(digit=None):
    """Images de test (non vues à l'entraînement) et leurs vraies classes ; digit filtre une classe."""
    _, x_test, _, y_test = _split()
    if digit is not None:
        keep = y_test == digit
        x_test, y_test = x_test[keep], y_test[keep]
    return list(x_test), [int(y) for y in y_test]


test_images.__test__ = False  # ce n'est pas un test pytest, malgré son nom


def main():
    parser = argparse.ArgumentParser(description="Entraîne et enregistre le classifieur du TP5.")
    parser.add_argument("--train", action="store_true", help="réentraîne le modèle")
    parser.add_argument("--out", type=Path, default=LOCAL_CACHE, help="fichier de sortie")
    args = parser.parse_args()
    classifier = train() if args.train else get_model()
    if args.train:
        save(classifier, args.out)
        print(f"Modèle enregistré : {args.out}")
    images, labels = test_images()
    accuracy = np.mean(np.array(predict_many(images)) == np.array(labels))
    print(f"Exactitude sur les {len(labels)} images de test : {accuracy:.3f}")


if __name__ == "__main__":
    main()

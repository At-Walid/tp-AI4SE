"""Tests de l'outillage : transformations du TP5, modèle, et mini_mutate du TP3."""

from pathlib import Path

import numpy as np
import pytest

import model
import transforms as T
from tools import mini_mutate

ROOT = Path(__file__).resolve().parents[1]
IMG = model.test_images()[0][0]


@pytest.mark.parametrize(
    "transform",
    [
        lambda x: T.brightness(x, 0.3),
        lambda x: T.brightness(x, -0.3),
        lambda x: T.contrast(x, 3.0),
        lambda x: T.noise(x, 0.5),
        lambda x: T.translate(x, 2, -1),
        lambda x: T.rotate(x, 33),
        lambda x: T.fog(x, 0.7),
    ],
)
def test_transformations_gardent_forme_et_bornes(transform):
    out = transform(IMG)
    assert out.shape == (8, 8) and out.min() >= 0.0 and out.max() <= 1.0
    assert out is not IMG


@pytest.mark.parametrize(
    "identity",
    [
        lambda x: T.brightness(x, 0.0),
        lambda x: T.contrast(x, 1.0),
        lambda x: T.fog(x, 0.0),
        lambda x: T.rotate(x, 0),
        lambda x: T.rotate(x, 360),
        lambda x: T.translate(x, 0, 0),
        lambda x: T.rotate(T.rotate(x, 90), -90),
    ],
)
def test_intensite_nulle_ne_change_rien(identity):
    assert np.allclose(identity(IMG), IMG)


def test_bruit_reproductible_avec_la_graine():
    assert np.array_equal(T.noise(IMG, 0.1, seed=3), T.noise(IMG, 0.1, seed=3))
    assert not np.array_equal(T.noise(IMG, 0.1, seed=3), T.noise(IMG, 0.1, seed=4))


def test_translation_deplace_les_pixels():
    img = np.zeros((8, 8))
    img[2, 3] = 1.0
    assert T.translate(img, 1)[2, 4] == 1.0 and T.translate(img, 0, 1)[3, 3] == 1.0


def test_fog_total_donne_un_gris_uniforme():
    assert np.allclose(T.fog(IMG, 1.0), 0.5)


def test_modele_deterministe_et_coherent():
    images, labels = model.test_images()
    assert len(images) == len(labels) == 540
    label, confidence = model.predict(images[0])
    assert label == model.predict_many(images[:1])[0] and 0 <= confidence <= 1
    assert all(lab == 6 for lab in model.test_images(digit=6)[1])


def test_mini_mutate_produit_les_trois_mutants_du_cours():
    source = (ROOT / "tp" / "tp1_generation" / "remise.py").read_text(encoding="utf-8")
    found = {(line, before, after) for line, before, after, _ in mini_mutate.generate(source)}
    assert set(mini_mutate.COURSE) <= found


def test_mini_mutate_mutants_valides_et_differents():
    source = (ROOT / "tp" / "tp1_generation" / "remise.py").read_text(encoding="utf-8")
    mutants = mini_mutate.generate(source) + mini_mutate.bonus(source)
    for _, _, _, mutated in mutants:
        compile(mutated, "mutant", "exec")
    assert len({m[3] for m in mutants}) == len(mutants)


def test_mini_mutate_complet_sur_une_petite_suite(tmp_path, capsys):
    suite = tmp_path / "test_petite_suite.py"
    suite.write_text(
        "from remise import remise\n"
        "def test_a():\n    assert remise(100, 10) == 80\n"
        "def test_rouge():\n    assert remise(100, -1) == 'ValueError attendue'\n",
        encoding="utf-8",
    )
    assert mini_mutate.main([str(ROOT / "tp" / "tp1_generation" / "remise.py"), str(suite)]) == 0
    out = capsys.readouterr().out
    assert "1 test(s) échouent déjà" in out and "Résumé : 12 mutants" in out

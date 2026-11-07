"""Tests de tools/voir_chiffres.py : la page des chiffres du TP5, avant et après une transformation."""

import re

import pytest

import model
from tools import voir_chiffres as vc
from transforms import fog, rotate

IMAGES, LABELS = model.test_images()


def cards(path):
    text = path.read_text(encoding="utf-8")
    return text, re.findall(r'<div class="card( flag)?">', text)


def test_page_avant_apres(tmp_path):
    avant, labels = IMAGES[:40], LABELS[:40]
    apres = [rotate(img, 90) for img in avant]
    path = vc.voir_chiffres(avant, apres, labels, nom="essai", dossier=tmp_path)
    text, found = cards(path)
    changed = sum(b != a for b, a in zip(model.predict_many(avant), model.predict_many(apres)))
    assert path == tmp_path / "essai.html"
    assert text.startswith("<!doctype html>") and '<meta charset="utf-8">' in text
    assert len(found) == 40 and found.count(" flag") == changed > 0
    assert f"{changed} image(s) sur 40 changent de classe" in text
    assert text.count('src="data:image/png;base64,') == 80
    assert found[:changed] == [" flag"] * changed  # images encadrées en premier


def test_page_sans_transformation_encadre_les_erreurs(tmp_path):
    path = vc.voir_chiffres(IMAGES, etiquettes=LABELS, nom="toutes", dossier=tmp_path)
    text, found = cards(path)
    wrong = sum(p != e for p, e in zip(model.predict_many(IMAGES), LABELS))
    assert len(found) == len(IMAGES) and found.count(" flag") == wrong
    assert f"le modèle se trompe sur {wrong}" in text


def test_longueurs_differentes_refusees(tmp_path):
    with pytest.raises(ValueError, match="même longueur"):
        vc.voir_chiffres(IMAGES[:3], IMAGES[:2], dossier=tmp_path)


@pytest.mark.parametrize("name, values, description", [
    ("rotate", ["10"], "rotate(img, 10)"),
    ("translate", ["1", "-1"], "translate(img, 1, -1)"),
    ("noise", ["0,1"], "noise(img, 0.1, seed=3)"),
    ("fog", ["0.3"], "fog(img, 0.3)"),
])
def test_parse_transformation(name, values, description):
    func, shown = vc.parse_transformation(name, values, graine=3)
    assert shown == description
    assert func(IMAGES[0]).shape == (8, 8)


def test_meme_image_que_transforms():
    func, _ = vc.parse_transformation("fog", ["0.3"])
    assert (func(IMAGES[0]) == fog(IMAGES[0], 0.3)).all()


@pytest.mark.parametrize("name, values, message", [
    ("flou", ["1"], "transformation inconnue"),
    ("rotate", [], "écrivez : rotate angle"),
    ("translate", ["0.5"], "entier"),
    ("fog", ["beaucoup"], "nombres"),
    ("aucune", ["1"], "ne prend pas de valeur"),
])
def test_parse_transformation_erreurs(name, values, message):
    with pytest.raises(ValueError, match=message):
        vc.parse_transformation(name, values)


def test_ligne_de_commande(tmp_path, capsys):
    assert vc.main(["rotate", "10", "--chiffre", "3", "--changees", "--dossier", str(tmp_path)]) == 0
    text, found = cards(tmp_path / "rotate_10_chiffre3.html")
    assert len(found) == len(model.test_images(digit=3)[0])
    assert 'id="only-flag" checked' in text
    out = capsys.readouterr().out
    assert "rotate(img, 10)" in out and "Vue écrite" in out


def test_ligne_de_commande_valeur_negative(tmp_path):
    assert vc.main(["brightness", "-0.1", "--chiffre", "1", "--dossier", str(tmp_path)]) == 0
    assert (tmp_path / "brightness_-0_1_chiffre1.html").exists()


def test_ligne_de_commande_erreur(tmp_path, capsys):
    assert vc.main(["rotate", "--dossier", str(tmp_path)]) == 2
    assert "écrivez : rotate angle" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())

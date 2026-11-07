"""Exemple 3 — tests générés pour normalize_age()."""

from normalize_age import normalize_age


def test_age_normal():
    assert normalize_age(42) == 42


def test_age_negatif():
    assert normalize_age(-1) == 0

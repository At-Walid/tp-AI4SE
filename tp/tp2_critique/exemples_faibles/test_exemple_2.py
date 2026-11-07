"""Exemple 2 — tests générés pour remise()."""

from remise import remise


def test_client_sans_points():
    assert remise(100, 0) == 100


def test_client_tres_fidele():
    assert remise(100, 50) == 80

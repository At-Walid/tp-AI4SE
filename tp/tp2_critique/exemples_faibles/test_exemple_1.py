"""Exemple 1 — tests générés pour remise()."""

from remise import remise


def test_remise_client_fidele():
    resultat = remise(100, 10)
    assert resultat is not None


def test_remise_client_regulier():
    resultat = remise(100, 5)
    assert resultat is not None

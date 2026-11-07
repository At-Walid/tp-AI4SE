# Exemple pédagogique de sortie plausible d'un LLM, pas un résultat d'expérience.
# Copié par `python tools/gen_tests.py normalize_age.py --spec SPEC.md --fallback`.
from normalize_age import normalize_age


def test_age_positif():
    assert normalize_age(25) == 25


def test_age_zero():
    assert normalize_age(0) == 0


def test_age_negatif_ramene_a_zero():
    assert normalize_age(-5) == 0


def test_age_est_un_entier():
    assert isinstance(normalize_age(30), int)

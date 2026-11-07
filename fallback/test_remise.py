# Exemple pédagogique de sortie plausible d'un LLM, pas un résultat d'expérience.
# Copié par `python tools/gen_tests.py remise.py --spec SPEC.md --fallback` quand aucun LLM n'est disponible.
import pytest

from remise import remise


def test_remise_sans_fidelite():
    assert remise(100, 0) == 100


def test_remise_fidelite_moyenne():
    assert remise(100, 7) == pytest.approx(90)


def test_remise_fidelite_elevee():
    assert remise(100, 15) == pytest.approx(80)


def test_remise_retourne_un_nombre():
    resultat = remise(50, 3)
    assert resultat is not None
    assert isinstance(resultat, (int, float))


def test_remise_prix_nul():
    assert remise(0, 12) == 0


@pytest.mark.parametrize("prix", [10, 20, 99.5])
def test_remise_grande_fidelite(prix):
    assert remise(prix, 20) == pytest.approx(prix * 0.80)


def test_remise_fidelite_negative():
    # Une fidélité négative est traitée comme une absence de fidélité.
    assert remise(100, -3) == 100

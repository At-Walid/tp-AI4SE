"""TP1 — Exemple de test écrit à la main (point de départ).

Les tests générés par le LLM arrivent dans generated_tests/.
Lancez tout : make test TP=1   |   couverture : make cov
"""

from remise import remise


def test_sans_fidelite_pas_de_remise():
    # SPEC, règle 3 : moins de 5 points, le client paie le prix initial.
    assert remise(100, 0) == 100

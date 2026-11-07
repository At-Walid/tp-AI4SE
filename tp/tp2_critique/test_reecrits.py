"""TP2 — Vos tests réécrits (au moins 3).

Chaque test vérifie une règle de tp/tp1_generation/SPEC.md : écrivez la valeur attendue
d'après la SPEC, pas d'après ce que renvoie le code. Indiquez la règle en commentaire.

Si un de vos tests échoue, ne le « corrigez » pas pour qu'il passe : demandez-vous d'abord
qui a tort, le test ou le code ? Notez la réponse dans tp/RENDU.md.

Ce fichier est aussi utilisé par le TP3 (make mutate).
"""

import pytest  # noqa: F401  (utile pour pytest.raises et pytest.mark.parametrize)

from normalize_age import normalize_age  # noqa: F401
from remise import remise


# Exemple de forme attendue : assertion précise, règle citée.
def test_exemple_regle_3_sans_remise():
    # SPEC remise, règle 3 : moins de 5 points, pas de remise.
    assert remise(100, 0) == 100


# Test réécrit n°1 (remplace : exemple ... / test généré ...)


# Test réécrit n°2


# Test réécrit n°3

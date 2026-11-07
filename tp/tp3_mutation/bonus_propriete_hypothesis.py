"""Défi bonus (TP1 à TP3) — une propriété Hypothesis pour remise().

Au lieu de choisir quelques exemples, on énonce une propriété vraie pour TOUTES les
entrées valides de la SPEC, et Hypothesis cherche un contre-exemple.

Pour l'activer : copiez ce fichier en tp/tp3_mutation/test_propriete.py, complétez
la propriété, puis lancez make test TP=3 et make mutate.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from remise import remise

prix_valides = st.floats(min_value=0, max_value=10_000, allow_nan=False)
fidelites_valides = st.integers(min_value=0, max_value=100)


@pytest.mark.skip(reason="défi bonus : à compléter")
@given(prix=prix_valides, fidelite=fidelites_valides)
def test_remise_jamais_superieure_au_prix(prix, fidelite):
    resultat = remise(prix, fidelite)
    # Propriété 1 : le client ne paie jamais plus que le prix initial.
    # Propriété 2 : la remise ne dépasse jamais 20 %.
    # Écrivez les deux assertions (attention aux arrondis des flottants).
    ...


# Propriété à imaginer : plus de points de fidélité => prix payé plus petit ou égal (monotonie).
# Quels mutants de make mutate cette propriété tue-t-elle ? Lesquels laisse-t-elle passer ?

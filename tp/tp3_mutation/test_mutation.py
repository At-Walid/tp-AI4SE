"""TP3 — Tests ajoutés pour tuer les mutants survivants.

make mutate lance la mutation de remise.py avec : tp/tp2_critique/test_reecrits.py + ce dossier.
Pour chaque survivant, ajoutez ici un test qui le tue (et notez lequel), ou justifiez
dans tp/RENDU.md pourquoi le mutant est équivalent.
"""

from remise import remise


# Tests de départ (ceux qu'un générateur produit souvent) : lancez make mutate avant d'en ajouter.
def test_sans_fidelite():
    assert remise(100, 0) == 100


def test_grande_fidelite_donne_une_remise():
    assert remise(200, 20) < 200


# Vos tests « tueurs de mutants » :

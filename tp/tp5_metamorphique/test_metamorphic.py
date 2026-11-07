"""TP5 — Tests métamorphiques du classifieur de chiffres.

Une relation métamorphique compare deux exécutions : on transforme l'entrée d'une façon qui,
selon une hypothèse justifiée, ne doit pas changer la réponse, et on vérifie que la sortie ne
change pas. Pas besoin de connaître la « bonne » réponse pour chaque image.
"""

import model
from transforms import brightness

IMAGES, LABELS = model.test_images()


def test_relation_1_luminosite_legere_garde_la_classe():
    """Relation 1 (remplie, voir relation.md)
    Entrée              : les images de test (model.test_images()).
    Transformation      : brightness(img, +0.03).
    Sortie attendue     : la classe prédite ne change pas.
    Hypothèse           : +3 % de luminosité ne change pas le chiffre lu par un humain.
    Critère de violation: au moins une image change de classe.
    """
    delta = 0.03  # illustratif, à justifier : pourquoi 3 % ? que se passe-t-il à 5 %, 10 %, 20 % ?
    before = model.predict_many(IMAGES)
    after = model.predict_many([brightness(img, delta) for img in IMAGES])
    changed = [i for i, (b, a) in enumerate(zip(before, after)) if b != a]
    assert changed == [], f"{len(changed)} image(s) sur {len(IMAGES)} changent de classe : {changed[:10]}"


# Relation 2 (la vôtre) : choisissez une transformation dans transforms.py, remplissez
# relation.md AVANT d'écrire le test, puis écrivez test_relation_2_... sur ce modèle.

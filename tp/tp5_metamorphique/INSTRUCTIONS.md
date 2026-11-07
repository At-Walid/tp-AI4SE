# TP5 — Relation métamorphique (10 min)

**Objectif** : tester un modèle d'IA **sans oracle** (on ne connaît pas toujours la bonne
réponse) grâce à une relation métamorphique, et apprendre à justifier cette relation.

**En binôme** : l'un écrit la relation (5 champs), l'autre joue l'avocat du diable sur
l'**hypothèse** avant qu'on écrive le moindre code. Puis échangez pour le test.

| Étapes | 1 | 2 | 3 | 4 |
|--------|---|---|---|---|
| Durée  | 2 min | 3 min | 3 min | 2 min |

Le système testé : un classifieur de chiffres manuscrits (images 8x8) entraîné sur le jeu
« digits » de scikit-learn ([`model.py`](model.py)). Transformations disponibles :
[`transforms.py`](transforms.py) (`brightness`, `contrast`, `noise`, `translate`, `rotate`, `fog`).

```python
import model
from transforms import rotate
images, labels = model.test_images()          # ou model.test_images(digit=6)
label, confidence = model.predict(images[0])
avant = model.predict_many(images)
apres = model.predict_many([rotate(img, 10) for img in images])
```

## Étapes

1. **Lisez et lancez** la relation fournie : `make test TP=5`
   ([`test_metamorphic.py`](test_metamorphic.py)). Elle est vérifiée. Que devient-elle si vous
   remplacez `0.03` par `0.2` ? La tolérance était-elle justifiée ?
2. **Remplissez [`relation.md`](relation.md)** pour une relation **à vous** : entrée,
   transformation, sortie attendue, **hypothèse justifiée**, critère de violation. Essayez une
   transformation géométrique (translation, rotation) ou une dégradation (brouillard, bruit).
3. **Écrivez le test** `test_relation_2_...` dans `test_metamorphic.py` et lancez-le.
4. **Si la relation est violée**, regardez les images concernées (`print(np.round(img, 1))`) et
   tranchez : **bug du modèle** (l'hypothèse tient, le modèle a tort) ou **relation
   injustifiée** (l'hypothèse ne tient pas pour ces entrées) ?

## À rendre

`tp/tp5_metamorphique/relation.md` complété : la relation (5 champs) **avec une hypothèse
justifiée**, le résultat du test et votre verdict « bug du modèle ou relation injustifiée ».

## Si vous êtes bloqué

1. Relisez la relation fournie et les docstrings de `transforms.py`.
2. Comparez avec votre voisin.
3. Toujours bloqués après 5 minutes ? Appelez l'enseignant.

## Défis bonus (binômes rapides)

- Une **seconde relation**, d'une autre famille, avec son hypothèse : [`relation_bonus.md`](relation_bonus.md).
- Trouvez l'intensité à partir de laquelle votre relation cesse d'être vérifiée (balayage du paramètre).

> **Ce que vous devez savoir expliquer en sortant de ce TP**
>
> - Ce qu'une relation métamorphique remplace (l'oracle) et ce qu'elle ne remplace pas.
> - Pourquoi une violation n'est pas automatiquement un bug du modèle.

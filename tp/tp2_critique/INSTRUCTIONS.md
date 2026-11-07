# TP2 — Critiquer les tests générés (10 min)

**Objectif** : apprendre à juger un test avec une grille explicite, puis réécrire les tests
faibles pour qu'ils vérifient vraiment la spécification.

**En binôme** : celui qui a tapé au TP1 conteste maintenant ; l'autre écrit. Pour chaque test,
le « contesteur » doit convaincre l'autre avec une question de la grille.

| Étapes | 1 | 2 | 3 | 4 |
|--------|---|---|---|---|
| Durée  | 3 min | 2 min | 4 min | 1 min |

## Étapes

1. **Classez les 3 exemples** de [`exemples_faibles/`](exemples_faibles/) avec
   [`critique_checklist.md`](critique_checklist.md) : chaque fichier a **une** faiblesse principale
   (code A à F). Remarquez qu'ils passent tous :
   ```bash
   python -m pytest tp/tp2_critique/exemples_faibles -q
   ```
2. **Appliquez la grille à vos tests du TP1** (`tp/tp1_generation/generated_tests/`), en jugeant
   **par rapport à `SPEC.md`**, pas par rapport au code.
3. **Réécrivez au moins 3 tests** dans [`test_reecrits.py`](test_reecrits.py). Formes utiles :
   ```python
   @pytest.mark.parametrize("fidelite, attendu", [(4, 100), (5, 90), (6, 90)])
   def test_bornes_autour_de_5(fidelite, attendu):
       assert remise(100, fidelite) == pytest.approx(attendu)   # SPEC, règles 2 et 3

   def test_entree_invalide_rejetee():
       with pytest.raises(ValueError):    # forme d'un test « doit lever une exception »
           ...                            # appel avec une entrée que la SPEC déclare invalide
   ```
4. **Lancez-les** : `make test TP=2`. Un test réécrit échoue ? Décidez qui a tort (test ou code)
   et notez-le : c'est une découverte, pas une erreur.

## À rendre (dans `tp/RENDU.md`, section TP2)

- Le **type de faiblesse** (A à F) de chacun des 3 exemples, justifié en une ligne.
- Vos **3 tests réécrits** (dans `test_reecrits.py`), chacun avec la règle de la SPEC qu'il vérifie.

## Si vous êtes bloqué

1. Relisez la question de la grille et la règle de `SPEC.md`.
2. Comparez avec votre voisin.
3. Toujours bloqués après 5 minutes ? Appelez l'enseignant.

## Défis bonus (binômes rapides)

- Écrivez la propriété Hypothesis de `tp/tp3_mutation/bonus_propriete_hypothesis.py` : elle
  vérifie toute une famille d'entrées d'un coup.
- Pour chaque test généré, répondez à la question 4 de la grille en imaginant le code corrigé.

> **Ce que vous devez savoir expliquer en sortant de ce TP**
>
> - Pourquoi un test qui passe peut être un mauvais test (il peut même protéger un bug).
> - La différence entre « le test est rouge » et « le test est faux ».

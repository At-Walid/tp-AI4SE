# TP3 — Test de mutation (18 min)

**Objectif** : mesurer l'efficacité d'une suite de tests en injectant de petites fautes
(« mutants ») dans le code, puis renforcer la suite pour tuer les mutants qui survivent.

**En binôme** : l'un lit les survivants et propose un test, l'autre vérifie qu'il est conforme
à la SPEC avant de l'ajouter. Échangez à chaque survivant.

| Étapes | 1 | 2 | 3–4 | 5 | 6 |
|--------|---|---|-----|---|---|
| Durée  | 3 min | 3 min | 8 min | 2 min | 2 min |

## Le principe

Un mutant est une copie de `remise.py` avec **une** petite modification. On relance les tests :
- au moins un test échoue → le mutant est **tué** (la suite a vu la faute) ;
- tous les tests passent → le mutant **survit** (la suite est aveugle à cette faute).

## Les trois mutants du cours

| Mutant | Modification dans `remise.py` |
|--------|-------------------------------|
| M1 | `fidelite >= 10` devient `fidelite > 10` |
| M2 | `0.90` devient `0.85` |
| M3 | `fidelite >= 5` devient `fidelite >= 6` |

**Question : quel test tue chacun d'eux ?** Écrivez l'appel exact et la valeur attendue
(par exemple `remise(100, ?) == ?`). `make mutate` les signale par « mutant du cours M1/M2/M3 ».

## Étapes

1. **Lancez la mutation** sur la suite actuelle (vos tests du TP2 + `test_mutation.py`) :
   ```bash
   make mutate
   ```
   Copiez le **résumé** (mutants, tués, survivants) dans `tp/RENDU.md` : c'est votre « avant ».
   Les tests qui échouent déjà sur le code d'origine (écarts à la SPEC) sont mis de côté
   automatiquement : la mutation se mesure sur une suite verte.
2. **Répondez à la question des trois mutants du cours** (tableau ci-dessus).
3. Pour chaque **survivant**, lisez la ligne mutée et cherchez l'entrée qui fait différer
   l'original et le mutant. Exemple de forme :
   ```python
   def test_tue_le_mutant_n():                 # nommez le mutant visé
       assert remise(PRIX, FIDELITE) == pytest.approx(ATTENDU)   # ATTENDU d'après la SPEC
   ```
   Vérifiez à la main : avec ces valeurs, l'original et le mutant donnent-ils deux résultats différents ?
4. **Ajoutez ces tests** dans [`test_mutation.py`](test_mutation.py) et relancez `make mutate`.
5. Un survivant résiste ? Demandez-vous s'il est **équivalent** : aucune entrée valide de la SPEC
   ne distingue le mutant de l'original. Justifiez-le en une phrase.
6. Copiez le nouveau résumé : c'est votre « après ».

> Outil : `tools/mini_mutate.py` (lisible, une centaine de lignes, lancé par `make mutate`).
> `make mutmut` lance l'outil standard **mutmut** sur le même fichier, pour comparer
> (il exige une suite entièrement verte).

## À rendre (dans `tp/RENDU.md`, section TP3)

- Le **résumé de mutation avant / après** (nombre de mutants, tués, survivants).
- Les **survivants expliqués** : pour chacun, le test qui l'a tué, ou la justification de son équivalence.
- La réponse pour **M1, M2, M3**.

## Si vous êtes bloqué

1. Relisez la ligne mutée et la règle de `SPEC.md` concernée.
2. Comparez avec votre voisin.
3. Toujours bloqués après 5 minutes ? Appelez l'enseignant.

## Défis bonus (binômes rapides)

- `make mutate EXTRA=1` ajoute les mutants écrits à la main de
  [`mutants_bonus.txt`](mutants_bonus.txt) : lesquels sont équivalents ? lesquels révèlent une
  faiblesse de vos assertions ?
- Complétez la propriété Hypothesis de [`bonus_propriete_hypothesis.py`](bonus_propriete_hypothesis.py) :
  combien de mutants tue-t-elle à elle seule ?

> **Ce que vous devez savoir expliquer en sortant de ce TP**
>
> - Pourquoi le score de mutation dit plus que la couverture sur l'efficacité d'une suite.
> - Ce qu'est un mutant équivalent, et pourquoi on ne peut pas toujours le tuer.

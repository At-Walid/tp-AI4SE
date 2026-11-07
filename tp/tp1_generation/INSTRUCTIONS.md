# TP1 — Générer des tests avec l'IA (15 min)

**Objectif** : faire générer des tests par un LLM, les exécuter, mesurer la couverture, puis
établir la liste des cas couverts… et des cas oubliés, **par rapport à la spécification**.

**En binôme** : l'un tape les commandes, l'autre conteste (« ce test vérifie-t-il vraiment
la SPEC ? »). Échangez les rôles à chaque TP.

| Étapes | 1 | 2–3 | 4 | 5–6 |
|--------|---|-----|---|-----|
| Durée  | 2 min | 4 min | 3 min | 6 min |

## Étapes

1. **Lisez** [`SPEC.md`](SPEC.md), puis [`remise.py`](remise.py) et [`normalize_age.py`](normalize_age.py).
   Ne corrigez rien : aujourd'hui, on teste.
2. **Générez** des tests pour `remise.py` (depuis la racine du dépôt) :
   ```bash
   python tools/gen_tests.py remise.py --spec SPEC.md
   ```
   Résultat : `tp/tp1_generation/generated_tests/test_remise.py`. **Lisez-le en entier.**
   Le LLM ne répond pas (ou trop lentement) ? Utilisez la sortie d'exemple :
   `python tools/gen_tests.py remise.py --spec SPEC.md --fallback`
3. Recommencez avec `normalize_age.py`.
4. **Exécutez** les tests et mesurez la couverture (lignes et branches) :
   ```bash
   make test TP=1
   make cov
   ```
   Notez : combien de tests passent ? quelle couverture ?
5. **Comparez à la SPEC, pas au code.** Pour chaque règle de `SPEC.md`, cherchez le test qui la
   vérifie. Remplissez le tableau dans `tp/RENDU.md` :

   | Règle de la SPEC | Test qui la vérifie | Couverte ? |
   |------------------|---------------------|------------|
   | remise, règle 1 (≥ 10 points : −20 %) | `test_...` | oui / non / partiellement |

   Pistes : les valeurs limites (4, 5, 6 et 9, 10, 11) sont-elles testées ? les valeurs
   négatives ? que fait le test quand le code et la SPEC ne sont pas d'accord ?
6. Mettez en regard la **couverture affichée** et le **nombre de règles réellement vérifiées**.

## À rendre (dans `tp/RENDU.md`, section TP1)

La **liste des cas couverts et des cas manquants** (le tableau de l'étape 5), avec la couverture mesurée.

## Si vous êtes bloqué

1. Relisez la question et la règle concernée de `SPEC.md`.
2. Comparez avec votre voisin.
3. Toujours bloqués après 5 minutes ? Appelez l'enseignant.

## Défis bonus (binômes rapides)

- Affichez le prompt (`--show-prompt`), écrivez-en un meilleur dans un fichier et relancez avec
  `--prompt-file mon_prompt.txt`. Les tests générés sont-ils meilleurs ? Pourquoi ?
- Générez sans `--spec` : qu'est-ce qui change ?
- Lisez `tp/tp3_mutation/bonus_propriete_hypothesis.py` : une propriété Hypothesis à écrire
  pour `remise` (elle sert aussi au TP3).

> **Ce que vous devez savoir expliquer en sortant de ce TP**
>
> - Pourquoi 100 % de couverture ne garantit pas que la spécification est vérifiée.
> - Ce qu'un LLM « voit » quand il génère des tests à partir du code (et ce qu'il ne voit pas).

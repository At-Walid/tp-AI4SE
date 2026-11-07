# Rendu du TP — binôme : ………………… / …………………

## TP1 — Cas couverts et manquants

Couverture mesurée (`make cov`) : lignes … % ; branches … %. Tests générés : … ; verts : …

| Règle de la SPEC | Test qui la vérifie | Couverte ? (oui / non / partiellement) |
|------------------|---------------------|----------------------------------------|
| remise, règle 1 (≥ 10 points : −20 %) | | |
| remise, règle 2 (5 à 9 points : −10 %) | | |
| remise, règle 3 (< 5 points : pas de remise) | | |
| remise, règle 4 (fidélité négative : ValueError) | | |
| remise, règle 5 (prix négatif : ValueError) | | |
| normalize_age, règle 1 (âge ≥ 0 inchangé) | | |
| normalize_age, règle 2 (âge négatif : ValueError) | | |

Cas manquants importants : …

## TP2 — Critique

| Exemple | Type de faiblesse (A à F) | Justification (une ligne) |
|---------|---------------------------|---------------------------|
| `exemples_faibles/test_exemple_1.py` | | |
| `exemples_faibles/test_exemple_2.py` | | |
| `exemples_faibles/test_exemple_3.py` | | |

Tests réécrits (dans `tp2_critique/test_reecrits.py`) : … (pour chacun : règle vérifiée, et
résultat — vert, ou rouge parce que le code ne respecte pas la SPEC ?)

## TP3 — Mutation

| | Mutants | Tués | Survivants | Score |
|---|---|---|---|---|
| Avant | | | | |
| Après | | | | |

Mutants du cours : M1 tué par `…` ; M2 tué par `…` ; M3 tué par `…`

Survivants restants et explication (test ajouté, ou pourquoi le mutant est équivalent) : …

## TP4 — Stratégie de test

| Question de sécurité | Technique | Test (nom) | Exigence |
|----------------------|-----------|------------|----------|
| | génération de scénarios / pannes / métamorphique / différentiel | | R… |

Score `make check` : … / 5 ; fausse alarme : oui / non ; variantes détectées : …

Quelle technique a trouvé quoi ? Qu'est-ce qu'aucun de vos tests n'aurait pu trouver ? …

## TP5

Voir `tp/tp5_metamorphique/relation.md`.

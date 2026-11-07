# Grille de critique d'un test

Pour chaque test, répondez **oui / non / ?** à chaque question et justifiez en une ligne.
On juge le test **par rapport à la spécification** (`tp/tp1_generation/SPEC.md`), pas par
rapport au code.

| # | Question | Ce qu'il faut regarder |
|---|----------|------------------------|
| 1 | **Assertion forte ?** | Le test vérifie-t-il une valeur précise (`== 90`) plutôt qu'une propriété vague (`is not None`, `> 0`, `isinstance`) ? |
| 2 | **Bornes ?** | Les valeurs limites sont-elles testées : **4 / 5 / 6** et **9 / 10 / 11** ? |
| 3 | **Valeurs invalides ?** | Que demande la SPEC pour un prix ou une fidélité négatifs, un âge négatif ? Le test le vérifie-t-il (`pytest.raises(ValueError)`) ? |
| 4 | **Protège un bug ?** | Ce test **échouerait-il si le code était correct** (conforme à la SPEC) ? Si oui, il fige un bug. |
| 5 | **Redondant ?** | Apporte-t-il un cas nouveau, ou répète-t-il un autre test avec d'autres valeurs du même cas ? |
| 6 | **Couverture réelle ?** | Exécuté ≠ vérifié : la ligne est-elle seulement exécutée, ou son résultat est-il contrôlé par une assertion ? |

## Types de faiblesse (pour classer les exemples)

| Code | Faiblesse |
|------|-----------|
| A | Assertion faible (question 1) |
| B | Bornes absentes (question 2) |
| C | Valeurs invalides absentes (question 3) |
| D | Test qui confirme un bug (question 4) |
| E | Test redondant (question 5) |
| F | Couverture sans vérification (question 6) |

Un test peut cumuler plusieurs faiblesses : donnez la principale.

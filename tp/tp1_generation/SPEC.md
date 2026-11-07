# Spécification — module de tarification

Cette spécification fait foi. En cas de désaccord entre le code et ce document,
c'est le **code** qui est à corriger.

## `remise(prix, fidelite)`

Calcule le prix à payer après la remise de fidélité.

| Paramètre  | Signification                                   | Domaine valide      |
|------------|-------------------------------------------------|---------------------|
| `prix`     | prix initial, en euros                          | nombre réel ≥ 0     |
| `fidelite` | nombre de points de fidélité du client          | entier ≥ 0          |

Règles :

1. **À partir de 10 points** (10 inclus) : remise de 20 % — le client paie 80 % du prix.
2. **De 5 à 9 points** (5 inclus) : remise de 10 % — le client paie 90 % du prix.
3. **Moins de 5 points** : pas de remise — le client paie le prix initial.
4. Un nombre de points **négatif** est invalide : la fonction doit lever `ValueError`.
5. Un prix **négatif** est invalide : la fonction doit lever `ValueError`.

Exemples : `remise(100, 12) == 80`, `remise(100, 7) == 90`, `remise(100, 2) == 100`.

## `normalize_age(age)`

Normalise un âge saisi dans un formulaire.

1. Un âge positif ou nul est renvoyé tel quel.
2. Un âge **négatif** est invalide : la fonction doit lever `ValueError`.

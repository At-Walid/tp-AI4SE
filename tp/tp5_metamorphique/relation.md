# TP5 — Votre relation métamorphique

Binôme : ……………………

Remplissez les **cinq champs** avant d'écrire le test.
**Une relation sans hypothèse justifiée est incomplète.**

## 1. Entrée (*Input*)

Quelles images ? (toutes les images de test, une classe précise, celles prédites avec une confiance ≥ … ?)

…

## 2. Transformation

Fonction de `transforms.py` et valeur du paramètre d'intensité.

…

## 3. Sortie attendue (*Expected output*)

Relation entre la sortie avant et après transformation (même classe ? confiance qui ne baisse pas de plus de … ?).

…

## 4. Hypothèse (*Hypothesis*) — obligatoire

Pourquoi cette transformation **ne devrait pas** changer la réponse ? Sur quoi repose cette
affirmation (perception humaine, physique du capteur, définition de la classe) ? Pour quelle
plage d'intensité reste-t-elle vraie ?

…

## 5. Critère de violation (*Violation criterion*)

À partir de quand dit-on que la relation est violée (une image ? plus de x % ?). Justifiez le seuil.

…

---

## Résultat

- Test : `test_metamorphic.py::test_relation_2_…`
- Relation **vérifiée** ou **violée** ? Sur combien d'images ?
- Si elle est violée : **bug du modèle ou relation injustifiée ?** Argumentez en 2–3 lignes
  (regardez quelques images concernées : un humain dirait-il la même chose que la relation ?).

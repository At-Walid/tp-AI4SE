# TP : tester une IA critique avec des tests générés par IA

**Durée : 90 minutes · en binômes · Master 2 Génie Logiciel**

Question de fil rouge : *« L'IA générative facilite la génération de tests. Est-ce suffisant quand le système testé est lui-même une IA critique ? »*

Vous ne construisez rien. Vous **testez** du code et un petit système autonome fournis, et vous essayez de trouver le plus de défauts possible.

---

## 1. Démarrage (à faire avant le cours si possible)

Tout est dans un conteneur : Python, pytest, coverage, Hypothesis, mutmut, un modèle de langage local (Ollama) et le simulateur. Pas de compte, pas de clé, pas d'installation supplémentaire.

### Option A : Docker sur votre machine

Avec `make` (Linux, macOS) :

```bash
make build     # une seule fois, avec une bonne connexion (long)
make shell     # ouvre un terminal dans le conteneur
make test      # vérifie que tout fonctionne
```

Sans `make` (Windows) : dans **PowerShell** (pas Git Bash), depuis le dossier du dépôt.

```powershell
docker build -t ia4se-tests .
docker run --rm -it -v "${PWD}:/workspace" -v ia4se-ollama:/opt/ollama/models -w /workspace ia4se-tests bash
```

La première commande se lance une seule fois. Si l'enseignant fournit une archive, utilisez
plutôt `docker load -i ia4se-tests.tar`. La seconde ouvre le terminal du conteneur, à chaque
séance. Dans ce terminal, tapez `make test`, puis toutes les commandes `make` du TP.

### Option B : GitHub Codespaces ou VS Code

Ouvrez le dépôt, puis « Reopen in Container » (VS Code) ou « Create codespace » (GitHub). La première création est lente. Lancez ensuite `make test` dans le terminal.

**Si `make test` ne passe pas, prévenez l'enseignant avant le début du TP.**

---

## 2. Déroulé (90 min)

| TP | Dossier | Durée | À rendre |
|----|---------|-------|----------|
| 1. Générer des tests avec l'IA | `tp/tp1_generation/` | 15 min | liste des cas couverts et manquants |
| 2. Critiquer les tests générés | `tp/tp2_critique/` | 10 min | 3 tests réécrits + type de faiblesse de chaque exemple |
| 3. Test de mutation | `tp/tp3_mutation/` | 18 min | résumé de mutation avant/après, survivants expliqués |
| 4. Stratégie de test d'un système autonome | `tp/tp4_simulator/` | 25 min | tests + justification (question → technique → test) + score `make check` |
| 5. Relation métamorphique | `tp/tp5_metamorphique/` | 10 min | `relation.md` avec hypothèse justifiée |
| Débrief | | 7 min | |
| Questionnaire de satisfaction | | 5 min | |

Les durées sont des repères. Chaque dossier contient un `INSTRUCTIONS.md` d'une page : lisez-le en premier.

---

## 3. Carte du dépôt

```
tp/
  RENDU.md                 votre unique livrable
  tp1_generation/          remise.py, normalize_age.py, SPEC.md
  tp2_critique/            critique_checklist.md, exemples_faibles/
  tp3_mutation/            tests à compléter (test_mutation.py)
  tp4_simulator/           simulateur, EXIGENCES.md, scénarios
  tp5_metamorphique/       classifieur, transformations, relation.md
tools/                     gen_tests.py, llm.py, voir_simulation.py, voir_chiffres.py
fallback/                  exemples de sortie d'un LLM (secours)
tests/                     tests de l'outillage du dépôt
Makefile
```

> Il manque peut-être des détails si le dépôt a évolué : la référence est toujours le `INSTRUCTIONS.md` de chaque TP.

---

## 4. Commandes

| Commande | Rôle |
|----------|------|
| `make test` | lance les tests |
| `make cov` | mesure la couverture |
| `make mutate` | lance le test de mutation et affiche un résumé |
| `make check` | (TP4) calcule votre score contre les variantes défectueuses |
| `python tools/voir_simulation.py jour_nominal` | (TP4) voir une simulation : page animée dans `tp/tp4_simulator/vues/` |
| `python tools/voir_chiffres.py rotate 10` | (TP5) voir les chiffres avant et après une transformation : page dans `tp/tp5_metamorphique/vues/` |
| `make pull-model` | télécharge le modèle de langage local si absent |
| `make clean` | nettoie les fichiers générés |

Générer des tests avec l'IA (TP1), depuis la racine du dépôt :

```bash
python tools/gen_tests.py remise.py --spec SPEC.md
```

Les tests générés sont écrits dans `generated_tests/`.

---

## 5. L'assistant IA

- Par défaut, un **modèle local** (Ollama) tourne sur CPU. Il est petit : il peut être lent ou produire des tests médiocres. C'est instructif.
- Si l'outil affiche que le modèle est injoignable, utilisez les exemples du dossier `fallback/` (ce sont des exemples pédagogiques de sortie plausible, **pas un résultat d'expérience**), ou lancez `make pull-model`.
- Facultatif : vous pouvez utiliser un fournisseur externe si vous définissez vous-même `OPENAI_API_KEY`, ou `ANTHROPIC_API_KEY` avec le nom du modèle dans `ANTHROPIC_MODEL`, dans votre terminal. Ne mettez jamais une clé dans un fichier du dépôt.

---

## 6. Règles du jeu

1. **Jugez les tests par rapport à la spécification, jamais par rapport au code.** Un test qui passe n'est pas forcément un bon test.
2. **Justifiez.** Pour chaque technique : à quelle question de test répond-elle ?
3. **Pas de chiffres inventés.** Rapportez ce que vous avez mesuré.
4. **Travaillez en binômes.** L'un écrit, l'autre conteste. Échangez les rôles à chaque TP.
5. **N'ouvrez pas le dossier `.check_data/`.** `check.py` s'en sert pour vous noter.
6. Le simulateur est un **modèle jouet**. Il ne reproduit aucun accident ni système réel.

### Le score du TP4

`make check` lance votre suite contre plusieurs variantes défectueuses et contre la version correcte. Il indique :

- combien de variantes défectueuses votre suite détecte ;
- si elle passe sur la version correcte (**pas de fausse alarme**).

Une suite qui échoue partout ne marque pas de points.

---

## 7. Bloqué ? Terminé en avance ?

**Bloqué :**
1. relisez la question de `INSTRUCTIONS.md` ;
2. relisez la checklist et la spécification ;
3. demandez à votre binôme, puis à un voisin ;
4. au bout de 5 minutes, levez la main.

**Terminé en avance :** chaque `INSTRUCTIONS.md` contient une section « Défis bonus » (mutants supplémentaires, propriété Hypothesis, seconde relation métamorphique avec son hypothèse).

---

## 8. Rendu

Remplissez **`tp/RENDU.md`** (un seul fichier par binôme) : vos listes, vos analyses, votre justification de stratégie et votre `relation.md`.

- Format et date de remise : **une archive zip de votre dossier `tp/`, déposée sur Moodle à la fin de la séance** (un dépôt par binôme). Sur les postes de la salle, vos fichiers peuvent être effacés à la déconnexion : déposez avant de partir.
- Ce que vous emportez : vos suites de tests, votre analyse des cas couverts/manquants et des survivants, votre relation métamorphique avec son hypothèse, votre score. Le dépôt est à vous.

---

## 9. Dépannage

| Problème | Que faire |
|----------|-----------|
| `make build` échoue ou est très lent | vérifiez Docker et votre connexion, relancez ; sinon utilisez Codespaces |
| `make test` échoue juste après le build | prévenez l'enseignant |
| L'IA locale ne répond pas | `make pull-model`, ou utilisez `fallback/` |
| L'IA est trop lente | utilisez `fallback/` et passez au TP2 |
| Apple Silicon (M1/M2/M3) | l'image est prévue pour `arm64` ; signalez tout problème |
| Windows sans `make` | commandes PowerShell de l'option A ; sinon Codespaces |
| Docker : « error during connect » | démarrez Docker Desktop, puis relancez la commande |

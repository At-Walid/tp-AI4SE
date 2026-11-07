# TP « IA pour le Génie Logiciel : génération de tests assistée par IA pour les systèmes IA critiques »

> **Question du cours** : l'IA générative facilite la génération de tests. Est-ce suffisant
> quand le système testé est lui-même une IA critique ?

Séance de 90 minutes, **en binôme** : 78 min de TP, 7 min de débriefing, 5 min de questionnaire.
Vous **testez** le code fourni : vous ne le corrigez pas.

## 1. Démarrer (moins de 5 minutes)

Choisissez **une** option. Tout est déjà installé dans l'environnement : Python, pytest,
Hypothesis, outils de mutation, un LLM local (Ollama) et son modèle.

| Option | Étapes |
|--------|--------|
| **A. GitHub Codespaces** (rien à installer) | Bouton **Code → Codespaces → Create codespace**. La première ouverture construit l'environnement (plusieurs minutes). |
| **B. VS Code + Dev Containers** | Ouvrez le dossier dans VS Code, puis **Reopen in Container**. |
| **C. Docker** | Docker démarré. Avec `make` (Linux, macOS) : `make build` (une seule fois, plusieurs minutes), puis `make shell`. Sans `make` (Windows) : commandes ci-dessous. |

Sans `make` (Windows) : dans **PowerShell** (pas Git Bash), depuis le dossier du dépôt.
Construisez l'image une seule fois. Si l'enseignant fournit une archive, utilisez plutôt
`docker load -i ia4se-tests.tar`.

```powershell
docker build -t ia4se-tests .
```

Puis, à chaque séance, ouvrez le terminal du conteneur :

```powershell
docker run --rm -it -v "${PWD}:/workspace" -v ia4se-ollama:/opt/ollama/models -w /workspace ia4se-tests bash
```

Dans ce terminal, `make` fonctionne : toutes les commandes `make ...` du TP se tapent là.

**Vérifiez que tout marche** — dans le terminal du conteneur :

```bash
make test
```

Tous les tests doivent être verts. Sinon, appelez l'enseignant.

## 2. Plan de la séance

| Partie | Dossier | Durée | À rendre |
|--------|---------|-------|----------|
| TP1 Générer des tests avec l'IA | `tp/tp1_generation/` | 15 min | liste des cas couverts et manquants |
| TP2 Critiquer les tests générés | `tp/tp2_critique/` | 10 min | 3 tests réécrits + type de faiblesse de chaque exemple |
| TP3 Test de mutation | `tp/tp3_mutation/` | 18 min | résumé de mutation avant/après + survivants expliqués |
| TP4 Stratégie de test d'un système autonome | `tp/tp4_simulator/` | 25 min | tests + justification (question → technique → test) + score `make check` |
| TP5 Relation métamorphique | `tp/tp5_metamorphique/` | 10 min | `relation.md` avec une hypothèse justifiée |
| Débriefing | — | 7 min | — |
| Questionnaire | — | 5 min | — |

Chaque dossier contient un `INSTRUCTIONS.md` (une page) : lisez-le en premier.

## 3. Carte du dépôt

```
tp/
  README.md              ce fichier
  RENDU.md               vos réponses (une section par TP)
  tp1_generation/        remise.py, normalize_age.py, SPEC.md, generated_tests/
  tp2_critique/          critique_checklist.md, exemples_faibles/, test_reecrits.py
  tp3_mutation/          test_mutation.py, mutants_bonus.txt
  tp4_simulator/         sim/ (le simulateur), scenarios/, EXIGENCES.md, test_scenarios.py, check.py
  tp5_metamorphique/     model.py, transforms.py, relation.md, test_metamorphic.py
tools/                   gen_tests.py, llm.py, mini_mutate.py, random_scenarios.py,
                         voir_simulation.py (TP4), voir_chiffres.py (TP5)
fallback/                sorties d'exemple d'un LLM (si le LLM local ne répond pas)
tests/                   tests de l'outillage du dépôt (make selftest)
```

## 4. Commandes

| Commande | Effet |
|----------|-------|
| `make test` / `make test TP=4` | lance les tests (tous les TP / un seul) |
| `make cov` / `make cov TP=4` | couverture lignes + branches (TP1 / simulateur) |
| `make mutate` / `make mutate EXTRA=1` | test de mutation de `remise.py` (+ mutants bonus) |
| `make mutmut` | mutation avec l'outil standard mutmut (comparaison) |
| `make check` / `make check EQUIPE=binome-07` | score de vos tests TP4 (+ ligne pour le classement) |
| `python tools/voir_simulation.py jour_nominal --set luminosity=0.5` | TP4 : voir une simulation (page animée dans `tp/tp4_simulator/vues/`) |
| `python tools/voir_chiffres.py rotate 10` | TP5 : voir les chiffres avant et après une transformation (page dans `tp/tp5_metamorphique/vues/`) |
| `python tools/gen_tests.py remise.py --spec SPEC.md` | génère des tests avec le LLM |
| `make pull-model` | télécharge le modèle LLM si l'image a été construite sans |

## 5. Règles

- **En binôme** : l'un écrit, l'autre conteste ; échangez les rôles à chaque TP.
- **On teste, on ne corrige pas** le code fourni. Un test rouge est souvent une découverte : notez-la.
- Jugez les tests **par rapport à la spécification** (`SPEC.md`, `EXIGENCES.md`), pas par rapport au code.
- **N'ouvrez pas `tp/tp4_simulator/.check_data/`** : il contient les versions cachées utilisées par `make check`.
- LLM : le modèle local (Ollama) est utilisé par défaut. Une clé d'API personnelle peut être
  fournie par variable d'environnement (`OPENAI_API_KEY`, ou `ANTHROPIC_API_KEY` avec le nom du
  modèle dans `ANTHROPIC_MODEL`), **jamais dans le code**.
  LLM indisponible ? Ajoutez `--fallback` : une sortie d'exemple est copiée depuis `fallback/`.
- Bloqué ? Relisez la consigne, puis la grille ou la spécification, puis demandez à vos voisins ;
  après 5 minutes, appelez l'enseignant.

## 6. Rendre votre travail

1. Complétez `tp/RENDU.md` (TP1 à TP4) et `tp/tp5_metamorphique/relation.md` (TP5).
2. Vos tests restent dans les dossiers des TP (`test_reecrits.py`, `test_mutation.py`,
   `test_scenarios.py`, `test_metamorphic.py`).
3. À la fin de la séance, déposez sur Moodle une archive zip de votre dossier `tp/` (un dépôt
   par binôme). Sur les postes de la salle, vos fichiers peuvent être effacés à la
   déconnexion : déposez avant de partir.

# TP4 — Stratégie de test d'un système autonome (25 min)

**Objectif** : tester un système dont un composant est une IA (la perception) sans oracle
parfait : choisir une **question** de sécurité, la **technique** adaptée, puis écrire le **test**.
`make check` mesure combien de défauts cachés votre suite détecte, sans fausse alarme.

**En binôme** : l'un propose la question et la technique, l'autre écrit le test et vérifie qu'il
respecte [`EXIGENCES.md`](EXIGENCES.md) (ODD, seuils). Échangez à chaque test.

| Étapes | 1 | 2 | 3 | 4 | 5 |
|--------|---|---|---|---|---|
| Durée  | 3 min | 4 min | 12 min | 3 min | 3 min |

## L'essentiel de l'API (`from sim import ...`)

```python
from sim import (Scenario, run, run_baseline, load_scenario, validate_scenario, in_odd, odd_violations,
                 no_collision, min_distance_at_least, brakes_when_pedestrian_detected, check,
                 fault, CameraDegraded, GPSLost, SensorDelay, LidarNoise)

s = Scenario(car_speed=13.9, initial_distance=45, pedestrian_y=-3, pedestrian_speed=1.2,
             luminosity=0.3, occlusion=0.5)            # champs et unités : sim/scenario.py
validate_scenario(s)                                   # ValueError si physiquement impossible
r = run(s, seed=0)                                     # simulation déterministe
print(r)                                               # résumé + journal des événements
check(r, no_collision, min_distance_at_least(2.0))     # échec = message détaillé
with fault(CameraDegraded(0.6)):                       # injection de panne
    r = run(s, seed=0)
s2 = s.replace(luminosity=0.8)                         # scénario dérivé (métamorphique)
rb = run_baseline(s, seed=0)                           # système de comparaison (différentiel)
```

## Créer une situation

Une situation est un `Scenario` : dix réglages. Partez d'un scénario fourni (dossier `scenarios/`)
ou des valeurs par défaut, et changez ce que vous voulez avec `.replace(...)`. Le scénario de
départ n'est pas modifié : `.replace` en crée un nouveau.

```python
NOMINAL = load_scenario(SCENARIOS / "jour_nominal.json")              # une situation fournie
mouille = NOMINAL.replace(friction=0.5, initial_distance=35.0)        # route mouillée, passage à 35 m
gauche = Scenario(pedestrian_y=4.0, pedestrian_speed=-1.2)            # piéton venant de la gauche
```

| Réglage (nom dans le code) | Signification | Défaut | Limite des exigences (ODD) |
|----------------------------|---------------|--------|----------------------------|
| `car_speed` | vitesse de la voiture, en m/s | 13.9 (50 km/h) | 13,9 au plus |
| `initial_distance` | distance au passage piéton au départ, en m | 45 | voir ci-dessous |
| `pedestrian_y` | position du piéton en travers de la route, en m | −3 | aucune |
| `pedestrian_speed` | vitesse du piéton en travers de la route, en m/s | 1.2 | de −2 à 2 |
| `luminosity` | lumière : 0 nuit noire, 1 plein jour | 1.0 | 0,2 au moins |
| `occlusion` | part du piéton masquée, de 0 à 1 | 0.0 | 0,6 au plus |
| `friction` | adhérence : 0,8 sec, 0,5 mouillé, 0,1 verglas | 0.8 | 0,4 au moins |
| `sensor_noise` | imprécision du lidar, en m | 0.1 | 0,3 au plus |
| `sensor_latency_ms` | retard normal des mesures, en ms | 0 | 100 au plus |
| `sensor_dropout` | part des trames capteur perdues, de 0 à 1 | 0.0 | 0,3 au plus |

- `initial_distance` : au moins la distance de freinage + 15 m, soit 27,3 m sur route sèche à
  50 km/h, davantage sur route mouillée. `in_odd` fait le calcul pour vous.
- `pedestrian_y` : 0 est le milieu de la voie de la voiture, qui va de −1,75 à +1,75 ; une valeur
  négative est sur le trottoir de droite, où le piéton attend par défaut.
- `pedestrian_speed` : positive, le piéton va vers les y croissants (depuis le trottoir de droite,
  il traverse) ; négative, il va dans l'autre sens ; 0, il reste immobile.
- `sensor_latency_ms` : au-delà de 100 ms, ce n'est plus un réglage mais une panne (`SensorDelay`).

**Les pannes** se placent autour de `run`, avec `with fault(...)` :

| Panne | Signification | Limite de R4 |
|-------|---------------|--------------|
| `CameraDegraded(level)` | caméra salie ou éblouie : 0 intacte, 1 aveugle | tout niveau |
| `SensorDelay(ms)` | retard supplémentaire de toutes les mesures, en ms | 300 au plus |
| `LidarNoise(sigma)` | bruit supplémentaire du lidar, en m | 0,3 au plus |
| `GPSLost()` | plus de signal GPS | toujours |

R4 couvre **une** panne à la fois. **La graine** (`run(s, seed=3)`) fixe le hasard des capteurs :
même situation et même graine donnent le même résultat. Bouclez sur plusieurs graines pour
tester une situation plusieurs fois.

## Rester dans les limites (sinon : fausse alarme)

Les exigences R1 à R3 ne s'appliquent que **dans l'ODD** (colonne de droite du premier tableau),
et R4 seulement avec **une** panne dans ses limites. En dehors, la voiture n'a rien promis : un test
qui y exige « pas de collision » peut échouer aussi sur la version correcte. C'est une **fausse
alarme**, et votre score de `make check` tombe à 0.

Mettez la vérification dans le test, avant d'exiger un bon comportement :

```python
def test_route_mouillee():
    scenario = NOMINAL.replace(friction=0.5, initial_distance=35.0)
    assert in_odd(scenario), odd_violations(scenario)    # s'arrête ici, avec la raison, si hors limites
    check(run(scenario, seed=0), no_collision)
```

`odd_violations(scenario)` explique ce qui sort des limites. Pour une route verglacée
(`friction=0.1`), elle répond : `friction = 0.1 hors de l'ODD [0.4, 1.0]` et
`initial_distance = 45.0 < 113.5 m nécessaires`. Une situation physiquement impossible (une
latence de 300 ms comme réglage, par exemple) est refusée dès `run`, avec un message.

## Voir une simulation

Depuis la racine du dépôt, dans le terminal du conteneur :

```bash
python tools/voir_simulation.py jour_nominal                                     # un scénario fourni
python tools/voir_simulation.py jour_nominal --set friction=0.5 initial_distance=35   # avec vos réglages
python tools/voir_simulation.py jour_nominal --panne "LidarNoise(0.2)" --graine 3     # avec une panne
python tools/voir_simulation.py jour_nominal --comparer friction=0.5             # deux voitures côte à côte
python tools/voir_simulation.py jour_nominal --baseline                          # avec le robot simple
```

La commande affiche le résumé de la simulation et écrit une page animée dans
`tp/tp4_simulator/vues/` : vue de dessus, vitesse, distance au piéton, journal. Ouvrez-la sur
votre ordinateur par un double-clic (Codespaces : clic droit sur le fichier, puis *Download*).
La page signale **HORS DES LIMITES** toute situation où les exigences ne s'appliquent pas.

Depuis un test, `voir` écrit la page des résultats que vous lui donnez :

```python
from tools.voir_simulation import voir

result = run(scenario, seed=0)
voir(result)                  # ou voir(result_1, result_2) pour comparer deux exécutions
```

## Étapes

1. **Lisez** [`EXIGENCES.md`](EXIGENCES.md) (exigences R1–R5, domaine opérationnel) et lancez
   `make test TP=4` : les deux tests fournis passent.
2. **Le cas du cours** : nuit + piéton partiellement caché
   ([`scenarios/nuit_pieton_partiellement_cache.json`](scenarios/)). Écrivez le test dans
   [`test_scenarios.py`](test_scenarios.py), lancez-le, lisez `print(result)`. Que se passe-t-il ?
   Pour le voir : `python tools/voir_simulation.py nuit_pieton_partiellement_cache`.
3. **Une question, une technique, un test.** Écrivez au moins un test par technique :
   - **Génération de scénarios** : valeurs limites de l'ODD, familles de scénarios, tirage
     aléatoire (`python tools/random_scenarios.py --n 200` : que contient vraiment un tirage
     naïf ?). Bouclez sur plusieurs scénarios et plusieurs graines.
   - **Injection de pannes** : `with fault(...)` (bornes de R4).
   - **Métamorphique** : une transformation du scénario qui ne doit pas rendre le système moins
     sûr (exemple : plus de lumière, toutes choses égales par ailleurs).
   - **Différentiel** : comparez `run` et `run_baseline` (freinage d'urgence simple, sans IA) :
     quand la baseline évite le piéton, le système complet doit l'éviter aussi.
   Choisissez l'oracle le plus fort justifié par EXIGENCES.md (pas seulement `no_collision`).
   Option LLM : `python tools/random_scenarios.py --llm "piétons difficiles à voir"` demande des
   scénarios au LLM puis les passe à `validate_scenario()` (sans LLM : `--llm-fallback`).
4. **Évaluez** votre suite : `make check`. Une fausse alarme (échec sur la version correcte)
   annule le score : corrigez l'oracle ou sortez le scénario de vos tests s'il est hors ODD.
5. **Justifiez** dans `tp/RENDU.md` : tableau question → technique → test, et score de `make check`.

> Règle du jeu : le dossier `.check_data/` contient les versions cachées utilisées par
> `make check`. **Ne l'ouvrez pas et ne cherchez pas à le décoder** : le but est de trouver les
> défauts par vos tests. Lire le code de `sim/` est en revanche autorisé.

## À rendre (dans `tp/RENDU.md`, section TP4)

- Vos **tests** (`test_scenarios.py`, et d'autres fichiers `test_*.py` si besoin).
- La **justification** de chaque test : question → technique → test.
- Le **score** affiché par `make check` (et les variantes détectées).

## Si vous êtes bloqué

1. Relisez la question, `EXIGENCES.md` et le journal (`print(result)`).
2. Comparez avec votre voisin.
3. Toujours bloqués après 5 minutes ? Appelez l'enseignant.

## Défis bonus (binômes rapides)

- **Famille de scénarios « pluie »** : `python tools/random_scenarios.py --famille pluie --n 30`
  (fonction `famille_pluie()` dans `tools/random_scenarios.py`). Écrivez le test qui l'utilise.
  Trouve-t-il un défaut que vos autres tests ne trouvent pas ?
- Écrivez une propriété Hypothesis sur des scénarios tirés dans l'ODD (`@given` avec
  `st.floats(...)` pour chaque champ, puis `assume(in_odd(s))`).
- Testez R5 (mode dégradé GPS) à partir de `result.trace`.

> **Ce que vous devez savoir expliquer en sortant de ce TP**
>
> - Pourquoi la couverture ne suffit pas pour un système dont la perception est une IA.
> - Quelle technique a trouvé quel défaut, et pourquoi les autres ne pouvaient pas le trouver.
> - Pourquoi une fausse alarme compte autant qu'un défaut manqué.

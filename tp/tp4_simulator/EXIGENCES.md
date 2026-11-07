# Exigences de sécurité du système (TP4)

Système testé : un véhicule autonome **jouet** approche d'un passage piéton. Chaîne de
traitement : capteurs → perception (classe + confiance) → prédiction (suivi, trajectoire) →
planification (continuer / ralentir / freiner) → contrôle (décélération).
Modèle simplifié à visée pédagogique : il ne reproduit aucun véhicule ni aucun événement réel.

## Domaine opérationnel (ODD)

Les exigences R1 à R3 s'appliquent aux scénarios **valides** (`validate_scenario`) et
**dans l'ODD** (`in_odd(scenario)` ; `odd_violations(scenario)` explique pourquoi un scénario en sort).

| Paramètre | Dans l'ODD |
|-----------|-----------|
| `car_speed` | ≤ 13,9 m/s (50 km/h) |
| `friction` | ≥ 0,4 |
| `luminosity` | ≥ 0,2 |
| `occlusion` | ≤ 0,6 |
| `sensor_noise` | ≤ 0,3 m |
| `sensor_dropout` | ≤ 0,3 |
| `pedestrian_speed` | entre −2 et 2 m/s |
| `sensor_latency_ms` | ≤ 100 ms (toujours : c'est la spécification du capteur) |
| `initial_distance` | ≥ distance de freinage (`stopping_distance(car_speed, friction)`) + 15 m |

## Exigences

| Id | Exigence | Oracle fourni |
|----|----------|---------------|
| R1 | Le véhicule ne percute jamais le piéton. | `no_collision` |
| R2 | Tant que le piéton est sur la voie du véhicule, la distance entre eux reste **d'au moins 2 m**. | `min_distance_at_least(2.0)` |
| R3 | Si les capteurs mesurent le piéton alors qu'il est sur la voie devant le véhicule, le véhicule **freine dans la seconde** (ou est déjà arrêté). | `brakes_when_pedestrian_detected` |
| R4 | Avec **une** panne parmi `CameraDegraded` (tout niveau), `SensorDelay` (jusqu'à 300 ms), `LidarNoise` (σ ≤ 0,3 m), `GPSLost`, R1 reste vraie dans l'ODD. | `with fault(...)` + `no_collision` |
| R5 | En cas de perte GPS, le véhicule passe en mode dégradé et ralentit vers 30 km/h (8,3 m/s) s'il n'y a pas d'obstacle. | à écrire (`result.trace`, `result.final_speed`) |

En dehors de l'ODD ou au-delà des pannes de R4, **rien n'est exigé** : un test qui y attend
une absence de collision est un oracle injustifié (il peut échouer sur un système correct).

## Ce que renvoie `run(scenario, seed)`

`Result` : `collision` (bool), `collision_time`, `min_distance` (m, mesurée tant que le piéton
est sur la voie), `first_detection_time` (s), `final_speed`, `log` (journal lisible),
`trace` (un dictionnaire par pas de 50 ms : `t`, `car_x`, `speed`, `pedestrian_y`,
`observed`, `action`, `decel`). `print(result)` affiche un résumé et le journal.
Même scénario + même graine (`seed`) = même résultat.

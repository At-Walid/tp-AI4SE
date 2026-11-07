"""Scénarios : description, validation physique et domaine opérationnel (ODD)."""

import dataclasses
import json
import math
from dataclasses import dataclass
from pathlib import Path

from .world import ROAD_MODEL_HALF_WIDTH, stopping_distance


@dataclass(frozen=True)
class Scenario:
    """Un scénario de test. Unités : m, m/s, ms ; valeurs sans unité entre 0 et 1."""

    car_speed: float = 13.9  # m/s (13.9 m/s ≈ 50 km/h)
    initial_distance: float = 45.0  # m entre l'avant du véhicule et le passage piéton
    pedestrian_y: float = -3.0  # m, position latérale initiale (0 = centre de la voie)
    pedestrian_speed: float = 1.2  # m/s, vitesse latérale (> 0 : vers les y croissants)
    occlusion: float = 0.0  # 0 = piéton entièrement visible, 1 = entièrement masqué
    luminosity: float = 1.0  # 0 = nuit noire, 1 = plein jour
    friction: float = 0.8  # adhérence : 0.8 sec, 0.5 mouillé, 0.1 verglas
    sensor_noise: float = 0.1  # m, écart-type du bruit de position du lidar
    sensor_latency_ms: float = 0.0  # ms, retard nominal des mesures (arrondi à 50 ms)
    sensor_dropout: float = 0.0  # probabilité qu'une trame capteur soit perdue
    name: str = ""

    def replace(self, **changes):
        """Copie du scénario avec quelques champs modifiés : s.replace(luminosity=0.5)."""
        return dataclasses.replace(self, **changes)

    def to_dict(self):
        return dataclasses.asdict(self)


# Bornes physiques (validate_scenario) : en dehors, le scénario n'a pas de sens.
LIMITS = {
    "car_speed": (0.0, 40.0, "vitesse négative impossible ; au-delà de 40 m/s, hors modèle"),
    "initial_distance": (1.0, 200.0, "le véhicule doit être en amont du passage (1 à 200 m)"),
    "pedestrian_y": (
        -ROAD_MODEL_HALF_WIDTH,
        ROAD_MODEL_HALF_WIDTH,
        "piéton hors du modèle de route (chaussée + trottoirs)",
    ),
    "pedestrian_speed": (-3.0, 3.0, "plus rapide qu'un piéton qui court"),
    "occlusion": (0.0, 1.0, "fraction masquée entre 0 et 1"),
    "luminosity": (0.0, 1.0, "luminosité entre 0 et 1"),
    "friction": (0.1, 1.0, "adhérence physiquement impossible"),
    "sensor_noise": (0.0, 1.0, "écart-type de bruit entre 0 et 1 m"),
    "sensor_latency_ms": (
        0.0,
        100.0,
        "spécification du capteur : 0 à 100 ms ; au-delà c'est une panne (SensorDelay)",
    ),
    "sensor_dropout": (0.0, 1.0, "probabilité entre 0 et 1"),
}

# Domaine opérationnel (ODD) : conditions dans lesquelles les exigences s'appliquent.
ODD = {
    "car_speed": (0.0, 13.9),
    "friction": (0.4, 1.0),
    "luminosity": (0.2, 1.0),
    "occlusion": (0.0, 0.6),
    "sensor_noise": (0.0, 0.3),
    "sensor_dropout": (0.0, 0.3),
    "pedestrian_speed": (-2.0, 2.0),
}
ODD_REACTION_MARGIN = 15.0  # m de marge au-delà de la distance de freinage


def validate_scenario(scenario):
    """Lève ValueError si le scénario est physiquement impossible ; sinon le renvoie."""
    if not isinstance(scenario, Scenario):
        raise ValueError(f"Scénario invalide : un Scenario est attendu, pas {type(scenario).__name__}")
    errors = []
    for field, (low, high, why) in LIMITS.items():
        value = getattr(scenario, field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or math.isnan(value):
            errors.append(f"{field} = {value!r} : valeur numérique attendue")
        elif not low <= value <= high:
            errors.append(f"{field} = {value} hors de [{low}, {high}] : {why}")
    if errors:
        raise ValueError("Scénario invalide :\n  - " + "\n  - ".join(errors))
    return scenario


def odd_violations(scenario):
    """Liste des raisons pour lesquelles le scénario sort du domaine opérationnel."""
    validate_scenario(scenario)
    reasons = []
    for field, (low, high) in ODD.items():
        value = getattr(scenario, field)
        if not low <= value <= high:
            reasons.append(f"{field} = {value} hors de l'ODD [{low}, {high}]")
    needed = stopping_distance(scenario.car_speed, scenario.friction) + ODD_REACTION_MARGIN
    if scenario.initial_distance < needed:
        reasons.append(f"initial_distance = {scenario.initial_distance} < {needed:.1f} m nécessaires")
    return reasons


def in_odd(scenario):
    """Vrai si le scénario est valide et dans le domaine opérationnel (voir EXIGENCES.md)."""
    return not odd_violations(scenario)


def scenario_from_dict(data):
    """Construit un Scenario à partir d'un dictionnaire (clés inconnues refusées)."""
    data = dict(data)
    data.pop("description", None)
    known = {f.name for f in dataclasses.fields(Scenario)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise ValueError(f"Champs inconnus dans le scénario : {', '.join(unknown)}")
    return Scenario(**data)


def load_scenario(path):
    """Charge un scénario depuis un fichier JSON (voir le dossier scenarios/)."""
    with open(Path(path), encoding="utf-8") as f:
        return scenario_from_dict(json.load(f))

"""Perception : transforme les observations capteur en objets classés (classe + confiance)."""

from dataclasses import dataclass

LABELS = ("pieton", "inconnu", "vehicule")
PEDESTRIAN_MIN_SCORE = 0.55  # score caméra minimal pour la classe « pieton »
VEHICLE_MIN_WIDTH = 1.5  # m : un objet plus large est classé « vehicule »
MAX_MEASUREMENT_AGE_MS = 150  # ms : au-delà, une mesure est périmée


@dataclass(frozen=True)
class DetectedObject:
    timestamp: float  # s : instant de la mesure
    distance: float  # m : distance depuis le lidar
    y: float  # m : position latérale
    label: str  # une valeur de LABELS
    confidence: float  # 0..1 : score de la caméra


def classify(width, camera_score):
    """Classe d'un objet d'après sa largeur (lidar) et le score de la caméra."""
    if width >= VEHICLE_MIN_WIDTH:
        return "vehicule"
    if camera_score >= PEDESTRIAN_MIN_SCORE:
        return "pieton"
    return "inconnu"


def perceive(frame):
    """Liste des objets détectés dans une trame capteur."""
    objects = []
    for obs in frame.observations:
        if round((frame.t - obs.timestamp) * 1000) > MAX_MEASUREMENT_AGE_MS:
            continue
        label = classify(obs.width, obs.camera_score)
        objects.append(DetectedObject(obs.timestamp, obs.distance, obs.y, label, obs.camera_score))
    return objects

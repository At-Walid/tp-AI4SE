"""Planification : décide de continuer, ralentir ou freiner."""

from dataclasses import dataclass

from .world import LANE_HALF_WIDTH

STOP_MARGIN = 3.0  # m : distance visée entre l'avant du véhicule et le piéton à l'arrêt
MIN_CONFIDENCE = 0.5  # confiance minimale pour prendre un objet en compte
PATH_HALF_WIDTH = LANE_HALF_WIDTH + 0.5  # m : couloir surveillé (voie + marge)
HYSTERESIS = 1.0  # m : une menace le reste tant qu'elle n'est pas sortie du couloir + cette marge
COMFORT_DECEL = 3.0  # m/s² : au-delà, l'action est « brake » plutôt que « slow »
DEGRADED_SPEED = 8.3  # m/s (30 km/h) : vitesse visée en mode dégradé (GPS perdu)
DEGRADED_DECEL = 1.0  # m/s²
MAX_LOOKAHEAD = 6.0  # s : horizon maximal de prédiction
LOOKAHEAD_STEP = 0.25  # s


@dataclass(frozen=True)
class Command:
    action: str  # "continue", "slow" ou "brake"
    stop_distance: float = None  # m, du lidar jusqu'au point d'arrêt visé (None : pas d'arrêt visé)
    decel: float = 0.0  # m/s², pour un ralentissement sans point d'arrêt
    reason: str = ""


def is_threat(track, ego_speed):
    """Vrai si la piste est, ou sera d'après la prédiction, dans le couloir avant le passage du véhicule."""
    if track.distance <= 0:
        return False
    lookahead = min(track.distance / max(ego_speed, 0.5) + 1.0, MAX_LOOKAHEAD)
    steps = int(lookahead / LOOKAHEAD_STEP)
    return any(abs(track.predict_y(k * LOOKAHEAD_STEP)) <= PATH_HALF_WIDTH for k in range(steps + 1))


class Planner:
    def __init__(self):
        self.threat_ids = set()  # pistes considérées comme menaces au pas précédent

    def _is_threat(self, track, ego_speed):
        if track.id in self.threat_ids and track.distance > 0:
            if abs(track.y) <= PATH_HALF_WIDTH + HYSTERESIS:
                return True
        return is_threat(track, ego_speed)

    def plan(self, tracks, ego_speed, gps_ok):
        threats = [
            track
            for track in tracks
            if track.confidence >= MIN_CONFIDENCE and self._is_threat(track, ego_speed)
        ]
        self.threat_ids = {track.id for track in threats}
        if threats:
            target = min(threats, key=lambda track: track.distance)
            stop_distance = target.distance - STOP_MARGIN
            needed = ego_speed**2 / (2 * max(stop_distance, 0.1))
            action = "brake" if needed > COMFORT_DECEL else "slow"
            why = f"{target.label} (confiance {target.confidence:.2f}) à {target.distance:.1f} m"
            return Command(action, stop_distance=stop_distance, reason=why)
        if not gps_ok and ego_speed > DEGRADED_SPEED:
            return Command("slow", decel=DEGRADED_DECEL, reason="mode dégradé : GPS perdu")
        return Command("continue")

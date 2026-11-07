"""Prédiction : suivi des objets (pistes) et trajectoire à court terme du piéton.

Une piste regroupe les détections successives d'un même objet. Sa vitesse
latérale est estimée par régression linéaire sur les dernières positions, ce
qui permet de prédire où sera le piéton dans quelques secondes.
"""

from dataclasses import dataclass, field

from .world import DT

GATE = 2.0  # m : distance maximale pour associer une détection à une piste
CONFIRM_HITS = 3  # détections nécessaires pour confirmer une piste
MAX_MISSES = 10  # pas sans détection avant d'abandonner une piste confirmée (0.5 s)
MAX_MISSES_TENTATIVE = 2  # idem pour une piste pas encore confirmée
HISTORY = 20  # positions conservées pour estimer la vitesse
MIN_HISTORY = 5  # positions nécessaires avant d'estimer une vitesse
SMOOTHING = 0.5  # lissage de la distance (0 : aucune mise à jour, 1 : dernière mesure)


@dataclass
class Track:
    id: int
    label: str
    confidence: float
    distance: float  # m depuis le lidar, ramenée à l'instant courant
    y: float  # m, ramenée à l'instant courant
    vy: float = 0.0  # m/s, vitesse latérale estimée
    hits: int = 1
    misses: int = 0
    history: list = field(default_factory=list)  # [(timestamp, y), ...]

    @property
    def confirmed(self):
        return self.hits >= CONFIRM_HITS

    def predict_y(self, dt):
        """Position latérale prédite dans dt secondes (vitesse constante)."""
        return self.y + self.vy * dt


def fit_line(points, t):
    """Régression linéaire y = a + b * t sur points ; renvoie (y à l'instant t, pente b)."""
    n = len(points)
    mean_t = sum(p[0] for p in points) / n
    mean_y = sum(p[1] for p in points) / n
    var_t = sum((p[0] - mean_t) ** 2 for p in points)
    if var_t == 0:
        return mean_y, 0.0
    slope = sum((p[0] - mean_t) * (p[1] - mean_y) for p in points) / var_t
    return mean_y + slope * (t - mean_t), slope


class Tracker:
    def __init__(self):
        self.tracks = []
        self._next_id = 1

    def confirmed_tracks(self):
        return [track for track in self.tracks if track.confirmed]

    def update(self, frame, objects):
        """Met à jour les pistes avec les objets perçus ; renvoie les pistes confirmées."""
        for track in self.tracks:  # le véhicule a avancé, le piéton a bougé
            track.distance -= frame.ego_speed * DT
            track.y = track.predict_y(DT)
        if not frame.valid:
            # Trame vide : aucun objet devant le véhicule.
            self.tracks = []
            return []
        unmatched = list(self.tracks)
        for obj in objects:
            age = frame.t - obj.timestamp
            distance = obj.distance - frame.ego_speed * age  # compensation du retard
            track = self._closest(unmatched, distance, obj.y)
            if track is None:
                self._create(obj, distance, frame.t)
            else:
                unmatched.remove(track)
                self._update(track, obj, distance, frame.t)
        for track in unmatched:
            track.misses += 1
        self.tracks = [
            track
            for track in self.tracks
            if track.misses <= (MAX_MISSES if track.confirmed else MAX_MISSES_TENTATIVE)
        ]
        return self.confirmed_tracks()

    def _closest(self, tracks, distance, y):
        def gap(track):
            return abs(track.distance - distance) + abs(track.y - y)

        candidates = [track for track in tracks if gap(track) <= GATE]
        return min(candidates, key=gap, default=None)

    def _create(self, obj, distance, t):
        track = Track(self._next_id, obj.label, obj.confidence, distance, obj.y)
        track.history.append((obj.timestamp, obj.y))
        self._next_id += 1
        self.tracks.append(track)

    def _update(self, track, obj, distance, t):
        if obj.label != track.label:
            # Nouvelle classe : on repart d'une piste neuve pour cet objet.
            self.tracks.remove(track)
            self._create(obj, distance, t)
            return
        track.confidence = obj.confidence
        track.distance += SMOOTHING * (distance - track.distance)
        track.history = (track.history + [(obj.timestamp, obj.y)])[-HISTORY:]
        if len(track.history) >= MIN_HISTORY:
            track.y, track.vy = fit_line(track.history, t)
        else:
            track.y, track.vy = obj.y, 0.0
        track.hits += 1
        track.misses = 0

"""Capteurs : lidar (position du piéton) et caméra (score de reconnaissance).

Le lidar est monté sur le toit, 1 m en retrait du pare-chocs avant : toutes les
distances qu'il mesure partent de sa position, pas de l'avant du véhicule.
Chaque mesure porte l'instant où elle a été prise (timestamp) ; avec de la
latence, elle arrive plus tard (frame.t > timestamp).
"""

import math
from dataclasses import dataclass

from .faults import CameraDegraded, GPSLost, LidarNoise, SensorDelay
from .world import DT, tick_time

SENSOR_RANGE = 60.0  # m : portée du lidar
SENSOR_SETBACK = 1.0  # m : retrait du lidar par rapport au pare-chocs avant
PEDESTRIAN_WIDTH = 0.6  # m : largeur réelle d'un piéton
LIDAR_OCCLUSION_MISS = 0.5  # probabilité de non-détection par unité d'occlusion
CAMERA_SCORE_NOISE = 0.07  # écart-type du bruit sur le score caméra


@dataclass(frozen=True)
class Observation:
    timestamp: float  # s : instant de la mesure
    distance: float  # m : distance longitudinale lidar -> piéton
    y: float  # m : position latérale du piéton
    width: float  # m : largeur apparente
    camera_score: float  # 0..1 : score « piéton » donné par la caméra


@dataclass(frozen=True)
class Frame:
    t: float  # s : instant de réception
    valid: bool  # False : trame perdue, aucune donnée reçue
    observations: tuple
    ego_speed: float  # m/s : vitesse mesurée par l'odométrie
    gps_ok: bool


class SensorSuite:
    def __init__(self, scenario, faults, rng):
        self.scenario = scenario
        self.rng = rng
        delay_ms = scenario.sensor_latency_ms + sum(f.ms for f in faults if isinstance(f, SensorDelay))
        self.lag = round(delay_ms / 1000 / DT)  # retard en nombre de pas
        extra_noise = sum(f.sigma for f in faults if isinstance(f, LidarNoise))
        self.noise = math.hypot(scenario.sensor_noise, extra_noise)
        degraded = max((f.level for f in faults if isinstance(f, CameraDegraded)), default=0.0)
        self.camera_factor = 1.0 - degraded
        self.gps_ok = not any(isinstance(f, GPSLost) for f in faults)

    def visibility(self):
        """Score caméra moyen (0..1) selon la lumière, l'occlusion et l'état de la caméra."""
        s = self.scenario
        return (0.3 + 0.7 * s.luminosity) * (1 - s.occlusion) * self.camera_factor

    def read(self, k, world):
        """Trame reçue au pas k. Les tirages aléatoires sont toujours faits dans le même ordre."""
        rng = self.rng
        lost, missed = rng.random(), rng.random()
        noise_d, noise_y, noise_w, noise_c = (rng.gauss(0, 1) for _ in range(4))
        t = tick_time(k)
        if lost < self.scenario.sensor_dropout:
            return Frame(t, False, (), world.speed, self.gps_ok)
        if k < self.lag:
            return Frame(t, True, (), world.speed, self.gps_ok)  # première mesure pas encore arrivée
        car_x, pedestrian_y = world.history[k - self.lag]
        distance = -car_x + SENSOR_SETBACK
        observations = ()
        visible = missed >= self.scenario.occlusion * LIDAR_OCCLUSION_MISS
        if 0 < distance <= SENSOR_RANGE and visible:
            score = self.visibility() + noise_c * CAMERA_SCORE_NOISE
            observation = Observation(
                timestamp=tick_time(k - self.lag),
                distance=distance + noise_d * self.noise,
                y=pedestrian_y + noise_y * self.noise,
                width=PEDESTRIAN_WIDTH + noise_w * self.noise,
                camera_score=min(max(score, 0.0), 1.0),
            )
            observations = (observation,)
        return Frame(t, True, observations, world.speed, self.gps_ok)

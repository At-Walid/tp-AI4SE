"""Boucle de simulation : capteurs -> perception -> prédiction -> planification -> contrôle."""

import math
import random
from dataclasses import dataclass, field

from .controller import Controller
from .faults import active_faults
from .perception import perceive
from .planner import PATH_HALF_WIDTH, STOP_MARGIN, Command, Planner
from .prediction import Tracker
from .scenario import validate_scenario
from .sensors import SENSOR_SETBACK, SensorSuite
from .world import (
    CAR_LENGTH,
    DT,
    G,
    LANE_HALF_WIDTH,
    MAX_DURATION,
    PEDESTRIAN_RADIUS,
    World,
    distance_car_pedestrian,
    stopping_distance,
    tick_time,
)


@dataclass
class Result:
    """Résultat d'une simulation."""

    scenario: object
    seed: int
    faults: tuple
    system: str  # "pipeline" (système complet) ou "baseline"
    collision: bool = False
    collision_time: float = None  # s
    min_distance: float = math.inf  # m, mesurée tant que le piéton est sur la voie du véhicule
    first_detection_time: float = None  # s : première mesure du piéton reçue par le système
    final_speed: float = 0.0  # m/s
    log: list = field(default_factory=list)  # événements datés, en clair
    trace: list = field(default_factory=list)  # un dictionnaire par pas de temps

    def summary(self):
        status = f"COLLISION à t={self.collision_time:.2f} s" if self.collision else "pas de collision"
        detection = "jamais" if self.first_detection_time is None else f"t={self.first_detection_time:.2f} s"
        faults = ", ".join(map(repr, self.faults)) or "aucune"
        lines = [
            f"Scénario {self.scenario.name or '(sans nom)'}, graine {self.seed}, système {self.system}",
            f"  pannes : {faults}",
            f"  {status} ; distance minimale {self.min_distance:.2f} m ; "
            f"première détection {detection} ; vitesse finale {self.final_speed:.1f} m/s",
            "  journal :",
        ]
        lines += [f"    {event}" for event in self.log]
        return "\n".join(lines)

    def __str__(self):
        return self.summary()


def _simulate(scenario, seed, decide, system):
    validate_scenario(scenario)
    faults = active_faults()
    rng = random.Random(seed)
    world = World(scenario)
    sensors = SensorSuite(scenario, faults, rng)
    result = Result(scenario, seed, faults, system)
    for f in faults:
        result.log.append(f"t=0.00 s : panne active {f!r}")
    last_action = None
    for k in range(int(MAX_DURATION / DT)):
        t = tick_time(k)
        frame = sensors.read(k, world)
        if frame.observations and result.first_detection_time is None:
            result.first_detection_time = t
            result.log.append(f"t={t:.2f} s : premières mesures du piéton reçues")
        command, decel = decide(frame, world.speed, scenario.friction)
        if command.action != last_action:
            detail = f" ({command.reason})" if command.reason else ""
            result.log.append(f"t={t:.2f} s : action {command.action}{detail}")
            last_action = command.action
        result.trace.append(
            {
                "t": t,
                "car_x": world.car_x,
                "speed": world.speed,
                "pedestrian_y": world.pedestrian_y,
                "observed": bool(frame.observations),
                "action": command.action,
                "decel": decel,
            }
        )
        world.step(decel)
        distance = distance_car_pedestrian(world.car_x, world.pedestrian_y)
        if abs(world.pedestrian_y) <= LANE_HALF_WIDTH:
            result.min_distance = min(result.min_distance, distance)
        if distance <= 0:
            result.collision = True
            result.collision_time = tick_time(k + 1)
            result.log.append(
                f"t={result.collision_time:.2f} s : COLLISION à {world.speed * 3.6:.0f} km/h"
            )
            break
        if world.car_x - CAR_LENGTH > PEDESTRIAN_RADIUS:
            result.log.append(f"t={tick_time(k + 1):.2f} s : le véhicule a franchi le passage")
            break
    result.final_speed = world.speed
    return result


def run(scenario, seed=0):
    """Simule le système complet sur un scénario. Même scénario + même graine = même résultat."""
    tracker, planner, controller = Tracker(), Planner(), Controller()

    def decide(frame, speed, friction):
        objects = perceive(frame)
        tracks = tracker.update(frame, objects)
        command = planner.plan(tracks, frame.ego_speed, frame.gps_ok)
        return command, controller.decel(command, speed, friction)

    return _simulate(scenario, seed, decide, "pipeline")


BASELINE_BUFFER = 2.0  # m ajoutés à la distance de freinage par la baseline


def run_baseline(scenario, seed=0):
    """Système de comparaison très simple, pour les tests différentiels.

    Freinage d'urgence « à l'ancienne » : pas de classification ni de prédiction.
    Dès qu'un objet mesuré par le lidar est dans le couloir et que la distance
    restante l'exige, freinage maximal jusqu'à l'arrêt. Il utilise les mêmes
    capteurs (mêmes tirages aléatoires) que le système complet.
    """
    braking = False

    def decide(frame, speed, friction):
        nonlocal braking
        if frame.valid and not braking:
            for obs in frame.observations:
                distance = obs.distance - speed * (frame.t - obs.timestamp)
                travel = distance - SENSOR_SETBACK - STOP_MARGIN
                close = travel <= stopping_distance(speed, friction) + BASELINE_BUFFER
                if abs(obs.y) <= PATH_HALF_WIDTH and close:
                    braking = True
        if braking:
            return Command("brake", reason="objet dans le couloir"), friction * G
        return Command("continue"), 0.0

    return _simulate(scenario, seed, decide, "baseline")

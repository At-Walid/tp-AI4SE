"""Simulateur jouet de conduite autonome devant un passage piéton (TP4).

    from sim import Scenario, run, no_collision, fault, CameraDegraded
    result = run(Scenario(luminosity=0.3), seed=0)
    assert no_collision(result)

Modèle simplifié à visée pédagogique, inspiré de modes de défaillance génériques
(perception, prédiction, contrôle). Il ne reproduit aucun événement réel.
"""

from .faults import CameraDegraded, GPSLost, LidarNoise, SensorDelay, fault
from .properties import (
    Property,
    brakes_when_pedestrian_detected,
    check,
    min_distance_at_least,
    no_collision,
)
from .scenario import (
    LIMITS,
    ODD,
    Scenario,
    in_odd,
    load_scenario,
    odd_violations,
    scenario_from_dict,
    validate_scenario,
)
from .simulation import Result, run, run_baseline
from .world import stopping_distance

__all__ = [
    "CameraDegraded",
    "GPSLost",
    "LidarNoise",
    "SensorDelay",
    "fault",
    "Property",
    "brakes_when_pedestrian_detected",
    "check",
    "min_distance_at_least",
    "no_collision",
    "LIMITS",
    "ODD",
    "Scenario",
    "in_odd",
    "load_scenario",
    "odd_violations",
    "scenario_from_dict",
    "validate_scenario",
    "Result",
    "run",
    "run_baseline",
    "stopping_distance",
]

"""Injection de pannes.

Exemple :
    with fault(CameraDegraded(0.6)):
        result = run(scenario, seed=0)

Plusieurs pannes à la fois : with fault(SensorDelay(200), LidarNoise(0.3)): ...
Une panne est active pendant toute la simulation lancée dans le bloc `with`.
"""

from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraDegraded:
    """Caméra dégradée (salissure, éblouissement) : level de 0 (intacte) à 1 (aveugle)."""

    level: float


@dataclass(frozen=True)
class GPSLost:
    """Perte du signal GPS pendant toute la simulation."""


@dataclass(frozen=True)
class SensorDelay:
    """Retard supplémentaire des mesures capteur, en millisecondes (arrondi à 50 ms)."""

    ms: float


@dataclass(frozen=True)
class LidarNoise:
    """Bruit supplémentaire du lidar : écart-type sigma en mètres."""

    sigma: float


_active = []


def _check(f):
    if isinstance(f, type):
        f = f()  # on accepte fault(GPSLost) comme fault(GPSLost())
    if isinstance(f, CameraDegraded) and not 0 <= f.level <= 1:
        raise ValueError("CameraDegraded : level doit être entre 0 et 1")
    if isinstance(f, SensorDelay) and f.ms < 0:
        raise ValueError("SensorDelay : ms doit être positif ou nul")
    if isinstance(f, LidarNoise) and f.sigma < 0:
        raise ValueError("LidarNoise : sigma doit être positif ou nul")
    if not isinstance(f, (CameraDegraded, GPSLost, SensorDelay, LidarNoise)):
        raise ValueError(f"Panne inconnue : {f!r}")
    return f


@contextmanager
def fault(*faults):
    """Active une ou plusieurs pannes pendant le bloc `with`."""
    checked = [_check(f) for f in faults]
    _active.extend(checked)
    try:
        yield
    finally:
        for f in checked:
            _active.remove(f)


def active_faults():
    return tuple(_active)

"""Propriétés de sécurité, utilisables comme oracles dans les tests.

    result = run(scenario, seed=0)
    assert no_collision(result)
    assert min_distance_at_least(2.0)(result)
    check(result, no_collision, min_distance_at_least(2.0))   # message d'erreur détaillé
"""

from .world import DT, LANE_HALF_WIDTH


class Property:
    """Une propriété : appelée sur un Result, elle renvoie True ou False."""

    def __init__(self, name, predicate):
        self.name = name
        self.predicate = predicate

    def __call__(self, result):
        return bool(self.predicate(result))

    def __repr__(self):
        return self.name


def _no_collision(result):
    return not result.collision


def _brakes_after_detection(result, max_delay=1.0):
    """Si le piéton est mesuré alors qu'il est sur la voie devant le véhicule en mouvement,
    le véhicule doit freiner (ou être arrêté) dans les max_delay secondes."""
    window = int(round(max_delay / DT)) + 1
    for i, step in enumerate(result.trace):
        on_lane = abs(step["pedestrian_y"]) <= LANE_HALF_WIDTH
        ahead = step["car_x"] < 0
        if step["observed"] and on_lane and ahead and step["speed"] > 0:
            return any(s["decel"] > 0 or s["speed"] == 0 for s in result.trace[i : i + window])
    return True


no_collision = Property("no_collision", _no_collision)
brakes_when_pedestrian_detected = Property(
    "brakes_when_pedestrian_detected", _brakes_after_detection
)


def min_distance_at_least(x):
    """Propriété : la distance minimale au piéton (sur la voie) est d'au moins x mètres."""
    return Property(f"min_distance_at_least({x})", lambda result: result.min_distance >= x)


def check(result, *properties):
    """Vérifie toutes les propriétés ; en cas d'échec, l'erreur affiche lesquelles et le journal."""
    failed = [p for p in properties if not p(result)]
    if failed:
        names = ", ".join(map(repr, failed))
        raise AssertionError(f"Propriété(s) violée(s) : {names}\n{result.summary()}")

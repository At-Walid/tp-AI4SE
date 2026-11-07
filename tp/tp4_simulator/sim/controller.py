"""Contrôle : transforme la commande du planificateur en décélération (limitée par l'adhérence)."""

from .world import G

MIN_TRAVEL = 0.1  # m : en dessous, freinage maximal


class Controller:
    def decel(self, command, speed, friction):
        """Décélération à appliquer (m/s²) pour exécuter la commande."""
        max_decel = friction * G
        if command.action == "continue":
            return 0.0
        if command.stop_distance is None:
            return min(command.decel, max_decel)
        # Distance que le véhicule peut encore parcourir avant le point d'arrêt.
        travel = command.stop_distance
        if travel <= MIN_TRAVEL:
            return max_decel
        return min(speed**2 / (2 * travel), max_decel)

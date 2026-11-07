"""Monde physique du simulateur : constantes, géométrie et cinématique.

Repère : le véhicule roule sur l'axe x, vers les x croissants. Le passage piéton
est en x = 0. Le piéton se déplace sur l'axe y (latéral) ; y = 0 est le centre de
la voie du véhicule, y < 0 le trottoir de droite, y > 0 l'autre côté.

Modèle jouet à visée pédagogique : il ne reproduit aucun véhicule ni aucun
événement réel.
"""

import math

DT = 0.05  # s : pas de simulation (20 Hz)
G = 9.81  # m/s²
MAX_DURATION = 15.0  # s : durée maximale d'une simulation

CAR_LENGTH = 4.5  # m
CAR_HALF_WIDTH = 0.9  # m
PEDESTRIAN_RADIUS = 0.3  # m
LANE_HALF_WIDTH = 1.75  # m : demi-largeur de la voie du véhicule
ROAD_MODEL_HALF_WIDTH = 10.0  # m : chaussée + trottoirs couverts par le modèle


def tick_time(k):
    """Instant (s) du pas numéro k, arrondi pour éviter les erreurs d'arrondi cumulées."""
    return round(k * DT, 6)


def stopping_distance(speed, friction):
    """Distance de freinage (m) à décélération maximale (friction * G), sans temps de réaction."""
    return speed**2 / (2 * friction * G)


def distance_car_pedestrian(car_front_x, pedestrian_y):
    """Distance (m) entre la carrosserie du véhicule et le bord du piéton ; 0 en cas de contact."""
    rear_x = car_front_x - CAR_LENGTH
    if car_front_x < 0:
        dx = -car_front_x
    elif rear_x > 0:
        dx = rear_x
    else:
        dx = 0.0
    dy = max(abs(pedestrian_y) - CAR_HALF_WIDTH, 0.0)
    return max(math.hypot(dx, dy) - PEDESTRIAN_RADIUS, 0.0)


class World:
    """Vérité terrain : position et vitesse du véhicule, position du piéton."""

    def __init__(self, scenario):
        self.car_x = -scenario.initial_distance  # position du pare-chocs avant
        self.speed = scenario.car_speed
        self.pedestrian_y = scenario.pedestrian_y
        self.pedestrian_speed = scenario.pedestrian_speed
        self.history = [(self.car_x, self.pedestrian_y)]  # un état par pas

    def step(self, decel):
        """Avance d'un pas de temps avec la décélération donnée (m/s²)."""
        if decel > 0 and self.speed <= decel * DT:
            self.car_x += self.speed**2 / (2 * decel)  # arrêt au cours du pas
            self.speed = 0.0
        else:
            self.car_x += (self.speed - decel * DT / 2) * DT
            self.speed -= decel * DT
        self.pedestrian_y += self.pedestrian_speed * DT
        self.history.append((self.car_x, self.pedestrian_y))

# Exemple pédagogique de sortie plausible d'un LLM, pas un résultat d'expérience.
# Tests « générés » pour le simulateur TP4. Pour les évaluer :
#   python tp/tp4_simulator/check.py --tests fallback/test_scenarios_llm.py
import pytest

from sim import CameraDegraded, GPSLost, Scenario, fault, no_collision, run


def test_scenario_par_defaut():
    result = run(Scenario(), seed=0)
    assert result is not None
    assert no_collision(result)


def test_vehicule_lent():
    result = run(Scenario(car_speed=5.0), seed=0)
    assert not result.collision


def test_pieton_loin_de_la_route():
    result = run(Scenario(pedestrian_y=-8.0, pedestrian_speed=0.0), seed=0)
    assert no_collision(result)


def test_nuit_noire():
    result = run(Scenario(luminosity=0.1), seed=0)
    assert no_collision(result)


def test_nuit_pieton_detecte():
    result = run(Scenario(luminosity=0.1, occlusion=0.3), seed=0)
    assert result.first_detection_time is not None


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_resultat_reproductible(seed):
    assert run(Scenario(), seed).collision == run(Scenario(), seed).collision


def test_camera_legerement_degradee():
    with fault(CameraDegraded(0.3)):
        result = run(Scenario(), seed=0)
    assert no_collision(result)


def test_gps_perdu():
    with fault(GPSLost()):
        result = run(Scenario(), seed=0)
    assert result.final_speed >= 0


def test_distance_minimale_positive():
    result = run(Scenario(), seed=0)
    assert result.min_distance > 0

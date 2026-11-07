"""Tests de l'outillage du TP4 : validation des scénarios, déterminisme, pannes, générateurs."""

import json
from pathlib import Path

import pytest

import sim
from sim import CameraDegraded, GPSLost, Scenario, SensorDelay, fault, run, run_baseline, validate_scenario
from tools import random_scenarios as rs

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tp" / "tp4_simulator" / "scenarios"


def test_scenario_par_defaut_valide_et_dans_odd():
    assert validate_scenario(Scenario()) == Scenario()
    assert sim.in_odd(Scenario())


@pytest.mark.parametrize(
    "changes, field",
    [
        ({"car_speed": -1.0}, "car_speed"),
        ({"pedestrian_y": 15.0}, "pedestrian_y"),
        ({"friction": 0.0}, "friction"),
        ({"luminosity": 1.5}, "luminosity"),
        ({"sensor_latency_ms": 250}, "sensor_latency_ms"),
        ({"initial_distance": 0.0}, "initial_distance"),
        ({"pedestrian_speed": float("nan")}, "pedestrian_speed"),
    ],
)
def test_validate_scenario_rejette_l_impossible(changes, field):
    with pytest.raises(ValueError, match=field):
        validate_scenario(Scenario(**changes))


def test_run_refuse_un_scenario_invalide():
    with pytest.raises(ValueError):
        run(Scenario(car_speed=-3.0), seed=0)


def test_champs_inconnus_refuses():
    with pytest.raises(ValueError, match="visibility"):
        sim.scenario_from_dict({"car_speed": 10, "visibility": 0.2})


def test_odd_explique_les_ecarts():
    reasons = sim.odd_violations(Scenario(car_speed=20.0, initial_distance=30.0))
    assert any("car_speed" in r for r in reasons) and any("initial_distance" in r for r in reasons)


@pytest.mark.parametrize("path", sorted(SCENARIOS.glob("*.json")), ids=lambda p: p.stem)
def test_scenarios_fournis_valides_et_dans_odd(path):
    assert sim.in_odd(sim.load_scenario(path))


@pytest.mark.parametrize("runner", [run, run_baseline])
def test_run_deterministe(runner):
    scenario = Scenario(sensor_noise=0.3, sensor_dropout=0.2, luminosity=0.5)
    first, second = runner(scenario, seed=7), runner(scenario, seed=7)
    assert first.trace == second.trace and first.log == second.log
    assert runner(scenario, seed=8).trace != first.trace  # la graine change bien le bruit


def test_pannes_actives_seulement_dans_le_bloc():
    with fault(GPSLost, CameraDegraded(0.5)):  # une classe est acceptée comme une instance
        inside = run(Scenario(), seed=0)
        assert len(sim.faults.active_faults()) == 2
    assert sim.faults.active_faults() == ()
    assert GPSLost() in inside.faults and CameraDegraded(0.5) in inside.faults


def test_panne_retirée_meme_en_cas_d_erreur():
    with pytest.raises(RuntimeError):
        with fault(SensorDelay(200)):
            raise RuntimeError
    assert sim.faults.active_faults() == ()


@pytest.mark.parametrize("bad", [CameraDegraded(2.0), SensorDelay(-1), "panne"])
def test_panne_invalide_refusee(bad):
    with pytest.raises(ValueError):
        with fault(bad):
            pass


def test_proprietes_sur_un_resultat():
    result = run(Scenario(), seed=0)
    assert sim.no_collision(result) == (not result.collision)
    assert sim.min_distance_at_least(0.0)(result)
    assert "min_distance_at_least(2.0)" == repr(sim.min_distance_at_least(2.0))
    with pytest.raises(AssertionError, match="Propriété"):
        sim.check(result, sim.min_distance_at_least(1000.0))


def test_tirage_aleatoire_reproductible_et_valide():
    first = rs.random_scenarios(20, seed=1)
    assert first == rs.random_scenarios(20, seed=1)
    for scenario in first:
        validate_scenario(scenario)
    assert all(sim.in_odd(s) for s in rs.random_scenarios(10, seed=2, odd_only=True))
    assert all(sim.in_odd(s) for s in rs.famille_pluie(10))


def test_crochet_llm_valide_les_propositions():
    text = (ROOT / "fallback" / "scenarios_llm.json").read_text(encoding="utf-8")
    valid, rejected = rs.check_proposals(rs.parse_json_list(text))
    names = {name for name, _ in rejected}
    assert {"marche_arriere", "pieton_sur_le_terre_plein", "brouillard_epais", "verglas"} <= names
    assert valid and all(isinstance(s, Scenario) for s in valid)


def test_parse_json_list_avec_bloc_markdown():
    answer = "Voici :\n```json\n" + json.dumps([{"name": "a", "car_speed": 5}]) + "\n```"
    assert rs.parse_json_list(answer) == [{"name": "a", "car_speed": 5}]


def test_paquet_de_variantes_lisible_par_check():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check", ROOT / "tp" / "tp4_simulator" / "check.py")
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    variants = check.load_variants()
    assert sorted(variants) == ["A", "B", "C", "D", "E", "reference"]
    assert all("simulation.py" in files for files in variants.values())

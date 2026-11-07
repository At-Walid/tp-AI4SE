"""Tests de tools/voir_simulation.py : la page animée d'une simulation du TP4."""

import json
import re

import pytest

import sim
from sim import GPSLost, LidarNoise, Scenario, SensorDelay, fault, run, run_baseline
from tools import voir_simulation as vs


def page_data(path):
    text = path.read_text(encoding="utf-8")
    payload = re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S).group(1)
    return text, json.loads(payload.replace("<\\/", "</"))


def test_voir_ecrit_une_page_autonome(tmp_path):
    result = run(Scenario(name="essai"), seed=0)
    path = vs.voir(result, dossier=tmp_path)
    text, data = page_data(path)
    assert path == tmp_path / "essai.html"
    assert text.startswith("<!doctype html>") and "__" not in text.replace("__init__", "")
    (case,) = data["cases"]
    (only,) = case["runs"]
    assert len(only["steps"]) == len(result.trace) + 1
    assert only["min_distance"] == round(result.min_distance, 2)
    assert "Dans les limites" in case["note"][0]


def test_comparaison_et_situation_hors_limites(tmp_path):
    s = Scenario(name="comparaison")
    path = vs.voir(run(s, 0), run(s.replace(friction=0.1), 0), run_baseline(s, 0), dossier=tmp_path)
    _, data = page_data(path)
    labels = [r["label"] for r in data["cases"][0]["runs"]]
    assert labels[0] == "Votre voiture"
    assert "friction = 0.1" in labels[1]
    assert labels[2].startswith("Robot de freinage simple")
    notes = data["cases"][0]["note"]
    assert len(notes) == 1 and "HORS DES LIMITES" in notes[0] and "friction" in notes[0]


@pytest.mark.parametrize(
    "faults, expected",
    [
        ((SensorDelay(300),), []),
        ((SensorDelay(400),), ["SensorDelay(400)"]),
        ((LidarNoise(0.5),), ["LidarNoise(0.5)"]),
        ((GPSLost(), LidarNoise(0.1)), ["plusieurs pannes"]),
    ],
)
def test_limites_des_pannes_de_r4(faults, expected):
    with fault(*faults):
        result = run(Scenario(), 0)
    reasons = vs.outside_limits(result, sim)
    assert len(reasons) == len(expected)
    for reason, word in zip(reasons, expected):
        assert word in reason


def test_lecture_des_reglages_et_des_pannes():
    assert vs.parse_settings(["luminosity=0.5", "initial_distance=35"]) == {"luminosity": 0.5, "initial_distance": 35.0}
    assert vs.parse_fault("SensorDelay(200)", sim) == SensorDelay(200.0)
    assert vs.parse_fault("GPSLost", sim) == GPSLost()
    for bad in ("Pluie(3)", "SensorDelay(beaucoup)"):
        with pytest.raises(ValueError):
            vs.parse_fault(bad, sim)
    with pytest.raises(ValueError):
        vs.parse_settings(["luminosity"])


def test_ligne_de_commande(tmp_path, capsys):
    code = vs.main(["jour_nominal", "--set", "friction=0.5", "initial_distance=35",
                    "--comparer", "friction=0.8", "--nom", "essai", "--dossier", str(tmp_path)])
    assert code == 0
    _, data = page_data(tmp_path / "essai.html")
    assert len(data["cases"][0]["runs"]) == 2
    assert "Vue écrite" in capsys.readouterr().out
    assert vs.main(["jour_nominal", "--set", "vitesse=10", "--dossier", str(tmp_path)]) == 2

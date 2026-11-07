"""TP4 — Vos tests du système de conduite.

Pour chaque test : une QUESTION de sécurité -> une TECHNIQUE -> le TEST (voir INSTRUCTIONS.md).
make test TP=4 lance ces tests sur le code fourni ; make check les évalue (score).
"""

from pathlib import Path

from sim import GPSLost, check, fault, load_scenario, no_collision, run

SCENARIOS = Path(__file__).parent / "scenarios"


def test_jour_nominal_pas_de_collision():
    """Question : en plein jour, le véhicule laisse-t-il le piéton traverser sans le heurter ?
    Technique : scénario écrit à la main (cas nominal). Exigence : R1."""
    scenario = load_scenario(SCENARIOS / "jour_nominal.json")
    result = run(scenario, seed=0)
    check(result, no_collision)


def test_perte_gps_pas_de_collision():
    """Question : la perte du GPS met-elle le piéton en danger ?
    Technique : injection de panne. Exigence : R4."""
    scenario = load_scenario(SCENARIOS / "jour_nominal.json")
    with fault(GPSLost()):
        result = run(scenario, seed=0)
    check(result, no_collision)


# À vous : le cas du cours (scenarios/nuit_pieton_partiellement_cache.json), puis au moins
# un test par technique : génération de scénarios, injection de pannes, métamorphique, différentiel.

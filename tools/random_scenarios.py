"""Génération de scénarios pour le TP4 : tirage aléatoire naïf, et scénarios proposés par un LLM.

    python tools/random_scenarios.py --n 200                # statistiques d'un tirage naïf
    python tools/random_scenarios.py --n 200 --odd          # tirage limité au domaine opérationnel
    python tools/random_scenarios.py --famille pluie        # famille de scénarios bonus
    python tools/random_scenarios.py --llm "piétons difficiles à voir la nuit"
    python tools/random_scenarios.py --llm-fallback         # sortie LLM d'exemple (sans LLM)
    ... --save tp/tp4_simulator/scenarios/generes.json      # pour réutiliser les scénarios valides

Dans un test :
    from tools.random_scenarios import random_scenarios, load_scenarios
    for s in random_scenarios(30, seed=1, odd_only=True): ...

Le tirage naïf est uniforme dans les bornes physiques : il produit surtout des cas
« faciles » (piéton loin de la trajectoire, véhicule hors ODD...). Regardez les
statistiques avant de lui faire confiance.
"""

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
try:
    import sim
except ImportError:
    sys.path.insert(0, str(REPO / "tp" / "tp4_simulator"))
    import sim
try:
    from tools import llm
except ImportError:
    import llm

LLM_FALLBACK = REPO / "fallback" / "scenarios_llm.json"
FIELDS = [name for name in sim.LIMITS]


def random_scenario(rng):
    """Un scénario tiré uniformément dans les bornes physiques (toujours valide)."""
    values = {name: rng.uniform(low, high) for name, (low, high, _) in sim.LIMITS.items()}
    values["sensor_latency_ms"] = rng.choice([0, 50, 100])
    return sim.Scenario(**values, name="aleatoire")


def random_scenarios(n, seed=0, odd_only=False):
    """n scénarios aléatoires reproductibles ; odd_only : on rejette ceux hors ODD."""
    rng = random.Random(seed)
    scenarios = []
    while len(scenarios) < n:
        s = random_scenario(rng)
        if not odd_only or sim.in_odd(s):
            scenarios.append(s.replace(name=f"aleatoire_{len(scenarios)}"))
    return scenarios


def famille_pluie(n, seed=0):
    """Famille bonus : chaussée mouillée en fin de journée, piéton qui traverse."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(n):
        speed = rng.uniform(8.0, 13.9)
        friction = rng.uniform(0.4, 0.6)
        distance = sim.stopping_distance(speed, friction) + rng.uniform(16.0, 30.0)
        scenarios.append(
            sim.Scenario(
                car_speed=speed,
                initial_distance=distance,
                pedestrian_y=rng.uniform(-5.0, -2.5),
                pedestrian_speed=rng.uniform(0.8, 1.8),
                luminosity=rng.uniform(0.3, 0.6),
                occlusion=rng.uniform(0.0, 0.4),
                friction=friction,
                sensor_noise=rng.uniform(0.15, 0.3),
                name=f"pluie_{i}",
            )
        )
    return scenarios


def conflict(s):
    """Vrai si, sans freiner, le véhicule percuterait le piéton (vérité terrain)."""
    if s.car_speed <= 0:
        return False
    t_front = s.initial_distance / s.car_speed  # l'avant atteint le passage
    t_rear = (s.initial_distance + 4.5) / s.car_speed  # l'arrière l'a franchi
    for k in range(101):
        t = t_front + (t_rear - t_front) * k / 100
        if abs(s.pedestrian_y + s.pedestrian_speed * t) <= 1.2:
            return True
    return False


def stats(scenarios, seed=0):
    """Affiche ce que contient vraiment un ensemble de scénarios."""
    n = len(scenarios)
    in_odd = [s for s in scenarios if sim.in_odd(s)]
    conflicts = [s for s in scenarios if conflict(s)]
    hard = [s for s in in_odd if conflict(s)]
    collisions = sum(sim.run(s, seed).collision for s in scenarios)
    print(f"{n} scénarios")
    print(f"  dans l'ODD (exigences applicables)       : {len(in_odd):4d} ({100 * len(in_odd) // max(n, 1)} %)")
    print(f"  conflictuels (collision sans freinage)   : {len(conflicts):4d} ({100 * len(conflicts) // max(n, 1)} %)")
    print(f"  conflictuels ET dans l'ODD (intéressants): {len(hard):4d} ({100 * len(hard) // max(n, 1)} %)")
    print(f"  collisions du système actuel (graine {seed}) : {collisions:4d}")


PROMPT = """Propose {n} scénarios de test pour un simulateur de véhicule autonome qui approche d'un passage piéton.
Objectif : {goal}
Réponds uniquement par une liste JSON d'objets avec exactement ces champs (unités SI) :
{fields}
Bornes : {limits}
"""


def parse_json_list(text):
    """Extrait une liste de dictionnaires d'une réponse de LLM (gère les blocs ```json)."""
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("pas de liste JSON dans la réponse")
    data = json.loads(text[start : end + 1])
    return [item for item in data if isinstance(item, dict)]


def check_proposals(items):
    """Valide chaque scénario proposé ; renvoie (valides, [(proposition, raison du rejet)])."""
    valid, rejected = [], []
    for item in items:
        try:
            valid.append(sim.validate_scenario(sim.scenario_from_dict(item)))
        except (TypeError, ValueError) as error:
            rejected.append((item.get("name", "?"), str(error).replace("\n", " ")))
    return valid, rejected


def propose_scenarios_llm(goal, n=8):
    """Crochet TP4 : demande des scénarios au LLM puis les passe à validate_scenario()."""
    limits = ", ".join(f"{k} dans [{lo}, {hi}]" for k, (lo, hi, _) in sim.LIMITS.items())
    prompt = PROMPT.format(n=n, goal=goal, fields=", ".join(FIELDS + ["name"]), limits=limits)
    return check_proposals(parse_json_list(llm.ask(prompt)))


def load_scenarios(path):
    """Charge une liste de scénarios JSON (format de --save)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data["scenarios"] if isinstance(data, dict) else data
    return [sim.scenario_from_dict(item) for item in items]


def report(valid, rejected):
    print(f"{len(valid)} scénario(s) valide(s), {len(rejected)} rejeté(s) par validate_scenario() :")
    for name, why in rejected:
        print(f"  - {name} : {why}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # console non UTF-8 : pas de plantage sur ✓ ou →
    parser = argparse.ArgumentParser(description="Génération de scénarios TP4.")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--odd", action="store_true", help="seulement des scénarios dans l'ODD")
    parser.add_argument("--famille", choices=["pluie"], help="famille de scénarios bonus")
    parser.add_argument("--llm", metavar="OBJECTIF", help="demande des scénarios au LLM")
    parser.add_argument("--llm-fallback", action="store_true", help="utilise fallback/scenarios_llm.json")
    parser.add_argument("--save", help="enregistre les scénarios (JSON)")
    args = parser.parse_args(argv)

    if args.llm or args.llm_fallback:
        if args.llm_fallback:
            print("Sortie d'exemple (exemple pédagogique de sortie plausible, pas un résultat d'expérience)")
            valid, rejected = check_proposals(parse_json_list(LLM_FALLBACK.read_text(encoding="utf-8")))
        else:
            try:
                valid, rejected = propose_scenarios_llm(args.llm)
            except (llm.LLMError, ValueError) as error:
                print(f"Erreur LLM : {error}\nEssayez : python tools/random_scenarios.py --llm-fallback")
                return 2
        report(valid, rejected)
        scenarios = valid
    elif args.famille == "pluie":
        scenarios = famille_pluie(args.n, args.seed)
    else:
        scenarios = random_scenarios(args.n, args.seed, odd_only=args.odd)
    if scenarios:
        stats(scenarios, args.seed)
    if args.save:
        Path(args.save).write_text(
            json.dumps([s.to_dict() for s in scenarios], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Enregistré : {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

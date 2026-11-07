"""Voir une simulation du TP4 : écrit une page animée (vue de dessus, vitesse, distance, journal).

En ligne de commande, depuis la racine du dépôt :

    python tools/voir_simulation.py jour_nominal
    python tools/voir_simulation.py jour_nominal --set friction=0.5 initial_distance=35
    python tools/voir_simulation.py jour_nominal --panne "LidarNoise(0.2)" --graine 3
    python tools/voir_simulation.py jour_nominal --comparer friction=0.5    # deux voitures côte à côte
    python tools/voir_simulation.py jour_nominal --baseline                 # votre voiture et le robot simple

Depuis un test (make test TP=4) :

    from tools.voir_simulation import voir
    voir(result)                      # ou voir(result_1, result_2) pour comparer

La page est écrite dans tp/tp4_simulator/vues/ : ouvrez-la sur votre ordinateur (double-clic).
Elle signale les situations hors des limites des exigences (ODD, pannes de R4).
"""

import argparse
import dataclasses
import html
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP4 = ROOT / "tp" / "tp4_simulator"
OUTPUT_DIR = TP4 / "vues"
TEMPLATE = Path(__file__).with_name("vue_modele.html")
HEAD = ('<!doctype html>\n<html lang="fr">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
FAULTS = ("CameraDegraded", "SensorDelay", "LidarNoise", "GPSLost")
R4_LIMITS = {"SensorDelay": ("ms", 300, "ms"), "LidarNoise": ("sigma", 0.3, "m")}  # EXIGENCES.md, R4


# ---------------------------------------------------------------- données de la page (partagées avec la vue enseignant)

def steps_from_result(result, world, actions):
    """Une simulation réduite à ce que la page affiche (un pas = une liste de nombres)."""

    def step(t, x, v, y, observed, action, decel):
        if action not in actions:
            actions.append(action)
        return [round(t, 2), round(x, 3), round(v, 3), round(y, 3), int(observed), actions.index(action),
                round(decel, 2), round(world.distance_car_pedestrian(x, y), 3)]

    steps = [step(s["t"], s["car_x"], s["speed"], s["pedestrian_y"], s["observed"], s["action"], s["decel"])
             for s in result.trace]
    # La trace s'arrête avant le dernier pas (contact ou franchissement) : on l'ajoute pour l'animation.
    last = result.trace[-1]
    x, v, a, dt = last["car_x"], last["speed"], last["decel"], world.DT
    if a > 0 and v <= a * dt:
        x, v = x + v * v / (2 * a), 0.0
    else:
        x, v = x + (v - a * dt / 2) * dt, v - a * dt
    y = last["pedestrian_y"] + result.scenario.pedestrian_speed * dt
    steps.append(step(last["t"] + dt, x, v, y, last["observed"], last["action"], a))
    return steps


def run_data(result, world, actions, label, color):
    """Une voiture de la page : son résultat, sa situation et sa trace."""
    return {
        "label": label,
        "color": color,
        "params": result.scenario.to_dict(),
        "collision": result.collision,
        "collision_time": result.collision_time,
        "min_distance": None if result.min_distance == float("inf") else round(result.min_distance, 2),
        "first_detection": result.first_detection_time,
        "final_speed": round(result.final_speed, 2),
        "log": result.log,
        "steps": steps_from_result(result, world, actions),
    }


def geometry(world):
    return {"car_length": world.CAR_LENGTH, "car_half_width": world.CAR_HALF_WIDTH,
            "lane_half_width": world.LANE_HALF_WIDTH, "pedestrian_radius": world.PEDESTRIAN_RADIUS, "dt": world.DT}


def page_html(data, eyebrow, notice_html, footer):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = TEMPLATE.read_text(encoding="utf-8")
    page = (page.replace("__EYEBROW__", html.escape(eyebrow)).replace("__NOTICE__", notice_html)
                .replace("__FOOTER__", html.escape(footer)).replace("__DATA__", payload, 1))
    return HEAD + page


# ---------------------------------------------------------------- limites des exigences

def outside_limits(result, sim):
    """Pourquoi les exigences ne s'appliquent pas à cette simulation (liste vide : dans les limites)."""
    reasons = list(sim.odd_violations(result.scenario))
    if len(result.faults) > 1:
        reasons.append("plusieurs pannes à la fois : R4 n'en couvre qu'une")
    for f in result.faults:
        name = type(f).__name__
        if name in R4_LIMITS:
            attr, limit, unit = R4_LIMITS[name]
            if getattr(f, attr) > limit:
                reasons.append(f"{name}({getattr(f, attr):g}) dépasse la limite de R4 ({limit:g} {unit})")
    return reasons


def labels(results):
    """Nom de chaque voiture ; les suivantes indiquent ce qui change par rapport à la première."""
    first = results[0].scenario.to_dict()
    out = []
    for i, r in enumerate(results):
        name = "Votre voiture" if r.system == "pipeline" else "Robot de freinage simple (run_baseline)"
        details = []
        if i > 0:
            details += [f"{k} = {v:g}" for k, v in r.scenario.to_dict().items() if k != "name" and v != first[k]]
            if r.faults != results[0].faults:
                details.append("pannes : " + (", ".join(map(repr, r.faults)) or "aucune"))
            if r.seed != results[0].seed:
                details.append(f"graine {r.seed}")
        out.append(name + (" · " + ", ".join(details) if details else ""))
    return out


# ---------------------------------------------------------------- voir()

def voir(*results, nom=None, dossier=None):
    """Écrit la page animée d'une ou plusieurs simulations (résultats de run ou run_baseline).

    Renvoie le chemin de la page. Ne fonctionne qu'avec le simulateur de votre dépôt."""
    if not results:
        raise ValueError("voir() attend au moins un résultat, par exemple voir(run(scenario, seed=0))")
    sim = importlib.import_module("sim")
    if Path(sim.__file__).resolve().parent != TP4 / "sim":
        print("voir() : ce n'est pas le simulateur de votre dépôt, aucune page écrite.")
        return None
    world = importlib.import_module("sim.world")
    names = labels(results)
    actions = []
    runs = [run_data(r, world, actions, label, 1 + i % 3) for i, (r, label) in enumerate(zip(results, names))]
    notes = []
    for r, label in zip(results, names):
        reasons = outside_limits(r, sim)
        if reasons:
            notes.append(f"{label} : HORS DES LIMITES des exigences ({' ; '.join(reasons)}). Ici la voiture n'a "
                         "rien promis : un test qui y exige un bon comportement est une fausse alarme.")
    if not notes:
        notes.append("Dans les limites des exigences (ODD, au plus une panne dans les limites de R4) : "
                     "un test peut y exiger les règles d'EXIGENCES.md.")
    first = results[0]
    title = nom or first.scenario.name or "simulation"
    case = {"id": "votre_simulation", "group": "Votre simulation", "label": title,
            "text": "Simulation lancée par voir() ou tools/voir_simulation.py.", "params": first.scenario.to_dict(),
            "fault": ", ".join(map(repr, first.faults)) or None, "seed": first.seed, "note": notes, "runs": runs}
    data = {"geometry": geometry(world), "actions": actions, "start": "votre_simulation", "cases": [case]}
    path = Path(dossier or OUTPUT_DIR) / (re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_") + ".html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page_html(data, "TP4 · IA pour le GL, Tests", "",
                              "Simulation du simulateur de votre dépôt (tp/tp4_simulator/sim/)."), encoding="utf-8")
    for note in notes:
        if "HORS DES LIMITES" in note:
            print("Attention :", note)
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"Vue écrite : {shown}  (ouvrez ce fichier sur votre ordinateur, par un double-clic)")
    return path


# ---------------------------------------------------------------- ligne de commande

def parse_settings(pairs):
    """["luminosity=0.5", ...] -> {"luminosity": 0.5, ...}"""
    settings = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise ValueError(f"« {pair} » : écrivez reglage=valeur, par exemple luminosity=0.5")
        try:
            settings[key.strip()] = float(value)
        except ValueError:
            raise ValueError(f"« {pair} » : la valeur doit être un nombre") from None
    return settings


def parse_fault(text, sim):
    """« SensorDelay(200) » -> SensorDelay(200) ; « GPSLost » ou « GPSLost() » -> GPSLost()."""
    match = re.fullmatch(r"\s*(\w+)\s*(?:\(\s*([^)]*?)\s*\))?\s*", text)
    if not match or match.group(1) not in FAULTS:
        raise ValueError(f"panne inconnue « {text} » ; pannes possibles : {', '.join(FAULTS)}")
    cls = getattr(sim, match.group(1))
    try:
        return cls(float(match.group(2))) if match.group(2) else cls()
    except (TypeError, ValueError):
        raise ValueError(f"« {text} » : écrivez par exemple SensorDelay(200), LidarNoise(0.2), "
                         "CameraDegraded(0.5) ou GPSLost()") from None


def load_base(name, sim):
    if name == "defaut":
        return sim.Scenario(name="defaut")
    path = Path(name) if name.endswith(".json") else TP4 / "scenarios" / f"{name}.json"
    if not path.exists():
        known = ", ".join(sorted(p.stem for p in (TP4 / "scenarios").glob("*.json")))
        raise ValueError(f"scénario introuvable « {name} » ; scénarios fournis : {known}, ou « defaut »")
    return sim.load_scenario(path)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Voir une simulation du TP4 dans une page animée.")
    parser.add_argument("scenario", help="nom d'un scénario fourni (jour_nominal, ...), un fichier .json, ou « defaut »")
    parser.add_argument("--set", nargs="+", default=[], metavar="REGLAGE=VALEUR",
                        help="réglages modifiés, par exemple friction=0.5 initial_distance=35")
    parser.add_argument("--panne", action="append", default=[], metavar="PANNE",
                        help='panne active, par exemple "SensorDelay(200)" (peut être répété)')
    parser.add_argument("--graine", type=int, default=0, help="graine de la simulation (défaut : 0)")
    parser.add_argument("--comparer", nargs="+", default=[], metavar="REGLAGE=VALEUR",
                        help="ajoute une seconde voiture, dans la même situation avec ces réglages modifiés")
    parser.add_argument("--baseline", action="store_true", help="ajoute le robot de freinage simple (run_baseline)")
    parser.add_argument("--nom", help="nom de la page (défaut : nom du scénario)")
    parser.add_argument("--dossier", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if str(TP4) not in sys.path:
        sys.path.insert(0, str(TP4))
    sim = importlib.import_module("sim")
    try:
        scenario = load_base(args.scenario, sim).replace(**parse_settings(args.set))
        situations = [scenario] + ([scenario.replace(**parse_settings(args.comparer))] if args.comparer else [])
        faults = [parse_fault(text, sim) for text in args.panne]
        with sim.fault(*faults):
            results = [sim.run(s, args.graine) for s in situations]
            if args.baseline:
                results.append(sim.run_baseline(scenario, args.graine))
    except TypeError:
        fields = ", ".join(f.name for f in dataclasses.fields(sim.Scenario) if f.name != "name")
        print(f"Erreur : réglage inconnu. Réglages possibles : {fields}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 2
    for result in results:
        print(result, end="\n\n")
    voir(*results, nom=args.nom, dossier=args.dossier)
    return 0


if __name__ == "__main__":
    sys.exit(main())

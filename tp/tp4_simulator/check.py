"""Évalue votre suite de tests TP4 contre des versions cachées du simulateur.

    make check
    python tp/tp4_simulator/check.py --equipe "binome-07"     # pour le classement

Vos tests (tp/tp4_simulator/test_*.py) sont exécutés :
  - sur la version CORRECTE du simulateur : ils doivent tous passer (sinon : fausse alarme) ;
  - sur 5 variantes DÉFECTUEUSES (A à E) : une variante est détectée si au moins un test échoue.
Score = nombre de variantes détectées, compté seulement s'il n'y a aucune fausse alarme.
Une suite qui échoue partout ne marque donc aucun point.

Les variantes sont volontairement illisibles : ne cherchez pas à les décoder.
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BUNDLE = HERE / ".check_data" / "variants.dat"
KEY = b"ia4se-tp4-ne-pas-lire"
TIMEOUT = 600  # s par exécution de la suite
CONFTEST = (
    "from hypothesis import settings\n"
    "settings.register_profile('check', derandomize=True, database=None, deadline=None)\n"
    "settings.load_profile('check')\n"
)


def load_variants():
    lines = [line for line in BUNDLE.read_text(encoding="utf-8").splitlines() if not line.startswith("#")]
    scrambled = base64.b64decode("".join(lines))
    raw = bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(scrambled))
    return json.loads(zlib.decompress(raw))["variants"]


def prepare(workdir, files):
    """Copie vos tests dans un dossier temporaire, avec la variante à la place de sim/."""
    tp4 = workdir / "tp" / "tp4_simulator"
    junk = shutil.ignore_patterns("sim", ".check_data", "check.py", "__pycache__", ".pytest_cache", ".hypothesis", "vues")
    shutil.copytree(HERE, tp4, ignore=junk)
    (tp4 / "sim").mkdir()
    for name, text in files.items():
        (tp4 / "sim" / name).write_text(text, encoding="utf-8")
    shutil.copytree(REPO / "tools", workdir / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    (workdir / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (workdir / "conftest.py").write_text(CONFTEST, encoding="utf-8")
    return tp4


def targets_in(tp4, tests):
    """Chemins des tests dans la copie ; un fichier hors du TP4 y est copié."""
    if not tests:
        return [str(tp4)]
    targets = []
    for test in tests:
        path = Path(test).resolve()
        if path.is_relative_to(HERE):
            targets.append(str(tp4 / path.relative_to(HERE)))
        else:
            shutil.copyfile(path, tp4 / path.name)
            targets.append(str(tp4 / path.name))
    return targets


def run_suite(name, files, tests):
    with tempfile.TemporaryDirectory(prefix=f"check_{name}_") as tmp:
        workdir = Path(tmp)
        tp4 = prepare(workdir, files)
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(tp4), str(workdir)]))
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
        targets = targets_in(tp4, tests)
        command = [sys.executable, "-m", "pytest", "-q", "-rfE", "--tb=no", "-p", "no:cacheprovider"]
        command += ["--import-mode=importlib", "-c", str(workdir / "pytest.ini"), *targets]
        try:
            proc = subprocess.run(
                command, cwd=workdir, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return {"status": "erreur", "detail": f"plus de {TIMEOUT} s", "failed": []}
    output = proc.stdout + proc.stderr
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", output, flags=re.M)))
    failed = [f.split("::", 1)[-1] if "::" in f else Path(f).name for f in failed]
    status = {0: "vert", 1: "rouge", 5: "vide"}.get(proc.returncode, "erreur")
    detail = output.strip().splitlines()[-1] if output.strip() else ""
    return {"status": status, "detail": detail, "failed": failed}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # console non UTF-8 : pas de plantage sur ✓ ou →
    parser = argparse.ArgumentParser(description="Score de votre suite de tests TP4.")
    parser.add_argument("--tests", nargs="*", help="fichiers de test (défaut : tous les test_*.py du TP4)")
    parser.add_argument("--equipe", help="nom du binôme : écrit score.json pour le classement")
    args = parser.parse_args()

    variants = load_variants()
    names = ["reference"] + sorted(n for n in variants if n != "reference")
    print("Vérification de votre suite de tests TP4 (cela prend une minute)...\n")
    with ThreadPoolExecutor(max_workers=min(len(names), os.cpu_count() or 2)) as pool:
        futures = {n: pool.submit(run_suite, n, variants[n], args.tests) for n in names}
        results = {n: f.result() for n, f in futures.items()}

    ref = results["reference"]
    if ref["status"] == "vide":
        print("Aucun test trouvé : écrivez des tests dans tp/tp4_simulator/test_*.py. Score : 0")
        return 1
    false_alarm = ref["status"] != "vert"
    if false_alarm:
        print("Version CORRECTE      : ✗ ÉCHEC — fausse alarme : vos tests échouent sur un simulateur sans défaut.")
        for test in ref["failed"] or [ref["detail"]]:
            print(f"    - {test}")
        print("    Corrigez ces tests (oracle trop strict ? scénario hors ODD ? voir EXIGENCES.md).")
    else:
        print("Version CORRECTE      : ✓ tous vos tests passent (aucune fausse alarme)")

    detected = []
    for n in names[1:]:
        r = results[n]
        if r["status"] == "rouge":
            detected.append(n)
            shown = ", ".join(r["failed"][:4]) + (" ..." if len(r["failed"]) > 4 else "")
            print(f"Variante défectueuse {n} : ✓ détectée par {shown}")
        elif r["status"] == "erreur":
            print(f"Variante défectueuse {n} : ? erreur d'exécution ({r['detail']})")
        else:
            print(f"Variante défectueuse {n} : ✗ non détectée (tous vos tests passent)")

    total = len(names) - 1
    score = 0 if false_alarm else len(detected)
    print(f"\nScore : {score} / {total}")
    if false_alarm:
        print(
            f"(Vos tests échouent sur {len(detected)} variante(s), mais aussi sur la version correcte : "
            "une suite qui échoue partout ne détecte rien. Score compté à 0.)"
        )
    if args.equipe:
        data = {"equipe": args.equipe, "score": score, "sur": total, "detectees": detected, "fausse_alarme": false_alarm}
        (HERE / "score.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Classement : {args.equipe};{score}/{total} (écrit dans tp/tp4_simulator/score.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

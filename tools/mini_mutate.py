"""Test de mutation minimal et lisible (outil principal du TP3).

    python tools/mini_mutate.py tp/tp1_generation/remise.py tp/tp2_critique/test_reecrits.py tp/tp3_mutation
    python tools/mini_mutate.py ... --bonus     # ajoute les mutants de tp/tp3_mutation/mutants_bonus.txt

Principe : on fabrique des copies légèrement modifiées du module (des « mutants »),
puis on relance la suite de tests sur chacune. Un mutant est TUÉ si au moins un test
échoue ; il SURVIT si tous les tests passent : la suite ne voit pas la différence.
Opérateurs : comparaisons (>= devient > ou <, etc.), constantes numériques
(entier ± 1, réel ± 0.05) et opérateurs booléens (and <-> or).
"""

import argparse
import ast
import copy
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BONUS = REPO / "tp" / "tp3_mutation" / "mutants_bonus.txt"
COMPARE_SWAPS = {
    ast.GtE: (ast.Gt, ast.Lt),
    ast.Gt: (ast.GtE, ast.LtE),
    ast.LtE: (ast.Lt, ast.Gt),
    ast.Lt: (ast.LtE, ast.GtE),
    ast.Eq: (ast.NotEq,),
    ast.NotEq: (ast.Eq,),
}
# Les trois mutants des diapositives (remise.py) : (ligne, avant, après).
COURSE = {
    (2, "fidelite >= 10", "fidelite > 10"): "M1",
    (5, "0.9", "0.85"): "M2",
    (4, "5", "6"): "M3",
}


def generate(source):
    """Mutants automatiques : liste de (ligne, avant, après, source mutée)."""
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    changes = []
    for index, node in enumerate(nodes):
        if isinstance(node, ast.Compare):
            for pos, op in enumerate(node.ops):
                changes += [(index, "op", (pos, new)) for new in COMPARE_SWAPS.get(type(op), ())]
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float):
            step = 1 if isinstance(node.value, int) else 0.05
            changes += [(index, "value", round(node.value + d, 10)) for d in (step, -step)]
        elif isinstance(node, ast.BoolOp):
            changes.append((index, "bool", ast.Or if isinstance(node.op, ast.And) else ast.And))
    mutants = []
    for index, kind, change in changes:
        mutated = copy.deepcopy(tree)
        node = list(ast.walk(mutated))[index]
        before = ast.unparse(node)
        if kind == "op":
            node.ops[change[0]] = change[1]()
        elif kind == "value":
            node.value = change
        else:
            node.op = change()
        mutants.append((node.lineno, before, ast.unparse(node), ast.unparse(mutated) + "\n"))
    return mutants


def bonus(source):
    """Mutants écrits à la main dans mutants_bonus.txt : « ligne | avant | après | question »."""
    lines = source.splitlines(keepends=True)
    mutants = []
    for row in BONUS.read_text(encoding="utf-8").splitlines():
        if not row.strip() or row.startswith("#"):
            continue
        number, before, after, _question = (part.strip() for part in row.split("|"))
        line = lines[int(number) - 1]
        if line.count(before) != 1:
            raise SystemExit(f"mutants_bonus.txt : « {before} » introuvable ligne {number}")
        mutated = lines[: int(number) - 1] + [line.replace(before, after)] + lines[int(number) :]
        mutants.append((int(number), before, after, "".join(mutated)))
    return mutants


def run_tests(module_name, source, tests, deselect=(), stop_first=True):
    """Lance pytest avec `source` à la place du module ; renvoie (code retour, sortie)."""
    with tempfile.TemporaryDirectory(prefix="mutant_") as tmp:
        Path(tmp, module_name).write_text(source, encoding="utf-8")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        env["PYTHONPATH"] = os.pathsep.join(p for p in [tmp, os.environ.get("PYTHONPATH", "")] if p)
        command = [sys.executable, "-m", "pytest", "-q", "-rfE", "--tb=no", "-p", "no:cacheprovider"]
        command += (["-x"] if stop_first else []) + [*tests] + [f"--deselect={d}" for d in deselect]
        try:
            proc = subprocess.run(
                command, cwd=REPO, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=120
            )
        except subprocess.TimeoutExpired:
            return 1, "délai dépassé (boucle infinie ?)"
        return proc.returncode, proc.stdout + proc.stderr


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # console non UTF-8 : pas de plantage sur ✓ ou →
    parser = argparse.ArgumentParser(description="Test de mutation minimal.")
    parser.add_argument("module", help="fichier à muter (ex. tp/tp1_generation/remise.py)")
    parser.add_argument("tests", nargs="+", help="fichiers ou dossiers de tests")
    parser.add_argument("--bonus", action="store_true", help="ajoute les mutants de mutants_bonus.txt")
    args = parser.parse_args(argv)

    module = Path(args.module)
    source = module.read_text(encoding="utf-8")
    print(f"Mutation de {module.as_posix()} — tests : {' '.join(args.tests)}\n")

    code, output = run_tests(module.name, source, args.tests, stop_first=False)
    failing = re.findall(r"^(?:FAILED|ERROR) (\S+)", output, flags=re.M)
    if code not in (0, 1) or (code == 1 and not failing):
        print("Impossible d'exécuter la suite sur le code d'origine :\n" + output[-1500:])
        return 2
    if failing:
        print(f"{len(failing)} test(s) échouent déjà sur le code d'origine : ils sont ignorés ici.")
        print("Ils révèlent peut-être un écart avec la spécification : notez-le dans RENDU.md.")
        for test in failing:
            print(f"   - {test}")
        print()
        if run_tests(module.name, source, args.tests, failing)[0] == 5:
            print("Aucun test vert sur le code d'origine : rien à évaluer.")
            return 2

    mutants = generate(source) + (bonus(source) if args.bonus else [])
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
        codes = list(pool.map(lambda m: run_tests(module.name, m[3], args.tests, failing)[0], mutants))

    lines = source.splitlines()
    survivors = []
    print(" n°  ligne  code d'origine                 mutation                              résultat")
    for n, ((line, before, after, _), code) in enumerate(zip(mutants, codes), start=1):
        killed = code != 0
        tag = COURSE.get((line, before, after)) if module.name == "remise.py" else None
        note = f"   <- mutant du cours {tag}" if tag else ""
        status = "tué" if killed else "SURVIT"
        change = f"{before} -> {after}"
        print(f"{n:3d}  L{line:<4d}  {lines[line - 1].strip():30s} {change:37s} {status}{note}")
        if not killed:
            survivors.append(f"#{n} L{line} : {change}{note}")

    killed = len(mutants) - len(survivors)
    print(f"\nRésumé : {len(mutants)} mutants, {killed} tués, {len(survivors)} survivants", end="")
    print(f" — score de mutation {100 * killed // len(mutants)} %")
    if survivors:
        print("Survivants à analyser (ajoutez un test qui les tue, ou justifiez qu'ils sont équivalents) :")
        for s in survivors:
            print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

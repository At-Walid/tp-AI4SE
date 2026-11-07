"""Génère des tests pytest avec un LLM (TP1).

Depuis la racine du dépôt :
    python tools/gen_tests.py remise.py --spec SPEC.md
    python tools/gen_tests.py normalize_age.py --spec SPEC.md
    python tools/gen_tests.py remise.py --spec SPEC.md --fallback      # sans LLM : sortie d'exemple
    python tools/gen_tests.py remise.py --show-prompt                  # affiche le prompt envoyé

Le fichier produit est écrit dans generated_tests/ à côté du code testé :
    tp/tp1_generation/generated_tests/test_remise.py
"""

import argparse
import ast
import re
import shutil
import sys
from pathlib import Path

try:
    from tools import llm
except ImportError:  # lancé comme script : tools/ est déjà dans le chemin
    import llm

REPO = Path(__file__).resolve().parents[1]
FALLBACK = REPO / "fallback"

PROMPT = """Tu es un développeur Python. Écris des tests unitaires pytest pour le module `{module}` ci-dessous.
{spec_block}
Contraintes :
- importe ce qui est testé avec `from {module} import ...` ;
- réponds uniquement avec le code Python du fichier de test.

Code du module `{module}.py` :
```python
{source}
```
"""

SPEC_BLOCK = """
Spécification à respecter :
<<<
{spec}
>>>
"""


def strip_fences(text):
    """Extrait le code des blocs ``` ... ``` d'une réponse de LLM (ou renvoie le texte tel quel)."""
    blocks = re.findall(r"```[^\n`]*\n(.*?)(?:```|\Z)", text, flags=re.S)
    code = "\n\n".join(block.strip("\n") for block in blocks) if blocks else text
    return code.strip() + "\n"


def ensure_import(code, module):
    """Ajoute `from module import *` si le code généré n'importe pas le module testé."""
    pattern = rf"^\s*(from\s+{re.escape(module)}\s+import|import\s+{re.escape(module)}\b)"
    if re.search(pattern, code, flags=re.M):
        return code
    note = "  # ajouté par gen_tests.py : la réponse du LLM n'importait pas le module"
    return f"from {module} import *{note}\n\n{code}"


def build_prompt(module, source, spec=None, template=PROMPT):
    spec_block = SPEC_BLOCK.format(spec=spec.strip()) if spec else ""
    return template.format(module=module, source=source.rstrip(), spec_block=spec_block)


def find_file(name, near=None):
    """Trouve un fichier : chemin donné, sinon à côté de `near`, sinon dans un dossier tp/*/."""
    path = Path(name)
    if path.exists():
        return path.resolve()
    if near is not None and (near / name).exists():
        return (near / name).resolve()
    matches = sorted(REPO.glob(f"tp/*/{name}"))
    if len(matches) == 1:
        print(f"→ fichier trouvé : {matches[0].relative_to(REPO).as_posix()}")
        return matches[0]
    raise SystemExit(f"Fichier introuvable : {name} (donnez son chemin, par ex. tp/tp1_generation/{name})")


def header(source_path, spec_path, origin):
    rel = source_path.relative_to(REPO).as_posix() if source_path.is_relative_to(REPO) else source_path
    spec = spec_path.name if spec_path else "aucune"
    return (
        "# Tests générés automatiquement par tools/gen_tests.py\n"
        f"# Code testé : {rel} — spécification fournie : {spec}\n"
        f"# Origine : {origin}\n"
        "# Personne n'a relu ces tests : à critiquer au TP2.\n\n"
    )


def explain_failure(error, args):
    print(f"Erreur : le LLM est injoignable — {llm.describe()}\n  {error}\n", file=sys.stderr)
    print("Que faire ?", file=sys.stderr)
    print("  1. Démarrez le serveur local : lab-start-ollama   (puis relancez la commande)", file=sys.stderr)
    print("  2. Modèle absent ? make pull-model", file=sys.stderr)
    spec = f" --spec {args.spec}" if args.spec else ""
    print("  3. Sinon, utilisez la sortie d'exemple du dossier fallback/ :", file=sys.stderr)
    print(f"     python tools/gen_tests.py {args.file}{spec} --fallback", file=sys.stderr)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # console non UTF-8 : pas de plantage sur ✓ ou →
    parser = argparse.ArgumentParser(description="Génère des tests pytest avec un LLM.")
    parser.add_argument("file", help="fichier Python à tester (ex. remise.py)")
    parser.add_argument("--spec", help="spécification à joindre au prompt (ex. SPEC.md)")
    parser.add_argument("--out", help="fichier de sortie (défaut : generated_tests/test_<nom>.py)")
    parser.add_argument("--prompt-file", help="modèle de prompt personnalisé ({module}, {source}, {spec_block})")
    parser.add_argument("--show-prompt", action="store_true", help="affiche le prompt sans appeler le LLM")
    parser.add_argument("--fallback", action="store_true", help="copie la sortie d'exemple de fallback/")
    args = parser.parse_args(argv)

    source_path = find_file(args.file)
    spec_path = find_file(args.spec, near=source_path.parent) if args.spec else None
    module = source_path.stem
    out = Path(args.out) if args.out else source_path.parent / "generated_tests" / f"test_{module}.py"

    if args.fallback:
        example = FALLBACK / f"test_{module}.py"
        if not example.exists():
            raise SystemExit(f"Pas de sortie d'exemple pour {module} dans fallback/.")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example, out)
        print(f"Sortie d'exemple copiée : {example.relative_to(REPO).as_posix()} -> {out}")
        print("(exemple pédagogique de sortie plausible, pas un résultat d'expérience)")
        return 0

    template = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else PROMPT
    spec = spec_path.read_text(encoding="utf-8") if spec_path else None
    prompt = build_prompt(module, source_path.read_text(encoding="utf-8"), spec, template)
    if args.show_prompt:
        print(prompt)
        return 0

    print(f"Génération des tests de {module}.py avec {llm.describe()}... (jusqu'à 1 à 2 minutes sur CPU)")
    try:
        answer = llm.ask(prompt)
    except llm.LLMError as error:
        explain_failure(error, args)
        return 2

    code = ensure_import(strip_fences(answer), module)
    try:
        ast.parse(code)
    except SyntaxError as error:
        print(f"Attention : le code généré n'est pas du Python valide ({error}). Notez-le, c'est un résultat !")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        shutil.copyfile(out, out.with_name(out.name + ".bak"))
        print(f"(version précédente sauvegardée dans {out.name}.bak)")
    out.write_text(header(source_path, spec_path, llm.describe()) + code, encoding="utf-8")
    n_tests = len(re.findall(r"^\s*def test_", code, flags=re.M))
    print(f"Écrit : {out} ({n_tests} fonctions de test). Lancez : make test TP=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Configuration pytest commune à tout le dépôt."""

import sys
from pathlib import Path

from hypothesis import settings

ROOT = Path(__file__).resolve().parent

# Les modules testés (remise, sim, model...) sont importables depuis n'importe quel test.
# Ajoutés en FIN de chemin : PYTHONPATH reste prioritaire (mutants du TP3, variantes du TP4).
for folder in ("tp/tp1_generation", "tp/tp4_simulator", "tp/tp5_metamorphique", "."):
    path = str(ROOT / folder)
    if path not in sys.path:
        sys.path.append(path)

# Hypothesis déterministe : mêmes exemples à chaque exécution, pas de base d'exemples sur disque.
settings.register_profile("tp", derandomize=True, database=None, deadline=None)
settings.load_profile("tp")

# Sorties d'exemple (quand le LLM ne répond pas)

Chaque fichier est un **exemple pédagogique de sortie plausible d'un LLM, pas un résultat
d'expérience** : il a été écrit pour ressembler à ce qu'un générateur produit souvent
(tests qui passent, mais pas forcément les bons).

| Fichier | Utilisation |
|---------|-------------|
| `test_remise.py` | `python tools/gen_tests.py remise.py --spec SPEC.md --fallback` |
| `test_normalize_age.py` | `python tools/gen_tests.py normalize_age.py --spec SPEC.md --fallback` |
| `test_scenarios_llm.py` | TP4 : `python tp/tp4_simulator/check.py --tests fallback/test_scenarios_llm.py` |
| `scenarios_llm.json` | TP4 : `python tools/random_scenarios.py --llm-fallback` |

Ces fichiers ne sont pas exécutés par `make test` : copiez-les ou passez-les en argument.

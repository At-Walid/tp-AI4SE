# TP « IA pour le GL, Tests » — commandes du TP (make help).
#
# Sur votre machine : make build, puis make shell (ou ouvrez le dépôt dans Codespaces).
# Dans le conteneur  : make test, make cov, make mutate, make check...
# Hors conteneur, les cibles du TP s'exécutent dans Docker ; LOCAL=1 utilise votre Python.

IMAGE        ?= ia4se-tests
OLLAMA_MODEL ?= qwen2.5-coder:1.5b
PYTHON       ?= python
TP           ?=
TESTS        ?= tp/tp2_critique/test_reecrits.py tp/tp3_mutation

TP_DIR    := $(if $(TP),$(firstword $(wildcard tp/tp$(TP)_*)),tp)
COV_SRC   := $(if $(filter 4,$(TP)),tp/tp4_simulator/sim,tp/tp1_generation)
COV_TESTS := $(if $(TP),$(TP_DIR),tp/tp1_generation)
DOCKER_RUN = docker run --rm $(shell [ -t 0 ] && echo -it) -v "$(CURDIR)":/workspace \
             -v ia4se-ollama:/opt/ollama/models -w /workspace $(IMAGE)

ifneq ($(LAB_CONTAINER)$(LOCAL),)
  IN :=
else
  IN := $(DOCKER_RUN)
endif

.PHONY: help build build-instructor shell test cov mutate mutmut check pull-model selftest clean

help:
	@echo "make build              construit l'image Docker du TP"
	@echo "make shell              ouvre un terminal dans le conteneur (dépôt monté dans /workspace)"
	@echo "make test [TP=1..5]     lance les tests (tous les TP, ou un seul)"
	@echo "make cov [TP=4]         couverture lignes + branches (TP1 par défaut, TP=4 : simulateur)"
	@echo "make mutate [EXTRA=1]   test de mutation de remise.py (TP3)"
	@echo "make mutmut             même chose avec l'outil mutmut (suite entièrement verte exigée)"
	@echo "make check [EQUIPE=nom] score de vos tests TP4 contre les variantes cachées"
	@echo "make pull-model         télécharge le modèle LLM local ($(OLLAMA_MODEL))"
	@echo "make selftest           tests de l'outillage du dépôt"
	@echo "make clean              supprime les caches (pas vos tests)"

build:
	docker build -t $(IMAGE) .

build-instructor:
	docker build --build-arg INSTRUCTOR=1 --build-context instructor=instructor -t $(IMAGE):instructor .

shell:
	docker run --rm -it -v "$(CURDIR)":/workspace -v ia4se-ollama:/opt/ollama/models -w /workspace $(IMAGE) bash

test:
	$(IN) $(PYTHON) -m pytest $(TP_DIR)

cov:
	$(IN) $(PYTHON) -m pytest -q --cov=$(COV_SRC) --cov-branch --cov-report=term-missing $(COV_TESTS)

mutate:
	$(IN) $(PYTHON) tools/mini_mutate.py tp/tp1_generation/remise.py $(TESTS) $(if $(EXTRA),--bonus)

mutmut:
	$(IN) bash -c "mutmut run; mutmut results"

check:
	$(IN) $(PYTHON) tp/tp4_simulator/check.py $(if $(EQUIPE),--equipe "$(EQUIPE)")

pull-model:
	$(IN) bash -c "lab-start-ollama --wait && ollama pull $(OLLAMA_MODEL)"

selftest:
	$(IN) $(PYTHON) -m pytest -q tests

clean:
	rm -rf .pytest_cache .coverage htmlcov .mutmut-cache mutants .hypothesis
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

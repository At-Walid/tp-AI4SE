# syntax=docker/dockerfile:1
# Image du TP « IA pour le GL, Tests » : Python 3.11, outils de test, Ollama (CPU) et un petit
# modèle de code. Fonctionne sur amd64 et arm64 (Apple Silicon). Aucun GPU nécessaire.
#
#   make build                                   (= docker build -t ia4se-tests .)
#   docker build --build-arg PULL_MODEL=0 ...    image plus légère, modèle téléchargé plus tard (make pull-model)
#   make build-instructor                        ajoute instructor/ (--build-arg INSTRUCTOR=1)
#
# Le dossier instructor/ est exclu du contexte par .dockerignore : il n'entre dans l'image que
# via le contexte nommé « instructor » (make build-instructor).

ARG INSTRUCTOR=0

FROM scratch AS instructor-0
COPY docker/no-instructor /NO_INSTRUCTOR
FROM scratch AS instructor-1
COPY --from=instructor . /
FROM instructor-${INSTRUCTOR} AS instructor-files

FROM python:3.11.16-slim-trixie AS lab
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV LANG=C.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LAB_CONTAINER=1 \
    OLLAMA_MODELS=/opt/ollama/models \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_KEEP_ALIVE=30m \
    LAB_LLM_MODEL=qwen2.5-coder:1.5b \
    TP5_MODEL_PATH=/opt/lab/digits_model.pkl

# Outils système + Ollama, version CPU seulement (les bibliothèques GPU de l'archive ne sont pas extraites).
ARG OLLAMA_VERSION=0.35.1
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl make git zstd libgomp1 libstdc++6 \
 && arch="$(dpkg --print-architecture)" \
 && curl -fsSL "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${arch}.tar.zst" \
    | zstd -d | tar -x -C /usr/local \
        --exclude='lib/ollama/*/*' --exclude='lib/ollama/*cuda*' --exclude='lib/ollama/*rocm*' \
        --exclude='lib/ollama/*mlx*' --exclude='lib/ollama/*vulkan*' \
 && apt-get purge -y zstd && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && ollama --help >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY docker/lab-start-ollama docker/lab-entrypoint /usr/local/bin/
RUN chmod +x /usr/local/bin/lab-start-ollama /usr/local/bin/lab-entrypoint \
 && useradd --create-home --uid 1000 --shell /bin/bash etudiant \
 && mkdir -p /opt/ollama/models /opt/lab /workspace \
 && chown -R etudiant:etudiant /opt/ollama /opt/lab /workspace
USER etudiant

# Petit modèle de code pour le TP1, téléchargé pendant la construction (hors ligne ensuite).
ARG PULL_MODEL=1
RUN if [ "$PULL_MODEL" = "1" ]; then \
      ollama serve >/tmp/ollama-build.log 2>&1 & pid=$!; \
      for i in $(seq 1 60); do ollama list >/dev/null 2>&1 && break; sleep 1; done; \
      ollama pull "$LAB_LLM_MODEL" && kill "$pid"; \
    fi

WORKDIR /workspace
COPY --chown=etudiant:etudiant . /workspace
COPY --from=instructor-files --chown=etudiant:etudiant / /workspace/instructor/
# Image étudiante : on retire le dossier qui ne contient que le marqueur NO_INSTRUCTOR.
# Puis : entraînement du modèle du TP5 et vérification que make test passe dès la construction.
RUN if [ -f instructor/NO_INSTRUCTOR ]; then rm -rf instructor; fi \
 && python tp/tp5_metamorphique/model.py --train --out "$TP5_MODEL_PATH" \
 && python -m pytest -q -p no:cacheprovider tp tests

ENTRYPOINT ["/usr/local/bin/lab-entrypoint"]
CMD ["bash"]

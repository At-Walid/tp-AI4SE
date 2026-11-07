"""Client LLM minimal : une seule fonction, ask(prompt) -> str.

Fournisseur choisi automatiquement :
  - ANTHROPIC_API_KEY définie  -> API Anthropic (modèle à indiquer : ANTHROPIC_MODEL ; ANTHROPIC_BASE_URL) ;
  - sinon OPENAI_API_KEY définie -> API OpenAI ou compatible (OPENAI_MODEL, OPENAI_BASE_URL) ;
  - sinon                        -> Ollama local (modèle : LAB_LLM_MODEL, serveur : OLLAMA_HOST).
LAB_LLM_PROVIDER=ollama|anthropic|openai force un fournisseur.
Aucune clé n'est écrite dans le code : elles viennent uniquement des variables d'environnement.
"""

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:1.5b"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
TIMEOUT = float(os.environ.get("LAB_LLM_TIMEOUT", "600"))  # s : un petit modèle sur CPU est lent


class LLMError(RuntimeError):
    """Le LLM est injoignable ou a renvoyé une erreur."""


def provider():
    forced = os.environ.get("LAB_LLM_PROVIDER")
    if forced:
        return forced
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "ollama"


def ollama_url():
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    return host if host.startswith("http") else f"http://{host}"


def describe():
    """Fournisseur et modèle utilisés, pour les messages."""
    p = provider()
    if p == "anthropic":
        return f"anthropic ({os.environ.get('ANTHROPIC_MODEL', 'modèle non défini')})"
    if p == "openai":
        return f"openai ({os.environ.get('OPENAI_MODEL', DEFAULT_OPENAI_MODEL)})"
    return f"ollama ({os.environ.get('LAB_LLM_MODEL', DEFAULT_OLLAMA_MODEL)}, {ollama_url()})"


def _post(url, payload, headers):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"{url} a répondu {e.code} : {body}") from e
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise LLMError(f"impossible de joindre {url} : {e}") from e


def _ask_ollama(prompt):
    model = os.environ.get("LAB_LLM_MODEL", DEFAULT_OLLAMA_MODEL)
    options = {"temperature": 0, "seed": 42, "num_predict": 1500}  # réponses reproductibles
    payload = {"model": model, "prompt": prompt, "stream": False, "options": options}
    attempts = 10 if os.environ.get("LAB_CONTAINER") else 1  # le serveur démarre avec le conteneur
    for attempt in range(attempts):
        try:
            return _post(f"{ollama_url()}/api/generate", payload, {}).get("response", "")
        except LLMError as error:
            if "impossible de joindre" not in str(error) or attempt == attempts - 1:
                raise
            time.sleep(1)


def _ask_anthropic(prompt):
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model:
        raise LLMError("définissez ANTHROPIC_MODEL : le nom du modèle Anthropic à utiliser")
    headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
    payload = {"model": model, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    data = _post(f"{base}/v1/messages", payload, headers)
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def _ask_openai(prompt):
    model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
    data = _post(f"{base}/chat/completions", payload, headers)
    return data["choices"][0]["message"]["content"]


def ask(prompt):
    """Envoie prompt au LLM et renvoie sa réponse (texte brut). Lève LLMError en cas d'échec."""
    p = provider()
    if p == "anthropic":
        return _ask_anthropic(prompt)
    if p == "openai":
        return _ask_openai(prompt)
    if p == "ollama":
        return _ask_ollama(prompt)
    raise LLMError(f"fournisseur inconnu : {p} (attendu : ollama, anthropic ou openai)")

"""gen_tests.py de bout en bout avec un faux serveur LLM local (Ollama, Anthropic, OpenAI).

Vérifie le format des requêtes envoyées et le traitement des réponses, sans réseau ni modèle.
"""

import ast
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tools import gen_tests

ANSWER = "Voici les tests :\n```python\nfrom remise import remise\n\ndef test_a():\n    assert remise(100, 0) == 100\n```"


@pytest.fixture
def fake_server():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            headers = {k.lower(): v for k, v in self.headers.items()}  # noms insensibles à la casse
            requests.append({"path": self.path, "headers": headers, "body": body})
            if self.path == "/api/generate":
                reply = {"response": ANSWER}
            elif self.path == "/v1/messages":
                reply = {"content": [{"type": "text", "text": ANSWER}]}
            else:
                reply = {"choices": [{"message": {"content": ANSWER}}]}
            data = json.dumps(reply).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"127.0.0.1:{server.server_address[1]}", requests
    server.shutdown()


@pytest.mark.parametrize("provider", ["ollama", "anthropic", "openai"])
def test_generation_complete(provider, fake_server, tmp_path, monkeypatch):
    address, requests = fake_server
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LAB_CONTAINER"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LAB_LLM_PROVIDER", provider)
    monkeypatch.setenv("OLLAMA_HOST", address)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
    monkeypatch.setenv("ANTHROPIC_MODEL", "modele-de-test")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://{address}")
    monkeypatch.setenv("OPENAI_API_KEY", "cle-de-test")
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://{address}/v1")

    out = tmp_path / "test_remise.py"
    assert gen_tests.main(["remise.py", "--spec", "SPEC.md", "--out", str(out)]) == 0

    code = out.read_text(encoding="utf-8")
    ast.parse(code)
    assert "def test_a" in code and "```" not in code and "Voici" not in code
    (request,) = requests
    body = request["body"]
    if provider == "ollama":
        assert request["path"] == "/api/generate"
        assert body["model"] == "qwen2.5-coder:1.5b" and body["stream"] is False
        assert body["options"]["temperature"] == 0
        prompt = body["prompt"]
    elif provider == "anthropic":
        assert request["path"] == "/v1/messages"
        assert request["headers"]["x-api-key"] == "cle-de-test" and "anthropic-version" in request["headers"]
        assert body["model"] == "modele-de-test"
        prompt = body["messages"][0]["content"]
    else:
        assert request["path"] == "/v1/chat/completions"
        assert request["headers"]["authorization"] == "Bearer cle-de-test"
        prompt = body["messages"][0]["content"]
    assert "def remise" in prompt and "ValueError" in prompt  # code et SPEC dans le prompt


def test_anthropic_sans_modele(monkeypatch):
    from tools import llm

    monkeypatch.setenv("LAB_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    with pytest.raises(llm.LLMError, match="ANTHROPIC_MODEL"):
        llm.ask("bonjour")

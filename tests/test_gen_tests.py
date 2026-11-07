"""Tests de l'outillage : tools/gen_tests.py et tools/llm.py."""

import ast

import pytest

from tools import gen_tests, llm


@pytest.mark.parametrize(
    "answer",
    [
        "```python\ndef test_a():\n    assert 1\n```",
        "Voici les tests :\n```python\ndef test_a():\n    assert 1\n```\nBonne journée !",
        "```py\ndef test_a():\n    assert 1\n```",
        "```\ndef test_a():\n    assert 1\n```",
        "```python\ndef test_a():\n    assert 1\n",  # bloc jamais refermé (réponse tronquée)
        "def test_a():\n    assert 1\n",  # pas de bloc du tout
    ],
)
def test_strip_fences_extrait_le_code(answer):
    code = gen_tests.strip_fences(answer)
    assert code == "def test_a():\n    assert 1\n"


def test_strip_fences_concatene_plusieurs_blocs():
    answer = "A :\n```python\nimport x\n```\nB :\n```python\ndef test_b():\n    pass\n```"
    code = gen_tests.strip_fences(answer)
    assert "import x" in code and "def test_b" in code
    ast.parse(code)


def test_ensure_import_ajoute_l_import_manquant():
    code = gen_tests.ensure_import("def test_a():\n    assert remise(1, 0) == 1\n", "remise")
    assert code.startswith("from remise import *")


def test_ensure_import_ne_duplique_pas():
    code = "from remise import remise\n\ndef test_a():\n    pass\n"
    assert gen_tests.ensure_import(code, "remise") == code


def test_prompt_contient_code_et_spec():
    prompt = gen_tests.build_prompt("remise", "def remise(): ...", spec="Règle 1")
    assert "def remise(): ..." in prompt and "Règle 1" in prompt and "from remise import" in prompt


def test_find_file_cherche_dans_les_dossiers_tp():
    assert gen_tests.find_file("remise.py").name == "remise.py"
    spec = gen_tests.find_file("SPEC.md", near=gen_tests.find_file("remise.py").parent)
    assert spec.parent.name == "tp1_generation"


def test_fallback_copie_la_sortie_d_exemple(tmp_path):
    out = tmp_path / "test_remise.py"
    assert gen_tests.main(["remise.py", "--spec", "SPEC.md", "--fallback", "--out", str(out)]) == 0
    assert "exemple pédagogique" in out.read_text(encoding="utf-8").lower()


def test_llm_injoignable_message_et_code_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LAB_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:9")  # port fermé
    monkeypatch.delenv("LAB_CONTAINER", raising=False)
    code = gen_tests.main(["remise.py", "--spec", "SPEC.md", "--out", str(tmp_path / "t.py")])
    assert code == 2
    err = capsys.readouterr().err
    assert "injoignable" in err and "--fallback" in err
    assert not (tmp_path / "t.py").exists()


def test_choix_du_fournisseur(monkeypatch):
    for var in ("LAB_LLM_PROVIDER", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert llm.provider() == "ollama"
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert llm.provider() == "openai"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert llm.provider() == "anthropic"

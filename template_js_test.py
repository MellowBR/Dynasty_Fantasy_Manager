"""
template_js_test.py — o JS inline de TODO template parseia (OFF26-23-FIX).

Origem: regressão do `6ecb90e` — um `\\n` de string JS virou quebra de linha real
dentro do template durante uma edição gerada, o parse do bloco inteiro morreu
(`Uncaught SyntaxError`) e NENHUMA função do bloco existia mais (`toggleFlag is not
defined`) — o poka-yoke do passo 5 ficou mudo em produção. A lição: **poka-yoke
silencioso é meio poka-yoke — a mensagem é parte do mecanismo**, e um SyntaxError de
template não pode voltar a chegar em prod calado.

Estratégia em duas camadas, nunca silenciosa:
- **node disponível** (dev/CI local): `node --check` em cada bloco `<script>`, com as
  expressões Jinja neutralizadas — cobertura sintática completa.
- **node ausente**: heurística de string não terminada (aspas simples/duplas abertas no
  fim da linha física — exatamente a classe do incidente). Menor cobertura, mas o teste
  RODA e o relatório diz qual camada rodou.
"""

import io
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = sorted((BASE_DIR / "templates").glob("*.html"))

_SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.S)


def _neutralize_jinja(js: str) -> str:
    """Troca {{ ... }} por literal inerte e remove {% ... %} — o que o browser recebe
    é o resultado da renderização; para fins de PARSE, o placeholder equivale."""
    js = re.sub(r"\{\{.*?\}\}", "0", js)
    js = re.sub(r"\{%.*?%\}", "", js)
    return js


def _blocks():
    for tpl in TEMPLATES:
        text = tpl.read_text(encoding="utf-8")
        for i, block in enumerate(_SCRIPT_RE.findall(text)):
            yield tpl.name, i, _neutralize_jinja(block)


def _unterminated_quote_lines(js: str):
    """Linhas com string de aspas simples/duplas aberta no fim da linha física —
    a classe exata do incidente (template literal com crase pode multi-linha; fica
    fora da heurística de propósito)."""
    bad = []
    for n, line in enumerate(js.split("\n"), start=1):
        stripped = re.sub(r"//.*$", "", line)
        in_str = None
        prev = ""
        for ch in stripped:
            if in_str:
                if ch == in_str and prev != "\\":
                    in_str = None
            elif ch in ("'", '"'):
                in_str = ch
            prev = ch if prev != "\\" or ch != "\\" else ""
        if in_str:
            bad.append((n, line.strip()[:80]))
    return bad


class TestTemplateJs(unittest.TestCase):

    NODE = shutil.which("node")

    def test_todo_bloco_script_parseia(self):
        falhas = []
        camada = "node --check" if self.NODE else "heurística de string não terminada"
        for name, i, js in _blocks():
            label = f"{name}[script #{i}]"
            if self.NODE:
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                                 encoding="utf-8") as f:
                    f.write(js)
                    path = f.name
                r = subprocess.run([self.NODE, "--check", path],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    falhas.append(f"{label}: {r.stderr.strip().splitlines()[-1][:120]}")
            else:
                for n, linha in _unterminated_quote_lines(js):
                    falhas.append(f"{label} linha {n}: string aberta → {linha}")
        self.assertEqual(falhas, [],
                         f"JS inline quebrado (camada: {camada}):\n" + "\n".join(falhas))

    def test_ha_templates_para_conferir(self):
        """O glob não pode silenciosamente varrer nada."""
        self.assertGreater(len(TEMPLATES), 10)
        self.assertTrue(any(True for _ in _blocks()))

    def test_heuristica_pega_a_classe_do_incidente(self):
        """A camada de fallback detecta exatamente o que quebrou o 6ecb90e."""
        quebrado = "if (confirm(d.error + '\n\nProsseguir?')) {"
        self.assertTrue(_unterminated_quote_lines(quebrado))
        ok = "if (confirm(d.error + '\\n\\nProsseguir?')) {"
        self.assertEqual(_unterminated_quote_lines(ok), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

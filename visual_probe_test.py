"""
visual_probe_test.py — núcleo puro da sonda de validação visual (O7).

Exercita o que DECIDE: classificação novo × conhecido, exit code, detecção de anatomia
divergente e a integridade da própria configuração. **Sem browser, sem Flask, sem DB** —
o driver (`cli.py`) é exercido pela demonstração bidirecional registrada no backlog.

⚠️ O teste mais importante desta suíte é `TestConhecidoNaoViraTapete`: o mecanismo de
defeito conhecido existe para o gate não nascer vermelho — e é exatamente o mecanismo
que, mal feito, esconderia regressão nova.
"""

import unittest
from pathlib import Path

from tools.visual_probe import core

BASE_DIR = Path(__file__).resolve().parent


def achado(tipo="colisao", pagina="league", largura=1280, culpados=("span.a", "span.b"),
           detalhe="x"):
    return {"tipo": tipo, "pagina": pagina, "largura": largura,
            "culpados": list(culpados), "detalhe": detalhe}


UX16 = {
    "id": "UX16", "tipo": "overflow_documento", "paginas": "*", "larguras": [860],
    "culpados": {"nav-right", "btn-sync", "nav-user-menu", "nav-user-button"},
    "nota": "navbar",
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. Classificação — o que bloqueia e o que só reporta
# ══════════════════════════════════════════════════════════════════════════════

class TestClassificacao(unittest.TestCase):

    def test_achado_novo_bloqueia(self):
        r = core.classificar([achado()], [UX16])
        self.assertEqual(len(r["novos"]), 1)
        self.assertEqual(core.exit_code(r), 1)

    def test_conhecido_reporta_e_nao_bloqueia(self):
        a = achado(tipo="overflow_documento", largura=860,
                   culpados=["nav-right", "btn-sync"])
        r = core.classificar([a], [UX16])
        self.assertEqual(r["novos"], [])
        self.assertEqual(len(r["conhecidos"]["UX16"]), 1)
        self.assertEqual(core.exit_code(r), 0)

    def test_conhecido_vale_em_qualquer_pagina(self):
        """A navbar mora no base.html — o defeito dela aparece em toda página."""
        for pag in ("league", "roster", "picks", "team_detail"):
            a = achado(tipo="overflow_documento", pagina=pag, largura=860,
                       culpados=["nav-right"])
            self.assertEqual(core.classificar([a], [UX16])["novos"], [], pag)

    def test_conhecido_nao_reproduzido_e_anunciado(self):
        """Se o defeito foi corrigido, a entrada tem de sair do registro — e o
        relatório precisa avisar, senão ela apodrece ali."""
        r = core.classificar([], [UX16])
        self.assertEqual(r["nao_reproduzidos"], ["UX16"])
        self.assertEqual(core.exit_code(r), 0)      # corrigir defeito não quebra o gate

    def test_sem_achados_e_sem_conhecidos(self):
        r = core.classificar([], [])
        self.assertEqual((r["novos"], r["conhecidos"]), ([], {}))
        self.assertEqual(core.exit_code(r), 0)


class TestConhecidoNaoViraTapete(unittest.TestCase):
    """O registro de dívida conhecida não pode virar anistia geral."""

    def test_largura_diferente_nao_casa(self):
        a = achado(tipo="overflow_documento", largura=1024, culpados=["nav-right"])
        self.assertEqual(len(core.classificar([a], [UX16])["novos"]), 1)

    def test_tipo_diferente_nao_casa(self):
        a = achado(tipo="colisao", largura=860, culpados=["nav-right"])
        self.assertEqual(len(core.classificar([a], [UX16])["novos"]), 1)

    def test_culpado_NOVO_na_conta_volta_a_bloquear(self):
        """O coração do mecanismo: se um elemento a mais passa a transbordar, aquilo
        deixou de ser o defeito registrado e volta a ser regressão."""
        a = achado(tipo="overflow_documento", largura=860,
                   culpados=["nav-right", "btn-sync", "tabela-nova"])
        r = core.classificar([a], [UX16])
        self.assertEqual(len(r["novos"]), 1)
        self.assertEqual(core.exit_code(r), 1)

    def test_pagina_fora_da_lista_nao_casa(self):
        restrito = {**UX16, "paginas": ["roster"]}
        a = achado(tipo="overflow_documento", pagina="league", largura=860,
                   culpados=["nav-right"])
        self.assertEqual(len(core.classificar([a], [restrito])["novos"]), 1)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Anatomia — estrutura, não dado
# ══════════════════════════════════════════════════════════════════════════════

class TestAnatomia(unittest.TestCase):

    def _m(self, i, assinatura, lefts=(12,), altura=123, linhas=4):
        return {"indice": i, "assinatura": assinatura, "lefts": list(lefts),
                "altura": altura, "linhas": linhas}

    def test_uniforme_passa(self):
        iguais = [self._m(i, "a@11 | b@31 | c@69 | c@93") for i in range(12)]
        self.assertIsNone(core.anatomia_divergente(iguais))

    def test_o_caso_real_do_L3_e_pego(self):
        """11 cards com os 2 itens na MESMA linha e o over-cap com o 2º em top=93 —
        a medição literal do controle da FIX-UX2."""
        medidas = [self._m(i, "label@11 | value@31 | item@69 | item@69") for i in range(11)]
        medidas.append(self._m(11, "label@11 | value@31 | item@69 | item@93", altura=100))
        d = core.anatomia_divergente(medidas)
        self.assertIsNotNone(d)
        self.assertEqual(d["n_assinaturas"], 2)

    def test_left_divergente_e_acusado_como_desalinhamento(self):
        medidas = [self._m(i, "a@11 | b@31", lefts=(12,)) for i in range(3)]
        medidas.append(self._m(3, "a@11 | b@31", lefts=(12, 181)))
        d = core.anatomia_divergente(medidas)
        self.assertIsNotNone(d)
        self.assertEqual(d["desalinhados"], [3])

    def test_left_NAO_entra_na_assinatura(self):
        """⚠️ 1px de diferença no `left` vem da largura do TEXTO ($5/$200 × $180/$200) —
        é dado, não anatomia. Foi um falso positivo real durante a FIX-UX2."""
        self.assertNotIn("left", core.JS_ANATOMIA.split("assinatura:")[1].split("\n")[0])

    def test_menos_de_dois_irmaos_nao_prova_nada(self):
        self.assertIsNone(core.anatomia_divergente([self._m(0, "a@1")]))
        self.assertIsNone(core.anatomia_divergente([]))


# ══════════════════════════════════════════════════════════════════════════════
# 3. Configuração — o gate não pode nascer torto
# ══════════════════════════════════════════════════════════════════════════════

class TestConfig(unittest.TestCase):

    def test_config_de_producao_integra(self):
        self.assertEqual(core.validar_config(), [])

    def test_1280_e_obrigatoria(self):
        """A largura que produz o card MAIS ESTREITO (auto-fill) — os 2 defeitos do L3
        apareceram nela."""
        sem = [w for w in core.WIDTHS if w["px"] != 1280]
        self.assertTrue(any("1280" in p for p in core.validar_config(widths=sem)))

    def test_mobile_e_obrigatorio(self):
        sem = [w for w in core.WIDTHS if w["px"] > 420]
        self.assertTrue(any("mobile" in p for p in core.validar_config(widths=sem)))

    def test_toda_largura_tem_motivo(self):
        for w in core.WIDTHS:
            self.assertTrue(w.get("motivo"), w["px"])

    def test_toda_pagina_declara_por_que_esta_na_lista(self):
        for p in core.PAGES:
            self.assertTrue(p.get("nota"), p["nome"])

    def test_pagina_sem_geometria_e_rejeitada(self):
        ruim = [{"nome": "x", "rota": "/x", "geometria": [], "anatomia": None, "nota": "n"}]
        self.assertTrue(core.validar_config(pages=ruim))

    def test_defeito_conhecido_exige_nota(self):
        ruim = [{k: v for k, v in UX16.items() if k != "nota"}]
        self.assertTrue(any("nota" in p for p in core.validar_config(conhecidos=ruim)))

    def test_tabela_fica_fora_da_anatomia(self):
        """Critério aprovado: <table> alinha por construção — anatomia ali é ruído."""
        for p in core.PAGES:
            if p["anatomia"]:
                self.assertNotIn("table", p["anatomia"]["grupo"])


# ══════════════════════════════════════════════════════════════════════════════
# 4. Guardas do instrumento — o que não pode se perder na manutenção
# ══════════════════════════════════════════════════════════════════════════════

class TestGuardasDoInstrumento(unittest.TestCase):

    CLI = (BASE_DIR / "tools" / "visual_probe" / "cli.py").read_text(encoding="utf-8")

    def test_controle_positivo_existe(self):
        """⭐ `--css` é o que impede a ferramenta de virar carimbo: mesma página, folha
        trocada. Sem ele, um verde nunca foi provado contra defeito nenhum."""
        self.assertIn("--css", self.CLI)

    def test_nao_degrada_para_verde_sem_browser(self):
        """Sem Playwright a sonda ABORTA (exit 2) — nunca 'passou'."""
        self.assertIn("raise SystemExit(2)", self.CLI)
        self.assertIn("NÃO degrada", self.CLI)

    def test_roda_sobre_copia_do_banco(self):
        self.assertIn("shutil.copyfile(origem, copia)", self.CLI)
        self.assertIn("DYNASTY_DB", self.CLI)

    def test_sem_rede(self):
        self.assertIn("run_sync = lambda", self.CLI)

    def test_colisao_ignora_pares_aninhados(self):
        """Pai × filho não é colisão — sem isto o relatório vira ruído puro."""
        self.assertIn("contains(B.el)", core.JS_GEOMETRIA)

    def test_overflow_nomeia_o_culpado(self):
        """Nomear é o que distingue tabela larga pré-existente de defeito novo."""
        self.assertIn("culpados", core.JS_OVERFLOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)

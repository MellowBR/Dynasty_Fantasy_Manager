"""
core.py — núcleo PURO da sonda de validação visual (O7).

Mesma separação do `salary_engine` e do `tools/phantom_board`: aqui não há Playwright,
Flask, banco nem rede. Só configuração, os trechos de JS que o driver injeta, e as
funções que **decidem** (classificar achados, formatar relatório, exit code). É o que os
testes exercem sem abrir browser.

⚠️ POR QUE ESTA FERRAMENTA EXISTE (saga [[L3]], 13/08/2026): três gerações de validação
queimaram num dia, **cada uma nascida de um defeito que a anterior aprovou**:

    regex sobre HTML  →  cego a layout      (aprovou 12 cards com texto SOBREPOSTO)
    geometria         →  cego a uniformidade (aprovou anatomias diferentes entre vizinhos)
    assinatura de anatomia

Nenhuma suíte de unidade cobre pixel; nenhuma leitura de HTML cobre sobreposição.
"""

# ══════════════════════════════════════════════════════════════════════════════
# Larguras canônicas — cada uma com o motivo de existir (F1 do O7)
# ══════════════════════════════════════════════════════════════════════════════

WIDTHS = [
    {
        "px": 1280,
        "motivo": (
            "⚠️ CONTRA-INTUITIVA E OBRIGATÓRIA: a grade da liga é "
            "`repeat(auto-fill, minmax(280px, 1fr))`, então o viewport MAIS LARGO produz "
            "o card MAIS ESTREITO (4 colunas × ~300px). Os DOIS defeitos de layout do L3 "
            "apareceram aqui. Testar largo não é testar fácil."
        ),
    },
    {
        "px": 1024,
        "motivo": "3 colunas × ~320px — a largura do screenshot de produção do owner.",
    },
    {
        "px": 860,
        "motivo": "2 colunas; é a faixa onde a navbar transborda ([[UX16]]).",
    },
    {
        "px": 390,
        "motivo": "viewport mobile (o owner deposita bilhete da urna pelo celular).",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Cobertura — o CRITÉRIO decide a lista, não o gosto (F1 do O7, aprovado)
# ══════════════════════════════════════════════════════════════════════════════
#
# ▸ ANATOMIA (assinatura `classe@topo` comparada entre irmãos) só onde houver
#   **N irmãos gerados pelo MESMO loop de template, em layout LIVRE (flex/grid), que
#   DEVEM parecer idênticos**.
#   ⛔ Tabela não entra: `<table>` já alinha por construção.
#   ⛔ Irmão que PODE divergir legitimamente não entra — ver a nota do /picks.
#
# ▸ GEOMETRIA (colisão / transbordo / overflow) em **superfície densa de instância
#   única**. A navbar mora no `base.html`, então entra de brinde em TODA página.
#
# ▸ Fora de alcance do modelo de serviço atual (`file://` sobre HTML salvo): páginas
#   cujo conteúdo principal é montado por `fetch` — `/cap_projector` (3 fetches) e
#   `/trades` (9). Medido, não suposto. Cobri-las exige servidor efêmero — decisão
#   registrada como próximo passo, não silenciada.

PAGES = [
    {
        "nome": "league",
        "rota": "/league",
        "geometria": [".league-card"],
        "anatomia": {
            "grupo": ".league-plan",
            "linhas": ".league-plan-label, .league-plan-value, .league-plan-item",
        },
        "nota": "12 cards do MESMO loop, em grade livre, que devem ser idênticos — "
                "o caso que originou a ferramenta.",
    },
    {
        "nome": "team_detail",
        "rota": "/team/{team_id}",
        "geometria": [".team-status-bar"],
        "anatomia": None,
        "nota": "barra de status = superfície densa de instância única (sem irmãos a "
                "comparar).",
    },
    {
        "nome": "roster",
        "rota": "/",
        "geometria": [".page-header", ".cap-bar-wrap"],
        "anatomia": None,
        "nota": "a tabela de roster fica FORA de propósito: <table> alinha por "
                "construção. Cobre-se o cabeçalho e a barra de cap.",
    },
    {
        "nome": "picks",
        "rota": "/picks",
        "geometria": [".picks-matrix"],
        "anatomia": None,
        "nota": "a matriz é grade livre e server-rendered, mas as células divergem "
                "LEGITIMAMENTE (vazia × preenchida × trocada) — anatomia aqui daria "
                "falso positivo. Só geometria até haver sub-seletor que isole as "
                "células comparáveis.",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# Defeitos CONHECIDOS — o que separa "regressão nova" de "pendência registrada"
# ══════════════════════════════════════════════════════════════════════════════
#
# Sem isto, o gate nasceria vermelho e seria desligado na primeira semana. Regras:
#   · achado que casa uma entrada  → REPORTADO, não bloqueia (tem item no backlog);
#   · achado que NÃO casa          → NOVO, bloqueia (exit 1);
#   · entrada que não reproduz     → avisa em voz alta (o defeito sumiu: tirar daqui).
#
# ⛔ Entrada aqui EXIGE item no backlog. Isto é registro de dívida conhecida, não
# tapete para varrer defeito novo.

KNOWN_DEFECTS = [
    # ✅ VAZIO — e este é o estado saudável.
    #
    # Nasceu com uma entrada: `UX16` (transbordo da navbar a ~860px, em toda página).
    # Ela saiu daqui em 13/08/2026, no MAN-UX16, **por indicação da própria sonda**: com
    # o defeito corrigido, o relatório passou a dizer
    #     "ℹ️ conhecido(s) que NÃO reproduziram: ['UX16'] — remover de KNOWN_DEFECTS"
    # — o mecanismo fechando o ciclo no sentido inverso ao da estreia (quando bloqueou
    # por não casar 4 culpados registrados contra 5 medidos).
    #
    # Para acrescentar uma entrada: **exige item no backlog**. Isto é registro de dívida
    # rastreada, não tapete para varrer defeito novo — ver README.
]


# ══════════════════════════════════════════════════════════════════════════════
# JS injetado — as duas famílias de verificação
# ══════════════════════════════════════════════════════════════════════════════

# Colisão entre caixas de texto NÃO-ANINHADAS dentro de um container, + transbordo
# para fora dele. `contains()` é o que impede acusar pai × filho.
JS_GEOMETRIA = r"""
(seletores) => {
  const achados = [];
  const nome = el => {
    const c = String(el.className || '').trim().split(/\s+/)[0];
    return el.tagName.toLowerCase() + (c ? '.' + c : '');
  };
  seletores.forEach(sel => {
    document.querySelectorAll(sel).forEach((raiz, idx) => {
      const cx = raiz.getBoundingClientRect();
      const caixas = [...raiz.querySelectorAll('*')].filter(el => {
        if (!(el.textContent || '').trim()) return false;
        const r = el.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0)) return false;
        const est = getComputedStyle(el);
        // ⚠️ LIMITE DECLARADO (medido no 1º run real): elemento INVISÍVEL não colide
        // visualmente. O `.pick-edit-btn` do /picks tem `opacity: 0` até o hover e
        // ocupa espaço — sem este filtro a sonda acusava 2 "colisões" a 390px que
        // ninguém vê. Preço: estados revelados por :hover ficam FORA da medição, que
        // é sempre do estado PADRÃO da página. Cobri-los é passo próprio.
        if (est.opacity === '0' || est.visibility === 'hidden') return false;
        return est.position !== 'absolute' && est.position !== 'fixed';
      }).map(el => ({el, r: el.getBoundingClientRect(),
                     txt: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30)}));
      for (let a = 0; a < caixas.length; a++) {
        for (let b = a + 1; b < caixas.length; b++) {
          const A = caixas[a], B = caixas[b];
          if (A.el.contains(B.el) || B.el.contains(A.el)) continue;
          if (A.r.left < B.r.right - 0.5 && B.r.left < A.r.right - 0.5 &&
              A.r.top < B.r.bottom - 0.5 && B.r.top < A.r.bottom - 0.5) {
            achados.push({tipo: 'colisao', seletor: sel, indice: idx,
                          detalhe: `"${A.txt}" x "${B.txt}"`,
                          culpados: [nome(A.el), nome(B.el)]});
          }
        }
      }
      caixas.forEach(c => {
        if (c.r.right > cx.right + 1 || c.r.left < cx.left - 1)
          achados.push({tipo: 'transbordo', seletor: sel, indice: idx,
                        detalhe: `"${c.txt}" fora de ${sel}`, culpados: [nome(c.el)]});
      });
    });
  });
  return achados;
}
"""

# Assinatura de ANATOMIA: `classe@topo` de cada linha, relativa ao topo do grupo.
# ⚠️ O `left` NÃO entra: ele varia com a largura do TEXTO ($5/$200 × $180/$200) — isso é
# dado, não anatomia. Alinhamento de coluna é verificação separada.
JS_ANATOMIA = r"""
({grupo, linhas}) => {
  const grupos = [...document.querySelectorAll(grupo)];
  return grupos.map((g, i) => {
    const cx = g.getBoundingClientRect();
    const alvos = [...g.querySelectorAll(linhas)].map(el => {
      const r = el.getBoundingClientRect();
      return {cls: String(el.className || '').trim().split(/\s+/)[0],
              top: Math.round(r.top - cx.top), left: Math.round(r.left - cx.left)};
    });
    return {
      indice: i,
      assinatura: alvos.map(a => `${a.cls}@${a.top}`).join(' | '),
      lefts: [...new Set(alvos.map(a => a.left))].sort((a, b) => a - b),
      altura: Math.round(cx.height),
      linhas: new Set(alvos.map(a => a.top)).size,
    };
  });
}
"""

# Overflow horizontal do DOCUMENTO + quem o causa (nomeado, para não confundir tabela
# larga pré-existente com defeito de bloco).
JS_OVERFLOW = r"""
() => {
  const nome = el => {
    const c = String(el.className || '').trim().split(/\s+/)[0];
    return c || el.tagName.toLowerCase();
  };
  const culpados = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > window.innerWidth + 1) culpados.push(nome(el));
  });
  return {
    transborda: document.documentElement.scrollWidth > window.innerWidth + 1,
    culpados: [...new Set(culpados)],
  };
}
"""


# ══════════════════════════════════════════════════════════════════════════════
# Decisão — puro, testável, sem browser
# ══════════════════════════════════════════════════════════════════════════════

def anatomia_divergente(medidas: list) -> dict | None:
    """Compara a assinatura dos irmãos. Devolve o diagnóstico ou None se uniforme.

    ⚠️ Menos de 2 grupos não prova nada — e "não prova nada" NÃO é aprovação: quem
    chama registra como cobertura ausente, não como verde.
    """
    if len(medidas) < 2:
        return None
    assinaturas = {}
    for m in medidas:
        assinaturas.setdefault(m["assinatura"], []).append(m["indice"])
    desalinhados = [m["indice"] for m in medidas if len(m["lefts"]) > 1]
    if len(assinaturas) == 1 and not desalinhados:
        return None
    return {
        "n_assinaturas": len(assinaturas),
        "grupos": {a: ids for a, ids in assinaturas.items()},
        "desalinhados": desalinhados,
        "alturas": sorted({m["altura"] for m in medidas}),
        "linhas": sorted({m["linhas"] for m in medidas}),
    }


def _casa(achado: dict, conhecido: dict) -> bool:
    """Um achado casa um defeito conhecido quando tipo, página e largura batem E os
    culpados são SUBCONJUNTO dos registrados — se um elemento novo entrar na conta,
    o achado deixa de ser o conhecido e volta a bloquear."""
    if achado["tipo"] != conhecido["tipo"]:
        return False
    paginas = conhecido["paginas"]
    if paginas != "*" and achado["pagina"] not in paginas:
        return False
    if achado["largura"] not in conhecido["larguras"]:
        return False
    return set(achado.get("culpados") or []) <= set(conhecido["culpados"])


def classificar(achados: list, conhecidos: list = None) -> dict:
    """Separa achados NOVOS (bloqueiam) de CONHECIDOS (reportam) e aponta entradas
    que não reproduziram (defeito corrigido → remover do registro)."""
    conhecidos = KNOWN_DEFECTS if conhecidos is None else conhecidos
    novos, casados = [], {c["id"]: [] for c in conhecidos}
    for a in achados:
        alvo = next((c for c in conhecidos if _casa(a, c)), None)
        if alvo:
            casados[alvo["id"]].append(a)
        else:
            novos.append(a)
    return {
        "novos": novos,
        "conhecidos": {k: v for k, v in casados.items() if v},
        "nao_reproduzidos": [c["id"] for c in conhecidos if not casados[c["id"]]],
    }


def exit_code(resultado: dict) -> int:
    """⛔ Só achado NOVO bloqueia. Defeito conhecido é dívida registrada; corrigir um
    defeito não pode quebrar o gate de quem o corrigiu."""
    return 1 if resultado["novos"] else 0


def validar_config(pages=None, widths=None, conhecidos=None) -> list:
    """Poka-yoke da própria configuração (o gate não pode nascer torto)."""
    pages = PAGES if pages is None else pages
    widths = WIDTHS if widths is None else widths
    conhecidos = KNOWN_DEFECTS if conhecidos is None else conhecidos
    problemas = []
    if not pages:
        problemas.append("nenhuma página coberta")
    nomes = [p["nome"] for p in pages]
    if len(set(nomes)) != len(nomes):
        problemas.append(f"nomes de página duplicados: {nomes}")
    for p in pages:
        for campo in ("nome", "rota", "geometria", "nota"):
            if campo not in p:
                problemas.append(f"página {p.get('nome', '?')} sem `{campo}`")
        if not p.get("geometria"):
            problemas.append(f"página {p.get('nome')} sem seletor de geometria")
        if p.get("anatomia") and not {"grupo", "linhas"} <= set(p["anatomia"]):
            problemas.append(f"anatomia incompleta em {p.get('nome')}")
    larguras = [w["px"] for w in widths]
    if len(set(larguras)) != len(larguras):
        problemas.append(f"larguras duplicadas: {larguras}")
    for w in widths:
        if not w.get("motivo"):
            problemas.append(f"largura {w['px']} sem motivo registrado")
    if 1280 not in larguras:
        problemas.append("1280px é obrigatória (produz o card MAIS ESTREITO da grade)")
    if not any(px <= 420 for px in larguras):
        problemas.append("falta um viewport mobile")
    for c in conhecidos:
        for campo in ("id", "tipo", "paginas", "larguras", "culpados", "nota"):
            if campo not in c:
                problemas.append(f"defeito conhecido {c.get('id', '?')} sem `{campo}`")
    return problemas


def formatar(relatorio: dict) -> str:
    """Relatório legível. `relatorio` = {'medicoes': [...], 'classificado': {...},
    'segundos': float, 'css': str|None}."""
    L = []
    css = relatorio.get("css")
    L.append("visual_probe — sonda de validação visual (O7)")
    if css:
        L.append(f"  ⚠️ MODO CONTROLE: folha de estilo trocada por {css}")
    for m in relatorio["medicoes"]:
        marca = "·" if not m["achados"] else "✗"
        extra = ""
        if m.get("anatomia") is not None:
            extra = (f" | anatomia: {m['anatomia']['n_assinaturas']} assinaturas"
                     if m["anatomia"] else " | anatomia: uniforme")
        elif m.get("anatomia_ausente"):
            extra = " | anatomia: n/a (menos de 2 irmãos)"
        L.append(f"  {marca} {m['pagina']:<14} {m['largura']:>5}px  "
                 f"{len(m['achados'])} achado(s){extra}")
    c = relatorio["classificado"]
    L.append("")
    if c["conhecidos"]:
        for cid, itens in c["conhecidos"].items():
            nota = next((k["nota"] for k in KNOWN_DEFECTS if k["id"] == cid), "")
            L.append(f"  ⚠️ CONHECIDO [{cid}] — {len(itens)} ocorrência(s), NÃO bloqueia")
            L.append(f"      {nota}")
            for i in itens[:3]:
                L.append(f"      · {i['pagina']} @{i['largura']}px: {i['detalhe']}")
    if c["nao_reproduzidos"]:
        L.append(f"  ℹ️ conhecido(s) que NÃO reproduziram: {c['nao_reproduzidos']} — "
                 f"se o defeito foi corrigido, remover de KNOWN_DEFECTS")
    if c["novos"]:
        L.append(f"  ⛔ {len(c['novos'])} ACHADO(S) NOVO(S) — bloqueia o push:")
        for n in c["novos"][:20]:
            L.append(f"      · {n['pagina']} @{n['largura']}px [{n['tipo']}] {n['detalhe']}")
            # a lista COMPLETA de culpados é a evidência que alimenta KNOWN_DEFECTS
            L.append(f"        culpados: {sorted(n.get('culpados') or [])}")
        if len(c["novos"]) > 20:
            L.append(f"      … e mais {len(c['novos']) - 20}")
    else:
        L.append("  ✅ nenhum achado novo")
    L.append(f"\n  {relatorio.get('segundos', 0):.0f}s")
    return "\n".join(L)

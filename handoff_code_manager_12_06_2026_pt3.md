# Handoff — Code Manager — 12/06/2026 (pt3: sessão Opus DOC1+F12+DP2)

> Ponte temporária entre sessões. **Fonte de verdade = `manager_devplan.md`** (log) +
> `improvements.md`/`improvements_archive.md` (backlog). Descartável após leitura.
> Substitui os handoffs `_12_06_2026.md` e `_12_06_2026_pt2.md` (sessões F11/F10).

## Resumo da sessão

Sessão multi-item no Opus 4.8, 3 commits separados (abertura no 1º). **F10 ✅** (smoke prod) +
**DOC1 ✅** + **F12 ⚠️** + **F11-FIX-UX** (layout) + **DP2 ⚠️**.

## Commits (cronológico, NÃO pushed — push é gatilho de deploy, fica com o owner)

1. `e4af9fd` — **DOC1 (docs-only) + abertura**: startup do CLAUDE.md reescrita contra o boot real;
   F10 → ✅ (smoke prod OK) + migrado ao archive; F11-FIX-UX layout (passo 2 encurtado).
2. `a84fd4f` — **F12**: CSV vira bootstrap one-shot p/ salary/contract (flag `csv_bootstrap_done`).
3. _(a criar nesta sessão)_ — **DP2**: cadeia única no cap projector.

## O que foi feito

- **F10 ✅** — smoke de prod passou ($157/$43/$38/5 spots conferido). Seção (4.699 chars) migrada
  verbatim+flip ao archive (O3).
- **DOC1 ✅ (docs-only)** — "App Startup Sequence" do CLAUDE.md reescrita lendo `app.py` passo a
  passo (âncoras de linha). Corrigidas as 2 divergências da AUD1 (ordem do `init_auth`; sync/backfill
  condicionais a `fresh_import`, backfill ainda atrás de `f8_rebuilt`) + 4 omissões (URI via
  `DYNASTY_DB`; filtro `utc_iso`; context processors/blueprints/error handlers; `app.run` só
  `__main__`). Migrada ao archive.
- **F11-FIX-UX (layout)** — o passo 2 do card "Ordem do Fluxo" fragmentava em colunas no smoke;
  encurtado p/ "— aplicado na etapa Season Rollover da página de Intertemporada; aqui, só a prévia".
  **Segue ⚠️** até smoke do layout em prod (carona do DP2 / commit 3? — não; foi no commit 1 da
  abertura. O ✅ depende do próximo deploy).
- **F12 ⚠️ localhost** — `run_import` deixa de reescrever salary/contract_year de player existente
  após a 1ª semeadura (flag `csv_bootstrap_done` em AppConfig — **decisão: flag própria, não
  `f8_rebuilt`**, que num DB dev fresco é false e não fecharia o caso). Branch de create intocado
  (player novo entra); prod (CSV ausente) retorna cedo, flag nunca setada. Escopo estrito a
  salary/cyr (observação ESPN/`set_espn_value` registrada como candidata a item próprio). CLAUDE.md
  (Commands) atualizado. Validado: boot duplo preserva edição, player novo entra, prod skip.
- **DP2 ⚠️ localhost** — cadeia única de planejamento (revisão consciente da base do DP1-F2). Board
  de rookies parte do cenário keep/corte (salário projetado, base = summary F10); barra **sticky**
  única (cortes + rookies). **Estendeu o `/budget` do F10 com `rookie_sids`; removeu o `/simulate`**
  (fonte única). Painel do board reduzido a nº+custo; `updateSummary`+`simulateScenario` →
  `refreshScenario`. Validado: retrocompat $256, 4 cenários × canônico, caso DP1 ($46→$55/$3→$3/+$58),
  `/simulate` 405, nada escrito.

## Estado dos bancos

Prod intocado. Local: `dynasty.db`/`.sleeper_players_cache.json` restaurados ao seed após os testes
(usuários e rookies temporários criados e removidos nas validações).

## Próximos passos

1. **Push** (owner) → deploy → **smoke F10-restantes em prod**:
   - **DP2**: `/cap_projector` — barra sticky visível ao rolar (desktop + mobile estreito); toggles
     keep/corte + adicionar rookies refletindo no topo; board mostrando só nº/custo.
   - **F11-FIX-UX**: `/admin` — passo 2 do card "Ordem do Fluxo" em 1 linha, sem fragmentar.
   - Aí **DP2 ⚠️→✅** (migrar seção ao archive) e **F11-FIX-UX ✅**.
   - **F12** é dev-local (sem smoke de prod) — done já registrado; owner confirma quando quiser.
2. **F9 (urgência alta)** — **antes da FA auction 2026** (rotear `bulk_register` por
   `record_acquisition` + remover hack `_noop`; sem backfill, veredito F1B).
3. **E4-d (Opus)** — antes da FA auction.
4. **M19** — carona futura. **M20** — bloqueado até M17 ✅.
5. **Observação ESPN do F12** (candidata a item): `set_espn_value` também re-aplica o snapshot ESPN
   do CSV todo boot local — mesma classe, fora do escopo F12. Abrir item se incomodar em dev.

## Pendências de owner

- Push dos 3 commits (`e4af9fd`, `a84fd4f`, + o do DP2) + smoke do item 1.
- **Re-upload no Project Knowledge:** `CLAUDE.md`, `improvements.md`, `improvements_archive.md`,
  `manager_devplan.md`.
- Não-commitados pré-existentes (não desta sessão): `AGENTS.md`, handoffs antigos — decisão com o
  owner.

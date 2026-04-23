# Handoff Code — Fantasy Manager — 23/04/2026

> Descartável após leitura. Fonte de verdade: `manager_devplan.md` (camadas + Log) e `improvements.md` (backlog). Handoff serve pra retomar rápido na próxima sessão.

## O que foi feito (sessão 22-23/04/2026)

Sessão longa de 2 dias. Entrega da **maioria das camadas Alta/Média** do backlog + refatorações estruturais do histórico + trinca de atalho universal pra propor trade.

### Commits (24 no total)

```
5da8a4a M9-FIX: todas as picks clicáveis + pré-seleção de pick no /trades
aac743f docs: atualizar improvements data + CLAUDE blueprints/models pós-sessão
95b38eb M13: página de jogador + Propor Trade em 1 clique
0758c06 M9: grid navegável de picks com atalho para trade
53cbf32 M14: /trades aceita ?team_a=&team_b= pra pré-selecionar os seletores
b5423c3 Backlog: M9 (reformulado) + M13 (novo) + M14 (pré-req trades query params)
f58720a M8 roleta: sorteio faseado pick a pick com teaser visual
a49bfde M8 fix: toggle não aparecia quando DraftLotteryResult tinha rows pré-M8
56f4566 M8-sim: unificar sorteio em 1 botão com flag 'oficial'
dadfa94 M8: lottery auditável + visualização de bolinhas + fluxo em duas fases
1baaf72 UI /salary_history: sort 'Por Posição' usa nome como tiebreaker
e9cdee2 Backlog: descartar T3 após review do T2 em produção
e338c28 Backlog: T3 — sugestões de assets para equilibrar trade
7eed6c8 T2: valores dynasty FantasyCalc no preview de trade
e7f778c UI /salary_history fix: passar event completo para renderEventRow
5a1af42 UI /salary_history: modal clicável de detalhe de trade
cd31f6e T1: Trade Manager como simulador puro + link compartilhável
453bea2 F8-ORDER: fix ordenação cronológica da timeline /salary_history
5b99fca F8-UI: fix /salary_history exibindo timeline duas vezes
... (anteriores F8a/b/c, F6, F8-GAP, F8-NOTES, F8-RESTORE-GAP)
```

### Camadas concluídas (ordem cronológica)

| ID | Camada | Commit |
|----|--------|--------|
| F8a/b/c + F8-GAP + F8-NOTES + F8-ORDER + F8-UI + F8-RESTORE-GAP | PlayerHistory canônico via Sleeper chain + UI polishing | pré-sessão atual |
| F6 | Remover `acquisition_type='keeper'` | pré-sessão atual |
| T1 | Trade Manager simulador + link compartilhável | cd31f6e |
| T2 | Valores dynasty FantasyCalc no preview | 7eed6c8 |
| T3 | (descartado após review — não vai implementar) | e9cdee2 |
| M8 | Lottery auditável + bolinhas + fluxo duas fases | dadfa94 / 56f4566 / a49bfde / f58720a |
| M14 | `/trades` aceita `?team_a=&team_b=` | 53cbf32 |
| M9 | Grid navegável de picks + atalho trade | 0758c06 |
| M13 | Página de jogador + "Propor Trade" | 95b38eb |
| M9-FIX | Todas as picks clicáveis + pré-seleção de pick no /trades | 5da8a4a |

### Estruturas novas

**Modelos (`models.py`):**
- `TradeProposal` (T1): UUID, assets JSON, TTL 7d
- `LotteryAudit` (M8): seed, weights_json, pool_json, result_hash, previous_audit_id, reason, is_canonical

**Módulo novo:**
- `dynasty_values.py` (T2): fetcher FantasyCalc + cache JSON `data/.dynasty_values_cache.json` (TTL 24h) + helper `pick_sleeper_id`

**Templates novos:**
- `templates/trade_proposal.html` (T1)
- `templates/lottery_audit.html` (M8)
- `templates/player_detail.html` (M13)
- `templates/_trade_detail_modal.html` (partial reutilizável, M13/O1)

**Endpoints novos (principais):**
- `POST /api/trades/proposals` + `GET /trades/proposta/<uuid>` (T1)
- `GET /api/dynasty_values` + `POST /api/admin/dynasty_values/refresh` (T2)
- `POST /api/offseason/lottery/simulate` + `POST /api/offseason/lottery/replace` (M8)
- `GET /picks/lottery/<season>` + `GET /api/picks/lottery/<season>/verify` (M8)
- `GET /player/<player_id>` (M13)
- `GET /api/trades/by_tx/<tx_id>` (F8-NOTES)

### Estado do banco (local, 23/04/2026)

- `LotteryAudit`: 1 row season 2026 (pode ter sido apagado/recriado em testes)
- `DraftLotteryResult`: 12 rows season 2026, `locked=0`
- `TradeProposal`: possíveis rows de teste (descartáveis)
- `PlayerHistory`: 1092 rows pós-F8
- `Trade`: 47 rows com 45 distinct tx_refs em player_history (2 patológicos conhecidos)
- `Player`: 278 rows ativos, 236 com dynasty_value via FantasyCalc (84.9% cobertura)
- `SeasonStandings`: 12 rows season 2025
- `LEAGUE_ID` atual: `1316547584378048512` (season 2026 pre_draft no Sleeper)

### dynasty.db local diverge do repo

Alterações locais nas tabelas `LotteryAudit`, `DraftLotteryResult`, `TradeProposal` por causa de testes de validação. **Não commitei essas alterações** porque produção usa `/data/dynasty.db` (persistent disk, não sobrescrito pelo `init_data.py`). Se quiser resetar local, pode fazer `git checkout dynasty.db` ou deixar como está — é ambiente de dev.

### Decisões não triviais registradas no Log de `manager_devplan.md`

- **T2 client-side vs M13 server-side** para dynasty_value: T2 recalcula em tempo real (toggle); M13 é render único, backend resolve.
- **M8 bolinhas literais + shuffle** (não cumulative sum): matematicamente equivalente mas alinha com UI visual.
- **M8 fluxo em 2 fases** (simulação + oficial unificados via checkbox): evita cherry-picking, commitment explícito.
- **M8 seed derivado contínuo** (random.seed uma vez): determinismo preservado.
- **M9 célula clicável apenas quando `traded_away AND current_team != my_team`**: foca no caso real.
- **M13 `event.stopPropagation()` no `<a>` dentro de `<label>`**: sem isso clicar no nome toggleava checkbox da trade.
- **M13 `player_id` em vez de `id`**: evita shadow builtin.
- **`_trade_detail_modal.html` partial** (M13/O1): modal de trade clicável reutilizado entre salary_history e player_detail.

## Pendente / deixei no caminho

- **F8-RESTORE-GAP automação no `/restore`**: já entregue (commit anterior). Fecha o gap.
- **F6 migrou 60 players** em prod no próximo deploy (Migration 6). Em dev local já rodou.
- **Migrations aplicadas em produção no próximo boot pós-deploy**: Migration 5 (F8a sleeper_event_ref) já deployada. Migration 6 (F6 keeper→auction_draft) já deployada. Não tem nada pendente de DB schema.

## Backlog restante (ordem sugerida)

### Alta (desbloqueadas para próximas sessões)
- Nenhuma hoje — todo F8 + T1/T2 + M8 + M9/M13/M14 entregues.

### Média
- **Q1** — Script de simulação de temporada (dev-only, valida rollover sem tocar DB). Sem UI.
- **M1** — Validação de cap antes de confirmar trade (se ainda fizer sentido pós-S1 que confirma via Sleeper — provavelmente desnecessário).
- **M2** — Tela de aprovação em lote de `needs_review=True`.

### Baixa
- **M3** — Endpoint JSON `/api/estado` read-only.
- **M4** — Banner de sync desatualizada + botão sincronizar.
- **M6** — Pipeline de stats CSV → ESPN ref values automático (médio-grande, na verdade).
- **M10** — Autocomplete de jogador na calculadora de salário.

### Deferidas
- **X2** — Propor/aceitar/recusar trade dentro do Manager (S1 cobre caminho feliz).
- **T3** — Descartada após review do T2.

## Regras confirmadas nesta sessão

- **Metodologia DEV_METHODOLOGY.md seguida:** diagnose → plano → análise crítica → implementação → validação 8-10 cenários → docs + commit → push.
- **Plans mode para diagnoses e designs**; auto mode para execuções aprovadas.
- **Templates server-side (Jinja) vs client-side (JS template string)**: verificar antes de planejar mudança (ex: roster server, salary_history JS).
- **Flask url_for preferível sobre URLs hardcoded** exceto quando string é montada dentro de JS template (impossível usar url_for — usar path literal `/player/${id}`).
- **`event.stopPropagation()` obrigatório** quando `<a>` está dentro de `<label>` com checkbox (descoberto no M13).
- **Cache JSON em `data/.*_cache.json`** é padrão do projeto (Sleeper, FantasyCalc).
- **LF→CRLF warnings** são esperados no Windows — ignoráveis.

## Próxima sessão — como retomar

1. Ler `manager_devplan.md` (header + últimas camadas) — estado atual.
2. Ler `improvements.md` (Status Rápido) — backlog priorizado.
3. Escolher próximo item (sugerido: Q1 ou M2).
4. Ler `DEV_METHODOLOGY.md` antes de planejar.
5. Rodar diagnose (prompt `MAN-<ID>-F1`) antes de implementação (prompt `MAN-<ID>`).

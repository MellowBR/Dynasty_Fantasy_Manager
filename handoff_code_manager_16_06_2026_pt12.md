# Handoff — FECHAMENTO da sessão (16/06/2026 pt12)

Handoff de encerramento da maratona OFF26. Fonte de verdade = `manager_devplan.md` (log) +
`improvements.md` (backlog). Este é descartável após leitura.

## O que entrou (tudo pushado em origin/main)

| Commit | Item | Status |
|--------|------|--------|
| `6b73141` | OFF26-8 registrado (Cowork aplica cortes no Sleeper) | 🔲 (op) docs-only |
| `2c243d4` | OFF26-1 — janela de cortes selada | ⚠️ localhost |
| `a8c6f0f` | OFF26-2 — keeper sheet consolidada | ⚠️ localhost |

Pipeline por item: F1 (diagnose read-only) → REFINE (spec do owner) → F2 (impl). Handoffs
pt5..pt11 cobrem cada fase; estão commitados.

## Estado de validação

- **OFF26-1:** e2e localhost 23/23 (sigilo, gate `needs_review`, default-zero, M8
  lock/replace/verify, não-mutação). `salary_engine` 48/48.
- **OFF26-2:** e2e localhost 20/20 (keepers=roster−cortes, budget==porta `projected:false`,
  paridade tabela×CSV, pré-condição, não-mutação, zero réplica). `salary_engine` 48/48.
- **Ambos ⚠️ — sem prod.** Nada foi a ✅ → nenhuma migração para o archive (regra O3).

## ⚠️ Pendências críticas para o smoke de prod

1. **Backup do `dynasty.db` vivo ANTES do 1º acesso pós-deploy** — OFF26-1 traz 2 models
   novos (`CutDeclaration`, `CutWindowAudit`); `create_all` cria as tabelas no
   `/data/dynasty.db` (aditivo, sem perda, mas é toque de schema em prod).
   `sqlite3 /data/dynasty.db ".backup '/data/dynasty_prod_backup_<data>_pre-off26.db'"`.
2. **Dependência de dados (D8):** a janela pressupõe **E4-a (ESPN definitiva) + Season
   Rollover (passo 4)** aplicados na season real, e **`needs_review` zerado** (gate de
   abertura). Só dá para fazer o smoke real na intertemporada (~ago).
3. **Roteiro do smoke:** abrir `/cuts` (admin) → owner declara cortes → admin lock+verify
   hash → abrir `/cuts/keeper_sheet` → conferir keepers/salário/budget por time → baixar CSV
   (paridade) → só então marcar OFF26-1 e OFF26-2 ✅.

## Próximos passos (fila)

- **OFF26-4** (auditoria pré-leilão) — próximo F1 natural do pacote; **consome
  `/api/cuts/keeper_sheet`** (JSON) como base de diff contra a config real da liga fantasma.
- **OFF26-7** (dry run E2E) — encadeia revelação → keeper sheet → Cowork → OFF26-4; depende
  de OFF26-1/2/4 existirem (1 e 2 já ⚠️). Decisão em aberto: gate único vs. por etapas.
- **Itens ⚠️ acumulados aguardando smoke prod:** F9, E2, M17, OFF26-1, OFF26-2.

## Working tree no fechamento

Limpo de OFF26. Intactos (decisão do owner): `AGENTS.md`, handoffs de abril (23/04 M, 24/04,
28/04_pt2), handoff 11/06. Nenhum `.db` em git.

## Pendência de owner

Re-upload no Project Knowledge (Claude.ai) de `improvements.md`, `manager_devplan.md` e
`CLAUDE.md` se o planejamento usar a versão antiga.

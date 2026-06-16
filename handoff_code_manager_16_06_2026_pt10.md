# Handoff — Sessão OFF26-2-REFINE (16/06/2026 pt10)

## Natureza

**Docs-only** (MAN-OFF26-2-REFINE) — sincroniza a seção OFF26-2 do `improvements.md` com as
decisões de design pós-F1. Nenhum código/schema/salary_engine/porta/OFF26-1 tocado. F1
preservada; spec entrou como **camada de decisão por cima**. Status segue **🔲** (sem ✅).

## Spec final do OFF26-2 (D1..D9)

- **D1** — sheet fala a língua do KEEPER por inversão: `keepers = roster_live − cut_ids` do
  snapshot canônico (chave `Player.id`).
- **D2** ⚙️ deliberada — **fonte mista** (cortes frozen do snapshot; salário/budget ao vivo) +
  **timestamp do lock + aviso**. Justificativa: não duplicar `p.salary` no audit, não mexer no
  OFF26-1 validado; risco coberto pelo aviso.
- **D3** — salário = `p.salary` (pós-rollover); não re-derivar via `project_next_salary`.
- **D4** — budget de FA = `usable_draft_budget` via porta em **`projected:false`** (mesma
  chamada da janela); não recalcular.
- **D5** — IR conta normal (D11); sheet sem coluna/flag de IR.
- **D6** — colunas: keeper, salário, budget de FA, `declared` (conferência). SEM slots
  vazios / 8.3.4.
- **D7** — consolidada (12 times).
- **D8** — saída: **CSV** principal + tabela na página. (F1: sem precedente de export → `csv`
  stdlib + `Content-Disposition` é padrão novo.)
- **D9** — pré-condição: só pós-revelação (snapshot canônico); página comunica se ainda não
  locked.

## Decisão de arquitetura marcada deliberada

**D2** — derivar salário/budget ao vivo + aviso de timestamp em vez de congelar no snapshot;
preserva fonte única `p.salary`/`draft_budget` e o OFF26-1 intocado.

## Como a spec fecha os gaps da F1

- "qual número é o budget de FA" → **D4** (`usable_draft_budget`).
- "formato de export" → **D8** (CSV + tabela).
- "por-time vs. consolidada" → **D7** (consolidada).
- "incluir IR/slots/8.3.4/declared" → **D5/D6** (só `declared`; sem IR/slots/8.3.4).
- "fonte mista live × frozen" → **D2** (assumida + mitigada por aviso de timestamp).

## Estado

- Docs-only. Arquivo tocado: `improvements.md` (só a seção OFF26-2) + este handoff.
- Sem push. Commit docs-only deste ciclo pode agrupar com a F1 (pt9).
- **F2 LIBERADA** para ler esta spec (REG-before-IMPL satisfeito).

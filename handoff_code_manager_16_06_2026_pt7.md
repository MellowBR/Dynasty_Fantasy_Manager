# Handoff — Sessão OFF26-1-REFINE (16/06/2026 pt7)

## Natureza

**Docs-only** (MAN-OFF26-1-REFINE) — sincroniza a seção OFF26-1 do `improvements.md` com as
decisões de design arbitradas pelo owner após a F1. Nenhum código, schema, salary_engine,
porta de budget ou diagnose nova. A F1 (terreno) foi **preservada**; a spec entrou como
**camada de decisão por cima** dela. Status do item segue **🔲** (sem ✅ prematuro).

## O que entrou (spec final do OFF26-1 — D1..D11)

- **D1** — unidade = **lista de cortes** (`cut_ids`), não keepers; keepers = complemento.
- **D2** — default de quem não declara: **zero cortes = mantém todos** (reg. 5.2; adequação
  resolvida depois pelo admin).
- **D3** — abertura da janela: **`needs_review` zerado é BLOQUEIO DURO** (gate na abertura).
- **D4** — lock + revelação: **admin-manual (botão), padrão M8**; deadline é data exibida.
- **D5** — owner ausente / time inadequado: **admin supre/ajusta antes do lock**.
- **D6** — sigilo só da **declaração de cortes** (inclusive p/ admins); expõe só contagem
  "8/12"; **roster segue público**.
- **D7** — revelação **congela snapshot** (molde M8); **não escreve no Sleeper (OFF26-8)** nem
  materializa cortes no estado oficial.
- **D8** ⚙️ infra — janela roda **DEPOIS do rollover (passo 4)**; lê salário já valorizado;
  cria dependência de dados **E4-a + rollover**.
- **D9** ⚙️ infra — budget consome a porta canônica em **MODO NÃO-PROJETADO** (salário já
  rollado; re-projetar duplicaria). **Ampliação deliberada da porta, não réplica/débito** —
  fonte de cálculo segue única (`draft_budget`); muda só a base de salário.
- **D10** — 8.3.4 na janela é **alerta**, não trava (enforcement mora no FA auction).
- **D11** — **IR e K/DEF contam** no budget, igual ao `draft_budget` atual.

## Decisões de infra marcadas como deliberadas (exigência do prompt)

- **(a) D8** — dependência de ordem pós-rollover.
- **(b) D9** — modo não-projetado na porta canônica de budget (fonte de cálculo ainda única;
  não viola o princípio do F10).

## Como a spec fecha os gaps da F1

- "keepers vs cuts" → **D1** (cortes).
- "timing pré/pós-rollover" → **D8** (pós).
- "base do budget / duplo project_next_salary" → **D9** (não-projetado).
- "IR/K-DEF" → **D11** (contam).
- "8.3.4 hard/soft" → **D10** (soft).
- "sigilo recai sobre declaração, não roster" → **D6**.

## Estado

- Docs-only. Arquivo tocado: `improvements.md` (só a seção OFF26-1) + este handoff.
- Dependências do item atualizadas: de "nenhuma" → dependência de dados E4-a + rollover (D8).
- Sem push. Commit docs-only deste ciclo pode agrupar com a F1 (pt6) se ainda não commitada.
- **F2 LIBERADA** para ler esta spec sincronizada (REG-before-IMPL satisfeito).

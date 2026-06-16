# Handoff — Sessão OFF26-6-7-REG (16/06/2026 pt4)

## Natureza

**Registro apenas** (MAN-OFF26-6-7-REG) — docs-only. Nenhuma implementação, nenhuma
diagnose, nenhum código tocado. Só `improvements.md` (tabela Status Rápido + seção do
pacote OFF26 + cabeçalho) e este handoff.

## Itens registrados (ambos 🔲, Prioridade Alta)

### OFF26-6 — PoC de viabilidade do Cowork montando a liga fantasma
- **Validação operacional (NÃO-código)** + **GATE**.
- Prova, em liga de teste descartável e com antecedência, que Cowork + Claude in Chrome
  montam a liga fantasma de ponta a ponta dirigindo a UI do Sleeper (criar sala → 12
  times → draft auction → keepers/budgets). Produz roteiro de experimento + registro do
  resultado (onde trava, que intervenção manual exige).
- Roda **cedo e isolado**, mecânica pura com **dados fake** (não espera a keeper sheet real).
- **Gate:** deve passar antes de confiar a FA auction real ao procedimento Cowork.
- Insumo do runbook **OFF26-5** (que documenta o caminho comprovado pelo PoC).
- Sem dependências para rodar.

### OFF26-7 — Dry run end-to-end da intertemporada
- **Ensaio geral operacional** da cadeia inteira encadeada: rookie draft teste → import
  (OFF26-3) → ESPN (E4-a) → janela selada (OFF26-1) → keeper sheet (OFF26-2) → Cowork
  monta (OFF26-6) → auditoria (OFF26-4) → FA auction teste → import (OFF26-3).
- Foco nas **COSTURAS** entre módulos (formato de handoff), não na lógica interna de cada
  peça.
- **Dependência:** só roda de verdade depois que **OFF26-1, OFF26-2 e OFF26-4 existirem**
  (OFF26-3 já ✅; E4-a já existe).
- **OFF26-6 ⊂ OFF26-7** (registrado): a etapa "Cowork monta" dentro do ensaio maior.

## DECISÃO EM ABERTO p/ o owner (OFF26-7 — não arbitrada)

OFF26-7 é um **gate único final** antes da intertemporada real, **ou** roda **por etapas**
conforme OFF26-1/2/4 ficam prontas? Registrada como pendência explícita; decidir antes da
F1 do item.

## Conferência da validação do prompt

- OFF26-6 e OFF26-7 com descrição, motivação, escopo, dependências, prioridade, status 🔲. ✅
- OFF26-6 marcado como validação operacional (não-código) e gate. ✅
- OFF26-7 registra dependência de OFF26-1/2/4 + decisão em aberto (gate único vs. etapas). ✅
- Relação OFF26-6 ⊂ OFF26-7 registrada (tabela + seção + linha de dependências do pacote). ✅
- Status Rápido reflete os dois novos itens. ✅
- Nenhum item OFF26 existente (1–5) teve descrição alterada — só referenciados nas
  dependências dos novos + 1 linha aditiva na seção de dependências do pacote. ✅

## Estado

- Docs-only, **sem push** (conforme instrução).
- Pendências do ciclo: F9 (`1ad8bd2`) aguarda smoke prod; E4-d aguarda decisões A/B/C
  (F1) + D/E/F (F1b) do owner antes da F2; OFF26-7 aguarda decisão gate-único-vs-etapas.

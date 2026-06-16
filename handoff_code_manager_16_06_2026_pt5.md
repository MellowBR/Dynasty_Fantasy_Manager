# Handoff — Sessão OFF26-8-REG (16/06/2026 pt5)

## Natureza

**Registro apenas** (MAN-OFF26-8-REG) — docs-only. Nenhuma implementação, nenhuma
diagnose, nenhum código tocado. Só `improvements.md` (tabela Status Rápido + seção do
pacote OFF26 + linha de validação do cabeçalho do pacote) e este handoff.

## Item registrado (🔲, Prioridade Média)

### OFF26-8 — Cowork aplica os cortes no roster real do Sleeper
- **Capability operacional (NÃO-código)**, status 🔲 `(op)`, Prioridade **Média**.
- A partir da **lista de cortes** revelada pelo OFF26-1 (janela selada), um agente
  **Cowork + Claude in Chrome** dirige a UI do Sleeper para **dropar os jogadores
  cortados** do roster real de cada time. O OFF26-1 produz a lista auditável mas **não
  a executa** em lugar nenhum; esta é a peça que efetiva os cortes no Sleeper.
- **Natureza:** mesma de OFF26-5 (runbook) e OFF26-6 (PoC) — itens `(op)` fora do código
  do Manager; a API do Sleeper é read-only, então mexer no roster só dirigindo a UI pelo
  navegador.
- **Dependência:** OFF26-1 (fonte da lista de cortes).
- **Relação:** **⊂ OFF26-7** (etapa "aplicar cortes no Sleeper" da cadeia E2E);
  **irmão de OFF26-6** (mesmo procedimento Cowork supervisionado).

## Conferência da validação do prompt

- OFF26-8 no Status Rápido com Prioridade Média, status 🔲 (op), descrição e ref
  MAN-OFF26-8-REG. ✅
- Seção do pacote OFF26 contém OFF26-8 com descrição, motivação, escopo, dependência
  (OFF26-1) e relação (⊂ OFF26-7, irmão de OFF26-6). ✅
- Nenhuma descrição de OFF26-1..7 alterada além de referências aditivas (1 linha na seção
  de validação do cabeçalho do pacote citando OFF26-8). ✅

## Estado

- Docs-only, **sem push** (exceção de commit docs-only deliberada — agrupar com os docs
  pendentes do ciclo: pt2/pt3/pt4 de 16/06 + esta sessão, se ainda não commitados).
- Pendências do ciclo (inalteradas): F9 (`1ad8bd2`) aguarda smoke prod; E4-d aguarda
  decisões A/B/C (F1) + D/E/F (F1b) do owner antes da F2; OFF26-7 aguarda decisão
  gate-único-vs-etapas.

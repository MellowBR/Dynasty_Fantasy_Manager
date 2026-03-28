# Dynasty SB — Fantasy Manager

Dynasty league manager para a Dynasty SB: 12 times, PPR, Salary Cap de $200.

**Meu time:** Cangaceiros da Colina (MellowBR)
**Sleeper League ID:** 1316547584378048512

---

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://127.0.0.1:5000

Na primeira execução, o sistema importa automaticamente `dynasty_rosters_clean.csv`.

---

## Funcionalidades

| Página | URL | Descrição |
|--------|-----|-----------|
| Roster | `/` | Elenco do time, cap bar, IR, filtro por equipe |
| Calculadora | `/salary` | Tabela de salários para qualquer contrato |
| Cap Projector | `/cap_projector` | Projeção 2026 com toggle keep/cut |
| Trades | `/trades` | Registrar trades com preview de cap impact |
| Picks | `/picks` | Gerenciar picks 2025–2028 |
| Auction | `/auction` | Registrar FA auction e rookie draft |
| Histórico | `/salary_history` | Histórico de salários por temporada |
| Admin | `/admin` | Sync Sleeper, season rollover, ESPN bulk update |

---

## Regras de Salário

### Contrato: 4 anos. Cap = $200. Salário mínimo = $1. Arredondamento para baixo.

### Ano 1 por tipo de aquisição:
| Tipo | Salário Ano 1 |
|------|---------------|
| `auction_draft` / `keeper` | Valor pago no auction |
| `rookie_draft` | `floor(ESPN × 1.2)` |
| `waiver` / `free_agent` | $1 |

### Ano 2+ — VALORIZAÇÃO:
```
salary = MAX(salário_anterior, floor(0.5 × ESPN × 1.2))
mínimo: $1
```

### Exceção — Waiver/FA Ano 2:
```
salary = floor(0.80 × ESPN × 1.2), mínimo $1
```

### Renovação (após Ano 4):
```
Novo contrato de 4 anos
Ano 1 = floor(ESPN × 1.2), mínimo $1
Anos 2–4 = VALORIZAÇÃO
```

### Draft Budget:
```
Budget = $200 − Σ(salários dos keepers)
Mínimo necessário = $1 × (22 − número de keepers)
```

---

## Sleeper Sync

O sync via Sleeper API atualiza:
- Nomes e posições dos jogadores (via player DB cacheado semanalmente)
- Roster de cada time (novos jogadores marcados para revisão)
- Slots de IR (`roster.reserve[]`)
- Traded picks

**Salários nunca são sobrescritos pelo Sleeper** — a DB local é a fonte da verdade.

Botão "🔄 Sync" na navbar, ou via `/admin`.

---

## Testes

```bash
python salary_engine_test.py
```

Testes cobrem: VALORIZAÇÃO, waiver ano 2 (80%), rookie draft, renovação, floor $1, draft budget.

---

## Estrutura

```
app.py                  ← Flask app factory
models.py               ← SQLAlchemy models
salary_engine.py        ← Toda lógica de salários (testável isolado)
import_csv.py           ← Import inicial do CSV
sync_sleeper.py         ← Sleeper API sync
salary_engine_test.py   ← Unit tests
routes/
  roster.py             ← Roster + IR
  salary.py             ← Calculadora + Cap Projector + Histórico
  trades.py             ← Trade Manager
  picks.py              ← Draft Picks
  auction.py            ← FA Auction + Rookie Draft
  admin.py              ← Season Rollover + ESPN Update + Sync
templates/              ← Jinja2 HTML
static/style.css        ← Dark theme
dynasty.db              ← SQLite (gerado automaticamente)
```

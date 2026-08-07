# Runbook — Ensaio da Janela Selada (OFF26-1/2) · localhost → produção

> **MAN-OFF26-1-ENSAIO (06/08/2026).** Pré-condição 1 da spec da urna ([[OFF26-10]]): lock,
> hash e reveal **nunca rodaram em produção** — este ensaio valida o alicerce antes de 20/08
> (janela real) e de 22/08 (urna, que reusa o mecanismo). O ensaio **não toca o Sleeper em
> nada**; o único estado em risco é o banco, protegido por backup + reset verificado.
>
> **Dry-run do Code (06/08, cópia do seed): 41/41 checks PASS** — o roteiro abaixo foi
> executado de ponta a ponta antes de ser entregue, incluindo o desfazer.

## ✅ ENSAIO CONCLUÍDO — Etapas 1 e 2 executadas em 06/08/2026

- **Etapa 1 (localhost, owner):** checklist **10/10**, hash `5024b17a…`.
- **Etapa 2 (produção, owner + co-admin RAFA):** **ciclo completo aprovado** — **12 declarações**
  de contas distintas (o Rafa usou o **manter-todos**), sigilo cruzado conferido, **hierarquia
  owner > admin recusando o suprimento** como desenhado, lock + revelação, hash **`52274d01…`**,
  keeper sheet, e **reset verificado** (0/0/fechada, banner off, janela reabrindo). Backup
  `/data/pre_ensaio_off26_1.db` = **618.496 bytes**.
- **Achado de campo:** o **`confirm()` nativo falhou no celular** e impediu a declaração do Rafa
  (no desktop funcionou) → a urna usa **confirmação inline**, nunca pop-up nativo (U-CONF do
  OFF26-10).

## ⚠️ ESTE RUNBOOK É REGISTRO HISTÓRICO — o fluxo principal MUDOU (06/08/2026)

Decisão do owner, tomada durante a Etapa 2: **os cortes de 20/08 acontecem direto no Sleeper**
(públicos e graduais) e **o Manager só fotografa por sync**. A **tela de declaração múltipla foi
APOSENTADA** — o roteiro abaixo, que a dirige, **não descreve mais o fluxo de 20/08**. O que o
Manager faz em 2026 é a **urna do late drop de 22/08** ([[OFF26-10]]), que **reusa o mecanismo
aqui validado** (lock · hash · revelação · snapshot · reset). O runbook do dia da urna é peça
própria e inclui a **janela de execução manual**: revelou → owners dropam no Sleeper → admin
confere → **sync final** → keeper sheet definitiva.

## A ferramenta

`ensaio_janela_selada.py` (na raiz do projeto; em prod, no Render Shell):

| Comando | O que faz |
|---|---|
| `python ensaio_janela_selada.py --status` | Relatório read-only: estado da janela, nº de declarações (sem conteúdo), snapshots, flags. É a **consulta de conferência** — use antes e depois. |
| `python ensaio_janela_selada.py --banner on` / `off` | Liga/desliga o rótulo **"🧪 ENSAIO — NÃO DECLARAR"** nas telas `/cuts` e `/cuts/keeper_sheet`. |
| `python ensaio_janela_selada.py --reset --backup <path>` | **Desfaz o ciclo de ensaio por completo**: apaga declarações + snapshots da season, fecha a janela, desliga o banner, e verifica (0/0/fechada). **Recusa rodar sem backup conferível.** |

Em localhost, acrescente `--db <caminho>` para apontar para um banco de teste
(sem `--db`, usa a env `DYNASTY_DB`, senão o `dynasty.db` local).
**POSENSAIO (06/08):** caminho **relativo funciona** — é resolvido contra o diretório de onde
você invoca (o bug da Etapa 1, que abria um banco vazio em outro diretório, foi corrigido);
e `--db` para arquivo **inexistente é recusado** com mensagem clara (nunca cria banco novo).

⚠️ **Por que o reset apaga a trilha do ensaio (comportamento esperado, decidido):** o estado
"travada" da janela É a existência do snapshot canônico — snapshot de ensaio deixado no banco
**bloquearia a abertura da janela real de 20/08** (o `/open` recusa com 409). O reset devolve o
banco ao estado pré-ensaio por inteiro; **a evidência do ensaio fica no backup** (obrigatório,
feito antes) e no relatório — não na trilha viva. Diff do banco pós-reset: **vazio**.

## Checklist do que o ensaio prova (marcar item a item)

| # | O que provar | Como verificar |
|---|---|---|
| 1 | Janela abre (gate `needs_review` zerado) | `/cuts` como admin → "🔓 Abrir janela" → banner de estado vira "Aberta" |
| 2 | Aceita declarações de contas distintas | Erico e Rafa, cada um logado na própria conta, marcam 1 jogador óbvio (ex.: **o próprio kicker**) e salvam |
| 3 | Declaração invisível a terceiros antes do reveal | Logado como **outro** usuário: `/cuts` mostra só o próprio roster vazio de marcações; `Aberta — 2/12` (contagem, sem conteúdo); `/cuts/keeper_sheet` diz "não revelada" |
| 4 | Substituição dentro da janela | Trocar o jogador marcado e salvar de novo → recarregar → vale a última |
| 5 | Lock trava novas declarações e alterações | Após o lock: salvar declaração → erro "janela não está aberta"; abrir de novo → recusado |
| 6 | Hash de integridade gerado e conferível | `GET /api/cuts/audit/verify` (logado, no navegador) → `"hash_match": true` |
| 7 | Reveal publica tudo simultaneamente | `GET /api/cuts/audit` → `revealed: true`, os 12 times, cortes de Erico e Rafa visíveis; ausentes = zero cortes |
| 8 | Keeper sheet gerada do resultado | `/cuts/keeper_sheet` → tabela dos 12 times, cortados fora da lista, CSV baixa |
| 9 | Trilha registra o ciclo | `--status` → 1 snapshot CANÔNICO com hash e timestamp |
| 10 | Reset devolve o estado pré-ensaio | `--reset` termina em "✅ RESET OK"; `--status` → 0 declarações, 0 snapshots, janela fechada; **abrir a janela volta a funcionar** |

---

## Etapa 1 — localhost (owner, quantas vezes quiser)

**Preparo (uma vez):**

```
cd "C:\Users\Erico Mello\Fantasy\fantasy_manager"
copy dynasty.db ensaio_local.db
copy ensaio_local.db ensaio_local_backup.db
set DYNASTY_DB=%CD%\ensaio_local.db
python app.py
```

(Novo terminal para os comandos do script, sempre com `--db ensaio_local.db`.)

**Ciclo (repetível):**

1. `python ensaio_janela_selada.py --status --db ensaio_local.db` → janela fechada, 0/0.
2. `python ensaio_janela_selada.py --banner on --db ensaio_local.db` → abrir
   `http://localhost:5000/cuts` e **ver o banner de ENSAIO** (item de fé do risco operacional).
3. Logado como você (admin): **Abrir janela** (se recusar por `needs_review`, zere a fila em
   `/admin/review` antes — o gate é real e é bom vê-lo funcionar).
4. Declarar 1 corte óbvio do seu roster (ex.: kicker) e salvar. **Substituir** por outro e
   salvar de novo (checklist 4).
5. Segunda conta em localhost (opcional — o multi-conta completo fica para a Etapa 2):
   `python seed_users.py --email <seu-gmail-alternativo> --name Teste --team-id 3` e logar
   numa janela anônima. Sem segunda conta: use o bloco admin **"Suprir/ajustar pelo time"**
   para declarar por outro time (exercita o write-by-team).
6. **Lock + Revelação** (botão admin) → conferir checklist 5–8 (URLs da tabela acima).
7. `python ensaio_janela_selada.py --reset --db ensaio_local.db --backup ensaio_local_backup.db`
   → "✅ RESET OK" → `--status` → 0/0/fechada → **Abrir janela** de novo funciona (checklist 10).
8. Repetir até o roteiro estar redondo. Ao final, apagar `ensaio_local*.db` e fechar o app
   (o `dynasty.db` real não foi tocado).

## Etapa 2 — produção (owner + co-admin **Rafa**) — EXECUTADA EM 06/08/2026

> **Pré-requisitos:** deploy com o ensaio no ar (push desta sessão já feito; conferir no
> Render que o deploy ficou live) · Etapa 1 redonda · horário combinado com Rafa.
> **Sequência travada — não pular passos:**

1. **Aviso no grupo:** *"teste do sistema hoje às X; ignorem qualquer tela de cortes até eu
   confirmar o fim"*.
2. **Render Shell** (Dashboard → serviço → Shell):
   ```
   sqlite3 /data/dynasty.db ".backup '/data/pre_ensaio_off26_1.db'"
   ls -la /data/pre_ensaio_off26_1.db
   python ensaio_janela_selada.py --status
   python ensaio_janela_selada.py --banner on
   ```
   Conferir: backup com tamanho plausível (~600 KB+); status = janela fechada, 0 declarações,
   0 snapshots. **Sem backup conferido, o ensaio não continua.**
3. **Ciclo do checklist** (na UI, `https://dynasty-fantasy-manager.onrender.com/cuts`):
   - Erico abre a janela (banner de ENSAIO visível);
   - Erico e Rafa declaram **cortes fictícios e óbvios** (o próprio kicker), cada um na sua
     conta; **um confere o sigilo do outro antes do reveal** (checklist 3 — Rafa não vê o
     corte do Erico em lugar nenhum, e vice-versa);
   - Erico substitui a própria declaração (checklist 4);
   - Erico dispara **Lock + Revelação**; os dois conferem 5–9 (verify, reveal, sheet, trilha
     via `--status` no Shell).
4. **Reset verificado** (Render Shell):
   ```
   python ensaio_janela_selada.py --reset --backup /data/pre_ensaio_off26_1.db
   python ensaio_janela_selada.py --status
   ```
   Esperado: "✅ RESET OK" e status 0 declarações / 0 snapshots / janela fechada / banner off.
   Prova final: abrir a janela na UI **funciona** (e fechar em seguida sem revelar) — é a
   garantia de que 20/08 não ficou bloqueado.
5. **Confirmação no grupo:** *"teste encerrado — podem ignorar o que apareceu"*.

### Adendo POSENSAIO — conferências EXTRAS na Etapa 2 (deploy de 06/08 no ar)

O deploy pós-Etapa-1 acrescentou o **manter-todos explícito** e a **hierarquia owner > admin**.
Se ele estiver no ar quando a Etapa 2 rodar (recomendado), acrescentar ao ciclo:

| # | O que provar | Como verificar |
|---|---|---|
| 11 | Manter-todos explícito | Rafa usa **"✋ Não vou cortar ninguém"** em vez de marcar corte → confirma → "Declarado: MANTER TODOS"; conta no "N/12" |
| 12 | Hierarquia owner > admin | Erico tenta **"Suprir/ajustar pelo time"** no time do Rafa → recusa "este time já declarou pessoalmente" **sem mostrar o conteúdo**; num time silencioso, o suprimento funciona |
| 13 | 3º status na sheet | Pós-reveal, `/cuts/keeper_sheet` mostra o time do Rafa como **"Declarou (manteve todos)"** — distinto de "Default (manteve todos)" |

(O reset da Etapa 2 desfaz tudo igual — os três itens não mudam o desfazer.)

**Se algo der errado no meio:** parar, não improvisar. O reset desfaz qualquer estado parcial
(declarações sem lock, lock sem reset anterior — tudo). Em último caso, o backup de
`/data/pre_ensaio_off26_1.db` restaura o banco inteiro
(`sqlite3 /data/dynasty.db ".restore '/data/pre_ensaio_off26_1.db'"` com o app parado —
só se o reset falhar, o que o dry-run não observou).

# Runbook — A Urna do Late Drop (OFF26-10) · smoke em produção + o dia 20→22/08

> **MAN-OFF26-10 (07/08/2026).** A urna é a **única porta de declaração do Manager em 2026**:
> os cortes de 20/08 acontecem direto no Sleeper e o Manager **só fotografa por sync**.
> Este runbook tem duas partes: **(A) o smoke em produção**, que o owner roda antes de 20/08,
> e **(B) o roteiro dos dias 20, 22 e 24**, incluindo a **janela de execução manual**.
>
> Dry-run do Code (07/08, cópia do seed, app real): **42/42 checks PASS** — ciclo completo,
> incluindo o bloqueio mútuo com o rollover e o reset. Suíte permanente: `late_drop_test.py`
> (**64 testes**).

---

## Onde fica cada coisa

| O quê | Onde | Quem |
|---|---|---|
| Urna (depositar o bilhete) | `/late_drop` — menu **Liga ▸ 🗳️ Late Drop (Urna)** | todos os owners |
| Agenda, flag do rookie, suprimento, lock | mesma tela, bloco **Admin** | admin |
| Keeper sheet (provisória/definitiva) | `/cuts/keeper_sheet` — menu **Admin ▸ 📋 Keeper Sheet** | **admin** |
| Auditoria pré-leilão | `/admin/keeper_audit` | admin |
| Bid Máximo por time | `/league` (cards) e `/cap_projector` | todos |
| Tela de cortes antiga | `/cuts` — explicação + motor legado | pública/admin |

⛔ **A urna tem flag de estado própria** (`late_drop_opens_at` / `late_drop_closes_at`).
Abrir a urna **não** reabre a porta de declaração antiga — e há teste que falha se alguém
"simplificar" reusando `cuts_window_open`.

🔒 **A ordem rollover → urna é BLOQUEIO DE CÓDIGO, não instrução** (MAN-OFF26-10-AJUSTES,
07/08/2026 — antes era só este aviso; o owner mandou travar o botão):

- **Rollover recusado (409)** enquanto a urna estiver **agendada/aberta e não revelada** na season
  corrente. Motivo: bilhetes e snapshot são escopados por `current_season`; virar a season no meio
  deixa os bilhetes **órfãos** e a revelação sai **vazia, sem erro nenhum**. A mensagem na tela do
  `/offseason` diz o que fazer: revelar a urna primeiro, ou limpar a agenda em `/late_drop`.
- **Agendamento da urna recusado (409)** enquanto o **rollover estiver pendente**
  (`rollover_done != true`) — a ordem do calendário é **rollover 18/08 → urna 20/08**.
- **Escape para ENSAIAR antes do rollover:** com o **banner de ensaio ligado**
  (`python ensaio_janela_selada.py --banner on`) o segundo bloqueio é liberado. Sem isso, o gate
  impediria o próprio smoke desta página. O banner é visível para todos na tela e o `--reset` o
  apaga — o escape é explícito, não silencioso.
- **Depois da revelação**, o snapshot está congelado e o rollover volta a ser liberado.

---

## (A) Smoke em produção — antes de 20/08

**Pré-requisitos:** deploy live no Render · backup feito · aviso no grupo
(*"teste do sistema hoje às X; ignorem a tela de Late Drop até eu confirmar o fim"*).

### A0 — Backup e banner de ensaio (Render Shell)

```
sqlite3 /data/dynasty.db ".backup '/data/pre_smoke_urna.db'"
ls -la /data/pre_smoke_urna.db
python ensaio_janela_selada.py --status
python ensaio_janela_selada.py --banner on
```

Conferir: backup com tamanho plausível (600 KB+); status mostrando a linha
**`URNA (late drop): sem_agenda`** e **0 bilhetes**. Sem backup conferido, o smoke não segue.

### A1 — Checklist (marcar item a item)

| # | O que provar | Como verificar |
|---|---|---|
| 1 | A urna está no menu, e no **celular** | Abrir o site **no telefone** → menu ☰ → **🗳️ Late Drop (Urna)** abre `/late_drop` |
| 2 | Fechada não aceita | Sem agenda gravada: a tela diz *"horário ainda não definido"* e o botão não deposita |
| 3 | Admin agenda | Bloco Admin → **Abre** = agora−10min, **Fecha** = daqui a 2h → "Gravado" → banner vira **🗳️ Urna ABERTA** |
| 4 | **Escolha única** | Marcar um jogador e depois outro → **o primeiro desmarca sozinho**. Não existe estado com dois marcados |
| 5 | **Confirmação inline no celular** | Tocar em **Depositar meu bilhete** → o botão vira **"✅ Confirmar: \<nome\>?"** → tocar de novo deposita. **Nenhum pop-up nativo** (foi o que travou o Rafa em 06/08) |
| 6 | Passo explícito | Segundo owner marca **"✋ Não vou dropar ninguém"** → confirma → "Bilhete depositado: sem late drop" |
| 7 | **Sigilo do conteúdo** | O outro owner, logado na conta dele: **não vê o jogador** nem de quem é o bilhete. Só o próprio |
| 7b | **Contagem agregada** | O banner mostra **"N/12 depositaram"** para todos, e o N **sobe igual** com drop e com passo (é o que impede a contagem de virar dedo-duro de inclinação) |
| 8 | Substituição | Trocar a marcação e depositar de novo → recarregar → **vale a última** |
| 9 | Hierarquia owner > admin | Admin → **Suprir por time** no time de quem já declarou → recusa *"já declarou pessoalmente"* **sem mostrar o conteúdo**; num time silencioso, funciona |
| 10 | Flag do rookie | Ligar **"Bloquear rookie de 1ª rodada"** → o rookie de 1ª aparece **PROTEGIDO** e o servidor recusa com mensagem clara → **desligar de novo** (o default da liga é OFF) |
| 11 | Lock + revelação | Admin → **🎬 Lock + Revelação** (2 cliques, inline) → tabela dos 12 times com **drops e "sem late drop"** |
| 12 | Hash | **🔐 Verificar hash** → *"Hash confere (snapshot íntegro)"* |
| 13 | Urna fecha de vez | Tentar depositar pós-lock → recusado |
| 14 | Sheet **provisória** com aviso | `/cuts/keeper_sheet` → selo **PROVISÓRIA** + aviso *"a urna já revelou N drops, mas não houve sync depois"* |
| 15 | Sheet **definitiva** | Rodar o **sync** (botão da navbar) → recarregar a sheet → selo **DEFINITIVA** e o carimbo do sync novo |
| 16 | Sheet é de admin | Um owner comum abrindo `/cuts/keeper_sheet` → **403** |
| 17 | CSV | **⬇️ Baixar CSV** → colunas `IR` e `Bid Maximo (time)`; keepers em IR marcados |
| 18 | Hub | `/league` → cada card com **Bid Máximo** e selo **PROV** (sai quando a ESPN definitiva entrar, 18/08) |
| 19 | Porta única | `/cuts` continua **sem** roster/checkbox/botão de declarar |
| 20 | **Bloqueio urna → rollover** | Com a urna agendada, `/offseason` → **Season Rollover** → recusa **explicando o que está bloqueando e o que fazer** (revelar ou limpar a agenda). Depois da revelação, libera |
| 21 | **Bloqueio rollover → urna** | Com o rollover pendente **e o banner de ensaio desligado**, gravar horários é recusado citando o passo 4 do `/offseason`. Com o banner ligado, passa (é o escape do ensaio) |

### A2 — Reset verificado (Render Shell)

```
python ensaio_janela_selada.py --reset --backup /data/pre_smoke_urna.db
python ensaio_janela_selada.py --status
```

Esperado: **"✅ RESET OK"** e status com **0 bilhetes, 0 snapshots de urna, urna sem agenda,
banner off**. **Prova final:** gravar uma agenda nova na UI **funciona** (e apagar em seguida) —
é a garantia de que 22/08 não ficou bloqueado.

> ⚠️ O reset **zera a agenda de propósito**: um horário de teste esquecido reabriria a urna
> sozinha em produção.

### A3 — Fim

Desligar o banner (`--banner off`, se o reset não o fez) e avisar no grupo:
*"teste encerrado — podem ignorar o que apareceu"*.

---

## (B) O roteiro dos dias

### 20/08 — cortes no Sleeper → sheet provisória

1. **Owners cortam no Sleeper**, em público, até o prazo combinado.
2. Admin roda o **sync** (botão da navbar) — o Manager fotografa os rosters.
3. `/cuts/keeper_sheet` → confere o carimbo do sync e o selo **PROVISÓRIA**.
   Esta sheet **já serve** para a 1ª leva de população do board da liga fantasma
   (times enquadrados no teto — ver `runbook_cowork_liga_fantasma.md`).
4. Admin abre a urna: `/late_drop` → **Abre** (após o sync) e **Fecha** (22/08, horário
   combinado) → avisar no grupo com o link.

⚠️ **Só abrir a urna depois do sync.** Sem ele, a lista de elegíveis mostra roster velho —
um jogador já cortado no Sleeper apareceria como dropável.

🔒 **E depois do rollover:** com `rollover_done` pendente, o agendamento é recusado (a season
viraria no meio da urna). Se o rollover ainda não rodou em 20/08, rode o passo 4 do `/offseason`
**antes** — e só então agende a urna.

### 20→22/08 — urna aberta

Cada owner deposita **um** bilhete: um jogador **ou** "não vou dropar ninguém". Pode trocar
até fechar. Quem não depositar fica sem late drop. **Ninguém vê nada** até a revelação.

### 22/08 — revelação e **janela de execução manual**

1. Passado o horário de fechamento, admin → **🎬 Lock + Revelação**.
2. A tela publica a **lista de drops a executar** + o hash. **Avisar no grupo.**
3. **Cada owner executa o próprio drop no Sleeper.** O Manager **não** dropa ninguém —
   ele declarou e revelou; a execução é onde sempre esteve.
4. **Admin confere**, roster a roster no Sleeper, que **cada jogador revelado sumiu**.
   Quem não executar aparece na auditoria do passo 6 — é a rede, e ela é para ser usada.
5. **Sync final** → `/cuts/keeper_sheet` deve virar **DEFINITIVA** (selo verde + carimbo do
   sync posterior à revelação). **Se continuar PROVISÓRIA, algum drop não foi executado ou o
   sync não rodou** — não transcreva nada antes de resolver.
6. **Auditoria** `/admin/keeper_audit` → zerar as divergências bloqueantes.
7. Cowork transcreve a sheet **definitiva** no board (times que faltavam).

> Com a urna revelada, o **rollover volta a ser liberado** (o snapshot está congelado; virar a
> season já não perde nada).

### 24/08 — leilão

Board 100% populado e auditado. ⛔ **Abrir o leilão com qualquer time não populado expõe os
keepers desse time** (achado do OFF26-4).

---

## Se algo der errado

- **Revelou cedo / com bilhete errado:** `POST /api/late_drop/admin/replace` com
  `{"reason": "..."}` — re-revela encadeando a trilha (a anterior fica `superseded`, o
  histórico não some). É o mesmo padrão M8 da lottery.
- **Bilhete de jogador que saiu do roster** (trade entre o depósito e o lock): vira **passo com
  aviso** na revelação, automaticamente. Não vira drop fantasma.
- **Estado parcial de teste no banco:** `ensaio_janela_selada.py --reset --backup <path>`
  desfaz janela **e** urna.
- **Último caso:** restaurar o backup com o app parado —
  `sqlite3 /data/dynasty.db ".restore '/data/pre_smoke_urna.db'"`.

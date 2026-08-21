# phantom_board — script de população do board da liga fantasma (OFF26-24, F2a)

Ferramenta operacional **standalone** (fora do app Flask). Comando via DOM (Playwright),
**verdade via API** — o board/toast do Sleeper mente (achado do ensaio de 11/08); um pick
só existe quando aparece em `/v1/draft/{id}/picks`.

⛔ **Guardas de nascença:** só opera na liga fantasma (`1389725099556372481`, hardcoded).
A identidade do board é provada **por construção**: o script deriva o `draft_id` da liga
pela API, navega até ele e confere que **a URL contém o draft_id derivado** — a página do
draft não exibe o nome da liga (mostra "MellowBR's Draft" etc.), então o título é só log.
START DRAFT, RESET DRAFT e **JOIN DRAFT** estão na lista de cliques proibidos do código.

## Instalar (uma vez)

```powershell
pip install playwright
```

**Requisito: Google Chrome instalado** (o navegador normal serve — o script abre o
**Chrome real** via `channel="chrome"`, com o perfil dedicado próprio; seu perfil do dia
a dia não é tocado). Motivo: o hCaptcha do Sleeper **recusa verificar no Chromium de
teste** do Playwright ("Failed to get captcha verification") — no Chrome real o desafio
renderiza e **você** o resolve manualmente no login. Nada no script resolve ou burla
captcha.

## Primeiro login (uma vez)

O script usa um **perfil de navegador dedicado** (`.phantom_board_profile/` dentro desta
pasta — criado no primeiro run; ⛔ nunca o seu Chrome principal). **Fluxo real da primeira
execução:** a janela abre **deslogada** — o board renderiza mesmo assim, como espectador,
com **"JOIN DRAFT" visível** (não clique; o script também nunca clica). O script detecta
isso, pausa e pede: *"logue na janela e pressione Enter"* — faça login no Sleeper **nessa
janela** e dê Enter no terminal. A sessão persiste no perfil; das próximas vezes esse
passo não aparece. Nenhuma credencial entra no código.

## Baixar a keeper sheet (a cada uso)

Logado como admin no Manager, abra e salve como `sheet.json`:

```
https://dynasty-fantasy-manager.onrender.com/api/admin/keeper_sheet_export
```

(É o pacote do `build_sheet` — keepers com sid + owner_id. A sheet JSON comum não os tem.)

## F2b — população por time e campanha completa

```powershell
# um time (a unidade verificável do runbook):
python -m tools.phantom_board.cli populate --sheet sheet.json --team-slot 10

# a campanha (12 times, em ordem de slot):
python -m tools.phantom_board.cli populate --sheet sheet.json --all
```

**Idempotência primeiro** (a lição da F2a): cada keeper é conferido na API **antes** de
qualquer clique — já assentado no time/preço certo = sucesso com zero cliques; divergente
= conflito (aborta o time, decisão humana); ausente = designa. **Retomável por
construção**: rodar de novo continua de onde parou. `bloqueado_teto` é **resultado
esperado** pré-late-drop (AlexTheDawg $203 > budget $200), não erro — e o teto tem
**DUAS caras** (FIX10): a recusa síncrona ("does not have enough budget") e o **clamp
silencioso do input de preço** ao max bid, detectado por **read-back antes do SET
PLAYER**. Ambas pulam **o keeper** (⛔ nada é gravado com preço fora da sheet) e o time
segue. Falha real → aborta O TIME (o que assentou permanece), segue aos demais,
relatório JSON com o placar — a conferência de cada time **nomeia** keepers com preço
divergente ou ausentes do board.

**⚖️ O veredito é da auditoria OFF26-4** — ao fim da campanha, abra `/admin/keeper_audit`
no Manager: ela compara o board vivo com a sheet, classe a classe. A contagem do script
não substitui o juiz.

## O critério de 19/08 — ✅ CUMPRIDO em 12/08/2026 (MAN-OFF26-24-GO)

Ciclo limpo executado com 7 dias de antecedência: RESET → `populate --all`
(`populate_20260812T185453Z`: **12/12 times, 235 designados + 2 `bloqueado_teto` declarados**
— AlexTheDawg, sheet $203 > budget —, 0 falhas, **zero intervenção manual**, Travis Hunter
designado) → **auditoria OFF26-4** (2 divergências = exatamente os 2 bloqueados; zero salário
divergente; 12/12 populados) → **RESET final** (validate pós-reset: 0 picks vivos, 237 na
sheet, draft_id novo derivado). **Decisão do owner: este script é o PLANO A da população real
de 22/08**; o `runbook_cowork_liga_fantasma.md` é a contingência.

## Uso em 22/08 (a população real) — nesta ordem

1. **Conferir a ALOCAÇÃO DE OWNERS** — Draft Settings → DRAFT ORDER na liga fantasma (12
   owners nos slots 1-12). A alocação é **permanente e sobrevive ao RESET DRAFT** (verificado
   em 12/08) — conferir mesmo assim: o `validate` deve reportar o mapa **`via draft_order`**
   (se cair para `slot_to_roster_id×rosters`, a alocação não está feita).
2. Baixar a **sheet DEFINITIVA** (pós-revelação da urna + sync) e rodar
   `python -m tools.phantom_board.cli populate --sheet sheet.json --all`.
3. **Auditoria OFF26-4** em `/admin/keeper_audit` — o juiz independente do board populado.
4. ⛔ **Não tocar, em hipótese alguma:** **RANDOMIZE** e **RESET BUDGETS** (tela de Draft
   Settings — RANDOMIZE embaralharia os owners sob board populado) e **START DRAFT**. O script
   não abre essa tela; a proibição é para o HUMANO na janela.

## Roteiro de validação da F2a (nesta ordem)

**1 — Validação read-only** (zero browser, zero escrita) — confere os 18 picks do ensaio:

```powershell
python -m tools.phantom_board.cli validate --sheet sheet.json
```

Esperado: 18 casados no MellowBR, total **$176**, zero divergências de salário/owner.

**2 — Probe** (uma vez): anotar o seletor da célula do board — o único que o relatório
resumido do ensaio não fixou. Abre o board com o Playwright Inspector; inspecione uma
célula vazia, copie a classe e cole em `config.py` → `BOARD_CELL_SELECTOR`:

```powershell
python -m tools.phantom_board.cli probe
```

**3 — Designação única** (a prova da fatia) — um keeper de **outro** time (não MellowBR,
que está cheio), escolhido na hora da sheet provisória:

```powershell
python -m tools.phantom_board.cli designate --sheet sheet.json --player "Nome Exato"
```

O preço default é o salário da sheet; o slot do time é derivado do owner do keeper.
Esperado: `assentado (confirmado na API, não no board)` — e o jogador aparece no board
após **reload** da página (o board vivo pode não atualizar sozinho; é o dessync
conhecido).

**4 — Guarda de liga:** para conferir o abort, edite temporariamente `LEAGUE_ID` no
`config.py` para outro id e rode o `validate` — deve recusar **antes de qualquer coisa**
com `⛔ GUARDA DE LIGA`. Desfaça a edição.

## Se o wrapper do modal mudar (abort "não achei o container do modal")

O modal de manual pick é localizado por estrutura: o menor ancestral do botão
"Assign a player"/"SET PLAYER" que contém o input de busca. Se o Sleeper mudar esse DOM,
rode o `probe`, abra o menu Set Player numa célula manualmente, e no Inspector examine o
ancestral comum do input de busca e do botão — ajuste o xpath em `board._modal` se preciso.

## Se o abort disser "o menu é de OUTRO time" (FIX12, 21/08)

O menu de contexto nomeia a coluna de **duas** formas, e a liga alterna entre elas sem
aviso: o genérico `Manually set a player for Team {N}` e o **nome do owner**
(`...for rafadgil`), que é o que a fantasma exibe desde que o `metadata` do draft ganhou
`show_team_names: "0"`. O script aceita os dois, com **casamento exato** contra o handle do
slot (o mesmo do `draft_order`) ou contra `Team {N}` — ⛔ nunca substring.

O abort traz **o rótulo visto × os esperados**, e toda designação registra o evento
`menu_rotulo` no relatório JSON. Se o formato mudar de novo, é ali que aparece: compare
`rotulos_observados` com `esperados` antes de mexer em qualquer seletor. O item
`Reset Nomination / Change nominator to <owner>` carrega o mesmo nome e **nunca** é lido
como designação.

⛔ **Escape não fecha o menu de contexto do Sleeper.** Quem fecha é o clique no
`.context-menu-underlay` — sem isso, o menu de um abort intercepta os cliques dos times
seguintes e derruba a campanha em cascata (medido em 21/08: 4 times com `TimeoutError` de
30s por uma causa que não era deles).

## Falhas

Qualquer mismatch **aborta barulhento**: screenshot + trace (`runs/abort.png`,
`runs/trace.zip`) + relatório JSON (`runs/designate_*.json`). O toast vermelho do Sleeper
("This pick could not be processed") **não é veredito** — só a API. Timeout sem assentar →
1 re-comando automático (o servidor rejeita duplicata — é seguro); segundo timeout →
aborta.

## Fronteiras (F1 do OFF26-24)

- A auditoria pré-leilão segue do OFF26-4 — o script a usa como verificador, não a replica.
- Quando popular é decisão do runbook/calendário — o script executa.
- O Manager só é **lido** (o arquivo da sheet). Nenhuma escrita fora da liga fantasma.

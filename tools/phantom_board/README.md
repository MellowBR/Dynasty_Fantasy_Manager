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

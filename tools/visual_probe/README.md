# visual_probe — sonda de validação visual (item O7)

Mede **layout renderizado** (Chromium via Playwright), que é o que nenhuma suíte de
unidade e nenhuma leitura de HTML alcançam.

```bash
python tools/visual_probe/cli.py            # suíte completa (~20s) — exit ≠ 0 em achado NOVO
python tools/visual_probe/cli.py --list     # cobertura, larguras e os motivos de cada uma
python tools/visual_probe/cli.py --page league --width 1280
python tools/visual_probe/cli.py --keep     # preserva HTML + screenshots do run
```

## Por que ela existe

Na saga do **L3** (13/08/2026) **três gerações de validação queimaram num dia**, cada uma
nascida de um defeito que a anterior **aprovou**:

| Geração | Mediu | Deixou passar |
|---|---|---|
| regex sobre HTML | valores, payloads, queries | **layout** — aprovou 12 cards com o texto **sobreposto** |
| geometria | colisão, transbordo, overflow | **uniformidade** — anatomias diferentes entre cards vizinhos |
| assinatura de anatomia | estrutura repetida entre N irmãos | — |

## As duas famílias de verificação

- **Geometria** — colisão entre caixas de texto **não-aninhadas**, transbordo para fora
  do container e overflow horizontal do documento (**com o elemento culpado nomeado**,
  que é o que distingue tabela larga pré-existente de defeito novo).
- **Anatomia** — assinatura `classe@topo` de cada linha, comparada entre irmãos.
  ⚠️ O `left` **não** entra na assinatura: ele varia com a largura do **texto**
  (`$5/$200` × `$180/$200`) — isso é dado, não anatomia. Alinhamento de coluna é
  verificação separada.

## Cobertura — o critério decide a lista

- **Anatomia** só onde houver **N irmãos gerados pelo MESMO loop de template, em layout
  LIVRE (flex/grid), que DEVEM parecer idênticos**.
  ⛔ Tabela não entra (`<table>` alinha por construção). ⛔ Irmão que pode divergir
  legitimamente não entra — é por isso que a matriz do `/picks` fica só na geometria
  (célula vazia × preenchida × trocada divergem de propósito).
- **Geometria** em superfície densa de instância única. A **navbar vive no `base.html`**,
  então é medida em toda página, de brinde.
- **Fora de alcance do modelo atual:** páginas cujo conteúdo principal é montado por
  `fetch` — `/cap_projector` (3 fetches) e `/trades` (9). O serviço é `file://` sobre
  HTML salvo; cobri-las exige servidor efêmero. Medido, não suposto — e registrado aqui
  em vez de silenciado.

`--list` imprime a cobertura vigente e a justificativa de cada largura.

## ⭐ `--css` — o controle positivo (não é enfeite)

```bash
git show <rev>:static/style.css > /tmp/antigo.css
python tools/visual_probe/cli.py --css /tmp/antigo.css --page league
```

Troca **só a folha de estilo** e roda a **mesma página**. Serve para provar que o
instrumento **enxerga** o defeito antes de o verde dele valer alguma coisa.

> **A regra que pagou caro:** um detector que só sabe dizer "não" precisa de controle
> positivo. Durante o L3, um poller sem controle deu **falso TIMEOUT de 10 minutos**
> sobre um deploy que já estava no ar.

Demonstração registrada (13/08/2026), contra o CSS pré-FIX-UX (`478b915`):

| | exit | 1280px | 1024px |
|---|---|---|---|
| CSS atual | **0** | 0 achados | 0 achados |
| CSS pré-FIX-UX (controle) | **1** | **37 colisões** | **26 colisões** |

Entre elas, o sintoma literal do screenshot do owner: `"PROV" x "PROV"` (as duas tags
empilhadas) e o rótulo do bid sobre o item de cap.

## Defeito conhecido × regressão nova

`core.KNOWN_DEFECTS` registra dívida **já rastreada no backlog**:

- achado que **casa** uma entrada → **reportado, não bloqueia**;
- achado que **não casa** → **novo, bloqueia** (`exit 1`);
- entrada que **não reproduz** → avisada em voz alta (defeito corrigido: remover daqui).

O casamento exige tipo + página + largura **e** que os culpados sejam **subconjunto** dos
registrados: se um elemento novo entra na conta, deixou de ser o defeito conhecido e
volta a bloquear. ⛔ Entrada aqui **exige item no backlog** — é registro de dívida, não
tapete.

Hoje há **um**: `UX16` (transbordo da navbar a ~860px, em toda página).

## Perfil de execução

**Sem app de pé** (test client) · **sem login real** (cookie de sessão injetado) ·
**sem rede** (`run_sync` neutralizado) · **sem estado** (o banco é **copiado** para um
diretório temporário e é essa cópia que o app abre via `DYNASTY_DB` — o `dynasty.db` real
nunca é aberto para escrita). Custo medido: **~20s** a suíte completa (4 páginas × 4
larguras).

⛔ **Sem Playwright/Chromium a sonda ABORTA (`exit 2`) — nunca "passa".** Instalar com
`pip install playwright && playwright install chromium`.

## Limites declarados

- Mede o **estado padrão** da página: estados revelados por `:hover` ficam fora (o filtro
  de `opacity: 0` / `visibility: hidden` existe porque o `.pick-edit-btn` invisível
  produzia 2 "colisões" a 390px que ninguém vê).
- Avatares e fotos remotas não carregam sob `file://` — têm `onerror` que os esconde, o
  mesmo caminho de um avatar ausente em produção.
- Anatomia com menos de 2 irmãos **não prova nada** e é reportada como `n/a` — ausência
  de cobertura, não aprovação.

## Testes

`python visual_probe_test.py` (28) exercita o **núcleo puro**: classificação
novo × conhecido, exit code, detecção de anatomia divergente, integridade da config e as
guardas do instrumento (o `--css` existe, a sonda não degrada para verde sem browser,
roda sobre cópia do banco, ignora pares aninhados, nomeia o culpado do overflow).

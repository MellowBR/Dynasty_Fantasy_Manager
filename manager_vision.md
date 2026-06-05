# vision.md — Fantasy Manager

> Escrito em: Março 2026  
> Propósito: motivação e casos de uso reais do projeto

---

## Por que existe

A Dynasty SB é uma liga de salary cap com 12 owners, contratos de 4 anos, valorização
anual baseada em valores ESPN, e um workflow de offseason com 7 passos obrigatórios.

Antes do Manager, tudo isso vivia numa planilha compartilhada. O problema não é a
planilha em si — é que a planilha não tem memória, não tem audit trail, e não impede
que dois owners editem ao mesmo tempo. Com salary cap, um erro de $3 num contrato
pode quebrar o planejamento de um time inteiro para a temporada.

O Manager resolve três coisas que a planilha não consegue:

**1. Fonte de verdade única**
`dynasty.db` é o único lugar onde salários, contratos e picks existem. O Optimizer
e o Predictor leem daqui, nunca escrevem. Se o Manager diz que um jogador ganha $18,
ele ganha $18 — não há versão alternativa numa aba diferente.

**2. Regras não são memorização**
A VALORIZAÇÃO, a exceção Waiver/FA do ano 2, a renovação após ano 4, o draft budget
mínimo — são regras com cálculo. O `salary_engine.py` executa essas regras de forma
determinística e tem unit tests. Nenhum owner precisa lembrar se `floor(0.8 × ESPN × 1.2)`
se aplica no ano 2 ou no ano 3 de um waiver.

**3. Acesso real dos 12 owners**
Com a migração para hosting compartilhado (PythonAnywhere → Render, X1), qualquer owner pode consultar o estado da liga
sem precisar perguntar pro comissário. Cap de cada time, contratos por expirar, picks
disponíveis — tudo acessível por qualquer pessoa com conta cadastrada.

---

## O que o Manager não é

O Manager não faz análise. Ele não diz se um trade é bom ou ruim, não ranqueia
jogadores por valor, não sugere keepers. Essas perguntas são papel do Fantasy Optimizer.

O Manager não prevê breakouts. Esse é papel do Predictor.

A separação é intencional: o Manager é um sistema de registro, não um sistema de decisão.
Misturar os dois criaria acoplamento frágil e responsabilidades confusas.

---

## Casos de uso reais

**Antes do draft de início de temporada:**
O comissário roda o ESPN PDF import, aplica o season rollover, e cada owner consulta
o cap projector para decidir quais jogadores manter. O Manager calcula automaticamente
o novo salário de cada keeper e projeta o draft budget disponível.

**Durante a temporada (trades):**
Dois owners combinam uma troca. Um deles abre o simulador de trade, confere o cap impact
dos dois lados antes de confirmar, e registra a troca. O estado do `dynasty.db` é
atualizado instantaneamente para o Optimizer ler na próxima análise.

**Offseason (draft lottery):**
O comissário executa o draft lottery com os pesos definidos no regulamento. O Manager
sorteia, registra o resultado, e a ordem do Round 1 passa a refletir o sorteio
(os Rounds 2 e 3 seguem standings invertidos) — sem necessidade de manter isso
manualmente numa planilha paralela.

**Consulta cotidiana:**
Qualquer owner acessa `/` e vê o roster atual do time dele: salários, anos de contrato,
slots de IR, cap utilizado. Sem precisar abrir o Sleeper ou perguntar pro comissário.

---

## Calendário Operacional da Liga

O Manager é apenas uma das peças do fluxo. A Dynasty SB opera em ciclo anual,
alternando entre o Manager (sistema de registro local) e o Sleeper (plataforma
onde os times efetivamente jogam). Conhecer a ordem importa porque alguns passos
dependem de outros, e um passo pulado ou feito fora de ordem deixa o estado da
liga inconsistente.

O ciclo do offseason começa com a **atualização dos valores ESPN** no Manager —
sem ESPN atualizado, a VALORIZAÇÃO aplicada no season rollover usa referências do
ano anterior e produz salários errados. Em seguida o comissário roda o **draft
lottery** no Manager, que sorteia os picks 1 a 6 do Round 1 (pesos por posição
final na temporada anterior, incluindo o 7º colocado com 1 bolinha — M15) e fixa
os picks 7 a 12 por standings. O sorteio define **apenas** o Round 1; os Rounds 2
e 3 seguem standings invertidos (12º abre, campeão fecha — M16). O **rookie
draft** acontece no Manager em seguida — é lá que os contratos dos novatos são
criados pela primeira vez.

Depois disso o foco muda para o Sleeper: **owners têm um prazo para fazer drops
e adequar o roster ao cap**, e o comissário **atualiza os rosters no Sleeper e
cria a liga fantasma de FA Auction**. O **FA Auction** em si roda dentro do
Sleeper (na liga fantasma), que serve só como ambiente de lances. Terminado o
leilão, **os resultados precisam ser registrados manualmente no Manager pela
tela `/auction`** — cada bid vencedor vira um contrato. Este é o passo que mais
concentra risco operacional: é a única etapa onde o comissário digita os dados,
e um erro aqui propaga cap errado para o resto da temporada.

Durante a temporada regular, **trades e movimentações feitas no Sleeper são
capturadas automaticamente pelo Manager** via o sync (camada S1, concluída em
22/04/2026). O Manager roda o sync periodicamente, detecta trades completas e
waivers, e atualiza `Player.team_id`, `PlayerHistory` e a tabela `Trade` sem
intervenção humana. Antes do S1, o Manager ficava cego para movimentações do
Sleeper e precisava de confirmação manual de trade por tela — agora a
confirmação é automática.

**Gap conhecido — standings não são sincronizados automaticamente.** A posição
final dos times (W-L-PF, ranking da temporada regular, campeão e vice) é input
manual no Manager hoje. O Sleeper tem esse dado acessível via
`/league/<id>/winners_bracket` e pelo roster settings da própria liga, mas o
sync atual não consome esses endpoints — é uma automação possível no futuro,
análoga em padrão ao S1. Enquanto isso, o comissário digita standings antes de
rodar o draft lottery.

**Observação histórica.** O Manager não existia no início da liga — a Dynasty
SB rodou sua primeira temporada com controle em planilha compartilhada. O
calendário acima é o estado atual, com o Manager operacional e a migração da
planilha já concluída. O retrofit da história de contratos anteriores à
existência do Manager foi feito via F8 (rebuild canônico a partir da Sleeper
chain 2024 → 2025 → 2026), em 22/04/2026.

---

## Resultado

O Manager existe para que a liga funcione com as suas próprias regras, de forma
transparente para os 12 owners, sem depender da memória ou disponibilidade do comissário.

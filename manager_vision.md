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
sorteia, registra o resultado, e a ordem do Round 1 passa a refletir o sorteio — sem
necessidade de manter isso manualmente numa planilha paralela.

**Consulta cotidiana:**
Qualquer owner acessa `/` e vê o roster atual do time dele: salários, anos de contrato,
slots de IR, cap utilizado. Sem precisar abrir o Sleeper ou perguntar pro comissário.

---

## Resultado

O Manager existe para que a liga funcione com as suas próprias regras, de forma
transparente para os 12 owners, sem depender da memória ou disponibilidade do comissário.

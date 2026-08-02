"""
board_mirror.py — S2: desconto da permutação administrativa do board do Sleeper.

## O problema

O Sleeper suporta **uma ordem única de draft** para todos os rounds, enquanto o
Manager modela **R1 = lottery** e **R2/R3 = standings invertido** (M16). Para o board
do Sleeper exibir a ordem certa no R1, o co-admin **permuta picks** na UI do Sleeper
(ferramenta de comissário, que altera `/traded_picks` **sem gerar transação**).

Essa permutação é um **artefato operacional**, não uma trade. Ingeri-la como
titularidade real corrompe o dono das picks no Manager — o item S2.

## A álgebra

Sejam, para a draft season:

    L(p) = time sorteado para a posição p          (DraftLotteryResult)
    S(p) = time do slot p no board do Sleeper      (standings invertido)
    O(t) = dono canônico da pick própria de t      (só trades reais)

A montagem estabelece, para todo p:  `dono_sleeper(pick de S(p)) = O(L(p))`.
O Manager projeta a posição pelo lottery, então exibe `O(L(π(p)))` com **π = S⁻¹∘L**
— errado exatamente onde π não é identidade.

**O desconto** re-chaveia a entrada de `/traded_picks`: o time original `x` vira
`L(S⁻¹(x))`. Isso **aniquila a ficção**: os movimentos puramente administrativos
viram no-ops (`pick de X → X`) e as trades **reais** da janela são **re-rotuladas
sozinhas** para o ativo que de fato mudou de mão (o direito de escolher naquela
posição). Não há tabela de permutação — π é derivado das fontes canônicas.

## Armamento — por temporada, explícito, com dois gates

`AppConfig["board_mirrored_season"]` guarda a **draft season** armada (ex.: "2026"),
não um booleano. Duas razões:

1. **O rollover desarma sozinho.** Ele avança `current_season`, logo `draft_season`
   muda e o valor guardado deixa de casar. Um booleano sobreviveria ao rollover e
   dispararia o desconto no ano seguinte, sobre um board ainda não montado —
   produzindo rótulos errados **com aparência de corretos**, que é pior que o bug.
2. É auditável e auto-documentado no `/admin`.

Gate 2: só opera se houver **audit canônica de lottery** para essa draft season —
sem sorteio canônico não existe L, e portanto não existe π.

**Por que toggle explícito e não detecção automática:** a montagem não deixa rastro
nenhum (não é transação). Inferi-la dos dados significaria adivinhar intenção a
partir de ausência de evidência, e uma montagem **parcial** ingerida com o desconto
ligado geraria corrupção silenciosa. O ato explícito de quem executou a montagem é
o único sinal honesto. O item futuro S2-F2-3 fecha o laço fazendo o Manager
**prescrever** a permutação — aí ele passa a saber o que vai ler de volta.

## Escopo

Estritamente **R1 da draft season armada**. R2/R3, temporadas futuras e movimentação
de jogadores não são tocados — fora desse recorte, `apply()` é a identidade.
"""

from models import (DraftLotteryResult, SeasonStandings, LotteryAudit,
                    get_config, set_config, get_current_season)

BOARD_MIRROR_KEY = "board_mirrored_season"


def get_mirrored_season():
    """Draft season armada em AppConfig, ou None. Não valida os gates."""
    raw = (get_config(BOARD_MIRROR_KEY, "") or "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def set_mirrored_season(season):
    """Arma (season int) ou desarma (None) o desconto. Fonte única: `set_config`."""
    value = "" if season is None else str(int(season))
    set_config(BOARD_MIRROR_KEY, value)
    return value


def _lottery_order(draft_season):
    """{pick_number: team_id} do R1 canônico. Fonte: DraftLotteryResult."""
    rows = DraftLotteryResult.query.filter_by(season=draft_season).all()
    return {r.pick_number: r.team_id for r in rows if r.team_id}


def _board_order(draft_season):
    """{slot: team_id} do board do Sleeper = standings invertido da season anterior.

    Deriva da MESMA fonte única do M15/M16 (`_build_default_draft_order`) usada pela
    projeção — não reimplementa a ordem por standings nem hardcoda nada.
    """
    from routes.offseason import _build_default_draft_order
    standings = (SeasonStandings.query.filter_by(season=draft_season - 1)
                 .order_by(SeasonStandings.rank).all())
    if not standings:
        return {}
    return {pick_num: team_id
            for pick_num, team_id, _name in _build_default_draft_order(standings)
            if team_id}


def build_permutation(draft_season):
    """
    π sobre ids: {team_id_do_slot_no_board: team_id_sorteado_para_a_posição}.

    Retorna {} se faltar qualquer das duas ordens ou se o resultado não for uma
    **bijeção** — colisão significa board meio-montado ou dado inconsistente, e nesse
    caso descontar produziria rótulos errados com cara de certos. Melhor não descontar.
    """
    L = _lottery_order(draft_season)
    S = _board_order(draft_season)
    if not L or not S:
        return {}
    perm = {S[p]: L[p] for p in S if p in L}
    if len(perm) != len(S) or len(set(perm.values())) != len(perm):
        return {}
    return perm


class BoardDiscount:
    """Desconto pronto para uso, computado uma vez por sync."""

    def __init__(self, draft_season=None, perm=None, teams_by_id=None, reason=""):
        self.draft_season = draft_season
        self.perm = perm or {}
        self.teams_by_id = teams_by_id or {}
        self.reason = reason
        self.applied = 0

    @property
    def active(self):
        return bool(self.draft_season and self.perm)

    def apply(self, season, round_num, orig_team):
        """
        Re-chaveia o time original de uma entrada de pick. Identidade fora do escopo
        (desarmado, season != draft season armada, round != 1, time desconhecido).
        """
        if not self.active or orig_team is None:
            return orig_team
        try:
            if int(season) != self.draft_season or int(round_num) != 1:
                return orig_team
        except (TypeError, ValueError):
            return orig_team
        target_id = self.perm.get(orig_team.id)
        if not target_id or target_id == orig_team.id:
            return orig_team
        target = self.teams_by_id.get(target_id)
        if target is None:
            return orig_team
        self.applied += 1
        return target


def load_board_discount(teams):
    """
    Monta o BoardDiscount do sync corrente a partir dos dois gates.
    `teams` = lista de Team já carregada pelo sync (evita query extra).
    """
    season = get_mirrored_season()
    if not season:
        return BoardDiscount(reason="desarmado")
    if season != get_current_season() + 1:
        # rollover já passou (ou armaram uma season que não é a do draft corrente)
        return BoardDiscount(reason=f"season armada {season} != draft season "
                                    f"{get_current_season() + 1}")
    if not LotteryAudit.query.filter_by(season=season, is_canonical=True).first():
        return BoardDiscount(reason=f"sem audit canônica de lottery p/ {season}")
    perm = build_permutation(season)
    if not perm:
        return BoardDiscount(reason=f"permutação indisponível/não-bijetiva p/ {season}")
    return BoardDiscount(draft_season=season, perm=perm,
                         teams_by_id={t.id: t for t in teams})

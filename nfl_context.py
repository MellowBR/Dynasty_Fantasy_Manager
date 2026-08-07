"""
nfl_context.py — O2 Batch 1: contexto NFL do jogador (idade + depth chart) derivado do POOL.

Mesma separação do salary_engine: NÚCLEO PURO (build_slim_index / compute_age /
build_depth_chart / assemble_context — sem DB, sem rede, sem filesystem; é o que
nfl_context_test.py exercita) + camada de IO (leitura do cache do pool do Sleeper).

Decisões de desenho (spec: seção O2 do improvements.md, F1 do MAN-O2-F1 + Q2 da UX12-F1):

⛔ NENHUMA coluna nova. O depth chart pede os RIVAIS de posição do time NFL, que em geral
   NÃO são Players do DB local (~280 rosterados vs ~12k no pool) — persistir
   `depth_chart_order` no Player não montaria o chart. Deriva-se do pool, sempre.

⛔ O caminho de PÁGINA nunca faz rede. `_get_index()` lê o arquivo de cache do pool
   (caminho único de `sync_sleeper._player_cache_path` — F13: dirname(DYNASTY_DB),
   carimbo `fetched_at` DENTRO do arquivo) e NÃO dispara download: pool ausente →
   contexto vazio, página renderiza sem o bloco (degradação explícita da spec). Quem
   renova o pool é o sync (TTL 168h). Pool VENCIDO ainda serve (stale-while-usable):
   depth chart de 8 dias > bloco sumindo — o staleness já é ressalva registrada na
   seção O2 (janela de trades NFL out–nov).

Nenhum cache NOVO em disco: o índice enxuto vive em memória de processo, invalidado por
(mtime, size) do arquivo do pool — mtime aqui é só chave de invalidação (rebuild espúrio
pós-deploy é inócuo), nunca critério de validade, que segue sendo o carimbo interno (F13).
"""

import json
import os
from datetime import date, datetime

# Posições com depth chart utilizável no pool (F1 de 28/04: DEF = 0% de cobertura;
# entradas de DEF nem têm os campos — o bloco degrada sozinho, isto é documentação).
_POS_NORMALIZE = {"DST": "DEF", "D/ST": "DEF"}

# Campos do pool que o índice enxuto preserva (o resto dos ~40 campos/entrada é descartado
# para não segurar o pool inteiro em memória).
_SLIM_FIELDS = ("full_name", "team", "position", "depth_chart_position",
                "depth_chart_order", "birth_date", "age")


# ── Núcleo puro ──────────────────────────────────────────────────────────────

def normalize_position(pos):
    """DST/D/ST → DEF (mesma normalização do roster). Demais posições passam intactas."""
    return _POS_NORMALIZE.get(pos, pos)


def build_slim_index(pool: dict) -> dict:
    """Reduz o pool cru {sid: {...~40 campos}} ao índice enxuto {sid: {..._SLIM_FIELDS}}.

    Mantém só entradas dict com `position` (o pool tem lixo estrutural). Puro."""
    index = {}
    for sid, info in (pool or {}).items():
        if not isinstance(info, dict) or not info.get("position"):
            continue
        index[sid] = {f: info.get(f) for f in _SLIM_FIELDS}
    return index


def compute_age(birth_date, today):
    """Idade em anos completos a partir de `birth_date` ('YYYY-MM-DD') e `today` (date).

    `today` é parâmetro (não date.today()) para o núcleo ficar puro/testável.
    Retorna None para birth_date ausente/ilegível — nunca levanta."""
    if not birth_date:
        return None
    try:
        b = datetime.strptime(str(birth_date), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def build_depth_chart(index: dict, team, position, self_sid=None):
    """Lista o depth chart de `position` em `team` a partir do índice enxuto.

    Só entra quem tem `depth_chart_order` (os ~25% sem o campo ficam de fora — spec:
    degradação sem erro). Ordena por (order, nome). Cada linha: sid, name, order,
    depth_chart_position e is_self (match por sid — nunca por nome; há dois DJ Moore
    no pool). Puro."""
    if not team or not position:
        return []
    position = normalize_position(position)
    rows = []
    for sid, info in index.items():
        if info.get("team") != team:
            continue
        if normalize_position(info.get("position")) != position:
            continue
        order = info.get("depth_chart_order")
        if order is None:
            continue
        rows.append({
            "sid": sid,
            "name": info.get("full_name") or sid,
            "order": order,
            "depth_chart_position": info.get("depth_chart_position") or "",
            "is_self": (self_sid is not None and sid == self_sid),
        })
    rows.sort(key=lambda r: (r["order"], r["name"]))
    return rows


def assemble_context(index: dict, sleeper_player_id, today):
    """Monta o contexto NFL de um jogador: idade + depth chart do time dele NO POOL.

    O time/posição do CHART vêm da entrada do próprio jogador no pool (autoridade do
    depth chart), não de Player.nfl_team — se divergirem, é o staleness já documentado.
    Jogador fora do pool → contexto vazio (página renderiza sem os dados, sem erro). Puro."""
    empty = {"age": None, "depth_chart": [], "team": None, "position": None,
             "in_chart": False}
    if not sleeper_player_id:
        return empty
    info = index.get(str(sleeper_player_id))
    if not info:
        return empty
    team = info.get("team")
    position = normalize_position(info.get("position"))
    chart = build_depth_chart(index, team, position, self_sid=str(sleeper_player_id))
    return {
        "age": compute_age(info.get("birth_date"), today),
        "depth_chart": chart,
        "team": team,
        "position": position,
        "in_chart": any(r["is_self"] for r in chart),
    }


# ── IO: leitura do cache do pool (sem rede, sem download) ────────────────────

_index_cache = {"key": None, "index": {}}


def _read_pool_file():
    """Lê o arquivo do pool no caminho único do F13. Envelope novo ({fetched_at, players})
    ou formato antigo (dict cru) — ambos servem para LEITURA (a validade por carimbo é
    regra de refresh do sync, não de consumo). Ausente/ilegível → {} (degradação)."""
    from sync_sleeper import _player_cache_path
    path = _player_cache_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    if isinstance(raw, dict) and "players" in raw and isinstance(raw["players"], dict):
        return raw["players"]
    return raw if isinstance(raw, dict) else {}


def _get_index():
    """Índice enxuto memoizado por processo; invalidado por (mtime, size) do arquivo
    (chave de invalidação barata — rebuild espúrio é inócuo; validade real = carimbo,
    responsabilidade do sync)."""
    from sync_sleeper import _player_cache_path
    path = _player_cache_path()
    try:
        st = os.stat(path)
        key = (st.st_mtime_ns, st.st_size)
    except OSError:
        _index_cache["key"], _index_cache["index"] = None, {}
        return {}
    if _index_cache["key"] != key:
        _index_cache["index"] = build_slim_index(_read_pool_file())
        _index_cache["key"] = key
    return _index_cache["index"]


def get_player_nfl_context(sleeper_player_id):
    """Porta única para a rota (routes/roster.py:player_detail). Nunca levanta."""
    try:
        return assemble_context(_get_index(), sleeper_player_id, date.today())
    except Exception:
        return {"age": None, "depth_chart": [], "team": None, "position": None,
                "in_chart": False}

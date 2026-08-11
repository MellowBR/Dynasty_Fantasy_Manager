"""
sleeper_api.py — camada de VERDADE do script (OFF26-24): API pública do Sleeper,
read-only, `/v1/...` documentada. ⛔ A API interna não documentada segue vetada —
este módulo só usa os endpoints públicos (o mesmo caminho D1 do OFF26-4).
"""

import requests

from .config import LEAGUE_ID, SLEEPER_API


def _get(url: str, timeout: int = 15):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_league(league_id: str = LEAGUE_ID) -> dict:
    return _get(f"{SLEEPER_API}/league/{league_id}") or {}


def fetch_draft_id(league_id: str = LEAGUE_ID) -> str:
    """⛔ O draft_id muda a cada RESET DRAFT — derivado a cada uso do objeto da liga
    (1 request), nunca persistido nem reaproveitado (regra D1 do OFF26-4)."""
    return str(fetch_league(league_id).get("draft_id") or "")


def fetch_draft(draft_id: str) -> dict:
    return _get(f"{SLEEPER_API}/draft/{draft_id}") or {}


def fetch_picks(draft_id: str) -> list:
    """A fonte do assentamento: o pick só existe quando aparece AQUI (lag ~3s;
    o board e o toast não são veredito)."""
    return _get(f"{SLEEPER_API}/draft/{draft_id}/picks") or []


def fetch_users(league_id: str = LEAGUE_ID) -> list:
    return _get(f"{SLEEPER_API}/league/{league_id}/users") or []


def fetch_rosters(league_id: str = LEAGUE_ID) -> list:
    """FIX3 — insumo do fallback (b) do mapa slot↔owner (roster_id → owner_id)."""
    return _get(f"{SLEEPER_API}/league/{league_id}/rosters") or []

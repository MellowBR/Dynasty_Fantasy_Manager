"""
player_lookup.py — Centralized player name matching.

Prevents the "3 Browns" bug by NEVER matching on partial name / substring.
All matching is full-name only, with progressive normalization.

Priority order:
  1. sleeper_player_id (exact, preferred when available)
  2. Exact name match (case-sensitive)
  3. Case-insensitive match
  4. Normalized match (strip accents, apostrophes, hyphens, dots, suffixes)
  5. None — never falls back to partial / substring / last-name matching

Usage:
  from player_lookup import find_player_by_name, find_player_by_sleeper_id
"""

import logging
import re
import unicodedata

from models import Player

log = logging.getLogger(__name__)

_SUFFIX_RE = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv|v)$", re.IGNORECASE)


def _normalize(name: str) -> str:
    """
    Normalize a name for fuzzy matching:
      - lowercase
      - strip leading/trailing whitespace
      - normalize unicode (NFD → strip accents → NFC)
      - remove apostrophes, hyphens, dots
      - remove suffixes (Jr, Sr, II-V)
      - collapse whitespace
    """
    n = name.lower().strip()
    # Decompose unicode, strip combining marks (accents), recompose
    n = unicodedata.normalize("NFD", n)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = unicodedata.normalize("NFC", n)
    # Remove punctuation that varies between sources
    n = re.sub(r"[''`'.\-]", "", n)
    # Remove common suffixes
    n = _SUFFIX_RE.sub("", n)
    # Collapse whitespace
    n = re.sub(r"\s+", " ", n).strip()
    return n


def find_player_by_sleeper_id(sleeper_id: str) -> Player | None:
    """Find a player by their Sleeper player ID. Always preferred when available."""
    if not sleeper_id:
        return None
    return Player.query.filter_by(
        sleeper_player_id=str(sleeper_id), is_dropped=False
    ).first()


def find_player_by_name(
    name: str,
    *,
    strict: bool = False,
    team_id: int | None = None,
    position: str | None = None,
) -> Player | None:
    """
    Find a player by full name with progressive normalization.

    Args:
        name: Player name to search for.
        strict: If True, only accept exact case-sensitive match.
        team_id: Optional — restrict to a specific team.
        position: Optional — restrict to a specific position.

    Returns:
        Player or None. NEVER matches on partial/substring names.
    """
    if not name or not name.strip():
        return None

    name = name.strip()

    # Build base query filters
    filters = [Player.is_dropped == False]
    if team_id is not None:
        filters.append(Player.team_id == team_id)
    if position:
        filters.append(Player.position == position.upper())

    base = Player.query.filter(*filters)

    # Step 1: Exact match (case-sensitive)
    p = base.filter(Player.name == name).first()
    if p:
        return p

    if strict:
        return None

    # Step 2: Case-insensitive match (full name, no wildcards)
    p = base.filter(Player.name.ilike(name)).first()
    if p:
        log.info("Player match (case-insensitive): '%s' → '%s'", name, p.name)
        return p

    # Step 3: Normalized match
    search_norm = _normalize(name)
    if not search_norm:
        return None

    candidates = base.all()
    for c in candidates:
        if _normalize(c.name) == search_norm:
            log.info("Player match (normalized): '%s' → '%s'", name, c.name)
            return c

    # No match found — do NOT try partial/substring matching
    return None


def find_player(
    name: str | None = None,
    sleeper_id: str | None = None,
    *,
    strict: bool = False,
    team_id: int | None = None,
    position: str | None = None,
) -> Player | None:
    """
    Unified lookup: tries sleeper_id first, then name.

    This is the recommended entry point for all player resolution.
    """
    if sleeper_id:
        p = find_player_by_sleeper_id(sleeper_id)
        if p:
            return p

    if name:
        return find_player_by_name(
            name, strict=strict, team_id=team_id, position=position
        )

    return None

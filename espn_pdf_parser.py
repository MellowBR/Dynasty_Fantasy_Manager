"""
espn_pdf_parser.py — Parse ESPN PPR rankings PDF and match to local DB players.

The ESPN PDF has 4 columns (1-80, 81-160, 161-240, 241-300) interleaved.
Each player appears as a group of lines:
  - Rank line: "N. (PosRank)" or "N. (PosRank) Name, TEAM"
  - Name line: "Name, TEAM" (only if not in rank line)
  - Value line: "$XX" or "$XX Bye"

Values are for 10-team leagues. We multiply by 1.2 for 12-team adjustment.
"""

import io
import re
import difflib
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

# ── Name normalization ───────────────────────────────────────────────────────

_SUFFIX_RE = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv|v)$", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[.'\-']")


def _norm(name: str) -> str:
    """Normalize name for matching: lowercase, strip suffixes and punctuation."""
    n = name.lower().strip()
    n = _PUNCT_RE.sub("", n)
    n = _SUFFIX_RE.sub("", n)
    return re.sub(r"\s+", " ", n).strip()


# ── PDF parsing ──────────────────────────────────────────────────────────────

_RANK_RE = re.compile(r"^(\d+)\.\s+\(([A-Z]+\d+)\)(?:\s+(.+),\s+([A-Z]{2,4}))?\s*$")
_NAME_RE = re.compile(r"^([A-Z][a-zA-Z'.  \-]+(?:\s(?:Jr\.|Sr\.|III|II|IV|V))?),\s+([A-Z]{2,4})\s*$")
_VAL_RE = re.compile(r"^\$(\d+)(?:\s+(\d+))?\s*$")
_POS_RE = re.compile(r"([A-Z]+)")


def parse_pdf_bytes(pdf_bytes: bytes) -> list[dict]:
    """
    Parse ESPN PPR rankings from PDF bytes.
    Returns list of {rank, name, position, nfl_team, espn_raw, espn_adjusted}.
    """
    laparams = LAParams(line_margin=0.3, word_margin=0.1, boxes_flow=None)
    text = extract_text(io.BytesIO(pdf_bytes), laparams=laparams)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # State machine: process line by line, collecting player entries
    results = []
    pending_rank = None  # waiting for name and/or value
    pending_name = None  # from rank line or name line
    pending_team = None
    pending_pos = None

    for line in lines:
        # Skip headers
        if line.startswith("RANKINGS") or line.startswith("2025 ESPN") or line == "PPR Top 300 Cheat Sheet":
            continue

        # Try rank line
        m = _RANK_RE.match(line)
        if m:
            # Flush previous pending if exists
            if pending_rank is not None and pending_name:
                results.append(_make_entry(pending_rank, pending_pos, pending_name, pending_team, 0))

            rank = int(m.group(1))
            pos_rank = m.group(2)
            pos_match = _POS_RE.match(pos_rank)
            pos = pos_match.group(1) if pos_match else ""

            if m.group(3):  # name inline with rank
                pending_rank = rank
                pending_pos = pos
                pending_name = m.group(3).strip()
                pending_team = m.group(4) or ""
            else:
                pending_rank = rank
                pending_pos = pos
                pending_name = None
                pending_team = None
            continue

        # Try value line
        m = _VAL_RE.match(line)
        if m and pending_rank is not None and pending_name:
            value = int(m.group(1))
            results.append(_make_entry(pending_rank, pending_pos, pending_name, pending_team, value))
            pending_rank = None
            pending_name = None
            pending_team = None
            pending_pos = None
            continue

        # Try name line (standalone)
        m = _NAME_RE.match(line)
        if m and pending_rank is not None and not pending_name:
            pending_name = m.group(1).strip()
            pending_team = m.group(2)
            continue

        # Bare number could be a bye week after a value-less line
        if re.match(r"^\d{1,2}$", line) and pending_rank is None:
            continue

    # Flush last pending
    if pending_rank is not None and pending_name:
        results.append(_make_entry(pending_rank, pending_pos, pending_name, pending_team, 0))

    # Sort by rank and deduplicate (prefer entries with value > 0)
    results.sort(key=lambda x: (x["rank"], -x["espn_raw"]))
    seen_ranks = set()
    deduped = []
    for r in results:
        if r["rank"] not in seen_ranks:
            seen_ranks.add(r["rank"])
            deduped.append(r)
    return deduped


def _make_entry(rank, position, name, team, espn_raw):
    if espn_raw == 0:
        espn_adjusted = 1.0
    else:
        espn_adjusted = max(1.0, float(int(espn_raw * 1.2)))
    return {
        "rank": rank,
        "name": name,
        "position": position or "",
        "nfl_team": team or "",
        "espn_raw": float(espn_raw),
        "espn_adjusted": espn_adjusted,
    }


# ── Player matching ──────────────────────────────────────────────────────────

MATCH_EXACT = "MATCHED"
MATCH_APPROX = "APPROXIMATE"
MATCH_NONE = "NOT_FOUND"


def match_players(parsed: list[dict], db_players: list) -> dict:
    """
    Match parsed ESPN entries to DB players using 3-layer matching.
    Returns {matched: [...], approximate: [...], not_found: [...], absent: [...]}.
    """
    by_norm = {}
    all_norms = []
    unmatched_db = {}

    for p in db_players:
        nn = _norm(p.name)
        by_norm[nn] = p
        all_norms.append((nn, p))
        unmatched_db[p.id] = p

    matched = []
    approximate = []
    not_found = []
    used_player_ids = set()

    for entry in parsed:
        espn_norm = _norm(entry["name"])

        # Layer 1: exact normalized match
        player = by_norm.get(espn_norm)
        if player and player.id not in used_player_ids:
            matched.append({**entry, "player_id": player.id, "db_name": player.name,
                            "match_type": MATCH_EXACT, "similarity": 1.0})
            used_player_ids.add(player.id)
            unmatched_db.pop(player.id, None)
            continue

        # Layer 2 & 3: fuzzy matching
        best_ratio = 0.0
        best_player = None
        for nn, p in all_norms:
            if p.id in used_player_ids:
                continue
            ratio = difflib.SequenceMatcher(None, espn_norm, nn).ratio()
            if ratio > 0.5:
                if entry.get("position") and p.position and entry["position"].upper() == p.position.upper():
                    ratio = min(1.0, ratio + 0.05)
                if entry.get("nfl_team") and p.nfl_team and entry["nfl_team"].upper() == p.nfl_team.upper():
                    ratio = min(1.0, ratio + 0.03)
            if ratio > best_ratio:
                best_ratio = ratio
                best_player = p

        if best_ratio >= 0.82 and best_player and best_player.id not in used_player_ids:
            matched.append({**entry, "player_id": best_player.id, "db_name": best_player.name,
                            "match_type": MATCH_EXACT, "similarity": round(best_ratio, 3)})
            used_player_ids.add(best_player.id)
            unmatched_db.pop(best_player.id, None)
        elif best_ratio >= 0.65 and best_player and best_player.id not in used_player_ids:
            candidates = []
            for nn, p in all_norms:
                if p.id in used_player_ids:
                    continue
                r = difflib.SequenceMatcher(None, espn_norm, nn).ratio()
                if r >= 0.5:
                    candidates.append({"player_id": p.id, "name": p.name,
                                       "position": p.position, "similarity": round(r, 3)})
            candidates.sort(key=lambda x: -x["similarity"])
            approximate.append({**entry, "player_id": best_player.id, "db_name": best_player.name,
                                "match_type": MATCH_APPROX, "similarity": round(best_ratio, 3),
                                "candidates": candidates[:5]})
        else:
            not_found.append({**entry, "match_type": MATCH_NONE})

    absent = [{"player_id": p.id, "name": p.name, "position": p.position,
               "fantasy_team": getattr(p, "fantasy_team", "")}
              for p in unmatched_db.values()]

    return {
        "matched": matched,
        "approximate": approximate,
        "not_found": not_found,
        "absent": absent,
    }

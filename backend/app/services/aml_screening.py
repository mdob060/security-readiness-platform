from difflib import SequenceMatcher

from app.models.sectors import AmlSanctionsEntry


def screen_name(query_name: str, entries: list[AmlSanctionsEntry]) -> tuple[AmlSanctionsEntry | None, float]:
    best_entry = None
    best_score = 0.0
    normalized_query = query_name.strip().lower()
    for entry in entries:
        score = SequenceMatcher(None, normalized_query, entry.full_name.strip().lower()).ratio()
        if score > best_score:
            best_score = score
            best_entry = entry
    return best_entry, round(best_score * 100, 1)

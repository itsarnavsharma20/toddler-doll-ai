"""Drop a leading greeting plus the toy's name: "Hey Kiko, sing a rhyme" becomes "sing a rhyme"."""
from playmate.content import hints
from playmate.core.text import normalize

_EDGE_PUNCTUATION = " ,.!?;:-।"  # includes the Devanagari danda


def strip_name(text):
    """Return the request without a leading greeting and name. Unchanged if the name is not there
    or if nothing else was said (so "Hey Kiko" alone still gets a greeting back)."""
    tokens = (text or "").split()
    if not tokens:
        return text
    normalized = [normalize(token) for token in tokens]
    start = 1 if normalized[0] in hints.greetings() else 0
    for variant in hints.name_variants():
        end = start + len(variant)
        if tuple(normalized[start:end]) == variant:
            rest = " ".join(tokens[end:]).lstrip(_EDGE_PUNCTUATION)
            return rest if rest else text
    return text

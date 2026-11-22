"""Athlete wording for stored activity feedback.

The activity classifier and the database default store Dutch feedback text with
each activity. That text is the key here, so stored feedback keeps its exact
meaning in both languages. Text that is not recognised (for example from an
older ruleset) falls back to the wording for the stored qualitative result.
"""

from collections.abc import Mapping
from typing import Final

from app.core.i18n import Language, LocalizedText

_AWAITING_RPE: Final[LocalizedText] = {
    "nl": "Voeg je ervaren inspanning toe om de training af te ronden.",
    "en": "Add your perceived effort to complete the workout.",
}
_HIDDEN_FATIGUE: Final[LocalizedText] = {
    "nl": (
        "Deze rustige training voelde duidelijk zwaarder dan verwacht. "
        "Controleer een eventueel herstelvoorstel."
    ),
    "en": (
        "This easy workout felt notably harder than expected. "
        "Review any recovery proposal."
    ),
}
_UNPLANNED: Final[LocalizedText] = {
    "nl": (
        "Deze extra training stond niet in je actieve planning. "
        "Een eventuele aanpassing blijft eerst een voorstel."
    ),
    "en": (
        "This extra workout was not in your active plan. "
        "Any adjustment will remain a proposal first."
    ),
}
_OVERSHOOT: Final[LocalizedText] = {
    "nl": (
        "Deze training viel zwaarder uit dan gepland. "
        "Een eventuele aanpassing blijft eerst een voorstel."
    ),
    "en": (
        "This workout was harder than planned. "
        "Any adjustment will remain a proposal first."
    ),
}
_PERFECT_MATCH: Final[LocalizedText] = {
    "nl": "De training sloot goed aan op de geplande inspanning.",
    "en": "The workout matched the planned effort well.",
}
_DEVIATION: Final[LocalizedText] = {
    "nl": (
        "De uitvoering week af van de planning, maar vraagt niet automatisch "
        "om een correctie."
    ),
    "en": (
        "The execution differed from the plan, but does not automatically "
        "require a correction."
    ),
}
_INCOMPLETE_MEASUREMENT: Final[LocalizedText] = {
    "nl": (
        "Training opgeslagen. Er zijn onvoldoende meetgegevens "
        "voor een volledige vergelijking."
    ),
    "en": "Workout saved. There is not enough measurement data for a full comparison.",
}
_NO_COMPARABLE_PLAN: Final[LocalizedText] = {
    "nl": (
        "Training opgeslagen. De eerdere planning heeft geen vergelijkbare meetbasis."
    ),
    "en": "Workout saved. The earlier plan has no comparable measurement basis.",
}

ACTIVITY_FEEDBACK_MESSAGES: Final[Mapping[str, LocalizedText]] = {
    text["nl"]: text
    for text in (
        _AWAITING_RPE,
        _HIDDEN_FATIGUE,
        _UNPLANNED,
        _OVERSHOOT,
        _PERFECT_MATCH,
        _DEVIATION,
        _INCOMPLETE_MEASUREMENT,
        _NO_COMPARABLE_PLAN,
    )
}

_RESULT_FALLBACK: Final[Mapping[str, LocalizedText]] = {
    "awaiting_rpe": _AWAITING_RPE,
    "perfect_match": _PERFECT_MATCH,
    "overshoot": _OVERSHOOT,
    "hidden_fatigue": _HIDDEN_FATIGUE,
    "deviation": _DEVIATION,
    "unplanned": _UNPLANNED,
}


def activity_feedback_message(
    stored_message: str,
    qualitative_result: str,
    language: Language,
) -> str:
    """Word stored activity feedback in the requested language."""
    text = ACTIVITY_FEEDBACK_MESSAGES.get(stored_message) or _RESULT_FALLBACK.get(
        qualitative_result,
        _DEVIATION,
    )
    return text[language]

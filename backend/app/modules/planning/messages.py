"""Athlete wording for planning warnings and proposal explanations.

Warnings are worded by their stable code, so stored warnings from older
revisions follow the requested language too. The wording matches the mobile
dictionary for the same codes. Proposal explanations are free text stored with
each proposal; only sentences written by the server itself are recognised here.
Explanations written by the optional language model are returned as stored.
"""

import re
from collections.abc import Mapping
from typing import Final

from app.core.i18n import Language, LocalizedText
from app.modules.activities.messages import ACTIVITY_FEEDBACK_MESSAGES

WARNING_MESSAGES: Final[Mapping[str, LocalizedText]] = {
    "all_disciplines_blocked_rest_only": {
        "nl": (
            "Alle disciplines zijn momenteel geblokkeerd. Daarom bevat dit "
            "voorstel alleen rust."
        ),
        "en": (
            "All disciplines are currently blocked, so this proposal contains "
            "only rest."
        ),
    },
    "anti_stack_violation": {
        "nl": (
            "Tussen deze intensieve trainingen is extra herstel nodig. "
            "Kies een andere datum."
        ),
        "en": (
            "These hard workouts need extra recovery between them. Choose another date."
        ),
    },
    "cross_training_choice_available": {
        "nl": (
            "Je kunt expliciet een beschikbare alternatieve sport kiezen voor "
            "crosstraining; een veilige startcapaciteit blijft vereist."
        ),
        "en": (
            "You can explicitly choose an available alternative sport for "
            "cross-training; a safe starting capacity is still required."
        ),
    },
    "distance_only_swim_excluded_from_time_ratio": {
        "nl": (
            "Afstandsgestuurde zwemtrainingen staan in meters in het plan; de "
            "80/20-tijdverdeling bevat alleen trainingen met een vastgelegde duur."
        ),
        "en": (
            "Distance-based swim workouts appear in metres in the plan; the 80/20 "
            "time split only includes workouts with a recorded duration."
        ),
    },
    "injured_disciplines_excluded": {
        "nl": (
            "Trainingen voor de bevestigde geblesseerde disciplines zijn niet "
            "opgenomen."
        ),
        "en": "Workouts for the confirmed injured disciplines are not included.",
    },
    "injury_replacement_capacity_limited": {
        "nl": (
            "Alleen de alternatieve training die past bij je huidige "
            "trainingsgeschiedenis is opgenomen."
        ),
        "en": (
            "Only the alternative training that fits your current training "
            "history was included."
        ),
    },
    "manual_review_required": {
        "nl": (
            "Er was geen veilig regulier weekdoel beschikbaar. Controleer dit "
            "herstelvoorstel extra zorgvuldig."
        ),
        "en": (
            "No safe regular weekly target was available. Review this recovery "
            "proposal with extra care."
        ),
    },
    "outside_confirmed_availability": {
        "nl": (
            "Een training valt buiten je bevestigde beschikbare dagen. Kies een "
            "beschikbare datum."
        ),
        "en": (
            "A workout falls outside your confirmed available days. Choose an "
            "available date."
        ),
    },
    "realized_intensity_debt_applied": {
        "nl": (
            "Je recente trainingsgegevens verlagen de intensieve tijd voor deze week."
        ),
        "en": "Your recent training data lowers the hard training time for this week.",
    },
    "restricted_disciplines_low_only": {
        "nl": (
            "Voor een beperkte discipline zijn alleen rustige trainingen opgenomen."
        ),
        "en": "Only easy workouts are included for a restricted discipline.",
    },
    "target_outside_catalog_capacity": {
        "nl": (
            "De gekozen trainingen sluiten niet precies aan op dit weekvoorstel. "
            "Controleer de combinatie voor goedkeuring."
        ),
        "en": (
            "The chosen workouts do not exactly match this weekly proposal. "
            "Review the combination before approving."
        ),
    },
    "workouts_consolidated_on_available_dates": {
        "nl": (
            "Er staan meerdere trainingen op dezelfde beschikbare dag. Plan "
            "voldoende herstel tussen de sessies."
        ),
        "en": (
            "Several workouts are on the same available day. Plan enough "
            "recovery between the sessions."
        ),
    },
}

UNKNOWN_WARNING_MESSAGE: Final[LocalizedText] = {
    "nl": "Dit voorstel heeft een aandachtspunt. Controleer het voor goedkeuring.",
    "en": "This proposal has a point of attention. Review it before approving.",
}


def warning_message(code: str, language: Language) -> str:
    """Word one planning warning by its stable code."""
    return WARNING_MESSAGES.get(code, UNKNOWN_WARNING_MESSAGE)[language]


_DETERMINISTIC_REST_ONLY = (
    "Deze week bevat bewust alleen rust vanwege de bevestigde beperkingen. "
    "Bekijk het voorstel en keur het pas goed als de situatie nog klopt."
)

_FIXED_EXPLANATIONS: Final[Mapping[str, LocalizedText]] = {
    "A deterministic weekly plan is ready for review.": {
        "nl": "Je persoonlijke weekvoorstel staat klaar om te controleren.",
        "en": "Your personal weekly proposal is ready to review.",
    },
    "A rest-only weekly revision is ready for review.": {
        "nl": "Je herstelvoorstel met alleen rust staat klaar om te controleren.",
        "en": "Your rest-only recovery proposal is ready to review.",
    },
    "Nieuwe berekende zones staan klaar. Je actieve zones wijzigen pas na "
    "jouw bevestiging.": {
        "nl": (
            "Nieuwe berekende zones staan klaar. Je actieve zones wijzigen pas "
            "na jouw bevestiging."
        ),
        "en": (
            "New calculated zones are ready. Your active zones only change "
            "after you confirm."
        ),
    },
    "Een veldtest staat klaar op de gekozen lokale datum en wacht op bevestiging.": {
        "nl": (
            "Een veldtest staat klaar op de gekozen lokale datum en wacht op "
            "bevestiging."
        ),
        "en": (
            "A field test is ready on the chosen local date and awaits your "
            "confirmation."
        ),
    },
    _DETERMINISTIC_REST_ONLY: {
        "nl": _DETERMINISTIC_REST_ONLY,
        "en": (
            "This week deliberately contains only rest because of the confirmed "
            "restrictions. Review the proposal and only approve it if the "
            "situation still applies."
        ),
    },
    # Activity corrections store the activity feedback as their explanation.
    **ACTIVITY_FEEDBACK_MESSAGES,
}

_DETERMINISTIC_WEEKLY = re.compile(
    r"Dit weekvoorstel verdeelt (?P<workouts>\d+) trainingen over "
    r"(?P<disciplines>(?:swim|bike|run)(?:, (?:swim|bike|run))*), met "
    r"(?P<rest_days>\d+) geplande rustdagen\. De trainingsdagen volgen je "
    r"bevestigde beschikbaarheid; bekijk het voorstel en keur het pas goed als "
    r"de week voor jou haalbaar voelt\."
)

_DISCIPLINE_NAMES: Final[Mapping[str, LocalizedText]] = {
    "swim": {"nl": "zwemmen", "en": "swimming"},
    "bike": {"nl": "fietsen", "en": "cycling"},
    "run": {"nl": "hardlopen", "en": "running"},
}


def proposal_explanation(explanation: str, language: Language) -> str:
    """Word a stored explanation the server wrote; keep any other text as stored."""
    fixed = _FIXED_EXPLANATIONS.get(explanation)
    if fixed is not None:
        return fixed[language]
    weekly = _DETERMINISTIC_WEEKLY.fullmatch(explanation)
    if weekly is None:
        return explanation
    disciplines = ", ".join(
        _DISCIPLINE_NAMES[name][language] for name in weekly["disciplines"].split(", ")
    )
    if language == "en":
        return (
            f"This weekly proposal spreads {weekly['workouts']} workouts over "
            f"{disciplines}, with {weekly['rest_days']} planned rest days. The "
            "training days follow your confirmed availability; review the "
            "proposal and only approve it if the week feels achievable for you."
        )
    return (
        f"Dit weekvoorstel verdeelt {weekly['workouts']} trainingen over "
        f"{disciplines}, met {weekly['rest_days']} geplande rustdagen. De "
        "trainingsdagen volgen je bevestigde beschikbaarheid; bekijk het voorstel "
        "en keur het pas goed als de week voor jou haalbaar voelt."
    )

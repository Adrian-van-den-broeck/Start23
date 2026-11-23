"""Dutch wording for public API errors, keyed by their stable error code.

English is the source language of every server error message, so an English
request keeps the message the server raised. A Dutch request gets the entry for
the error code, or the entry for the generic code of its HTTP status when the
error has no specific code. Unknown codes therefore never fall back to English.
"""

from collections.abc import Mapping
from typing import Final

GENERIC_DUTCH_MESSAGES: Final[Mapping[str, str]] = {
    "bad_request": "Het verzoek is ongeldig.",
    "authentication_required": "Je sessie is verlopen of ongeldig. Log opnieuw in.",
    "operation_forbidden": "Deze actie is niet toegestaan.",
    "resource_not_found": "De gevraagde gegevens zijn niet gevonden.",
    "state_conflict": (
        "De gegevens zijn intussen gewijzigd. Vernieuw en probeer opnieuw."
    ),
    "validation_failed": "Het verzoek bevat ongeldige gegevens.",
    "rate_limit_exceeded": "Te veel pogingen. Probeer het later opnieuw.",
    "service_unavailable": (
        "De dienst is tijdelijk niet beschikbaar. Probeer het later opnieuw."
    ),
    "request_failed": "Het verzoek kon niet worden voltooid.",
    "internal_error": "Er ging onverwacht iets mis.",
}

DUTCH_ERROR_MESSAGES: Final[Mapping[str, str]] = {
    **GENERIC_DUTCH_MESSAGES,
    # Weekly planning and swipe drafts.
    "anti_stack_violation": (
        "Tussen deze intensieve trainingen is extra herstel nodig. "
        "Kies een andere datum."
    ),
    "approved_plan_baseline_unavailable": (
        "Voor een terugkerende atleet is een geschikte historische basis nodig."
    ),
    "availability_outside_week": (
        "Beschikbare dagen moeten binnen de gevraagde trainingsweek vallen."
    ),
    "availability_required": "Kies minstens één beschikbare dag.",
    "catalog_capacity_unsatisfied": (
        "Er past geen veilige trainingscombinatie in deze week."
    ),
    "catalog_coverage_unsatisfied": (
        "De huidige trainingscatalogus dekt niet elke discipline van je doel "
        "zonder blessure."
    ),
    "catalog_empty": (
        "Er zijn geen trainingen die passen bij je bevestigde instellingen."
    ),
    "catalog_phase_coverage_unavailable": (
        "Voor deze trainingsfase is nog niet voor elke discipline een "
        "beoordeelde training beschikbaar."
    ),
    "discipline_selection_incomplete": (
        "De gekozen trainingen dekken niet elke beschikbare discipline."
    ),
    "duplicate_available_date": "Elke beschikbare dag mag maar één keer voorkomen.",
    "duplicate_template_selection": (
        "Een training kan maar één keer per versie gekozen worden."
    ),
    "explicit_test_date_required": (
        "Elke apart geplande veldtest heeft een exacte datum nodig."
    ),
    "field_test_assignment_required": (
        "Veldtesttrainingen moeten via de testplanning worden ingepland."
    ),
    "fixed_date_unavailable": (
        "Elke vaste trainingsdatum moet een van je beschikbare dagen zijn."
    ),
    "fixed_template_not_selected": (
        "Een vaste trainingsdatum moet bij een gekozen training horen."
    ),
    "injury_discipline_basis_unavailable": (
        "Voor deze beperking is een beoordeelde basis per discipline nodig."
    ),
    "injury_exclusion": (
        "Een bevestigde geblesseerde discipline kan niet worden ingepland."
    ),
    "legacy_setup_requires_calibration": (
        "Bevestig je bekende zones of kies kalibratie voordat je een nieuw plan maakt."
    ),
    "maintenance_baseline_unavailable": (
        "Voor onderhoud is eerst een eerder goedgekeurd weekplan nodig."
    ),
    "partial_week_taper_rule_required": (
        "Voor deze precieze periode voor de wedstrijd is nog geen beoordeeld "
        "weekdoel beschikbaar."
    ),
    "pending_revision_required": (
        "Alleen een openstaand weekvoorstel kan worden aangepast."
    ),
    "pending_workout_stale": (
        "Deze training hoort niet meer bij het openstaande voorstel."
    ),
    "physiological_debt_escalation_required": (
        "Herhaald onveilig trainen moet eerst door een gekwalificeerde persoon "
        "worden beoordeeld."
    ),
    "plan_revision_stale": "Je plan is gewijzigd nadat deze actie werd voorbereid.",
    "previous_month_history_required": (
        "Vul eerst je trainingsgeschiedenis van de vorige maand aan voordat je "
        "een nieuw plan maakt."
    ),
    "previous_week_availability_unavailable": (
        "Er is geen goedgekeurde beschikbaarheid van vorige week om over te nemen."
    ),
    "proposal_not_pending": "Over dit voorstel is al beslist.",
    "proposal_stale": "Dit voorstel is gebaseerd op een oudere versie van je plan.",
    "race_date_before_week": (
        "De datum van je hoofdwedstrijd ligt voor de gevraagde trainingsweek."
    ),
    "replacement_not_eligible": (
        "Deze training kan in dit voorstel niet worden verwijderd of vervangen."
    ),
    "rest_or_anti_stack_unsatisfied": (
        "Het weekschema past niet bij de rustdagen en de nodige hersteltijd "
        "tussen intensieve trainingen."
    ),
    "restricted_zero_base_allocation_unavailable": (
        "Voor deze beperkte introductieweek is eerst een beoordeelde "
        "startverdeling nodig."
    ),
    "schedule_outside_week": (
        "Een verplaatste training moet binnen haar trainingsweek blijven."
    ),
    "swipe_candidate_decided": "Over deze trainingskaart is al beslist.",
    "swipe_candidate_stale": (
        "De getoonde trainingskaart is gewijzigd. Vernieuw de trainingskeuze."
    ),
    "swipe_date_unavailable": (
        "De gekozen datum hoort niet bij je bevestigde beschikbaarheid."
    ),
    "swipe_draft_base_stale": (
        "Je plan is gewijzigd voordat deze trainingskeuze begon."
    ),
    "swipe_draft_closed": (
        "Deze trainingskeuze is afgesloten of vervangen door een nieuwere."
    ),
    "swipe_draft_context_stale": (
        "Je planningsgegevens zijn gewijzigd. Begin een nieuwe trainingskeuze."
    ),
    "swipe_draft_no_completion": (
        "Geen enkele volgorde van beschikbare trainingen vult dit weekdoel."
    ),
    "swipe_draft_owner_mismatch": "Deze trainingskeuze hoort niet bij jouw account.",
    "swipe_draft_stale": (
        "De trainingskeuze is gewijzigd nadat deze actie werd voorbereid."
    ),
    "swipe_draft_week_mismatch": "Het gekozen plan hoort niet bij deze week.",
    "swipe_layout_incomplete": (
        "Plan elke gekozen training in voordat je de week indient."
    ),
    "swipe_occurrence_not_accepted": (
        "Alleen een gekozen trainingskaart kan worden ingepland."
    ),
    "swipe_selection_complete": "De keuze van je trainingen is al afgerond.",
    "swipe_selection_incomplete": "Rond eerst de keuze van je trainingen af.",
    "swipe_selection_invalid": (
        "De gekozen trainingscombinatie past niet in deze week."
    ),
    "swipe_target_complete": "Het weekdoel is al volledig gevuld.",
    "swipe_undo_empty": "Er is geen keuze om ongedaan te maken.",
    "taper_baseline_unavailable": (
        "Voor een taperweek is eerst een eerdere opbouwweek als basis nodig."
    ),
    "taper_catalog_coverage_unavailable": (
        "Voor deze week voor de wedstrijd is nog niet voor elke discipline een "
        "beoordeelde tapertraining beschikbaar."
    ),
    "template_not_eligible": (
        "Een of meer gekozen trainingen zijn niet beschikbaar voor deze week."
    ),
    "test_date_unavailable": (
        "De gekozen testdatum is geen beschikbare dag in je plan."
    ),
    "test_discipline_missing": (
        "Je actieve plan heeft geen training in dezelfde discipline om te vervangen."
    ),
    "zero_history_discipline_baseline_unavailable": (
        "Voor een discipline zonder trainingsgeschiedenis is eerst een "
        "goedgekeurd startdoel nodig."
    ),
    # Completed activities.
    "activity_correction_stale": (
        "De aanpassing van deze training is verouderd. Vernieuw en probeer opnieuw."
    ),
    "activity_rpe_immutable": "De RPE voor deze training is al ingediend.",
    "activity_rpe_window_closed": (
        "RPE kan alleen tijdens de huidige trainingsweek worden aangepast."
    ),
    "activity_state_conflict": (
        "De training is intussen gewijzigd. Vernieuw en probeer opnieuw."
    ),
    "average_heart_rate_immutable": (
        "De gemiddelde hartslag kan na de berekening van deze training niet meer "
        "worden gewijzigd."
    ),
    "idempotency_key_reused": (
        "Deze verzoeksleutel is al gebruikt voor een andere training."
    ),
    "planned_external_activity_already_completed": (
        "Deze geplande externe training is al voltooid."
    ),
    "planned_workout_already_matched": (
        "Deze geplande training heeft al een voltooide training."
    ),
    # Weekly check-ins.
    "checkin_already_completed": "Deze check-in is al afgerond.",
    "checkin_context_stale": (
        "De check-in is gewijzigd nadat dit formulier werd geopend."
    ),
    "checkin_not_confirmed": (
        "Bevestig eerst je weekcontext voordat je een plan maakt."
    ),
    "checkin_state_conflict": (
        "De check-in is intussen gewijzigd. Vernieuw en probeer opnieuw."
    ),
    "restriction_review_required": (
        "Bekijk elke actieve beperking voordat je deze check-in afrondt."
    ),
    # Pioneer access codes.
    "pioneer_code_expired": "De Pioneer-toegangscode is verlopen.",
    "pioneer_code_invalid": "De Pioneer-toegangscode is ongeldig.",
    "pioneer_code_reused": "De Pioneer-toegangscode is al gebruikt.",
    "pioneer_code_revoked": "De Pioneer-toegangscode is ingetrokken.",
    "pioneer_code_unauthorized": (
        "Deze Pioneer-toegangscode is niet aan jou toegewezen."
    ),
    "pioneer_idempotency_conflict": (
        "Deze verzoeksleutel is al gebruikt voor een andere aanvraag."
    ),
    "pioneer_rate_limited": (
        "Te veel pogingen met een toegangscode. Probeer het later opnieuw."
    ),
    "pioneer_response_invalid": "De toegangscode kon niet worden verwerkt.",
}

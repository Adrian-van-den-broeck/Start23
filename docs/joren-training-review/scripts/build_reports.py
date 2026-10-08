# ruff: noqa: E501
# Long literals are Dutch handoff document paragraphs.
"""Build honest coverage/parity handoff reports from recorded local evidence."""

import json
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
STATUS = (
    "WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — "
    "SEE PARITY AND COVERAGE GAPS"
)
SOURCE_SHA = "6b1189b70a6505726fef70c4616a2f3d6dd4c94a"
report = json.loads(
    (OUT / "qa/native-parity-results.json").read_text(encoding="utf-8-sig")
)
quality = json.loads((OUT / "qa/artifact-validation.json").read_text(encoding="utf8"))
cases = json.loads((OUT / "fixtures/parity_cases.json").read_text(encoding="utf8"))
manifest = json.loads(
    (OUT / "fixtures/source_manifest.json").read_text(encoding="utf8")
)
rules = json.loads((OUT / "fixtures/reviewed_rules.json").read_text(encoding="utf8"))


def write(name, text):
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf8")


def table(headers, rows):
    def clean(value):
        return str(value).replace("|", "/").replace("\n", " ")

    return (
        "| "
        + " | ".join(headers)
        + " |\n| "
        + " | ".join(["---"] * len(headers))
        + " |\n"
        + "".join("| " + " | ".join(map(clean, row)) + " |\n" for row in rows)
    )


bycase = defaultdict(list)
for assertion in report["results"]:
    bycase[assertion["case"]].append(assertion)
assert set(bycase) == {case["id"] for case in cases}, "Fixture/report mismatch"
assert report["failed"] == 0 and not report["formula_errors"], "Native checks failed"
assert "INSPECTED" in quality["visual_review"], "Visual review remains open"
maxdiff = max(abs(row["difference"] or 0) for row in report["results"])
parity = "# Excel/Python-pariteitsrapport\n\n" + STATUS + "\n\n"
parity += f"Bron: fix/catalog-capacity-fresh-athlete, {SOURCE_SHA}. Native Excel {report['excel_version']}; run UTC {report.get('run_utc', 'recorded in JSON')}.\n\n"
parity += f"{report['cases']} uitgevoerde scenario’s; {report['assertions']} assertions; {report['passed']} PASS; {report['failed']} FAIL; {len(report['formula_errors'])} native formulefouten. Maximale waargenomen numerieke afwijking: {maxdiff:.16g}.\n\n"
parity += """Dit is pariteit voor beperkte numerieke onderdelen en enkele eigenschappen. Het is GEEN volledige engine-, branch-, sequence- of cataloguspariteit. De 40 reviewscenario’s op tab 22 zijn geen automatisch geladen en geteste volledige engineflows.

## Methode

1. make_parity_cases.py voert de gepinde Python-domeinfuncties offline uit: starting_baseline, calibrate, zone_load, average_hr_zone_load, classify_activity_match en resolve_target.
2. FRESH/MISSING bevatten daarnaast expliciete bronafgeleide invariant-/gateasserties. PROPERTY-cases zijn workbookeigenschappen, geen goedgekeurde alternatieve Python-ruleset. Ze tellen mee als assertions, niet als zelfstandige productie-algoritmen.
3. verify_excel.ps1 opent een tijdelijke kopie in werkelijke desktop Excel, wijzigt inputs, voert CalculateFullRebuild uit en leest Value2. Het stelt geen PASS vast door geschreven formuletekst te lezen.
4. Iedere input wordt hersteld inclusief oorspronkelijke formule/type. Na de hele set worden alle gebruikte cellen op formule-errors onderzocht. Een mismatch geeft een fout-exit.
5. De oorspronkelijke, nieuw gegenereerde handoff-XLSX wordt daarna herberekend en opgeslagen. Er zijn geen workbookcalls naar Python, de app, Supabase of Railway.

Numeriek wordt absolute tolerantie 1e-9 gebruikt. Strings en foutcodes worden exact vergeleken. HALF_UP-gedrag bij positieve getallen wordt met expliciete cases getoetst; Excel Double is geen Decimal en alle numerieke combinaties zijn niet bewezen. Datums zijn gehele Excel-kalenderdagen. De propertytest controleert dat voorbeelddata geen verborgen tijddeel behouden.

## Daadwerkelijk getoetste onderdelen

"""
parity += table(
    ["Groep", "Scenario’s", "Assertions", "Bereik"],
    [
        ("BASE", 12, 48, "Componenten en totaal; nul, gemengd, fracties, 168 uur"),
        ("CAL", 30, 330, "3 sporten × RPE1..10; drempel en alle zonegrenzen"),
        (
            "ZONELOAD",
            30,
            90,
            "3 sporten × 5 zones × complete/partial; load, coverage, status",
        ),
        ("MEAN", 10, 30, "Run/bike gemiddelde HR met bevestigde actieve zones"),
        ("MATCH", 14, 28, "RPE4/7; inclusief .90/1.10 en strikt >1.15"),
        ("TARGET", 7, 21, "Hold, 80%, <80%, 110%, debt, fatigue en geen completions"),
        ("FRESH", 2, 4, "Activiteiten zijn geen approval; eerste BASE blijft"),
        (
            "MISSING",
            3,
            3,
            "Expliciete nulzones, gedeeltelijke tijd, pending HR-profile",
        ),
        (
            "PHASE",
            8,
            12,
            "Recovery, full/partial taper, ontbrekende baseline, prioriteit, datumfouten",
        ),
        (
            "PROPERTY",
            4,
            11,
            "Original-isolation, rustHR onafhankelijk, gehele datums, eigen Joren-HR-zone",
        ),
    ],
)
parity += """
## Niet geverifieerd / bekende verschillen

- Geen exacte ordered candidate-/exclusionpariteit, UUID-tie-breakers of volledige RPE-projectie.
- Geen multisetsearch, workoutcomposition, swipe-eventlog, automatische plaatsing of cross-week-feasibilitypariteit.
- Geen volledige stale/idempotent approval/rejection/revision- of activiteitcorrectiesequentie.
- Geen injury-waterfill, intensiteitschuldpropagatie, maintenance of manual-review-escalatie.
- Geen complete 16-weekengineflow; vorige autoritatieve snapshots zijn expliciete input. Original en experiment hebben geen eigen volledige statehistorie.
- SQL mixed-known/NULL SUM-semantiek wordt niet exact nagebootst. Dit bekende verschil is niet als geslaagde case opgenomen.
- Algemene IANA/DST-historie en alle ongeldige Pydantic-/protocolcombinaties zijn open.
- Algemene Double/Decimal-precisiematch en exhaustieve property/branchcoverage zijn open.

## Per uitgevoerd scenario

"""
parity += table(
    ["ID", "Regel/eigenschap", "Assertions", "Resultaat"],
    [
        (
            c["id"],
            c["rule"],
            len(bycase[c["id"]]),
            "PASS" if all(a["passed"] for a in bycase[c["id"]]) else "FAIL",
        )
        for c in cases
    ],
)
parity += "\nVolledige actual/expected/difference per cel: qa/native-parity-results.json. Reproduceerbare inputs: fixtures/parity_cases.json. De handoff-hashes staan in FINAL_REPORT en qa/artifact-validation.json.\n"
write("PARITY_TEST_REPORT.md", parity)

files = [
    ".gitignore",
    ".gitattributes",
    "WOMBO_Complete_Training_Logic.pdf",
    "WOMBO_Training_Simulator.xlsx",
    "ENGINE_RULE_INVENTORY.md",
    "ENGINE_SOURCE_TRACEABILITY.md",
    "SIMULATOR_COVERAGE_MATRIX.md",
    "PARITY_TEST_REPORT.md",
    "KNOWN_GAPS_AND_QUESTIONS.md",
    "JOREN_CHANGE_REQUEST_TEMPLATE.md",
    "README.md",
    "HANDBOOK.md",
    "FINAL_REPORT.md",
    "DELIVERY_FILES.json",
] + [
    str(p.relative_to(OUT)).replace("\\", "/")
    for p in sorted((OUT / "fixtures").glob("*.json"))
]
files += [
    str(p.relative_to(OUT)).replace("\\", "/")
    for p in sorted((OUT / "scripts").iterdir())
    if p.is_file() and p.suffix in (".py", ".mjs", ".ps1")
]
files += [
    "qa/.gitignore",
    "qa/native-parity-results.json",
    "qa/artifact-validation.json",
    "qa/backend-tests.txt",
    "qa/reference-checks.txt",
]
write("DELIVERY_FILES.json", json.dumps(files, indent=2, ensure_ascii=False))
final = "# Eindrapport Joren-engine-review\n\n" + STATUS + "\n\n"
final += """INTERNAL BUSINESS / ENGINE REVIEW
NOT FOR END-USER DISTRIBUTION

De opdracht is niet volledig afgerond. Er zijn twee zelfstandig bruikbare reviewbestanden en reproduceerbaar testbewijs, maar geen complete standalone all-path trainingssimulator. De PDF beschrijft 66 uitgewerkte groepen; zij is geen afgeronde audit van iedere bereikbare regel.

## Bron en isolatie

"""
final += f"- Referentiebranch: fix/catalog-capacity-fresh-athlete.\n- Volledige engine-SHA: {SOURCE_SHA}.\n- Auditbranch: docs/joren-training-engine-simulator.\n- Werkboom: .worktrees/joren-training-engine-simulator.\n- Onverwante wijzigingen in de oorspronkelijke werkboom en UI V2 zijn niet gestasht, gereset, gemerged of overschreven.\n\n"
final += """De relevante backend/Supabasebestanden van de UI V2-werkboom waren gelijk aan de geselecteerde actuele enginebasis. De verse-athleetfix is onderdeel van de referentie. De oorspronkelijke dirty rootwijziging betrof o.a. een coachnaam, geen gewijzigde fysiologische regel. Geen bewijs van daadwerkelijk gedeployde SHA is opgevraagd: hosted toegang is verboden voor deze taak.

## Auditbereik en tellingen

"""
final += f"Bronmanifest: {len(manifest)} bestanden. Inhoudelijk beschreven: {len(rules)} regelgroepen. Automatisch ontdekt: 676 Pythonfunctie-/methoderecords en 1250 syntactische beslispunten. Deze telling is geen volledige human-reviewed regel-/branchinventaris. If/while/assert/comprehensionrecords bevatten ook parsing/transporthelpers. SQL/mobilebranches zijn niet exhaustief geteld; conditioninteracties evenmin.\n\n"
final += """Brononderzoek omvat physiology (Joren, zones, progression, recovery, taper, debt, intensity, injury, anti-stack en provenance), planning (domain, service, swipe, repository, schemas), workouts/catalogus, calibration, activities, onboarding, checkins en relevante providerintegraties. Daarnaast zijn migrations, offline tests, roadmap en toepasselijke AGENTS-instructies gelezen. Het discoverymanifest is ruimer dan de handmatig geauditeerde regels. ENGINE_SOURCE_TRACEABILITY maakt dat onderscheid.

Catalogus: 162 actieve lokale templates; alle 154 brontrainingen zijn opgenomen, met segments in de JSON-bijlage. V2 eigenschappen volgen de migratie. De v2 deployed UUIDs worden willekeurig gegenereerd en zijn onbekend; behouden v1 IDs zijn lokale fixture-identiteiten. Geen productie-UUIDvolgorde wordt beweerd. Alle 154 brontrainingen bevatten al replacementtekens in tekst; de display markeert ze, exacte brontekst blijft behouden. Distance-only swims behouden ontbrekende current planned load.

## Werkboekarchitectuur en mogelijkheden

"""
final += f"29 tabbladen, {quality['workbook_formula_count']} zichtbare native formules. Geen VBA, macrobeveiliging gewijzigd of verborgen runtime. Geen externe workbooklinks, geen formulebescherming, geen Python/backendcalls tijdens gebruik. Excel {report['excel_version']} heeft het werkboek geopend, met veranderde inputs herberekend en de handoff opgeslagen.\n\n"
final += """Bewerkbaar: sporturen, rustHR als niet-baselineafhankelijke context, race type/date, tijdzone, eerste maandag, submaxobservatie/RPE en expliciete actieve-zonebevestiging; weekavailability, beperkte sportrestrictie/capabilityprojectie; template/occurrence/date; activiteitduur, zoneminuten, raw-zone-present, gemiddelde HR en RPE; expliciete vorige goedgekeurde snapshots/flags. Niet iedere ingevoerde restriction/capability heeft een volledige equivalent: onbekende gates zijn expliciet gemarkeerd.

Numerieke formules: startcomponenten/totaal/nulfallback, Phase13 HR/CSS-drempels en integerzones, actuele zone-minuutload/coverage, bevestigde gemiddelde-HR-estimates, delen van matchmatrix en weektargetprioriteit.16 targetregels hebben expliciete previous-state-inputs. Dat is geen16-weekflow met automatisch gekozen/geplaatste workouts en volledige approvalevents.

Original/Joren: referentieconstanten blijven in PARAMETERS!B, voorstellen in C, Effective in D. Beide start-, zone-, actual- en targetuitkomsten blijven inspecteerbaar. Groei, baselinecoëfficiënten, sport-/zonecoëfficiënten, RPE-ankers en zonegrenzen zijn zichtbaar aanpasbaar voor de geporte onderdelen. Spacingparameters zijn zichtbaar, maar volledige plannerpariteit ontbreekt. Formules zelf zijn onbeveiligd bewerkbaar. Structurele search/statealgoritmen zijn niet als één bewerkbare formule voorgesteld. Eigen divergerende approved historie per ruleset ontbreekt.

Geen XLSM is geleverd. Excel VBProject was programmatisch onbeschikbaar; trustinstellingen zijn niet aangepast. Er is geen geschreven of geverifieerde volledige VBA-port. Dit is een open implementatiegate, geen bewijs dat een port principieel onmogelijk is.

## Uitgevoerde controles en open gates

"""
final += table(
    ["Controle", "Resultaat", "Grenzen"],
    [
        (
            "Native Excel",
            f"{report['cases']} scenario’s; {report['passed']}/{report['assertions']} PASS; 0 FAIL; 0 formule-errors",
            "Numerieke deelpariteit en properties, geen volledige workflows",
        ),
        (
            "Backend pytest",
            "778 PASS; 1 deprecationwarning; 179.23s",
            "Referentiebron; geen algemene Excel-branchproof",
        ),
        (
            "Ruff / format referentie",
            "PASS;139 bestanden geformatteerd",
            "Geen bronwijzigingen",
        ),
        ("Strict mypy referentie", "PASS;139 bestanden", "app en tests"),
        (
            "OpenAPI / private-load leaks",
            "Onderdeel van geslaagde backend suite",
            "Geen publieke contract-/UIwijzigingen",
        ),
        (
            "Nieuwe Python-generators",
            "Ruff en format PASS",
            "Documentprose-lengte en late oracleimports lokaal verklaard",
        ),
        (
            "PDF",
            f"{quality['pdf_pages']} pagina’s gerenderd en bekeken; geen lege pagina’s, overflow of ontbrekende rule IDs",
            "Inhoudelijke all-rule completeness OPEN",
        ),
        (
            "Werkboekstructuur",
            "29 tabs; geen externe links/VBA/protection",
            "29 header/eerste-rijsample-renders bekeken; geen every-cell-layoutproof",
        ),
        (
            "pgTAP/RLS",
            "NIET UITGEVOERD",
            "Geen databaseverbinding; hosted verificatiegate OPEN",
        ),
        (
            "Mobile/TypeScript",
            "Niet uitgevoerd",
            "Geen mobilecode veranderd; geen volledige mobilebranchaudit",
        ),
    ],
)
final += f"\nMaximale numerieke afwijking in uitgevoerde assertions: {maxdiff:.16g}; tolerantie 1e-9. Double is geen Decimal. De geteste .90/1.10/1.15-equalitybranches en zone-HALF_UPvoorbeelden matchen. Algemene rounding-/accumulationpariteit, historische IANA/DST en mixed-NULL SQL-sommen blijven open.\n\n"
final += """## Resterende blockers

1. Volledige bereikbare regelinventaris met SQL/mobile, exacte test-to-branchmapping en interactioncoverage.
2. Exacte candidatefilter/protocolprojectie, multisetsearch, deterministic tie-breakers en ontbrekende deployed IDs.
3. Volledige swipe/action/occurrence-engine, validatie en automatische backtrackingplaatsing.
4. Injury-waterfill, recipientcaps, intensiteitschuld, manual-review/escalatie en maintenance.
5. Volledige pending/active/superseded/rejected/revision-/retry-statehistorie en immutable activiteitcorrecties.
6. Exacte historical-reader/provenance-/NULL-semantiek en zelfstandig divergerende multiweekhistorie.
7. Fieldtestkwaliteitsgates, andere zonemodellen en alle contracts/invalidcases.
8. Volledige native Excel sequence-, property-, precision- en branchpariteit.

Deze gates worden niet gesloten door de 577 groene assertions. Zie KNOWN_GAPS_AND_QUESTIONS en SIMULATOR_COVERAGE_MATRIX.

## Wetenschappelijke/businessvragen

Beoordeel 56.25/.90/1/1.15 en nulfallback 45;80%-completion en10%-groei;110%-volumeschuld en115%-sessieovershoot;70-90% van 20%-highbudget tegenover tijdverdeling;72/48 elapsed uren;80% capped injurytransfer met positieve recipientbasis;35%-full-taper versus partial-weekblokkade; kalibratieankers en ontbrekende observaties. Pariteit bewijst geen fysiologische veiligheid. Geen nieuwe fysiologische waarde is bedacht of in de app verwerkt.

## Voor Joren

Open eerst 00_START_HERE en lees de onvolledigheidsmelding. Gebruik blauwe invoercellen, inspecteer groene uitkomsten en bewaar ORIGINAL. Leg voorstellen vast in 25_JOREN_CHANGES en JOREN_CHANGE_REQUEST_TEMPLATE. Gebruik een targetgetal niet als bewijs van een valide/goedgekeurd trainingsplan. De twee hoofdbestanden functioneren zonder repository voor het aangegeven deelbereik. Regenereren en Python-oraclevergelijking vereisen de gepinde bron en generatorafhankelijkheden; README geeft de stappen.

## Handoff-integriteit

"""
final += (
    f"PDF SHA256: {quality['pdf_sha256']}\n\nXLSX SHA256: {quality['xlsx_sha256']}\n\n"
)
final += """## Bestanden

DELIVERY_FILES.json is de exact-path commit-/handofflijst. Tijdelijke native testkopieën, PNGs en generatorinspectielogs staan lokaal onder qa maar zijn geen aparte productdeliverables en worden niet meegecommit. Geen authored VBA bestaat.

""" + "".join("- " + name + "\n" for name in files)
final += """
## Grenzen gerespecteerd

Alle wijzigingen bevinden zich onder docs/joren-training-review in de geïsoleerde werkboom. Geen app/backend/mobile/schemawijziging; geen fysiologieregel aangepast; geen productie-/stagingtoegang of mutatie; geen migration toegepast; geen push of deploy; geen real-athletegegevens; geen credentials in deliverables. Gitbranch/worktree en lokale document-/simulatorbestanden zijn de enige mutaties.

Fases A–F zijn gedeeltelijk uitgevoerd, niet compleet verklaard. Fase G levert een expliciet onvolledig reviewpakket met bewijs en vervolggrenzen. De oorspronkelijke volledigheidsacceptatie is NIET gehaald.
"""
write("FINAL_REPORT.md", final)
print(
    json.dumps(
        {
            "status": "INCOMPLETE",
            "cases": report["cases"],
            "assertions": report["assertions"],
            "files": len(files),
        }
    )
)

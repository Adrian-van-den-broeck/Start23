# ruff: noqa: E501
# Long literals are Dutch document paragraphs, not executable expressions.
"""Write Dutch audit documents and a readable, paginated handbook PDF."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/joren-training-review"
rules = json.loads((OUT / "fixtures/reviewed_rules.json").read_text(encoding="utf8"))
functions = json.loads(
    (OUT / "fixtures/function_inventory.json").read_text(encoding="utf8")
)
decisions = json.loads(
    (OUT / "fixtures/decision_inventory.json").read_text(encoding="utf8")
)
manifest = json.loads(
    (OUT / "fixtures/source_manifest.json").read_text(encoding="utf8")
)
cat = json.loads((OUT / "fixtures/catalog.json").read_text(encoding="utf8"))
STATUS = "WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS"
meta = "INTERNAL BUSINESS / ENGINE REVIEW\nNOT FOR END-USER DISTRIBUTION\n\nBronbranch: fix/catalog-capacity-fresh-athlete\nVolledige SHA: 6b1189b70a6505726fef70c4616a2f3d6dd4c94a\nAuditbranch: docs/joren-training-engine-simulator\nDatum: 8 oktober 2026\n"


def write(name, text):
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf8")


def mdtable(headers, rows):
    def clean(x):
        return str(x).replace("|", "/").replace("\n", " ")

    return (
        "| "
        + " | ".join(headers)
        + " |\n| "
        + " | ".join(["---"] * len(headers))
        + " |\n"
        + "".join("| " + " | ".join(map(clean, r)) + " |\n" for r in rows)
    )


inventory = "# Engine-regelinventaris\n\n" + meta + "\n" + STATUS + "\n\n"
inventory += "Er zijn 66 inhoudelijk beschreven regelgroepen. Dit is GEEN voltooide inventaris van alle geïmplementeerde regels. Daarnaast zijn 676 functie-/methoderecords en 1250 syntactische beslispunten ontdekt. De AST-lijst telt ook transport-, parsing- en orchestrationhelpers. Twee uitkomsten per if zijn niet hetzelfde als geteste productbranches. SQL- en mobiele branches zijn niet in deze telling opgenomen.\n\n"
for r in rules:
    inventory += f"## {r['id']} - {r['name']}\n\n"
    for label, key in [
        ("Categorie", "classification"),
        ("Bron", "path"),
        ("Functie", "function"),
        ("Regels", "start"),
        ("Inputs en types", "inputs"),
        ("Eenheden", "input_units"),
        ("Voorwaarden en grenzen", "conditions"),
        ("Formule / algoritme", "formula"),
        ("Afronding", "rounding"),
        ("Voorbeeld", "example"),
        ("Excel", "excel"),
        ("PDF hoofdstuk", "pdf_section"),
        ("Bewerkbaarheid", "changeability"),
        ("Tests", "test_coverage"),
    ]:
        inventory += f"**{label}:** {r[key]}\n\n"
    inventory += (
        "**Fout/no-result:** "
        + (
            "; ".join(r["failure"])
            or "Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul."
        )
        + "\n\n"
    )
write("ENGINE_RULE_INVENTORY.md", inventory)
trace = (
    "# Brontraceerbaarheid\n\n"
    + meta
    + "\nGebruik de gepinde werkboom voor lijnnummers. Source manifest bevat SHA256 per bestand; geen .env of persoonsgegevens zijn gelezen voor deze bijlagen.\n\n"
)
trace += mdtable(
    ["RULE ID", "Bron", "Functie", "Van", "Tot", "Excel"],
    [
        (r["id"], r["path"], r["function"], r["start"], r["end"], r["excel"])
        for r in rules
    ],
)
trace += (
    "\n## Volledige ontdekkingslijst\n\nDeze functies zijn gevonden, niet allemaal inhoudelijk geaudit. Handmatige reachability, test-to-branch-koppeling en SQL-conditionanalyse blijven open.\n\n"
    + mdtable(
        ["Discovery ID", "Bron", "Functie", "Regels", "Reviewstatus"],
        [
            (
                x["id"],
                x["path"],
                x["function"],
                str(x["start"]) + "-" + str(x["end"]),
                "OPEN",
            )
            for x in functions
        ],
    )
)
write("ENGINE_SOURCE_TRACEABILITY.md", trace)
coverage = (
    "# Simulator-dekkingsmatrix\n\n"
    + STATUS
    + "\n\n"
    + mdtable(
        ["Regel", "Rekenplaats", "Status"],
        [
            (
                r["id"],
                r["excel"],
                "NOT IMPLEMENTED"
                if r["excel"].startswith("NOT IMPLEMENTED")
                else "PARTIAL; alleen expliciete parity assertions zijn bewijs",
            )
            for r in rules
        ],
    )
)
coverage += "\n## Beslispunten\n\nfixtures/decision_inventory.json bevat ieder syntactisch gevonden if/if-expression/while/assert/comprehension-filter van de gekozen Python-modules. Alle records starten NOT VERIFIED. Niet gepromoveerd naar PASS op basis van algemene backendtests. SQL en mobiele beslispunten ontbreken nog.\n\n## Volledigheidsgates\n\nAutomatische search, exacte swipe-completion, injury-waterfill, volledige approval/revision/idempotencyhistorie, historical-loadcompatibiliteit, protocolkwaliteit, intensiteitschuld en algemene IANA/DST-dekking zijn niet volledig geport. Zestien targetregels betekenen niet zestien volledig gesimuleerde trainingsweken.\n"
write("SIMULATOR_COVERAGE_MATRIX.md", coverage)
gaps = (
    "# Bekende gaten en vragen\n\n"
    + STATUS
    + "\n\n"
    + """## Technische gaten

1. Native-formula XLSX implementeert geen exacte begrensde multisetsearch/backtracking. Er wordt geen vereenvoudigde selector als equivalent voorgesteld.
2. Er is geen functionele XLSM en geen authored VBA. Excel COM geeft hier een null VBProject terug. Macrotrust is niet aangepast. Dit blokkeert programmatische VBA-installatie; het verklaart niet dat de algoritmen al geschreven of geverifieerd zouden zijn.
3. De 154 v2 catalogus-ID's worden met gen_random_uuid() aangemaakt (20260929210000:10-13). De lokale bronprojectie behoudt v1 fixture-ID's bij v2 eigenschappen. De exacte deployed-ID/tie-breaker-volgorde is onbekend. Geen staging/production is gelezen.
4. 66 beschreven groepen zijn geen complete human-reviewed all-rule inventaris. 676 discoveryrecords en 1250 syntactische beslispunten moeten op reachability, contracten en tests worden beoordeeld. SQL/mobile-conditiondekking ontbreekt.
5. Weektargets gebruiken expliciete autoritatieve previous-state-inputs. De zesweekse SQL-historyreader en zijn NULL/zero/provenance-aggregatie worden niet volledig geëmuleerd. In het model blokkeert een ontbrekende approved snapshot verdere terugkerende berekening.
6. Complete planvalidation ontbreekt: juiste targetfit, vaste composition, eligible prefixes, protocoldata, stale context, exacte restspreiding en cross-week interacties zijn geen complete simulatorpoort.
7. Blessures en sick-historyfiltering geven waar nodig NOT IMPLEMENTED/expliciete-input-gate. De huidige waterfill wordt beschreven, niet nagebootst met onbeoordeelde eenvoudiger formule.
8. Intensiteitschuld en manual-review-recovery/escalatie worden niet downstream gesimuleerd. De .20 highfraction-parameter is geen bewezen volledige branchimplementatie.
9. Actuele Phase13-zones zijn berekenbaar. Legacy model1.0, handmatige grenzen, fieldtestkwaliteit, setup/onboarding/zoneapproval-events en RPE-correctie-immutability zijn niet volledig geport.
10. Calendar spacing is alleen voor Europe/Amsterdam (huidige EU-regel) en UTC uitgewerkt. Arbitrary IANA-zones/historische DST-wetten blijven open.
11. Origineel en Joren rekenen zij-aan-zij met dezelfde expliciete vorige inputs. Eigen volledige divergerende approved multieweek-state per ruleset ontbreekt.
12. Excel Double is geen Python Decimal. Een tolerantie van 1e-9 voor numerieke asserties is geen bewijs van volledige precisiematch. Boundaries en rounding moeten afzonderlijk gecontroleerd worden.
14. Broncatalogus bevat U+FFFD replacementtekens in namen/beschrijvingen. De Excel-display markeert [bronteken ontbreekt]; exacte ongewijzigde brontekst staat in fixtures/catalog.json en extra bronkolommen. Geen oorspronkelijke punctuatie/letter wordt geraden.
13. De 40 scenariotitels op het werkblad zijn reviewtargets. Ze zijn niet automatisch 40 uitgevoerde volledige engineflows. De executable parity JSON en het rapport zijn de testbron.

## Brondiscrepanties en bereik

- Oud roadmap-/Phase3-gedrag noemt zero injury redistribution. De nieuwe actuele planning v2 gebruikt bounded 80% transfer met recipientcaps. De historische helper blijft aanwezig, maar is niet de nieuwe proposalregel.
- srpe_formula en legacy RPE-hours zijn aanwezig; actuele activiteitprocessing gebruikt ze niet als missing-datafallback. Een formule kunnen vinden bewijst niet dat de MVP haar activeert.
- Joren HR/CSS-zones hebben inclusieve gehele grenzen; bestaande fieldtest/known-value model1.0 heeft gedeelde grens met hogere-intensiteitseigendom. Beide provenanceversies blijven onderscheiden.
- Whole-workout 80/20-minuten en private high-load-budget zijn verschillende grootheden. Een geselecteerde week kan andere minuutpercentages krijgen dan de high-loadband suggereert.
- Swim-brontrainingen op afstand hebben bronload-provenance, maar current planned load=None. Dat is een echt catalogusgat en geen reden om duur te gokken.
- Eén week zonder activiteiten is door SQL gerealiseerde load0. Activiteiten met ontbrekende actuele load kunnen NULL geven. SQL SUM negeert NULL naast bekende waarden; het model neemt bij bepaalde gemengde cases conservatiever unavailable aan. Dat is een expliciete mismatch, geen parity-pass.

## Wat Joren inhoudelijk moet beoordelen

- Is 56.25 belasting/uur met sportmultipliers .90/1/1.15 de juiste vorige-maandbaseline?
- Is totale nulhistorie45 bruikbaar terwijl componenten nul blijven en restricted/partial-historycases kunnen blokkeren?
- Zijn .80 completiondrempel, +10% growth, >110% debt en >115% sessionovershoot passend?
- Is high-load70-90% van nominaal20%-budget de gewenste intensiteitsverdeling tegenover whole-workoutminuten?
- Zijn 72/48 elapsed uren passend rondom DST en consolidated low workouts?
- Is 80% injury-transfer met recipientbasis/caps verantwoord, en hoort bestaande positieve bike/swim-basis zonder nieuwe opt-in replacement toe te staan?
- Is volledige maandag-race-taper35% en partial-week fail-closed de gewenste productuitkomst?
- Welke onafhankelijke reviewprovenance ondersteunt HR/RPE-ankers en discrete zonegrenzen?
- Hoe moeten mean-HR estimates, die geen complete match opleveren, in feedback en progression worden beoordeeld?

Geen inhoudelijk voorstel wordt automatisch in de app verwerkt.
"""
)
write("KNOWN_GAPS_AND_QUESTIONS.md", gaps)
write(
    "JOREN_CHANGE_REQUEST_TEMPLATE.md",
    "# Joren wijzigingsvoorstel\n\n"
    + meta
    + "\n"
    + """RULE ID:
Categorie: CURRENT IMPLEMENTATION / INTENDED BUSINESS RULE / POSSIBLE DEFECT / JOREN PROPOSED CHANGE
Bronversie:
Huidige formule/algoritme:
Voorgestelde formule/algoritme:
Variabelen en eenheden:
Geldigheidsvoorwaarden:
Afronding en boundary ownership:
Reden en review/evidence:
Voorbeeld voor:
Voorbeeld na:
Verwacht downstream effect:
Getroffen branches en catalogus:
Veiligheids-/provenancebeslissing die expliciet nodig is:
Prioriteit:
Status:
Benodigde pariteitsscenario's:

Numerieke edit: behoud ORIGINAL in PARAMETERS!B, gebruik voorstel in C. Structurele wijziging: schrijf exact pseudocode en failurecodes. Wijzig geen Python-appcode vanuit dit reviewpakket. Een experimentele Excel-uitkomst is geen goedgekeurde nieuwe regelspecificatie.
""",
)
readme = (
    "# Joren reviewpakket gebruiken\n\n"
    + meta
    + "\n"
    + STATUS
    + "\n\n"
    + """De PDF is een zelfstandig leesbaar bronhandboek van de 66 uitgewerkte groepen en de open auditgates. Het XLSX is een zelfstandig offline, bewerkbaar gedeeltelijk rekenmodel. Het is niet de volledig gevraagde trainingsengine.

## In Excel

1. Open WOMBO_Training_Simulator.xlsx in desktop Microsoft Excel. Macro's zijn niet nodig.
2. Lees 00_START_HERE. Bewerk uren in 01_ATHLETE_INPUTS en doel/datum in 02_GOAL.
3. Geef kalibratieobservatie en RPE in 03_CALIBRATION. I=active confirmation is een expliciete scenariokeuze; berekende pending zones zijn niet automatisch actief.
4. Inspecteer 04_ZONES, de hele catalogus en de weekselector bij 10_ELIGIBLE_WORKOUTS.
5. Een handmatige workoutkeuze in 11_WORKOUT_SELECTION vraagt een aparte occurrence-ID en datum. Dit is geen complete swipe- of approval-emulatie.
6. Leg expliciet goedgekeurde vorige snapshots vast. APPROVED zonder snapshot maakt de volgende terugkerende berekening unavailable. Weektargets zijn zichtbaar in 19_NEXT_WEEK en de overview.
7. Noteer uitgevoerde activiteiten inclusief raw-zonepresent/missing, duur, RPE en eventueel gemiddelde HR. Een gemiddelde-HR-berekening vereist actieve zones.
8. PARAMETERS bewaart ORIGINAL en JOREN VALUE gescheiden. Beide outputs staan naast elkaar. De volledige eigen ruleset-statepropagation is een open gate.
9. Schrijf wijzigingen op in 25_JOREN_CHANGES. Alleen geteste scenario's uit PARITY_TEST_REPORT gelden als verificatie.

## Regenereren (repository nodig)

- Gebruik de gepinde geïsoleerde branch. Scripts bevinden zich onder docs/joren-training-review/scripts.
- Python3.10+ met de backenddependencies: python scripts/inventory.py; python scripts/make_parity_cases.py.
- Gebruik de gebundelde @oai/artifact-tool JS-runtime en maak in scripts een node_modules-junction naar diens node_modules. node scripts/build_workbook.mjs bouwt de XLSX. Afhankelijkheid is geen normale workbook-runtimevereiste.
- powershell -File scripts/verify_excel.ps1 -PackagePath <absolute pakketmap> voert Excel COM tests uit op een tijdelijke kopie, herstelt inputscenario's en herberekent de handoff-XLSX.
- Python met reportlab: python scripts/build_documents.py. Poppler: pdftoppm -png -r 80 WOMBO_Complete_Training_Logic.pdf qa/pdf-final/page. Render alle pagina's en beoordeel layout.
- Python met pdfplumber/pypdf/Pillow: python scripts/verify_artifacts.py; bekijk alle renders en bevestig daarna met --visual-review-confirmed. python scripts/build_reports.py bouwt de rapporten.
- Generatorchecks vanaf de pakketmap: python -m ruff check --config ../../backend/pyproject.toml scripts; python -m ruff format --check --config ../../backend/pyproject.toml scripts. Gebruik expliciet deze backendconfiguratie.
- Na nieuwe edits: herbereken, controleer native Excel, vernieuw PARITY_TEST_REPORT, coverage en FINAL_REPORT. Een geschreven formule is geen geslaagde berekening.

Geen appcode, schema of data wordt door deze scripts gewijzigd. Geen productie/stagingverbinding is nodig. Alle voorbeelden zijn synthetisch.
"""
)
write("README.md", readme)
# Reader-facing narrative, followed by a rule reference that translates formulas rather than pastes functions.
chapters = [
    (
        "1. Samenvatting",
        "Dit pakket beschrijft de actuele bronversie en maakt een deel van de numerieke regels controleerbaar in Excel. De complete audit en alle-path simulator zijn niet afgerond. De volledigheidsgate blijft open. De hoofdbeperking is niet een ontbrekend opmaakdetail: automatische constrained search, volledige statehistorie en meerdere adaptationbranches ontbreken in het XLSX.",
    ),
    (
        "2. Hoe de engine werkt",
        "Onboarding levert bevestigde profiel-, doel-, historie- en zone-inputs. Deterministische Python bepaalt de target, fase en catalogusgeschiktheid. Een begrensde multisetsearch levert een mogelijke combinatie en vaste swipecompositie. De sporter kiest occurrences. Plaatsing wordt gevalideerd en opgeslagen als pending voorstel. Pas afzonderlijke goedkeuring activeert een revision. Observaties krijgen een eigen private-loadsnapshot. De volgende week gebruikt autoritatieve historie. De LLM legt uit en berekent of activeert niets.",
    ),
    (
        "3. Invoer en afhankelijkheden",
        "Historie is het gemiddelde aantal minuten per week in de vorige maand, per goalsport, met actuele baselineversie. Nul is een echte waarde; ontbrekend is geen nul. Rusthartslag en leeftijd komen niet voor in startbelasting. Rusthartslag is wel een onboardingvereiste en komt in historische biometrische fallback voor. Race type bepaalt sporten; race date bepaalt fase/taper. Gewenste tijd, afstanden en racenaam zijn opgeslagen doelcontext; resolve_target leidt daar geen tempo- of loadcoëfficiënt uit af. Beschikbare datums beperken plaatsing, niet een verzonnen uurvolume-cap.",
    ),
    (
        "4. Formuleoverzicht en eenheden",
        "Interne belasting is geen minuut, hartslag of sessie-RPE. Duur staat in minuten; HR in bpm; CSS in sec/100m; runtempo in sec/km; power in watt; kalenderdatum in lokale maandag-zondagweken. De startberekening gebruikt uren na minuten/60. Zone-load telt minuten maal per-sport/zonecoëfficiënten. De referentie hieronder geeft iedere formule met bron, voorwaarden en workbookkoppeling. Geen algemene sportwetenschappelijke formule is als vervanging ingevoerd.",
    ),
    (
        "5. Initiële capaciteit",
        "L_swim=h_swim×56.25×.90; L_bike=h_bike×56.25; L_run=h_run×56.25×1.15. Components worden niet individueel afgerond. Totale som krijgt HALF_UP op één decimaal. Bij totale nulhistorie is het target45.0, terwijl per-sportcomponents0 blijven. Voor run3uur resulteert194.0625 exact en194.1 totaal. Eerste gewone planning gebruikt BASE ongeacht nominale recoverypositie, zolang geen goedgekeurd priorplan bestaat. Kalibratieactiviteit is geen goedkeuring.",
    ),
    (
        "6. Kalibratie en zones",
        "Phase13 submaximale kalibratie deelt HR of zwemtempo door het RPE-anker en rondt de drempel geheel HALF_UP af. HR/CSS krijgen het Phase13-model. Veldtesten blijven een ander protocol en kunnen model1.0-profielen opleveren. Integergrenzen van Phase13 zijn aansluitend en inclusief. De oudere modelgrenzen geven gedeelde waarden aan hogere intensiteit. Een berekende drempel/zone is pending; expliciete athleteconfirmation blijft vereist. Geen sporter krijgt een actieve drempel omdat een formulecel een getal toont.",
    ),
    (
        "7. RPE en activiteitbelasting",
        "De tekstuele RPE-keuze is integer1..10. Zone-minuten bepalen actuele private load als betrouwbare totale duur en positieve validtime bestaan. Gedeeltelijke zonedata worden niet opgehoogd. Ontbrekende zonearray kan voor run/bike met bekende bevestigde HR-zones terugvallen op full-duration mean-HR-estimate. Een expliciete array met vijf nullen is niet hetzelfde als ontbrekend. RPE×uren en sRPE-factor² zijn historische/referentieformules; geen actieve missing-datafallback.",
    ),
    (
        "8. Fases en progressie",
        "De racemaandag verankert het4+1ritme. Taper gaat vóór recovery, die vóór schuld en gewone progressie gaat. Sicknesssamples worden uitgesloten. Gemist/vermoeid bij lagere realized gebruikt realized×1.10. Regulier bij minstens80% gebruikt planned×1.10. Meer dan110% activeert volumeschuld. Ontbrekende realized houdt planned; geen activiteiten is in de SQL-reader expliciet0. Recovery gebruikt.60×vorige planned. Volledige A-taper gebruikt.35×gemiddelde planned niet-recovery samples in42dagen.",
    ),
    (
        "9. Catalogus en geschiktheid",
        "De lokale auditprojectie omvat162 actuele templates, waaronder alle154 brontrainingen. Ze zijn inspecteerbaar inclusief duration/distance, whole-bucket, requirements, phase, source-ID en segments in JSON. De bron-CSV is niet vervangen door voorbeeldtrainingen. Distance-only swims behouden source-loadprovenance maar hebben current planned loadNone en vallen uit targetfit. De v2-migratie genereert willekeurige nieuwe UUIDs; die deployedidentiteit is niet uit de repository te reconstrueren. Exacte productiontie-breakerpariteit blijft daarom open.",
    ),
    (
        "10. Selectie als constrained search",
        "Automatische keuze is geen enkele spreadsheetvergelijking. De engine groepeert equivalente candidates op sport, load, whole-bucket en Z5-status. Kleinste immutable UUID is representant tenzij maximumuses gelden. Start met prefix; breid states uit met één occurrence tot maximaal24. Een state omvat total/highload, counts per sport, highcounts, limited-usecounts en Z5presence. Snoei ongeldige count-, highbudget-, load- en sportcapstates. Beoordeel volledige discipline/compositioncoverage, strikte targetfittolerantie en indien toepasselijk schedulefeasibility. Kies lexicografisch loadverschil, highloadbudgetverschil, count en UUID-pad. Stop na huidige count als exact target gevonden. Dit algoritme is beschreven, niet als simpeler Excelheuristiek nagebootst.",
    ),
    (
        "11. Plaatsing",
        "HIGH wordt eerst geplaatst, daarna sport en UUID. Backtracking onderzoekt beschikbare datums in volgorde laagste gebruik, kortste maximale reststreak na toevoeging en datum. Meerdere sessies op één dag zijn toegestaan. Een maximaal3daagse reststreak wordt alleen afgedwongen als de count en availability dat kunnen realiseren en er geen fixedplaatsingen zijn. Per sport HIGH moet run72/bike48/swim48 werkelijk verstreken uren vrij zijn. Lokale datum wordt intern op12:00 geprojecteerd; het is geen trainingsuurvoorschrift. DST kan dus kalenderafstand en uurafstand laten verschillen.",
    ),
    (
        "12. Blessures en cross-training",
        "Huidige v2 berekent eerst normaal weektarget. Per-sportbasis komt uit laatste goedgekeurde sportloads of onboardingcomponents. Projecteer het target proportioneel; verwijder blocked sporten. Hoogstens80% van verwijderde load mag naar bike/swim met positieve basis en geschikte lowtraining. Safe cap=max(normaal target,1.10×priorbasis). Waterfill verdeelt gewogen ruimte en herverdeelt na cap; overschot verdwijnt. Run ontvangt niets. Nulbasisopt-in creëert geen capacity. Replacement blijft low-only en creëert geen nieuw highbudget. Eerdere zero-redistributionhelpers zijn historisch, geen nieuweproposalgedrag.",
    ),
    (
        "13. Goedkeuring en revisions",
        "Het actieve plan en pending voorstel bestaan naast elkaar. Een swipeaccept is geen planapproval. Owner, proposalstate, targetrevisionstate en expected/base/active revision worden atomair gecontroleerd. Goedkeuren supersedet oude active, activeert target en markeert proposal applied. Verwerpen behoudt oude active. Idempotente applied/rejected retry is specifiek toegestaan volgens bronvoorwaarden. Een worksheetdropdown emuleert database-locking, ownerisolation of exacteventhistorie niet. Het workbook labelt zijn approvalkeuze daarom extern en de complete lifecycle als open.",
    ),
    (
        "14. Gepland versus geobserveerd",
        "Timed sourceworkouts behouden hun gereviewde predefinedload. Niet-source timed zoneworkouts gebruiken de actuele zonecoëfficiënten. Historische records blijven onder eigen versie/methode. Observaties kunnen meer/minder duren, andere zones hebben of los van plannedworkout bestaan. De matchmatrix geeft incomplete/estimated meting eerst deviation tenzij low+RPE≥7 hiddenfatigue. Complete unplanned krijgt unplanned. Daarna hiddenfatigue, ontbrekende plannedbasis, >115%overshoot, inclusieve90-110% met RPErange, anders deviation. Mean-HR-estimate is bewust niet complete.",
    ),
    (
        "15. Volgende week",
        "De SQL-reader creëert maximaalzes complete kalenderweken sinds vroegste plan/activityevidence, met expliciete NULL/0-semantiek en current-loadprovenance. Actorapproval komt uit approved active/superseded revisions, niet rowexistence. Het Excelmodel heeft zestien targetregels, maar gebruikt expliciete previous-state-inputs en handmatige approvalsnapshots. Het produceert geen volledig autonome reeks workouts/approvals/events. Eigen divergerende experimentalhistorie is niet geïmplementeerd.",
    ),
    (
        "16. Fout- en ontbrekende-datapaden",
        "Legitieme fouten zijn uitkomsten. Voorbeelden: previous_month_history_required; zero_history_discipline_baseline_unavailable; approved_plan_baseline_unavailable; partial_week_taper_rule_required; taper_baseline_unavailable; catalog_empty; catalog_phase_coverage_unavailable; catalog_capacity_unsatisfied; rest_or_anti_stack_unsatisfied; swipe_candidate_stale; anti_stack_violation. Nul kandidaten kan correct zijn. Geen output mag als succesvol plan worden gelabeld omdat een targetgetal bestaat. De appendixregels geven precondities en no-resultgedrag; discoveryrecords die nog niet handmatig zijn vertaald blijven open.",
    ),
    (
        "17. Volledige rekenvoorbeelden",
        "Voorbeeld A: nieuwe runathleet met3uur/week heeft194.0625component en194.1target. Zonder eerdere approval is gewone faseBASE, ook als kalibratieactiviteit bestaat. Vervolgens is echte eligible multisetsearch nodig; er wordt geen fictieve workoutcombinatie ingevuld. Voorbeeld B: vorige approved planned100 en complete realized80 geeft regulier110; realized79 geeft gemiddelde aanwezige realizedsamples, hier79. Met fatigue en realized50 wordt55 vóór gewone80%-logica. Voorbeeld C: planned100, realized120 activeert debt20; nexttarget110-20=90. Bij realized110 bestaat geen debt. Voorbeeld D: recovery na planned200 geeft120; volledige A-taper met eligible plannedbaseline200 geeft70. Een zondagwedstrijd maakt een partialweektaper waarvoor de planner fail-closed is. Voorbeeld E: run60min waarvan30min bekendeZ2 levert27.6, coverage.5 enpartial_observed;60min gemiddeldeHRZ2 levert55.2 als estimate, coverage0, niet complete. Dit zijn complete numerieke berekeningen, geen beweerde volledige workout-state-simulaties.",
    ),
    (
        "18. Aannames en wetenschappelijke toets",
        "Correcte softwarepariteit bewijst niet dat de fysiologische aannames verantwoord zijn. Coëfficiënten,45nulbasis, thresholds, anchors, recovery/taperfactoren en recipientcaps zijn geïmplementeerd beleid met bronprovenance. Dit auditpakket verzamelt geen nieuwe externe wetenschappelijke evidence en verklaart geen klinische geldigheid. Er zijn geen vervangende normen bedacht.",
    ),
    (
        "19. Implementatiebeperkingen",
        "Het XLSX is functioneel voor de expliciete numerieke onderdelen, met nativeherberekening en zichtbare formules. Het is ONVOLLEDIG als standalone all-path trainingsengine. Geen XLSM is geleverd: VBProject is hier programmatisch onbeschikbaar en er is geen geverifieerde VBA-port. Automatische selectie/plaatsing, injury-waterfill, intensiteitschuld, volledige protocolkwaliteit, historische RPE-correcties en alleapprovalevents zijn open. De mapping en parityreport specificeren wat wel werkelijk getest is.",
    ),
    (
        "20. Wat Joren inhoudelijk moet beoordelen",
        "Beoordeel56.25 en sportmultipliers; beginners45 en partial-historyblokkades;10%progressie en80%completion;debt110% ensessionovershoot115%; high-load70-90% van20%-budget versus whole-workoutminuten;72/48 elapseduur rondomDST; capped injurytransfer en consent bij bestaande basis; ontbrekende meetwaarden; mean-HR-estimates in feedback; volledige/partialtaper; traceerbare reviewer/evidence voor calibratieankers. Dit zijn reviewvragen, geen automatisch vastgestelde defecten.",
    ),
    (
        "21. Wijzigingen voorstellen",
        "Gebruik stabiele RULE ID en houd categorieën gescheiden: CURRENT IMPLEMENTATION, INTENDED BUSINESS RULE, POSSIBLE DEFECT, JOREN PROPOSED CHANGE. Leg huidige en voorgestelde formule, eenheden, activationbranches, equalityownership, rounding en voor/naexample vast. In Excel blijft ORIGINAL bewaard; JOREN VALUE activeert het voorstel. Structurele algoritmen vereisen expliciete port en eigen tests. Appcode, schema en historische records blijven ongewijzigd.",
    ),
    (
        "22. Bronnen en verificatie",
        "De bron is lokaal gepind; bronmanifest bevat bestandshashes. De PDF verwijst naar functies en lijnnummers, de traceabilityMarkdown naar discoveryfuncties. Bestaande backendtests en nativeExcelasserties zijn verschillend bewijs. NativeExcel controleert echte gewijzigde inputs en restore in een tijdelijke kopie; formuleteksten zijn geen bewijs. De 1250 syntactische beslispunten zijn niet allemaal reviewed of getest. SQL/mobilebranchanalyse en complete source-to-workbookdekking blijven open.",
    ),
    (
        "23. Regel naar Excel",
        "De volgende referentie koppelt66 beschreven regels aan bron en workbook. NOT IMPLEMENTED betekent werkelijk ontbrekende equivalentie. PARTIAL betekent dat slechts expliciete assertions in het rapport zijn gecontroleerd. De29tabs geven werkgebieden en open branches weer; aanwezigheid van een tab sluit geen featuregate. Raadpleeg het losgeleverde PARITY_TEST_REPORT en FINAL_REPORT voor de actuele aantallen en beperkingen.",
    ),
]
handbook = "# WOMBO - trainingslogica\n\n" + meta + "\n" + STATUS + "\n\n"
for title, body in chapters:
    handbook += "## " + title + "\n\n" + body + "\n\n"
handbook += "## Regelreferentie\n\n" + inventory[inventory.index("## INIT-01") :]
write("HANDBOOK.md", handbook)
# Readable PDF with actual TOC, named references and flowing paragraph formulas.
fontdir = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("AuditArial", str(fontdir / "arial.ttf")))
pdfmetrics.registerFont(TTFont("AuditArialBold", str(fontdir / "arialbd.ttf")))
pdfmetrics.registerFontFamily(
    "AuditArial",
    normal="AuditArial",
    bold="AuditArialBold",
    italic="AuditArial",
    boldItalic="AuditArialBold",
)
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="AuditBody", fontName="AuditArial", fontSize=10, leading=15, spaceAfter=9
    )
)
styles.add(
    ParagraphStyle(
        name="AuditHeading",
        fontName="AuditArialBold",
        fontSize=17,
        leading=22,
        spaceBefore=15,
        spaceAfter=12,
        keepWithNext=True,
        textColor=colors.HexColor("#243C58"),
    )
)
styles.add(
    ParagraphStyle(
        name="AuditSub",
        fontName="AuditArialBold",
        fontSize=12,
        leading=17,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="AuditSmall",
        fontName="AuditArial",
        fontSize=8,
        leading=11,
        spaceAfter=7,
        wordWrap="CJK",
    )
)
styles.add(
    ParagraphStyle(
        name="AuditEquation",
        fontName="AuditArial",
        fontSize=10,
        leading=16,
        spaceAfter=10,
        borderColor=colors.HexColor("#D8E2ED"),
        borderPadding=8,
        backColor=colors.HexColor("#F0F4F8"),
    )
)


class HandbookDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "AuditHeading":
            txt = flowable.getPlainText()
            if txt == "Inhoud" or txt.startswith("WOMBO"):
                return
            key = "heading" + str(self.seq.nextf("heading"))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, 0)
            self.notify("TOCEntry", (0, txt, self.page, key))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("AuditArial", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(
        42, 25, "WOMBO | INTERNAL BUSINESS / ENGINE REVIEW | bron 6b1189b"
    )
    canvas.drawRightString(A4[0] - 42, 25, str(doc.page))
    canvas.restoreState()


pdf = OUT / "WOMBO_Complete_Training_Logic.pdf"
doc = HandbookDoc(
    str(pdf),
    pagesize=A4,
    leftMargin=45,
    rightMargin=45,
    topMargin=44,
    bottomMargin=43,
    title="WOMBO - trainingslogica en simulatoraudit",
    author="WOMBO interne engine review",
)
doc.addPageTemplates(
    PageTemplate(
        id="normal",
        frames=[
            Frame(
                45,
                43,
                A4[0] - 90,
                A4[1] - 87,
                id="main",
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
            )
        ],
        onPage=footer,
    )
)
story = []


def readable(text):
    import re

    text = re.sub(r"([a-zé])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
    return text


def p(text, sty="AuditBody"):
    if sty in ("AuditBody", "AuditHeading", "AuditSub"):
        text = readable(text)
    return Paragraph(escape(text).replace("\n", "<br/>"), styles[sty])


story += [
    Spacer(1, 55),
    p("WOMBO\nTrainingslogica", "AuditHeading"),
    p("Formules, beslissingen en offline rekenmodel", "AuditSub"),
    Spacer(1, 22),
    p("INTERNAL BUSINESS / ENGINE REVIEW\nNOT FOR END-USER DISTRIBUTION"),
    p("8 oktober 2026"),
    p(
        "STATUS: ONVOLLEDIG\nVolledige all-path simulator en pariteit zijn niet bewezen.",
        "AuditEquation",
    ),
    p(
        "66 uitgewerkte regelgroepen; 676 ontdekte functies; 1250 syntactische beslispunten.\nAlle154 brontrainingen aanwezig in een162-template lokale catalogusprojectie."
    ),
    p(meta, "AuditSmall"),
    PageBreak(),
    p("Inhoud", "AuditHeading"),
]
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle(
        name="TOC0",
        fontName="AuditArial",
        fontSize=9,
        leading=12,
        leftIndent=0,
        firstLineIndent=0,
        spaceBefore=0,
    )
]
story += [toc, PageBreak()]


def review_table(headers, rows, widths):
    data = [[p(v, "AuditSmall") for v in headers]] + [
        [p(str(v), "AuditSmall") for v in row] for row in rows
    ]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F0")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F4F7FA")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return KeepTogether([table, Spacer(1, 8)])


for title, body in chapters:
    story += [p(title, "AuditHeading"), p(body)]
    if title.startswith("2."):
        story += [
            review_table(
                ["Stap", "Deterministische uitkomst", "Externe keuze / gate"],
                [
                    (
                        "Invoer en historie",
                        "Versies, expliciete minuten, goalsporten",
                        "Athleet bevestigt invoer",
                    ),
                    (
                        "Kalibratie en zones",
                        "Drempel/zonevoorstel met modelversie",
                        "Bevestiging vereist",
                    ),
                    (
                        "Weektarget",
                        "Fase, basis, target en eventuele fout",
                        "Autoritatieve approved historie",
                    ),
                    (
                        "Catalogus en selectie",
                        "Gefilterde kandidaten en constrained multiset",
                        "Swipes zijn keuzes",
                    ),
                    (
                        "Plaatsing en voorstel",
                        "Datums, validatie, pending revision",
                        "Nog niet actief",
                    ),
                    (
                        "Goedkeuring",
                        "Atomair actief/superseded/applied",
                        "Athleet bevestigt voorstel",
                    ),
                    (
                        "Activiteiten en volgende week",
                        "Loadsnapshot en historiebasis",
                        "Metingen kunnen ontbreken",
                    ),
                ],
                [115, 195, 195],
            ),
            Spacer(1, 12),
        ]
    if title.startswith("4."):
        story += [
            review_table(
                ["Sport", "Z1", "Z2", "Z3", "Z4", "Z5"],
                [
                    ("Swim", ".45", ".72", "1.08", "1.44", "1.80"),
                    ("Bike", ".50", ".80", "1.20", "1.60", "2.00"),
                    ("Run", ".58", ".92", "1.38", "1.84", "2.30"),
                ],
                [100, 81, 81, 81, 81, 81],
            ),
            p(
                "Alle tabelwaarden zijn interne belasting per minuut; bron: physiology/joren.py, LOAD-01."
            ),
        ]
    if title.startswith("6."):
        story += [
            review_table(
                ["RPE", "HR-anker", "Zwemanker"],
                [
                    (i + 1, h, s)
                    for i, (h, s) in enumerate(
                        zip(
                            [
                                ".70",
                                ".78",
                                ".84",
                                ".88",
                                ".91",
                                ".94",
                                ".97",
                                "1",
                                "1.03",
                                "1.06",
                            ],
                            [
                                "1.25",
                                "1.18",
                                "1.12",
                                "1.08",
                                "1.06",
                                "1.04",
                                "1.01",
                                "1",
                                ".96",
                                ".92",
                            ],
                        )
                    )
                ],
                [85, 210, 210],
            ),
            p("Ankers zijn dimensieloze delers; bron: CAL-01/02."),
        ]
    if title.startswith("8."):
        story += [
            review_table(
                ["Prioriteit", "Voorwaarde", "Uitkomst"],
                [
                    (
                        "1",
                        "Eerdere approval, geen eligible historie",
                        "approved_plan_baseline_unavailable",
                    ),
                    ("2", "Geen maandag / race voor week", "Inputfout"),
                    ("3", "Maintenance actief", "Historie vereist; 5e week recovery"),
                    (
                        "4",
                        "Taper overlap",
                        "Alleen volledige week ondersteund; planned baseline × .35",
                    ),
                    ("5", "Geen eerdere approval", "BASE en onboardingbaseline"),
                    ("6", "Recoverypositie", "Vorige planned × .60"),
                    ("7", "Minder uitgevoerd en reduced of count=0", "Realized × 1.10"),
                    (
                        "8",
                        "Realized > 1.10 × planned",
                        "Schuld; bij onveilig resultaat manual review",
                    ),
                    (
                        "9",
                        "Realized beschikbaar, geen schuld",
                        "80%-drempel of 42-daagse baseline",
                    ),
                    ("10", "Realized ontbreekt", "Houd vorige planned"),
                ],
                [65, 210, 230],
            ),
            p(
                "Deze volgorde komt uit resolve_target. Injury adjustment en catalogusvalidation volgen als aparte gates."
            ),
        ]
story += [PageBreak(), p("Regelreferentie", "AuditHeading")]
for r in rules:
    story += [
        p(r["id"] + " - " + r["name"], "AuditSub"),
        p(r["formula"], "AuditEquation"),
        p("Inputs: " + r["inputs"], "AuditSmall"),
        p("Eenheden: " + r["input_units"]),
        p("Voorwaarden: " + r["conditions"]),
        p("Voorbeeld: " + r["example"]),
        p("Afronding: " + r["rounding"]),
        p(
            "Fout/no-result: "
            + (
                "; ".join(r["failure"])
                or "Geen expliciete failure in deze functie; zie voorwaarden en callers."
            ),
            "AuditSmall",
        ),
        p(
            "Bron: "
            + r["path"]
            + "; "
            + r["function"]
            + "; regels "
            + str(r["start"])
            + "-"
            + str(r["end"]),
            "AuditSmall",
        ),
        p("Excel: " + r["excel"], "AuditSmall"),
    ]
story += [
    PageBreak(),
    p("Auditgates en bronbestanden", "AuditHeading"),
    p(
        "Dit handboek is geen bewijs dat alle676 functies handmatig beoordeeld zijn. De machineleesbare inventaris en de dekkingsmatrix zijn expliciet open waar vertaling/pariteit ontbreekt. SQLmigraties zijn bronbewijsmateriaal, niet uitgevoerd. Geen backend/mobilecode is gewijzigd."
    ),
    p(
        "Volledig bronmanifest staat in fixtures/source_manifest.json en ENGINE_SOURCE_TRACEABILITY.md. Onderstaande lijst geeft de gebruikte enginebronmodules."
    ),
]
for x in manifest:
    if "/app/modules/" in x["path"]:
        story.append(p(x["path"] + " (" + str(x["lines"]) + " regels)", "AuditSmall"))
doc.multiBuild(story)
print(json.dumps({"pdf": str(pdf), "rules": len(rules), "status": "INCOMPLETE"}))

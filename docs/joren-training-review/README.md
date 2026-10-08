# Joren reviewpakket gebruiken

INTERNAL BUSINESS / ENGINE REVIEW
NOT FOR END-USER DISTRIBUTION

Bronbranch: fix/catalog-capacity-fresh-athlete
Volledige SHA: 6b1189b70a6505726fef70c4616a2f3d6dd4c94a
Auditbranch: docs/joren-training-engine-simulator
Datum: 8 oktober 2026

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

De PDF is een zelfstandig leesbaar bronhandboek van de 66 uitgewerkte groepen en de open auditgates. Het XLSX is een zelfstandig offline, bewerkbaar gedeeltelijk rekenmodel. Het is niet de volledig gevraagde trainingsengine.

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
- Generatorchecks vanaf de pakketmap: python -m ruff check --config ../../backend/pyproject.toml scripts; python -m ruff format --check --config ../../backend/pyproject.toml scripts. Gebruik expliciet deze backendconfiguratie.
- Na nieuwe edits: herbereken, controleer native Excel, vernieuw PARITY_TEST_REPORT, coverage en FINAL_REPORT. Een geschreven formule is geen geslaagde berekening.

Geen appcode, schema of data wordt door deze scripts gewijzigd. Geen productie/stagingverbinding is nodig. Alle voorbeelden zijn synthetisch.

Na rendering: python scripts/verify_artifacts.py --visual-review-confirmed (alleen na het daadwerkelijk bekijken van de PNGs); python scripts/build_reports.py vernieuwt rapporten en DELIVERY_FILES.json uit opgenomen bewijs.

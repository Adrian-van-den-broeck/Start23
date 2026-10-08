# Excel/Python-pariteitsrapport

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

Bron: fix/catalog-capacity-fresh-athlete, 6b1189b70a6505726fef70c4616a2f3d6dd4c94a. Native Excel 16.0; run UTC 2026-10-08T21:19:49.5507055Z.

120 uitgevoerde scenario’s; 577 assertions; 577 PASS; 0 FAIL; 0 native formulefouten. Maximale waargenomen numerieke afwijking: 1.13686837721616e-13.

Dit is pariteit voor beperkte numerieke onderdelen en enkele eigenschappen. Het is GEEN volledige engine-, branch-, sequence- of cataloguspariteit. De 40 reviewscenario’s op tab 22 zijn geen automatisch geladen en geteste volledige engineflows.

## Methode

1. make_parity_cases.py voert de gepinde Python-domeinfuncties offline uit: starting_baseline, calibrate, zone_load, average_hr_zone_load, classify_activity_match en resolve_target.
2. FRESH/MISSING bevatten daarnaast expliciete bronafgeleide invariant-/gateasserties. PROPERTY-cases zijn workbookeigenschappen, geen goedgekeurde alternatieve Python-ruleset. Ze tellen mee als assertions, niet als zelfstandige productie-algoritmen.
3. verify_excel.ps1 opent een tijdelijke kopie in werkelijke desktop Excel, wijzigt inputs, voert CalculateFullRebuild uit en leest Value2. Het stelt geen PASS vast door geschreven formuletekst te lezen.
4. Iedere input wordt hersteld inclusief oorspronkelijke formule/type. Na de hele set worden alle gebruikte cellen op formule-errors onderzocht. Een mismatch geeft een fout-exit.
5. De oorspronkelijke, nieuw gegenereerde handoff-XLSX wordt daarna herberekend en opgeslagen. Er zijn geen workbookcalls naar Python, de app, Supabase of Railway.

Numeriek wordt absolute tolerantie 1e-9 gebruikt. Strings en foutcodes worden exact vergeleken. HALF_UP-gedrag bij positieve getallen wordt met expliciete cases getoetst; Excel Double is geen Decimal en alle numerieke combinaties zijn niet bewezen. Datums zijn gehele Excel-kalenderdagen. De propertytest controleert dat voorbeelddata geen verborgen tijddeel behouden.

## Daadwerkelijk getoetste onderdelen

| Groep | Scenario’s | Assertions | Bereik |
| --- | --- | --- | --- |
| BASE | 12 | 48 | Componenten en totaal; nul, gemengd, fracties, 168 uur |
| CAL | 30 | 330 | 3 sporten × RPE1..10; drempel en alle zonegrenzen |
| ZONELOAD | 30 | 90 | 3 sporten × 5 zones × complete/partial; load, coverage, status |
| MEAN | 10 | 30 | Run/bike gemiddelde HR met bevestigde actieve zones |
| MATCH | 14 | 28 | RPE4/7; inclusief .90/1.10 en strikt >1.15 |
| TARGET | 7 | 21 | Hold, 80%, <80%, 110%, debt, fatigue en geen completions |
| FRESH | 2 | 4 | Activiteiten zijn geen approval; eerste BASE blijft |
| MISSING | 3 | 3 | Expliciete nulzones, gedeeltelijke tijd, pending HR-profile |
| PHASE | 8 | 12 | Recovery, full/partial taper, ontbrekende baseline, prioriteit, datumfouten |
| PROPERTY | 4 | 11 | Original-isolation, rustHR onafhankelijk, gehele datums, eigen Joren-HR-zone |

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

| ID | Regel/eigenschap | Assertions | Resultaat |
| --- | --- | --- | --- |
| BASE-00 | INIT-01/02 | 4 | PASS |
| BASE-01 | INIT-01/02 | 4 | PASS |
| BASE-02 | INIT-01/02 | 4 | PASS |
| BASE-03 | INIT-01/02 | 4 | PASS |
| BASE-04 | INIT-01/02 | 4 | PASS |
| BASE-05 | INIT-01/02 | 4 | PASS |
| BASE-06 | INIT-01/02 | 4 | PASS |
| BASE-07 | INIT-01/02 | 4 | PASS |
| BASE-08 | INIT-01/02 | 4 | PASS |
| BASE-09 | INIT-01/02 | 4 | PASS |
| BASE-10 | INIT-01/02 | 4 | PASS |
| BASE-11 | INIT-01/02 | 4 | PASS |
| CAL-swim-1 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-2 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-3 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-4 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-5 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-6 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-7 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-8 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-9 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-swim-10 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-1 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-2 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-3 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-4 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-5 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-6 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-7 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-8 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-9 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-bike-10 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-1 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-2 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-3 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-4 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-5 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-6 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-7 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-8 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-9 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| CAL-run-10 | CAL-01/02;ZONE-01/02 | 11 | PASS |
| ZONELOAD-swim-1-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-1-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-2-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-2-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-3-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-3-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-4-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-4-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-5-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-swim-5-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-1-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-1-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-2-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-2-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-3-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-3-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-4-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-4-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-5-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-bike-5-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-1-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-1-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-2-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-2-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-3-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-3-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-4-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-4-0.5 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-5-1 | LOAD-01/02 | 3 | PASS |
| ZONELOAD-run-5-0.5 | LOAD-01/02 | 3 | PASS |
| MEAN-run-1 | LOAD-03 | 3 | PASS |
| MEAN-run-2 | LOAD-03 | 3 | PASS |
| MEAN-run-3 | LOAD-03 | 3 | PASS |
| MEAN-run-4 | LOAD-03 | 3 | PASS |
| MEAN-run-5 | LOAD-03 | 3 | PASS |
| MEAN-bike-1 | LOAD-03 | 3 | PASS |
| MEAN-bike-2 | LOAD-03 | 3 | PASS |
| MEAN-bike-3 | LOAD-03 | 3 | PASS |
| MEAN-bike-4 | LOAD-03 | 3 | PASS |
| MEAN-bike-5 | LOAD-03 | 3 | PASS |
| MATCH-.899-4 | ACT-01 | 2 | PASS |
| MATCH-.899-7 | ACT-01 | 2 | PASS |
| MATCH-.9-4 | ACT-01 | 2 | PASS |
| MATCH-.9-7 | ACT-01 | 2 | PASS |
| MATCH-1-4 | ACT-01 | 2 | PASS |
| MATCH-1-7 | ACT-01 | 2 | PASS |
| MATCH-1.1-4 | ACT-01 | 2 | PASS |
| MATCH-1.1-7 | ACT-01 | 2 | PASS |
| MATCH-1.1001-4 | ACT-01 | 2 | PASS |
| MATCH-1.1001-7 | ACT-01 | 2 | PASS |
| MATCH-1.15-4 | ACT-01 | 2 | PASS |
| MATCH-1.15-7 | ACT-01 | 2 | PASS |
| MATCH-1.1501-4 | ACT-01 | 2 | PASS |
| MATCH-1.1501-7 | ACT-01 | 2 | PASS |
| TARGET-00 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-01 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-02 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-03 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-04 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-05 | PLAN-07/08/09/10 | 3 | PASS |
| TARGET-06 | PLAN-07/08/09/10 | 3 | PASS |
| FRESH-False | PLAN-01 | 2 | PASS |
| FRESH-True | PLAN-01 | 2 | PASS |
| MISSING-00 | LOAD-02/03 | 1 | PASS |
| MISSING-01 | LOAD-02/03 | 1 | PASS |
| MISSING-02 | LOAD-02/03 | 1 | PASS |
| PHASE-RECOVERY | PLAN-01/02/03/05/06 | 3 | PASS |
| PHASE-FULL-TAPER | PLAN-01/02/03/05/06 | 3 | PASS |
| PHASE-PARTIAL-TAPER | PLAN-01/02/03/05/06 | 1 | PASS |
| PHASE-TAPER-MISSING | PLAN-01/02/03/05/06 | 1 | PASS |
| PHASE-PAST-RACE | PLAN-01/02/03/05/06 | 1 | PASS |
| PHASE-INVALID-MONDAY | PLAN-01/02/03/05/06 | 1 | PASS |
| PHASE-APPROVED-MISSING | PLAN-01/02/03/05/06 | 1 | PASS |
| PHASE-PRIORITY-MISSING-TAPER | PLAN-01/02/03/05/06 | 1 | PASS |
| PROPERTY-EXPERIMENTAL-GROWTH | PROPERTY: original constant/output isolation | 4 | PASS |
| PROPERTY-RESTHR-UNUSED | PROPERTY: resting HR not in baseline | 1 | PASS |
| PROPERTY-DEFAULT-CALENDAR-DATES | PROPERTY: exported calendar dates have no time component | 2 | PASS |
| PROPERTY-EXPERIMENTAL-HR-ZONE | PROPERTY: experimental HR threshold drives its own zone | 4 | PASS |

Volledige actual/expected/difference per cel: qa/native-parity-results.json. Reproduceerbare inputs: fixtures/parity_cases.json. De handoff-hashes staan in FINAL_REPORT en qa/artifact-validation.json.

# Eindrapport Joren-engine-review

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

INTERNAL BUSINESS / ENGINE REVIEW
NOT FOR END-USER DISTRIBUTION

De opdracht is niet volledig afgerond. Er zijn twee zelfstandig bruikbare reviewbestanden en reproduceerbaar testbewijs, maar geen complete standalone all-path trainingssimulator. De PDF beschrijft 66 uitgewerkte groepen; zij is geen afgeronde audit van iedere bereikbare regel.

## Bron en isolatie

- Referentiebranch: fix/catalog-capacity-fresh-athlete.
- Volledige engine-SHA: 6b1189b70a6505726fef70c4616a2f3d6dd4c94a.
- Auditbranch: docs/joren-training-engine-simulator.
- Werkboom: .worktrees/joren-training-engine-simulator.
- Onverwante wijzigingen in de oorspronkelijke werkboom en UI V2 zijn niet gestasht, gereset, gemerged of overschreven.

De relevante backend/Supabasebestanden van de UI V2-werkboom waren gelijk aan de geselecteerde actuele enginebasis. De verse-athleetfix is onderdeel van de referentie. De oorspronkelijke dirty rootwijziging betrof o.a. een coachnaam, geen gewijzigde fysiologische regel. Geen bewijs van daadwerkelijk gedeployde SHA is opgevraagd: hosted toegang is verboden voor deze taak.

## Auditbereik en tellingen

Bronmanifest: 184 bestanden. Inhoudelijk beschreven: 66 regelgroepen. Automatisch ontdekt: 676 Pythonfunctie-/methoderecords en 1250 syntactische beslispunten. Deze telling is geen volledige human-reviewed regel-/branchinventaris. If/while/assert/comprehensionrecords bevatten ook parsing/transporthelpers. SQL/mobilebranches zijn niet exhaustief geteld; conditioninteracties evenmin.

Brononderzoek omvat physiology (Joren, zones, progression, recovery, taper, debt, intensity, injury, anti-stack en provenance), planning (domain, service, swipe, repository, schemas), workouts/catalogus, calibration, activities, onboarding, checkins en relevante providerintegraties. Daarnaast zijn migrations, offline tests, roadmap en toepasselijke AGENTS-instructies gelezen. Het discoverymanifest is ruimer dan de handmatig geauditeerde regels. ENGINE_SOURCE_TRACEABILITY maakt dat onderscheid.

Catalogus: 162 actieve lokale templates; alle 154 brontrainingen zijn opgenomen, met segments in de JSON-bijlage. V2 eigenschappen volgen de migratie. De v2 deployed UUIDs worden willekeurig gegenereerd en zijn onbekend; behouden v1 IDs zijn lokale fixture-identiteiten. Geen productie-UUIDvolgorde wordt beweerd. Alle 154 brontrainingen bevatten al replacementtekens in tekst; de display markeert ze, exacte brontekst blijft behouden. Distance-only swims behouden ontbrekende current planned load.

## Werkboekarchitectuur en mogelijkheden

29 tabbladen, 14983 zichtbare native formules. Geen VBA, macrobeveiliging gewijzigd of verborgen runtime. Geen externe workbooklinks, geen formulebescherming, geen Python/backendcalls tijdens gebruik. Excel 16.0 heeft het werkboek geopend, met veranderde inputs herberekend en de handoff opgeslagen.

Bewerkbaar: sporturen, rustHR als niet-baselineafhankelijke context, race type/date, tijdzone, eerste maandag, submaxobservatie/RPE en expliciete actieve-zonebevestiging; weekavailability, beperkte sportrestrictie/capabilityprojectie; template/occurrence/date; activiteitduur, zoneminuten, raw-zone-present, gemiddelde HR en RPE; expliciete vorige goedgekeurde snapshots/flags. Niet iedere ingevoerde restriction/capability heeft een volledige equivalent: onbekende gates zijn expliciet gemarkeerd.

Numerieke formules: startcomponenten/totaal/nulfallback, Phase13 HR/CSS-drempels en integerzones, actuele zone-minuutload/coverage, bevestigde gemiddelde-HR-estimates, delen van matchmatrix en weektargetprioriteit.16 targetregels hebben expliciete previous-state-inputs. Dat is geen16-weekflow met automatisch gekozen/geplaatste workouts en volledige approvalevents.

Original/Joren: referentieconstanten blijven in PARAMETERS!B, voorstellen in C, Effective in D. Beide start-, zone-, actual- en targetuitkomsten blijven inspecteerbaar. Groei, baselinecoëfficiënten, sport-/zonecoëfficiënten, RPE-ankers en zonegrenzen zijn zichtbaar aanpasbaar voor de geporte onderdelen. Spacingparameters zijn zichtbaar, maar volledige plannerpariteit ontbreekt. Formules zelf zijn onbeveiligd bewerkbaar. Structurele search/statealgoritmen zijn niet als één bewerkbare formule voorgesteld. Eigen divergerende approved historie per ruleset ontbreekt.

Geen XLSM is geleverd. Excel VBProject was programmatisch onbeschikbaar; trustinstellingen zijn niet aangepast. Er is geen geschreven of geverifieerde volledige VBA-port. Dit is een open implementatiegate, geen bewijs dat een port principieel onmogelijk is.

## Uitgevoerde controles en open gates

| Controle | Resultaat | Grenzen |
| --- | --- | --- |
| Native Excel | 120 scenario’s; 577/577 PASS; 0 FAIL; 0 formule-errors | Numerieke deelpariteit en properties, geen volledige workflows |
| Backend pytest | 778 PASS; 1 deprecationwarning; 179.23s | Referentiebron; geen algemene Excel-branchproof |
| Ruff / format referentie | PASS;139 bestanden geformatteerd | Geen bronwijzigingen |
| Strict mypy referentie | PASS;139 bestanden | app en tests |
| OpenAPI / private-load leaks | Onderdeel van geslaagde backend suite | Geen publieke contract-/UIwijzigingen |
| Nieuwe Python-generators | Ruff en format PASS | Documentprose-lengte en late oracleimports lokaal verklaard |
| PDF | 36 pagina’s gerenderd en bekeken; geen lege pagina’s, overflow of ontbrekende rule IDs | Inhoudelijke all-rule completeness OPEN |
| Werkboekstructuur | 29 tabs; geen externe links/VBA/protection | 29 header/eerste-rijsample-renders bekeken; geen every-cell-layoutproof |
| pgTAP/RLS | NIET UITGEVOERD | Geen databaseverbinding; hosted verificatiegate OPEN |
| Mobile/TypeScript | Niet uitgevoerd | Geen mobilecode veranderd; geen volledige mobilebranchaudit |

Maximale numerieke afwijking in uitgevoerde assertions: 1.13686837721616e-13; tolerantie 1e-9. Double is geen Decimal. De geteste .90/1.10/1.15-equalitybranches en zone-HALF_UPvoorbeelden matchen. Algemene rounding-/accumulationpariteit, historische IANA/DST en mixed-NULL SQL-sommen blijven open.

## Resterende blockers

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

PDF SHA256: 703630236b160f08dc576000c43821446bff1374bb1ebfdd609d9f0546c8e7d2

XLSX SHA256: d77eae33da7f8bc0508d7cac3ad91b51592861e2bd748d3c1071d978a504b374

## Bestanden

DELIVERY_FILES.json is de exact-path commit-/handofflijst. Tijdelijke native testkopieën, PNGs en generatorinspectielogs staan lokaal onder qa maar zijn geen aparte productdeliverables en worden niet meegecommit. Geen authored VBA bestaat.

- .gitignore
- .gitattributes
- WOMBO_Complete_Training_Logic.pdf
- WOMBO_Training_Simulator.xlsx
- ENGINE_RULE_INVENTORY.md
- ENGINE_SOURCE_TRACEABILITY.md
- SIMULATOR_COVERAGE_MATRIX.md
- PARITY_TEST_REPORT.md
- KNOWN_GAPS_AND_QUESTIONS.md
- JOREN_CHANGE_REQUEST_TEMPLATE.md
- README.md
- HANDBOOK.md
- FINAL_REPORT.md
- DELIVERY_FILES.json
- fixtures/catalog.json
- fixtures/catalog_encoding_gaps.json
- fixtures/constant_inventory.json
- fixtures/decision_inventory.json
- fixtures/function_inventory.json
- fixtures/parity_cases.json
- fixtures/reviewed_rules.json
- fixtures/source_catalog_original.json
- fixtures/source_manifest.json
- scripts/build_documents.py
- scripts/build_reports.py
- scripts/build_workbook.mjs
- scripts/inventory.py
- scripts/make_parity_cases.py
- scripts/verify_artifacts.py
- scripts/verify_excel.ps1
- qa/.gitignore
- qa/native-parity-results.json
- qa/artifact-validation.json
- qa/backend-tests.txt
- qa/reference-checks.txt

## Grenzen gerespecteerd

Alle wijzigingen bevinden zich onder docs/joren-training-review in de geïsoleerde werkboom. Geen app/backend/mobile/schemawijziging; geen fysiologieregel aangepast; geen productie-/stagingtoegang of mutatie; geen migration toegepast; geen push of deploy; geen real-athletegegevens; geen credentials in deliverables. Gitbranch/worktree en lokale document-/simulatorbestanden zijn de enige mutaties.

Fases A–F zijn gedeeltelijk uitgevoerd, niet compleet verklaard. Fase G levert een expliciet onvolledig reviewpakket met bewijs en vervolggrenzen. De oorspronkelijke volledigheidsacceptatie is NIET gehaald.

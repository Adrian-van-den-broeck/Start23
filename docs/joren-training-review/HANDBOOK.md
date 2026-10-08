# WOMBO - trainingslogica

INTERNAL BUSINESS / ENGINE REVIEW
NOT FOR END-USER DISTRIBUTION

Bronbranch: fix/catalog-capacity-fresh-athlete
Volledige SHA: 6b1189b70a6505726fef70c4616a2f3d6dd4c94a
Auditbranch: docs/joren-training-engine-simulator
Datum: 8 oktober 2026

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

## 1. Samenvatting

Dit pakket beschrijft de actuele bronversie en maakt een deel van de numerieke regels controleerbaar in Excel. De complete audit en alle-path simulator zijn niet afgerond. De volledigheidsgate blijft open. De hoofdbeperking is niet een ontbrekend opmaakdetail: automatische constrained search, volledige statehistorie en meerdere adaptationbranches ontbreken in het XLSX.

## 2. Hoe de engine werkt

Onboarding levert bevestigde profiel-, doel-, historie- en zone-inputs. Deterministische Python bepaalt de target, fase en catalogusgeschiktheid. Een begrensde multisetsearch levert een mogelijke combinatie en vaste swipecompositie. De sporter kiest occurrences. Plaatsing wordt gevalideerd en opgeslagen als pending voorstel. Pas afzonderlijke goedkeuring activeert een revision. Observaties krijgen een eigen private-loadsnapshot. De volgende week gebruikt autoritatieve historie. De LLM legt uit en berekent of activeert niets.

## 3. Invoer en afhankelijkheden

Historie is het gemiddelde aantal minuten per week in de vorige maand, per goalsport, met actuele baselineversie. Nul is een echte waarde; ontbrekend is geen nul. Rusthartslag en leeftijd komen niet voor in startbelasting. Rusthartslag is wel een onboardingvereiste en komt in historische biometrische fallback voor. Race type bepaalt sporten; race date bepaalt fase/taper. Gewenste tijd, afstanden en racenaam zijn opgeslagen doelcontext; resolve_target leidt daar geen tempo- of loadcoëfficiënt uit af. Beschikbare datums beperken plaatsing, niet een verzonnen uurvolume-cap.

## 4. Formuleoverzicht en eenheden

Interne belasting is geen minuut, hartslag of sessie-RPE. Duur staat in minuten; HR in bpm; CSS in sec/100m; runtempo in sec/km; power in watt; kalenderdatum in lokale maandag-zondagweken. De startberekening gebruikt uren na minuten/60. Zone-load telt minuten maal per-sport/zonecoëfficiënten. De referentie hieronder geeft iedere formule met bron, voorwaarden en workbookkoppeling. Geen algemene sportwetenschappelijke formule is als vervanging ingevoerd.

## 5. Initiële capaciteit

L_swim=h_swim×56.25×.90; L_bike=h_bike×56.25; L_run=h_run×56.25×1.15. Components worden niet individueel afgerond. Totale som krijgt HALF_UP op één decimaal. Bij totale nulhistorie is het target45.0, terwijl per-sportcomponents0 blijven. Voor run3uur resulteert194.0625 exact en194.1 totaal. Eerste gewone planning gebruikt BASE ongeacht nominale recoverypositie, zolang geen goedgekeurd priorplan bestaat. Kalibratieactiviteit is geen goedkeuring.

## 6. Kalibratie en zones

Phase13 submaximale kalibratie deelt HR of zwemtempo door het RPE-anker en rondt de drempel geheel HALF_UP af. HR/CSS krijgen het Phase13-model. Veldtesten blijven een ander protocol en kunnen model1.0-profielen opleveren. Integergrenzen van Phase13 zijn aansluitend en inclusief. De oudere modelgrenzen geven gedeelde waarden aan hogere intensiteit. Een berekende drempel/zone is pending; expliciete athleteconfirmation blijft vereist. Geen sporter krijgt een actieve drempel omdat een formulecel een getal toont.

## 7. RPE en activiteitbelasting

De tekstuele RPE-keuze is integer1..10. Zone-minuten bepalen actuele private load als betrouwbare totale duur en positieve validtime bestaan. Gedeeltelijke zonedata worden niet opgehoogd. Ontbrekende zonearray kan voor run/bike met bekende bevestigde HR-zones terugvallen op full-duration mean-HR-estimate. Een expliciete array met vijf nullen is niet hetzelfde als ontbrekend. RPE×uren en sRPE-factor² zijn historische/referentieformules; geen actieve missing-datafallback.

## 8. Fases en progressie

De racemaandag verankert het4+1ritme. Taper gaat vóór recovery, die vóór schuld en gewone progressie gaat. Sicknesssamples worden uitgesloten. Gemist/vermoeid bij lagere realized gebruikt realized×1.10. Regulier bij minstens80% gebruikt planned×1.10. Meer dan110% activeert volumeschuld. Ontbrekende realized houdt planned; geen activiteiten is in de SQL-reader expliciet0. Recovery gebruikt.60×vorige planned. Volledige A-taper gebruikt.35×gemiddelde planned niet-recovery samples in42dagen.

## 9. Catalogus en geschiktheid

De lokale auditprojectie omvat162 actuele templates, waaronder alle154 brontrainingen. Ze zijn inspecteerbaar inclusief duration/distance, whole-bucket, requirements, phase, source-ID en segments in JSON. De bron-CSV is niet vervangen door voorbeeldtrainingen. Distance-only swims behouden source-loadprovenance maar hebben current planned loadNone en vallen uit targetfit. De v2-migratie genereert willekeurige nieuwe UUIDs; die deployedidentiteit is niet uit de repository te reconstrueren. Exacte productiontie-breakerpariteit blijft daarom open.

## 10. Selectie als constrained search

Automatische keuze is geen enkele spreadsheetvergelijking. De engine groepeert equivalente candidates op sport, load, whole-bucket en Z5-status. Kleinste immutable UUID is representant tenzij maximumuses gelden. Start met prefix; breid states uit met één occurrence tot maximaal24. Een state omvat total/highload, counts per sport, highcounts, limited-usecounts en Z5presence. Snoei ongeldige count-, highbudget-, load- en sportcapstates. Beoordeel volledige discipline/compositioncoverage, strikte targetfittolerantie en indien toepasselijk schedulefeasibility. Kies lexicografisch loadverschil, highloadbudgetverschil, count en UUID-pad. Stop na huidige count als exact target gevonden. Dit algoritme is beschreven, niet als simpeler Excelheuristiek nagebootst.

## 11. Plaatsing

HIGH wordt eerst geplaatst, daarna sport en UUID. Backtracking onderzoekt beschikbare datums in volgorde laagste gebruik, kortste maximale reststreak na toevoeging en datum. Meerdere sessies op één dag zijn toegestaan. Een maximaal3daagse reststreak wordt alleen afgedwongen als de count en availability dat kunnen realiseren en er geen fixedplaatsingen zijn. Per sport HIGH moet run72/bike48/swim48 werkelijk verstreken uren vrij zijn. Lokale datum wordt intern op12:00 geprojecteerd; het is geen trainingsuurvoorschrift. DST kan dus kalenderafstand en uurafstand laten verschillen.

## 12. Blessures en cross-training

Huidige v2 berekent eerst normaal weektarget. Per-sportbasis komt uit laatste goedgekeurde sportloads of onboardingcomponents. Projecteer het target proportioneel; verwijder blocked sporten. Hoogstens80% van verwijderde load mag naar bike/swim met positieve basis en geschikte lowtraining. Safe cap=max(normaal target,1.10×priorbasis). Waterfill verdeelt gewogen ruimte en herverdeelt na cap; overschot verdwijnt. Run ontvangt niets. Nulbasisopt-in creëert geen capacity. Replacement blijft low-only en creëert geen nieuw highbudget. Eerdere zero-redistributionhelpers zijn historisch, geen nieuweproposalgedrag.

## 13. Goedkeuring en revisions

Het actieve plan en pending voorstel bestaan naast elkaar. Een swipeaccept is geen planapproval. Owner, proposalstate, targetrevisionstate en expected/base/active revision worden atomair gecontroleerd. Goedkeuren supersedet oude active, activeert target en markeert proposal applied. Verwerpen behoudt oude active. Idempotente applied/rejected retry is specifiek toegestaan volgens bronvoorwaarden. Een worksheetdropdown emuleert database-locking, ownerisolation of exacteventhistorie niet. Het workbook labelt zijn approvalkeuze daarom extern en de complete lifecycle als open.

## 14. Gepland versus geobserveerd

Timed sourceworkouts behouden hun gereviewde predefinedload. Niet-source timed zoneworkouts gebruiken de actuele zonecoëfficiënten. Historische records blijven onder eigen versie/methode. Observaties kunnen meer/minder duren, andere zones hebben of los van plannedworkout bestaan. De matchmatrix geeft incomplete/estimated meting eerst deviation tenzij low+RPE≥7 hiddenfatigue. Complete unplanned krijgt unplanned. Daarna hiddenfatigue, ontbrekende plannedbasis, >115%overshoot, inclusieve90-110% met RPErange, anders deviation. Mean-HR-estimate is bewust niet complete.

## 15. Volgende week

De SQL-reader creëert maximaalzes complete kalenderweken sinds vroegste plan/activityevidence, met expliciete NULL/0-semantiek en current-loadprovenance. Actorapproval komt uit approved active/superseded revisions, niet rowexistence. Het Excelmodel heeft zestien targetregels, maar gebruikt expliciete previous-state-inputs en handmatige approvalsnapshots. Het produceert geen volledig autonome reeks workouts/approvals/events. Eigen divergerende experimentalhistorie is niet geïmplementeerd.

## 16. Fout- en ontbrekende-datapaden

Legitieme fouten zijn uitkomsten. Voorbeelden: previous_month_history_required; zero_history_discipline_baseline_unavailable; approved_plan_baseline_unavailable; partial_week_taper_rule_required; taper_baseline_unavailable; catalog_empty; catalog_phase_coverage_unavailable; catalog_capacity_unsatisfied; rest_or_anti_stack_unsatisfied; swipe_candidate_stale; anti_stack_violation. Nul kandidaten kan correct zijn. Geen output mag als succesvol plan worden gelabeld omdat een targetgetal bestaat. De appendixregels geven precondities en no-resultgedrag; discoveryrecords die nog niet handmatig zijn vertaald blijven open.

## 17. Volledige rekenvoorbeelden

Voorbeeld A: nieuwe runathleet met3uur/week heeft194.0625component en194.1target. Zonder eerdere approval is gewone faseBASE, ook als kalibratieactiviteit bestaat. Vervolgens is echte eligible multisetsearch nodig; er wordt geen fictieve workoutcombinatie ingevuld. Voorbeeld B: vorige approved planned100 en complete realized80 geeft regulier110; realized79 geeft gemiddelde aanwezige realizedsamples, hier79. Met fatigue en realized50 wordt55 vóór gewone80%-logica. Voorbeeld C: planned100, realized120 activeert debt20; nexttarget110-20=90. Bij realized110 bestaat geen debt. Voorbeeld D: recovery na planned200 geeft120; volledige A-taper met eligible plannedbaseline200 geeft70. Een zondagwedstrijd maakt een partialweektaper waarvoor de planner fail-closed is. Voorbeeld E: run60min waarvan30min bekendeZ2 levert27.6, coverage.5 enpartial_observed;60min gemiddeldeHRZ2 levert55.2 als estimate, coverage0, niet complete. Dit zijn complete numerieke berekeningen, geen beweerde volledige workout-state-simulaties.

## 18. Aannames en wetenschappelijke toets

Correcte softwarepariteit bewijst niet dat de fysiologische aannames verantwoord zijn. Coëfficiënten,45nulbasis, thresholds, anchors, recovery/taperfactoren en recipientcaps zijn geïmplementeerd beleid met bronprovenance. Dit auditpakket verzamelt geen nieuwe externe wetenschappelijke evidence en verklaart geen klinische geldigheid. Er zijn geen vervangende normen bedacht.

## 19. Implementatiebeperkingen

Het XLSX is functioneel voor de expliciete numerieke onderdelen, met nativeherberekening en zichtbare formules. Het is ONVOLLEDIG als standalone all-path trainingsengine. Geen XLSM is geleverd: VBProject is hier programmatisch onbeschikbaar en er is geen geverifieerde VBA-port. Automatische selectie/plaatsing, injury-waterfill, intensiteitschuld, volledige protocolkwaliteit, historische RPE-correcties en alleapprovalevents zijn open. De mapping en parityreport specificeren wat wel werkelijk getest is.

## 20. Wat Joren inhoudelijk moet beoordelen

Beoordeel56.25 en sportmultipliers; beginners45 en partial-historyblokkades;10%progressie en80%completion;debt110% ensessionovershoot115%; high-load70-90% van20%-budget versus whole-workoutminuten;72/48 elapseduur rondomDST; capped injurytransfer en consent bij bestaande basis; ontbrekende meetwaarden; mean-HR-estimates in feedback; volledige/partialtaper; traceerbare reviewer/evidence voor calibratieankers. Dit zijn reviewvragen, geen automatisch vastgestelde defecten.

## 21. Wijzigingen voorstellen

Gebruik stabiele RULE ID en houd categorieën gescheiden: CURRENT IMPLEMENTATION, INTENDED BUSINESS RULE, POSSIBLE DEFECT, JOREN PROPOSED CHANGE. Leg huidige en voorgestelde formule, eenheden, activationbranches, equalityownership, rounding en voor/naexample vast. In Excel blijft ORIGINAL bewaard; JOREN VALUE activeert het voorstel. Structurele algoritmen vereisen expliciete port en eigen tests. Appcode, schema en historische records blijven ongewijzigd.

## 22. Bronnen en verificatie

De bron is lokaal gepind; bronmanifest bevat bestandshashes. De PDF verwijst naar functies en lijnnummers, de traceabilityMarkdown naar discoveryfuncties. Bestaande backendtests en nativeExcelasserties zijn verschillend bewijs. NativeExcel controleert echte gewijzigde inputs en restore in een tijdelijke kopie; formuleteksten zijn geen bewijs. De 1250 syntactische beslispunten zijn niet allemaal reviewed of getest. SQL/mobilebranchanalyse en complete source-to-workbookdekking blijven open.

## 23. Regel naar Excel

De volgende referentie koppelt66 beschreven regels aan bron en workbook. NOT IMPLEMENTED betekent werkelijk ontbrekende equivalentie. PARTIAL betekent dat slechts expliciete assertions in het rapport zijn gecontroleerd. De29tabs geven werkgebieden en open branches weer; aanwezigheid van een tab sluit geen featuregate. Raadpleeg het losgeleverde PARITY_TEST_REPORT en FINAL_REPORT voor de actuele aantallen en beperkingen.

## Regelreferentie

## INIT-01 - Startbelasting per sport

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** starting_baseline

**Regels:** 106

**Inputs en types:** minutes: Mapping[Discipline, Decimal]

**Eenheden:** Geschiedenis: minuten per week; output: interne belasting. Sport en modelversie zijn labels.

**Voorwaarden en grenzen:** Niet-negatieve eindige Decimal-minuten; expliciete sportsleutels; gezamenlijk maximaal 10080 minuten. Alleen doelenrelevante historie gebruikt de service.

**Formule / algoritme:** L_s = minuten_s / 60 × 56.25 × m_s; m_swim=0.90, m_bike=1.00, m_run=1.15.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** 180 minuten run → 194.0625; eindtotaal 194.1.

**Excel:** 01_ATHLETE_INPUTS!F6:F8

**PDF hoofdstuk:** INIT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Explicit component discipline history is required.'); ValueError('Combined weekly duration cannot exceed 168 hours.')

## INIT-02 - Totaal en nulhistorie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** starting_baseline

**Regels:** 106

**Inputs en types:** minutes: Mapping[Discipline, Decimal]

**Eenheden:** Geschiedenis: minuten per week; output: interne belasting. Sport en modelversie zijn labels.

**Voorwaarden en grenzen:** Expliciet nul is geldig. Ontbrekende historie is geen nul. Rusthartslag komt niet voor in deze formule.

**Formule / algoritme:** Als som(L_s)=0: totaal=45.0. Anders HALF_UP(som(L_s),1 decimaal). Componenten blijven exact; 45 wordt niet automatisch over sporten verdeeld.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** Alle drie 0 → componenten 0/0/0, totaal 45.0.

**Excel:** 01_ATHLETE_INPUTS!F9

**PDF hoofdstuk:** INIT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Explicit component discipline history is required.'); ValueError('Combined weekly duration cannot exceed 168 hours.')

## INIT-03 - Actuele historiereferentie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/service.py

**Functie:** _onboarding_baseline

**Regels:** 444

**Inputs en types:** snapshot: Mapping[str, Any]

**Eenheden:** Geschiedenis: minuten per week; output: interne belasting. Sport en modelversie zijn labels.

**Voorwaarden en grenzen:** Geen terugval op oude weekly_hours of kalibratieactiviteiten.

**Formule / algoritme:** Filter historie op vereiste doelsport, baseline_model_version=phase-13-joren-ruleset-1 en aanwezige previous_month_weekly_minutes. Aantal moet aantal doelsporten zijn.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Run-doel vereist huidige runhistorie; triathlon vereist drie componenten.

**Excel:** 01_ATHLETE_INPUTS

**PDF hoofdstuk:** INIT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('previous_month_history_required', 'Complete previous-month training history before generating a new plan.')

## INIT-04 - Gemengde nulcomponent

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** build_weekly_plan

**Regels:** 1342

**Inputs en types:** *, week_start: date, timezone_name: str, race_date: date, catalog: tuple[WorkoutTemplate, ...], prior_loads: tuple[PlanLoadSample, ...], goal_disciplines: frozenset[Discipline], confirmed_injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline]=frozenset(), cross_training_opt_ins: frozenset[Discipline]=frozenset(), zone_capabilities: Mapping[Discipline, ZoneCapability], available_dates: tuple[date, ...], selected_template_ids: Collection[UUID] | None=None, fixed_template_dates: Mapping[UUID, date] | None=None, selected_occurrence_ids: Collection[UUID] | None=None, fixed_occurrence_dates: Mapping[UUID, date] | None=None, maintenance_active: bool=False, onboarding_baseline: StartingBaseline | None=None

**Eenheden:** Geschiedenis: minuten per week; output: interne belasting. Sport en modelversie zijn labels.

**Voorwaarden en grenzen:** Geen nieuwe capaciteit voor een ongetrainde sport verzinnen.

**Formule / algoritme:** Eerste plan + niet-volledig-nul baseline + een ongeblesseerde doelsport met component 0 → zero_history_discipline_baseline_unavailable.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Triathlon run=180, bike=0, swim=0 → geen plan.

**Excel:** NOT IMPLEMENTED: complete proposal gate ontbreekt; numeriek target is geen geldig plan

**PDF hoofdstuk:** INIT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('zero_history_discipline_baseline_unavailable', 'The catalog cannot fill this composition without an approved starting target for the untrained discipline.'); PlanningConstraintError('catalog_empty', 'No workout templates match the confirmed athlete configuration.'); PlanningConstraintError('catalog_coverage_unsatisfied', 'The current catalog cannot cover every uninjured goal discipline.'); PlanningConstraintError('catalog_phase_coverage_unavailable', f'No reviewed {target.phase.value} workout is available for: {missing_labels}.'); PlanningConstraintError('restricted_zero_base_allocation_unavailable', 'A reviewed starting allocation is required for this restricted introduction week.'); PlanningConstraintError('taper_catalog_coverage_unavailable', f'No reviewed taper workout is available for: {missing_labels}. This pre-race week cannot be generated yet.'); PlanningConstraintError('explicit_test_date_required', 'Every explicitly scheduled field test requires an exact date.')

## GOAL-01 - Doel naar sporten

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/onboarding/eligibility.py

**Functie:** required_disciplines_for_race_type

**Regels:** 18

**Inputs en types:** race_type: object

**Eenheden:** Race type en sporten zijn labels; gewenste tijd in seconden is alleen opgeslagen context.

**Voorwaarden en grenzen:** Afstanden, gewenste tijd en naam zijn onboardinggegevens. Geen tempo-naar-belastingformule in resolve_target.

**Formule / algoritme:** run→run; bike→bike; swim→swim; duathlon→bike/run; triathlon→swim/bike/run; onbekend→lege tuple.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Marathonnaam versus 10k-naam wijzigt catalogusfilter niet.

**Excel:** 02_GOAL

**PDF hoofdstuk:** GOAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-01 - Submaximale HR-kalibratie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** calibrate

**Regels:** 189

**Inputs en types:** *, discipline: Discipline, observation: Decimal, rpe: int

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Run/bike. Positieve observatie; RPE exact integer 1..10. Waarschuwing drempel <140; geen hard blok.

**Formule / algoritme:** Drempel = HALF_UP(observed_bpm / HR_ANCHORS[RPE],0). Anchors RPE 1..10: .70/.78/.84/.88/.91/.94/.97/1/1.03/1.06.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** Run HR=150, RPE=4 → 170 bpm.

**Excel:** 03_CALIBRATION!E7:E8 (CURRENT), F7:F8 (JOREN)

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Calibration observation must be positive.')

## CAL-02 - Submaximale zwemkalibratie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** calibrate

**Regels:** 189

**Inputs en types:** *, discipline: Discipline, observation: Decimal, rpe: int

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Tempo is tijd/afstand ×100. Geen HR-drempel voor zwemmen.

**Formule / algoritme:** CSS = HALF_UP(pace_sec_per_100m / SWIM_ANCHORS[RPE],0). Anchors 1.25/1.18/1.12/1.08/1.06/1.04/1.01/1/.96/.92.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** 120 sec/100m, RPE=4 → CSS 111 sec/100m.

**Excel:** 03_CALIBRATION!E6 (CURRENT), F6 (JOREN)

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Calibration observation must be positive.')

## CAL-03 - Kalibratiebewijs

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _evaluate_submaximal_calibration

**Regels:** 905

**Inputs en types:** protocol: CalibrationProtocol, mapped: dict[str, CalibrationObservation], initial_reasons: tuple[str, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Verplichte segmentmapping wordt eerst gevalideerd. unknown steady is niet hetzelfde als no. Optionele blokken vervangen het anker niet.

**Formule / algoritme:** Eerste verplichte calibration_observation is anker. Afwezig/niet voltooid/onderbroken → incomplete. Anders onvoldoende sensor → quality; anders RPE ontbreekt → missing; anders steady_execution=no → unstable.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Goede warming-up zonder anker levert geen drempel.

**Excel:** NOT IMPLEMENTED: protocolsegment evaluator

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-04 - Testobservaties koppelen

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _observation_map

**Regels:** 601

**Inputs en types:** protocol: CalibrationProtocol, observations: tuple[CalibrationObservation, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Redenen in ontdekvolgorde, ontdubbeld. Historische protocollen mogen niet opnieuw geëvalueerd worden.

**Formule / algoritme:** Controleer protocol/sport, bekende segment-ID, uniek segment; voeg daarna required_segment_missing toe voor ontbrekende verplichte segmenten.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Dubbele test_30min → duplicate_segment_observation.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-05 - Run veldtest

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _evaluate_run_test

**Regels:** 673

**Inputs en types:** protocol: CalibrationProtocol, mapped: dict[str, CalibrationObservation], initial_reasons: tuple[str, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Blok-RPE 8..9, stabiel segment, verplichte kwaliteits/duur/voltooiingsregels. Ontbrekende HR blokkeert bruikbaar tempo niet.

**Formule / algoritme:** Drempeltempo = HALF_UP(gemiddeld tempo 30-min-blok,0). LTHR = HALF_UP(gemiddelde HR laatste 20 min,0), alleen completeness ≥.95.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** Tempo 300.5 →301 sec/km; completeness .949 geeft geen HR-drempel.

**Excel:** NOT IMPLEMENTED: complete test gating

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-06 - Fiets FTP veldtest

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _evaluate_bike_ftp_test

**Regels:** 743

**Inputs en types:** protocol: CalibrationProtocol, mapped: dict[str, CalibrationObservation], initial_reasons: tuple[str, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Blok-RPE 8..9, gekalibreerde vermogensbron, stabiel, completeness≥.95; iedere reden blokkeert resultaat.

**Formule / algoritme:** FTP = HALF_UP(.95 × gemiddeld vermogen laatste 20 min,0).

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** 250 W →238 W.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-07 - Fiets HR veldtest

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _evaluate_bike_hr_test

**Regels:** 786

**Inputs en types:** protocol: CalibrationProtocol, mapped: dict[str, CalibrationObservation], initial_reasons: tuple[str, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Blok-RPE 8..9; completeness≥.95; iedere kwaliteitsreden blokkeert.

**Formule / algoritme:** Drempel = HALF_UP(gemiddelde HR 20-min-test,0).

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** 160.5 bpm →161 bpm.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-08 - CSS 400/200 veldtest

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** _evaluate_swim_css_test

**Regels:** 825

**Inputs en types:** protocol: CalibrationProtocol, mapped: dict[str, CalibrationObservation], initial_reasons: tuple[str, ...]

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** t400>t200 én 2×t200<t400; RPE 9..10; vrije slag; geen materiaal; gelijk bad 25/50m; herstel 300..600 sec.

**Formule / algoritme:** CSS = HALF_UP((t400-t200)/2,0).

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** t400=480, t200=230 →125 sec/100m.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAL-09 - Testdatum

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/calibration/domain.py

**Functie:** validate_test_schedule

**Regels:** 468

**Inputs en types:** *, protocol_id: str, discipline: Discipline, scheduling_mode: TestSchedulingMode, scheduled_date: date, athlete_today: date, plan_week_start: date | None=None

**Eenheden:** HR in bpm; zwemtempo in sec/100 m; looptempo in sec/km; vermogen in watt; testtijd in seconden; RPE integer 1–10; volledigheid als fractie; datum lokaal.

**Voorwaarden en grenzen:** Swim-integratie afgewezen wegens ontbrekende geplande duur/belastingsbehandeling. Standalone verwijst niet naar planweek.

**Formule / algoritme:** Actueel, actief veldprotocol voor juiste sport; datum≥lokale vandaag. Geïntegreerde test binnen maandag-zondag planweek.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Zwemtest als standalone kan; weekly_plan niet.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** CAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('The field-test protocol does not match the discipline.'); ValueError('The athlete-local test date cannot be in the past.'); ValueError('The swim test has no approved planned-duration/load treatment.'); ValueError('An integrated test requires its plan week.'); ValueError('The integrated test date must fall inside the plan week.'); ValueError('A standalone test does not reference a weekly plan.')

## ZONE-01 - HR-zones Phase 13

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** threshold_zones

**Regels:** 156

**Inputs en types:** discipline: Discipline, threshold: int

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Positieve gehele drempel; 0<a≤b<c<T. Inclusieve gehele grenzen; geen gaten.

**Formule / algoritme:** a=HALF_UP(.82T), b=HALF_UP(.89T), c=HALF_UP(.95T). Z1≤a-1; Z2=a..b; Z3=b+1..c; Z4=c+1..T; Z5≥T+1.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** T=170 →Z1≤138; Z2 139..151; Z3 152..162; Z4 163..170; Z5≥171.

**Excel:** 04_ZONES

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Threshold must be a positive whole number.'); ValueError('Unsupported discipline.'); ValueError('Threshold cannot represent five discrete zones.'); ValueError('Threshold cannot represent five discrete zones.')

## ZONE-02 - CSS-zones Phase 13

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** threshold_zones

**Regels:** 156

**Inputs en types:** discipline: Discipline, threshold: int

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Inverse tijdschaal; 0<a≤b<c<d. Sneller betekent kleinere seconden.

**Formule / algoritme:** a=HALF_UP(.98T), b=HALF_UP(1.02T), c=HALF_UP(1.07T), d=HALF_UP(1.15T). Z1≥d+1; Z2=c+1..d; Z3=b+1..c; Z4=a..b; Z5≤a-1.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** T=120 →Z1≥139, Z2 129..138, Z3 123..128, Z4 118..122, Z5≤117.

**Excel:** 04_ZONES

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Threshold must be a positive whole number.'); ValueError('Unsupported discipline.'); ValueError('Threshold cannot represent five discrete zones.'); ValueError('Threshold cannot represent five discrete zones.')

## ZONE-03 - Bestaand model 1.0

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/zones.py

**Functie:** calculate_zone_profile

**Regels:** 450

**Inputs en types:** metric: ZoneMetric | None, *, zone_model_version: RulesetVersion=ZONE_MODEL_VERSION, is_primary: bool=True

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Apart model, gebruikt bij veldtesten. Gedeelde grens naar hogere intensiteit. Niet stilzwijgend vervangen door Phase 13.

**Formule / algoritme:** FTP-grenzen T×(.56,.76,.91,1.06); HR T×(.85,.90,.95,1.03); tempo/CSS T÷(.78,.88,.95,1.02). Alle grenzen eenmaal HALF_UP geheel.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** FTP=250 →140/190/228/265 W.

**Excel:** NOT IMPLEMENTED: legacy model sheet

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('A threshold metric is required to calculate zones.'); ValueError('The requested zone model version is not active.'); ValueError('The Phase 13 calibration model requires HR or CSS.'); ValueError('Canonical threshold must use whole units.'); ValueError('Threshold is too low to produce distinct whole-second pace zones.'); ValueError('Threshold is too low to produce distinct whole-unit zones.')

## ZONE-04 - Zoneclassificatie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/zones.py

**Functie:** classify_calculated_zone_value

**Regels:** 553

**Inputs en types:** *, profile: CalculatedZoneMetricProfile, value: Decimal

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Phase13 meetwaarde moet geheel en >0 zijn. FTP supramaximal bij relatieve intensiteit>1.20.

**Formule / algoritme:** Phase13: lower≤value≤upper. Model1.0 stijgend: lower≤value<upper; dalend: lower<value≤upper. Open buitenranden.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Phase13 HR=151 bij T170 valt in Z2, 152 in Z3.

**Excel:** 18_ACTUAL_LOAD!G6:G405; alleen CURRENT Phase13 HR-classificatie

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Value falls outside the calculated zone profile.'); ValueError('Zone classification value must be finite and positive.'); ValueError('Phase 13 classification requires whole measurement units.')

## ZONE-05 - Handmatige grenzen

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/zones.py

**Functie:** classify_zone_value

**Regels:** 697

**Inputs en types:** *, metric_kind: ZoneMetricKind, value: Decimal, boundaries: tuple[ZoneBoundary, ...], specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Geen gaps, positieve intervallen, tempo hele seconden. Buiten bereik fout.

**Formule / algoritme:** Vijf opeenvolgende, aansluitende grenzen. Stijgend gedeelde grens naar hogere zone; dalend idem. Buitenste exacte rand telt mee.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Waarde op overgang Z2/Z3 hoort Z3.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Value falls outside the supplied zone boundaries.'); ValueError('Zone classification value must be finite and non-negative.')

## ZONE-06 - Biometrische fallback

**Categorie:** CURRENT IMPLEMENTATION / reference or historical

**Bron:** backend/app/modules/physiology/zones.py

**Functie:** calculate_karvonen_fallback

**Regels:** 762

**Inputs en types:** *, age_years: int, resting_heart_rate_bpm: Decimal, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Bestaande/historische schatting, onreviewed en bevestiging vereist. 220-leeftijd alternatief apart; huidig MVP vereist actuele zones/kalibratie.

**Formule / algoritme:** HRmax=208-.7×leeftijd; reserve=HRmax-rustHR; grens=rustHR+reserve×(.50,.60,.70,.80,.90,1.00).

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Leeftijd40, rustHR60 →HRmax180, 50%-grens120.

**Excel:** NOT IMPLEMENTED: historical fallback

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## ZONE-07 - HR-tolerantie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/zones.py

**Functie:** assess_heart_rate_tolerance

**Regels:** 170

**Inputs en types:** *, observed_bpm: int, reference_bpm: int, tolerance_bpm: int=10

**Eenheden:** HR in bpm; FTP in watt; tempo in sec/km of sec/100 m; leeftijd in jaren; zone-index integer 1–5; toleranties in bpm.

**Voorwaarden en grenzen:** Beide 20..260 bpm, booleans ongeldig, tolerance exact10. Alleen observatiecontext; verandert geen zones.

**Formule / algoritme:** Referentie-10≤observatie≤referentie+10 →within_tolerance.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Referentie150:140/160 binnen,139/161 buiten.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** ZONE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Observed heart rate must be between 20 and 260 bpm.'); ValueError('Reference heart rate must be between 20 and 260 bpm.'); ValueError('The reviewed heart-rate tolerance is exactly 10 bpm.')

## LOAD-01 - Zone-minuten

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** zone_load

**Regels:** 222

**Inputs en types:** *, discipline: Discipline, total_minutes: Decimal | None, minutes_by_zone: tuple[Decimal, ...] | None, planned: bool=False

**Eenheden:** Duur en zonetijd in minuten; RPE integer 1–10; coëfficiënt in interne belasting per minuut; output interne belasting; dekking als fractie.

**Voorwaarden en grenzen:** Vijf niet-negatieve waarden; bekende totale duur; zonesom≤totale duur; zonesom>0 vereist voor beschikbare belasting. Geen afronding in functie.

**Formule / algoritme:** Belasting=Σ minuten_z × coefficient_s,z. Swim .45/.72/1.08/1.44/1.80; bike .50/.80/1.20/1.60/2.00; run .58/.92/1.38/1.84/2.30.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Run 30 min Z2 →27.6.

**Excel:** 18_ACTUAL_LOAD

**PDF hoofdstuk:** LOAD

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Zone time requires reliable total duration.'); ValueError('Zone time cannot exceed total duration.'); ValueError('Exactly five zone durations are required.')

## LOAD-02 - Observatiedekking

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** zone_load

**Regels:** 222

**Inputs en types:** *, discipline: Discipline, total_minutes: Decimal | None, minutes_by_zone: tuple[Decimal, ...] | None, planned: bool=False

**Eenheden:** Duur en zonetijd in minuten; RPE integer 1–10; coëfficiënt in interne belasting per minuut; output interne belasting; dekking als fractie.

**Voorwaarden en grenzen:** Ontbrekende belasting blijft None. Expliciete vijf nullen leidt ook unavailable, niet belasting0.

**Formule / algoritme:** valid=Σzone-minuten; coverage=valid/total bij total>0. complete als valid=total>0; partial_observed bij 0<valid<total; anders unavailable.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Totale duur60, 30min Z2 run →27.6 en coverage .5, partial_observed.

**Excel:** 18_ACTUAL_LOAD

**PDF hoofdstuk:** LOAD

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Zone time requires reliable total duration.'); ValueError('Zone time cannot exceed total duration.'); ValueError('Exactly five zone durations are required.')

## LOAD-03 - Gemiddelde HR-schatting

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** average_hr_zone_load

**Regels:** 296

**Inputs en types:** *, discipline: Discipline, total_minutes: Decimal, zone: int

**Eenheden:** Duur en zonetijd in minuten; RPE integer 1–10; coëfficiënt in interne belasting per minuut; output interne belasting; dekking als fractie.

**Voorwaarden en grenzen:** Alleen run/bike, positieve duur, bevestigde HR-zone. Alleen als raw_zones is None. Lege/partial zone-observatie blokkeert deze terugval.

**Formule / algoritme:** Belasting=totale minuten×coefficient van toegewezen gemiddelde-HR-zone. valid_minutes=0, coverage=0.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Run60 min gemiddelde Z2 →55.2, estimated_from_average_hr.

**Excel:** 18_ACTUAL_LOAD

**PDF hoofdstuk:** LOAD

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('A known run/bike heart-rate zone is required.'); ValueError('A reliable positive duration is required.')

## LOAD-04 - sRPE referentie

**Categorie:** CURRENT IMPLEMENTATION / reference or historical

**Bron:** backend/app/modules/physiology/joren.py

**Functie:** srpe_formula

**Regels:** 272

**Inputs en types:** *, discipline: Discipline, duration_minutes: Decimal, rpe: int

**Eenheden:** Duur en zonetijd in minuten; RPE integer 1–10; coëfficiënt in interne belasting per minuut; output interne belasting; dekking als fractie.

**Voorwaarden en grenzen:** Referentieformule aanwezig; SRPE_FALLBACK_ENABLED=False. Geen actieve ontbrekende-data-terugval.

**Formule / algoritme:** L=minuten/60 × factor_RPE² ×100 × sportmultiplier. Factoren .45/.55/.65/.75/.82/.88/.94/1/1.05/1.15.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Run60min RPE4 →64.6875 als referentie, niet actuele activiteitbelasting.

**Excel:** NOT IMPLEMENTED: reference only

**PDF hoofdstuk:** LOAD

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## LOAD-05 - Historische RPE-duur

**Categorie:** CURRENT IMPLEMENTATION / reference or historical

**Bron:** backend/app/modules/physiology/activity.py

**Functie:** calculate_legacy_phase7_rpe_duration_load

**Regels:** 56

**Inputs en types:** *, duration: DurationMinutes, rpe: int

**Eenheden:** Duur en zonetijd in minuten; RPE integer 1–10; coëfficiënt in interne belasting per minuut; output interne belasting; dekking als fractie.

**Voorwaarden en grenzen:** Alleen historische compatibiliteit. Oude records behouden eigen versie en methode.

**Formule / algoritme:** L=RPE×minuten/60.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** RPE5,60min→5 historische eenheden.

**Excel:** NOT IMPLEMENTED: historical record path

**PDF hoofdstuk:** LOAD

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('RPE must be between 1 and 10.')

## ACT-01 - Activiteitvergelijking prioriteit

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/activity.py

**Functie:** classify_activity_match

**Regels:** 70

**Inputs en types:** *, duration: DurationMinutes, rpe: int, planned: PlannedActivityExpectation | None, measurement: ZoneLoad | None=None

**Eenheden:** Duur in minuten; belasting in interne eenheden; ratio als fractie; RPE integer 1–10; IDs en versies zijn labels.

**Voorwaarden en grenzen:** Gemiddelde-HR-schatting heeft status niet complete en wordt dus niet perfect/overshoot.

**Formule / algoritme:** Niet-complete meting eerst: low+RPE≥7→hidden_fatigue, anders deviation. Complete: unplanned eerst; vervolgens low+RPE≥7; ontbrekend gepland load; >1.15×plan; inclusieve .90..1.10 én RPE-band; anders deviation.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Complete100 versus plan100 en RPE-band→perfect; geschatte100→deviation.

**Excel:** 16_RPE_AND_OBSERVATIONS

**PDF hoofdstuk:** ACT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## ACT-02 - Correctie en provenance

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/activities/service.py

**Functie:** submit_rpe

**Regels:** 135

**Inputs en types:** self, athlete_id: UUID, activity_id: UUID, submission: ActivityRpeSubmission

**Eenheden:** Duur in minuten; belasting in interne eenheden; ratio als fractie; RPE integer 1–10; IDs en versies zijn labels.

**Voorwaarden en grenzen:** Nieuwe HR kan vóór initiële berekening worden opgeslagen; oude ruleset volgt oude compatibiliteit.

**Formule / algoritme:** Bestaande huidige private_load_snapshot behouden bij RPE-correctie. HR na berekening onveranderlijk. Andere RPE vereist expected_current_rpe; identieke retry idempotent.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** RPE4→5 met expected4 geldig; expected3 stale.

**Excel:** NOT IMPLEMENTED: immutable activity event log

**PDF hoofdstuk:** ACT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ActivityDomainError('An assigned RPE-guided workout requires an average heart-rate observation in bpm before session RPE can be completed.'); ActivityCorrectionConflictError('average_heart_rate_immutable', 'Average heart rate cannot be changed after its activity calculation.'); ActivityCorrectionConflictError('activity_correction_stale', 'An RPE correction requires the expected current RPE.'); ActivityCorrectionConflictError('activity_correction_stale', 'The activity correction is stale. Refresh and try again.'); ActivityDomainError('An initial RPE submission cannot include a correction precondition.'); ActivityDomainError('Stored activity duration is invalid.'); ActivityDomainError('Stored heart-rate zone context is invalid.')

## CAT-01 - Catalogusactivering

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/workouts/catalog.py

**Functie:** active_catalog

**Regels:** 985

**Inputs en types:** catalog: tuple[WorkoutTemplate, ...]=CURRENT_CATALOG

**Eenheden:** Duur in minuten; afstand in meter; belasting in interne eenheden of ontbrekend; zone-index 1–5; RPE integer 1–10; template/occurrence IDs en versies zijn labels.

**Voorwaarden en grenzen:** Broncatalogus omvat154 opvolgers; lokale Python-basiscatalogus vult dit aan. Migratie genereert nieuwe UUIDs willekeurig.

**Formule / algoritme:** Per template_key hoogste versie; duplicaat(key,version) fout. Sorteer sport.value,naam. Niet-actuele protocoltargets vallen af.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Versie1 blijft provenance, versie2 is selecteerbaar.

**Excel:** 08_TRAINING_CATALOG

**PDF hoofdstuk:** CAT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('The active catalog must cover swim, bike, and run.'); ValueError('Catalog template versions must be unique.')

## CAT-02 - Huidige geplande belasting

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/workouts/catalog.py

**Functie:** with_current_load

**Regels:** 1021

**Inputs en types:** template: WorkoutTemplate

**Eenheden:** Duur in minuten; afstand in meter; belasting in interne eenheden of ontbrekend; zone-index 1–5; RPE integer 1–10; template/occurrence IDs en versies zijn labels.

**Voorwaarden en grenzen:** Protocol-only zonder zones →onbeschikbaar. Geen duur schatten uit afstand.

**Formule / algoritme:** Timed source: behoud expliciete bronbelasting. Distance-only source swim: None. Overige templates: zone-minuten berekenen alleen met volledige zone/duurevidence.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Afstandzwemtraining heeft bronload maar geen actuele geplande load.

**Excel:** 08_TRAINING_CATALOG

**PDF hoofdstuk:** CAT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAT-03 - Geschiktheid volgorde

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** eligible_workouts

**Regels:** 533

**Inputs en types:** *, catalog: tuple[WorkoutTemplate, ...], phase: TrainingPhase, goal_disciplines: frozenset[Discipline], confirmed_injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline]=frozenset(), zone_capabilities: Mapping[Discipline, ZoneCapability], build_week: int | None=None

**Eenheden:** Duur in minuten; afstand in meter; belasting in interne eenheden of ontbrekend; zone-index 1–5; RPE integer 1–10; template/occurrence IDs en versies zijn labels.

**Voorwaarden en grenzen:** Base/recovery/taper alleen Z1/Z2 en whole-bucket low; build1..3 geen Z5; build4 Z5 mogelijk.

**Formule / algoritme:** 1 load aanwezig; 2 doelsport/blessure/fase/low-only/Z5; 3 capability; 4 protocolsubset; 5 fallbackcompatibility; 6 requirements of bestaande RPE-projectie. Sorteer sport,load,UUID.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Een Z3-workout met low-bronbucket valt toch af in BASE.

**Excel:** 10_ELIGIBLE_WORKOUTS

**PDF hoofdstuk:** CAT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## CAT-04 - RPE-uitvoeringsprojectie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/workouts/catalog.py

**Functie:** as_rpe_guided_template

**Regels:** 325

**Inputs en types:** template: WorkoutTemplate

**Eenheden:** Duur in minuten; afstand in meter; belasting in interne eenheden of ontbrekend; zone-index 1–5; RPE integer 1–10; template/occurrence IDs en versies zijn labels.

**Voorwaarden en grenzen:** Huidige kalibratieroute kan RPE-guidance gebruiken met HR-meter. Oud rpe_only-setup wordt door service geblokkeerd.

**Formule / algoritme:** Vervang uitvoeringsdoel door reeds gereviewde RPE-range; snapshot-ID, versie, bronload en whole-bucket behouden.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Ontbrekende numerieke match verandert geen load.

**Excel:** NOT IMPLEMENTED: segment projection

**PDF hoofdstuk:** CAT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## PLAN-01 - Eerdere goedkeuring

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** resolve_target

**Regels:** 211

**Inputs en types:** *, week_start: date, race_date: date, prior_loads: tuple[PlanLoadSample, ...], initial_catalog_load: InternalLoad, maintenance_active: bool=False, prior_approved_plan_exists: bool | None=None

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Activiteiten, pending en rejected plannen zijn geen goedkeuring. Terugkerende sporter krijgt geen verzonnen BASE.

**Formule / algoritme:** has_prior_approved_plan actorflag is onafhankelijk van activiteiten. Eerst flag vaststellen, dan sick_week-samples verwijderen. Flag true + geen eligible historie →approved_plan_baseline_unavailable.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Kalibratiehistorie zonder goedgekeurd plan →eerste BASE.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('approved_plan_baseline_unavailable', 'An eligible historical baseline is required for a returning athlete.'); ValueError('The training week must start on Monday.'); PlanningConstraintError('race_date_before_week', 'The primary race date is before the requested training week.'); PlanningConstraintError('partial_week_taper_rule_required', 'A reviewed target for this exact pre-race date window is required.'); PlanningConstraintError('maintenance_baseline_unavailable', 'Maintenance requires a prior approved weekly plan baseline.'); PlanningConstraintError('taper_baseline_unavailable', 'A taper week requires an available prior build-load baseline.'); PlanningConstraintError('physiological_debt_escalation_required', 'Repeated unsafe load requires review by a qualified person.')

## PLAN-02 - Faseritme

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _race_anchored_phase

**Regels:** 195

**Inputs en types:** *, week_start: date, race_date: date

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** weekStart maandag. Eerste plan gewone fase is BASE, ook op nominale recoverypositie.

**Formule / algoritme:** raceMonday=raceDate-weekday; w=floor((raceMonday-weekStart)/7). Gewone recovery als w mod5=0; buildpositie=5-(w mod5). Taper overlap eerst.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Vier BUILD-posities 1/2/3/4 volgen recovery0.

**Excel:** 09_WEEK_SETUP

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## PLAN-03 - Tapervenster

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** resolve_target

**Regels:** 211

**Inputs en types:** *, week_start: date, race_date: date, prior_loads: tuple[PlanLoadSample, ...], initial_catalog_load: InternalLoad, maintenance_active: bool=False, prior_approved_plan_exists: bool | None=None

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** BASE-uitzondering komt pas na taper; ontbrekende taperbaseline is geen eerste-week-fallback.

**Formule / algoritme:** D-7..D-1 inclusief. Overlappende week alleen berekenbaar als raceDate=weekStart+7, anders partial_week_taper_rule_required.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Maandagwedstrijd geeft volledige vorige week; zondagwedstrijd gedeeltelijk→blok.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('approved_plan_baseline_unavailable', 'An eligible historical baseline is required for a returning athlete.'); ValueError('The training week must start on Monday.'); PlanningConstraintError('race_date_before_week', 'The primary race date is before the requested training week.'); PlanningConstraintError('partial_week_taper_rule_required', 'A reviewed target for this exact pre-race date window is required.'); PlanningConstraintError('maintenance_baseline_unavailable', 'Maintenance requires a prior approved weekly plan baseline.'); PlanningConstraintError('taper_baseline_unavailable', 'A taper week requires an available prior build-load baseline.'); PlanningConstraintError('physiological_debt_escalation_required', 'Repeated unsafe load requires review by a qualified person.')

## PLAN-04 - 42-daags gemiddelde

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/progression.py

**Functie:** calculate_42_day_average

**Regels:** 53

**Inputs en types:** samples: tuple[WeeklyLoad, ...], *, as_of: date, exclude_recovery_weeks: bool=False, rule_id: RuleId=RuleId.PROGRESSIVE_LOAD, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Geen zesweken-deler bij minder samples; geen exponentieel CTL. SQL levert zelf calendar gaps sinds vroegste evidence.

**Formule / algoritme:** Selecteer starts in [as_of-41,as_of], gemiddelde van aanwezige samples. Duplicaat weekstart fout; recovery optioneel uitgesloten.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** 100,200,300 drie eligible→200.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Weekly load samples must have unique start dates.')

## PLAN-05 - Recoverybelasting

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/recovery.py

**Functie:** calculate_recovery_target

**Regels:** 78

**Inputs en types:** *, week_four_planned: InternalLoad, factor: Decimal=_RECOVERY_FACTOR, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Recovery wordt vóór reguliere progressie/debt afgehandeld. Niet afgerond in functie.

**Formule / algoritme:** Target=vorige geplande load×.60. Helper accepteert factor .40.. .60 inclusief; planner gebruikt .60.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Plan200→recovery120.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Recovery factor must be between 0.40 and 0.60.')

## PLAN-06 - Taperbelasting

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/taper.py

**Functie:** calculate_taper_target

**Regels:** 87

**Inputs en types:** *, priority: RacePriority, period: TaperPeriod | None, baseline: InternalLoad, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** A T-2/B/C zijn helpergedrag, geen huidige raceplannerroute.

**Formule / algoritme:** Actieve volledige A-taper target=gemiddelde geplande niet-recovery loads in42dagen×.35. Helper kent daarnaast A T-2 .60, B .50, C geen taper.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Baseline200→70.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('A- and B-races require a taper period.'); ValueError('A-races require an A-race taper period.'); ValueError('B-races require the B-race taper week.'); ValueError('C-races do not have a taper period.')

## PLAN-07 - Minder uitgevoerd bij gemist/vermoeid

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** resolve_target

**Regels:** 211

**Inputs en types:** *, week_start: date, race_date: date, prior_loads: tuple[PlanLoadSample, ...], initial_catalog_load: InternalLoad, maintenance_active: bool=False, prior_approved_plan_exists: bool | None=None

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Vóór volumede debt en gewone 80%-regel. Sick-weken uitgesloten.

**Formule / algoritme:** Als reduced_realized_progression of completed_activity_count=0 én realized<planned: target=realized×1.10.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Plan100,realized50,fatigue→55.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('approved_plan_baseline_unavailable', 'An eligible historical baseline is required for a returning athlete.'); ValueError('The training week must start on Monday.'); PlanningConstraintError('race_date_before_week', 'The primary race date is before the requested training week.'); PlanningConstraintError('partial_week_taper_rule_required', 'A reviewed target for this exact pre-race date window is required.'); PlanningConstraintError('maintenance_baseline_unavailable', 'Maintenance requires a prior approved weekly plan baseline.'); PlanningConstraintError('taper_baseline_unavailable', 'A taper week requires an available prior build-load baseline.'); PlanningConstraintError('physiological_debt_escalation_required', 'Repeated unsafe load requires review by a qualified person.')

## PLAN-08 - Volumeschuld

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/debt.py

**Functie:** calculate_volume_debt

**Regels:** 54

**Inputs en types:** *, prior_planned: InternalLoad, prior_realized: InternalLoad, exceptional_zero_allowed: bool=False, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Corrected≤0→review tenzij expliciete exceptional_zero_allowed. Planner recovery .60; herhaling manual-review-recovery→escalatie.

**Formule / algoritme:** Activeer uitsluitend realized>1.10×planned. Debt=realized-planned. Corrected=1.10×planned-debt=2.10×planned-realized.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Plan100,realized120→90; realized110 activeert niet.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## PLAN-09 - Reguliere progressie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/progression.py

**Functie:** calculate_progressive_target

**Regels:** 82

**Inputs en types:** *, prior_planned: InternalLoad, prior_realized: InternalLoad, baseline: InternalLoad | None, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Naam REALIZED_PROGRESSION betekent reguliere branch gebruikt planned×1.10. Exact80% hoort regulier.

**Formule / algoritme:** Als planned>0 én realized≥.80×planned: target=1.10×planned. Anders42-daagse realized baseline vereist.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Plan100,realized80→110; realized79→baseline.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('A baseline is required for heavy undershoot or zero load.')

## PLAN-10 - Onbekende realized

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** resolve_target

**Regels:** 211

**Inputs en types:** *, week_start: date, race_date: date, prior_loads: tuple[PlanLoadSample, ...], initial_catalog_load: InternalLoad, maintenance_active: bool=False, prior_approved_plan_exists: bool | None=None

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** SQL geen activiteiten geeft expliciet0; activiteiten zonder huidige load geeft None. Niet verwisselen.

**Formule / algoritme:** Laatste realized=None →houd laatste planned. Geen samples en geen eerdere approval →onboarding baseline.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Plan100, measurement unavailable→100; geen activiteit0→andere branch.

**Excel:** 19_NEXT_WEEK

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('approved_plan_baseline_unavailable', 'An eligible historical baseline is required for a returning athlete.'); ValueError('The training week must start on Monday.'); PlanningConstraintError('race_date_before_week', 'The primary race date is before the requested training week.'); PlanningConstraintError('partial_week_taper_rule_required', 'A reviewed target for this exact pre-race date window is required.'); PlanningConstraintError('maintenance_baseline_unavailable', 'Maintenance requires a prior approved weekly plan baseline.'); PlanningConstraintError('taper_baseline_unavailable', 'A taper week requires an available prior build-load baseline.'); PlanningConstraintError('physiological_debt_escalation_required', 'Repeated unsafe load requires review by a qualified person.')

## PLAN-11 - Maintenance

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** resolve_target

**Regels:** 211

**Inputs en types:** *, week_start: date, race_date: date, prior_loads: tuple[PlanLoadSample, ...], initial_catalog_load: InternalLoad, maintenance_active: bool=False, prior_approved_plan_exists: bool | None=None

**Eenheden:** Belasting in interne eenheden; voltooiingen als aantal; venster in kalenderdagen; weekstart en wedstrijd als lokale datum; flags booleans.

**Voorwaarden en grenzen:** Gebruikt zeswekenlijst, geen globaal weeknummer. Race-before-week check uitgezonderd bij maintenance.

**Formule / algoritme:** Geen prior→maintenance_baseline_unavailable. Elke vijfde op basis len(filtered prior)+1 recovery .60; anders prior planned hold.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Vier eligible historyrows→recovery.

**Excel:** NOT IMPLEMENTED: maintenance selector

**PDF hoofdstuk:** PLAN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('approved_plan_baseline_unavailable', 'An eligible historical baseline is required for a returning athlete.'); ValueError('The training week must start on Monday.'); PlanningConstraintError('race_date_before_week', 'The primary race date is before the requested training week.'); PlanningConstraintError('partial_week_taper_rule_required', 'A reviewed target for this exact pre-race date window is required.'); PlanningConstraintError('maintenance_baseline_unavailable', 'Maintenance requires a prior approved weekly plan baseline.'); PlanningConstraintError('taper_baseline_unavailable', 'A taper week requires an available prior build-load baseline.'); PlanningConstraintError('physiological_debt_escalation_required', 'Repeated unsafe load requires review by a qualified person.')

## INT-01 - Weekverdeling

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _workout_intensity

**Regels:** 1300

**Inputs en types:** workout: ProposedWorkout

**Eenheden:** Duur in minuten; belasting in interne eenheden; fracties 0–1 en displaypercentage 0–100.

**Voorwaarden en grenzen:** Z3 is high bij segmentclassificatie; equal low/high dominant→high. Afstand-only niet in tijddeler.

**Formule / algoritme:** Tijd van complete workout valt volledig in gereviewde whole-bucket low/high. Segmentzones blijven uitvoering/load.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** 90min low +30min high→75/25, los van private-load-ratio.

**Excel:** 17_PLANNED_LOAD

**PDF hoofdstuk:** INT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## INT-02 - Intensiteitschuld

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/debt.py

**Functie:** calculate_reliable_intensity_debt

**Regels:** 108

**Inputs en types:** *, planned_high: DurationMinutes, planned_total: DurationMinutes, realized_high: DurationMinutes, realized_classified: DurationMinutes, realized_total: DurationMinutes, base_next_high_fraction: Fraction=Fraction(Decimal('0.20')), discipline_injury_confirmed: bool=False, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Duur in minuten; belasting in interne eenheden; fracties 0–1 en displaypercentage 0–100.

**Voorwaarden en grenzen:** Positieve totals, high≤classified≤total. Injury helperfloor0. Planner eerste eligible non-recovery; sla één voorafgaande recovery over.

**Formule / algoritme:** Coverage=classified/total≥.60 vereist. Debt=max(0,realizedHigh/classified-plannedHigh/plannedTotal). NextHigh=max(.05,.20-debt).

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Planned .20,realized .40,coverage1→.05.

**Excel:** NOT IMPLEMENTED: downstream intensity debt

**PDF hoofdstuk:** INT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Planned and realized totals must be positive.'); ValueError('Planned high-intensity time cannot exceed its total.'); ValueError('Classified time cannot exceed realized activity time.'); ValueError('Realized high-intensity time cannot exceed classified time.')

## INT-03 - Displayafronding

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/intensity.py

**Functie:** display_time_distribution

**Regels:** 180

**Inputs en types:** distribution: TimeDistribution

**Eenheden:** Duur in minuten; belasting in interne eenheden; fracties 0–1 en displaypercentage 0–100.

**Voorwaarden en grenzen:** Exacte minuten blijven; lege verdeling helper error. Planner rest-only rapporteert0/0.

**Formule / algoritme:** Low%=HALF_UP(100×lowFraction,0); High%=100-Low%.

**Afronding:** Decimal ROUND_HALF_UP zoals expliciet beschreven

**Voorbeeld:** Low .795→80,high20.

**Excel:** 17_PLANNED_LOAD

**PDF hoofdstuk:** INT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('An evaluated intensity distribution is required.')

## INT-04 - Intensieve duurwaarschuwing

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/intensity.py

**Functie:** intensive_duration_warning

**Regels:** 203

**Inputs en types:** *, planned: DurationMinutes, realized: DurationMinutes, specification: PhysiologySpecification=PHASE_3_RULESET_V3

**Eenheden:** Duur in minuten; belasting in interne eenheden; fracties 0–1 en displaypercentage 0–100.

**Voorwaarden en grenzen:** Strict >; helper geen huidige loadproxy.

**Formule / algoritme:** Warn realized>1.30×planned; planned0→warn als realized>0.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** 130/100 geen waarschuwing;130.1 wel.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** INT

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## SEL-01 - Selectiebeleid

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _selection_policy_valid

**Regels:** 666

**Inputs en types:** selection: tuple[WorkoutTemplate, ...], *, target: InternalLoad, phase: TrainingPhase, build_week: int | None, desired_high_fraction: Fraction, high_available: bool, z5_available: bool, minimum_load: Decimal, discipline_caps: Mapping[Discipline, InternalLoad] | None=None

**Eenheden:** Belasting in interne eenheden; occurrences en sportcounts als gehele aantallen; datums lokaal; IDs als UUID; fracties 0–1.

**Voorwaarden en grenzen:** High_available kijkt load≤budget, niet totale plaatsbaarheid. Echte lege/no-solution mogelijk.

**Formule / algoritme:** Abs(target-sumload)<minimum deckload. Cap per sport. Niet-BUILD highload=0. BUILD high≤target×desiredHigh. Met high beschikbaar build1..3: .70.. .90×highbudget; build4 high>0 en Z5 indien beschikbaar.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Target100,min20:load80 afgewezen (gelijkheid20),81 kan.

**Excel:** NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie

**PDF hoofdstuk:** SEL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## SEL-02 - Begrensde multisetsearch

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _bounded_selection

**Regels:** 722

**Inputs en types:** *, deck: tuple[WorkoutTemplate, ...], prefix: tuple[WorkoutTemplate, ...], required_disciplines: frozenset[Discipline], target: InternalLoad, phase: TrainingPhase, build_week: int | None, desired_high_fraction: Fraction, required_count: int | None=None, required_composition: Mapping[Discipline, int] | None=None, maximum_uses: Mapping[UUID, int] | None=None, discipline_caps: Mapping[Discipline, InternalLoad] | None=None, feasible: Callable[[tuple[WorkoutTemplate, ...]], bool] | None=None

**Eenheden:** Belasting in interne eenheden; occurrences en sportcounts als gehele aantallen; datums lokaal; IDs als UUID; fracties 0–1.

**Voorwaarden en grenzen:** Score lexicografisch abs(total-target), abs(high-budget) bij BUILD, aantal, UUID-pad. Bij exact total beste gevonden stop na huidige count.

**Formule / algoritme:** Max24 occurrences. Group(sport,load,bucket,Z5), representant kleinste UUID. States(total,high,sportcounts,highcounts,limitedcounts,Z5). Breid één occurrence uit, snoei caps/counts/high/maxload.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Herhaling dezelfde template toegestaan; kaart-occurrence uniek.

**Excel:** NOT IMPLEMENTED: automatic search

**PDF hoofdstuk:** SEL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## SEL-03 - Swipetarget vast

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/service.py

**Functie:** _prepare_swipe_context

**Regels:** 544

**Inputs en types:** self, *, athlete_id: UUID, input_source: Mapping[str, Any], initial_plan_request_id: UUID, plan_id: UUID | None, base_plan_revision: int, context_plan_revision: int | None, week_start: date, available_dates: tuple[date, ...], availability_source: str, injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline], cross_training_opt_ins: frozenset[Discipline]=frozenset()

**Eenheden:** Belasting in interne eenheden; occurrences en sportcounts als gehele aantallen; datums lokaal; IDs als UUID; fracties 0–1.

**Voorwaarden en grenzen:** Geen acceptactie die op zichzelf plan activeert.

**Formule / algoritme:** Automatisch geldig voorstel bepaalt fixed target count en sportcomposition. Hash omvat context, history, regels, catalogus-ID/versie, availability en basisrevision.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Doelaantal3 blijft3 terwijl cards wisselen.

**Excel:** NOT IMPLEMENTED: exact swipe composition

**PDF hoofdstuk:** SEL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningDomainError('The planning input fingerprint is missing.')

## SEL-04 - Swipemogelijke completion

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/service.py

**Functie:** _selection_has_completion

**Regels:** 692

**Inputs en types:** self, *, context: _SwipePlanningContext, week_start: date, available_dates: tuple[date, ...], injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline], accepted_template_ids: tuple[UUID, ...], passed_template_ids: tuple[UUID, ...]

**Eenheden:** Belasting in interne eenheden; occurrences en sportcounts als gehele aantallen; datums lokaal; IDs als UUID; fracties 0–1.

**Voorwaarden en grenzen:** Next candidate is completion[len(accepted)]. Passen sluit occurrence uit, niet noodzakelijk template voor altijd.

**Formule / algoritme:** Prefix=accepted. Maxuses=id:targetCount-passCount. Eerst pool zonder gepasseerde templates, dan pool met resterende uses. Search met exact count/composition en finale build validation.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Zelfde template later opnieuw als composition dit nodig heeft.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** SEL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## SEL-05 - CHOOSE/SKIP/UNDO/RESET

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/swipe.py

**Functie:** apply_swipe_decision

**Regels:** 67

**Inputs en types:** state: SwipeSelectionState, *, action: SwipeDecisionKind, current_template_id: UUID, expected_template_id: UUID, target_workout_count: int, current_occurrence_id: UUID | None=None, expected_occurrence_id: UUID | None=None

**Eenheden:** Belasting in interne eenheden; occurrences en sportcounts als gehele aantallen; datums lokaal; IDs als UUID; fracties 0–1.

**Voorwaarden en grenzen:** Template mag herhalen; occurrence niet. Stale actie mag geen historie veranderen.

**Formule / algoritme:** Huidige template+occurrence moeten expected gelijk zijn. Reeds decided occurrence fout; accept voorbij fixed count fout. UNDO verwijdert exact laatste historyentry; RESET behoudt alleen ACCEPT.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** RESET na acceptA/passB behoudtA.

**Excel:** NOT IMPLEMENTED: immutable action history

**PDF hoofdstuk:** SEL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('swipe_candidate_stale', 'The visible workout card changed. Refresh the swipe draft.'); PlanningConstraintError('swipe_candidate_stale', 'The visible workout card changed. Refresh the swipe draft.'); PlanningConstraintError('swipe_candidate_decided', 'This workout card was already decided in the current draft.'); PlanningConstraintError('swipe_target_complete', 'The fixed workout target is already complete.')

## PLACE-01 - Elapsed anti-stack

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/anti_stack.py

**Functie:** find_anti_stack_violations

**Regels:** 56

**Inputs en types:** workouts: tuple[ScheduledWorkout, ...], *, specification: PhysiologySpecification=JOREN_PLANNING_RULESET_V2

**Eenheden:** Lokale kalenderdatums met IANA-zone; intern UTC-tijdstip; spacing in werkelijk verstreken uren; reststreak in dagen.

**Voorwaarden en grenzen:** Gelijkheid geldig. Verschillende sporten onafhankelijk. Date-only wordt lokale middag; DST kan kalenderdagenverschil±1uur geven.

**Formule / algoritme:** Per sport sorteer HIGH op UTC instant; adjacent verschil moet run≥72h,bike/swim≥48h.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Run za→di rond voorjaar kan71h zijn en faalt.

**Excel:** 12_PLACEMENT

**PDF hoofdstuk:** PLACE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## PLACE-02 - Automatische plaatsing

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** schedule_workouts

**Regels:** 1132

**Inputs en types:** *, selected: tuple[SelectedWorkout, ...], available_dates: tuple[date, ...], week_start: date, timezone_name: str, fixed_template_dates: Mapping[UUID, date] | None=None, fixed_occurrence_dates: Mapping[UUID, date] | None=None

**Eenheden:** Lokale kalenderdatums met IANA-zone; intern UTC-tijdstip; spacing in werkelijk verstreken uren; reststreak in dagen.

**Voorwaarden en grenzen:** Meer sessies per dag toegestaan. Restlimiet≤3 enkel als enige subset van maximaal min(count,availabledays) dit kan realiseren én geen fixed.

**Formule / algoritme:** Volgorde HIGH eerst,sport,templateUUID. Backtracking datums geordend usage, langste reststreak na toevoeging,datum. Fixed occurrence heeft voorrang.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Eén workout mag >3 restdagen opleveren als onhaalbaar.

**Excel:** NOT IMPLEMENTED: automatic placement

**PDF hoofdstuk:** PLACE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('rest_or_anti_stack_unsatisfied', 'The generated schedule cannot satisfy rest-day and anti-stack constraints.'); PlanningConstraintError('availability_required', 'At least one available date is required for auto-scheduling.'); PlanningConstraintError('duplicate_available_date', 'Available dates must be unique.'); PlanningConstraintError('fixed_template_not_selected', 'A fixed workout date must reference an accepted workout.'); PlanningConstraintError('availability_outside_week', 'Available dates must fall inside the requested athlete week.'); PlanningConstraintError('fixed_date_unavailable', 'Every fixed workout date must be one of the available dates.')

## PLACE-03 - Handmatige plaatsing

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** validate_manual_schedule

**Regels:** 1792

**Inputs en types:** *, workouts: tuple[ScheduledWorkout, ...], moved_workout_id: str | None

**Eenheden:** Lokale kalenderdatums met IANA-zone; intern UTC-tijdstip; spacing in werkelijk verstreken uren; reststreak in dagen.

**Voorwaarden en grenzen:** Available unique/inweek/fixed selected/available worden schedule_workouts afzonderlijk gecontroleerd.

**Formule / algoritme:** Bij spacing violation betreffende moved workout (of moveID=None) hard anti_stack_violation; anders geen warnings.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Invalid move mag actieve plan niet wijzigen.

**Excel:** 12_PLACEMENT

**PDF hoofdstuk:** PLACE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('anti_stack_violation', 'High-intensity workouts need more time between sessions.')

## INJ-01 - Functionele beperkingen

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/checkins/domain.py

**Functie:** confirmed_restriction_sets

**Regels:** 89

**Inputs en types:** decisions: Sequence[RestrictionDecision]

**Eenheden:** Belasting in interne eenheden; transferable en high als fracties; sportrestricties als labels/booleans.

**Voorwaarden en grenzen:** Reviewdatum auto-clear niet; professionele bron/datum samen vereist.

**Formule / algoritme:** none→unrestricted; self_reported_limited→low_only; blocked/professional/clearance/expired→none. Eén beslissing per sport.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Expired blijft blocked tot nieuwe expliciete keuze.

**Excel:** 09_WEEK_SETUP

**PDF hoofdstuk:** INJ

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** ValueError('Each discipline can have only one restriction decision.')

## INJ-02 - Projecteer vooraf

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _injury_adjusted_target

**Regels:** 438

**Inputs en types:** *, target: PlanningTarget, prior_loads: tuple[PlanLoadSample, ...], onboarding_baseline: StartingBaseline | None, blocked: frozenset[Discipline], goal_disciplines: frozenset[Discipline], eligible_recipients: frozenset[Discipline], cross_training_opt_ins: frozenset[Discipline], desired_high_fraction: Fraction

**Eenheden:** Belasting in interne eenheden; transferable en high als fracties; sportrestricties als labels/booleans.

**Voorwaarden en grenzen:** Positieve totale basis nodig. Pas nadat normale target/phase is bepaald.

**Formule / algoritme:** basis=laatste history met sportloads, anders onboardingcomponents. normal_s=target×basis_s/sombasis; safeCap_s=max(normal_s,1.10×basis_s).

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Basisrun100,bike100,target220→normal110/110, recipientruimte0.

**Excel:** NOT IMPLEMENTED: injury allocation

**PDF hoofdstuk:** INJ

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('injury_discipline_basis_unavailable', 'A reviewed discipline load basis is required for this restriction.')

## INJ-03 - Begrensde waterfill

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/injury.py

**Functie:** redistribute_confirmed_injury_load

**Regels:** 132

**Inputs en types:** *, pre_injury_targets: Mapping[Discipline, InternalLoad], recipient_safe_caps: Mapping[Discipline, InternalLoad], blocked_disciplines: frozenset[Discipline], cross_training_opt_ins: frozenset[Discipline]=frozenset(), specification: PhysiologySpecification=JOREN_PLANNING_RULESET_V2

**Eenheden:** Belasting in interne eenheden; transferable en high als fracties; sportrestricties als labels/booleans.

**Voorwaarden en grenzen:** Run nooit ontvanger. Opt-in met nulbasis creëert geen capaciteit. Overcapaciteit weggegooid.

**Formule / algoritme:** Transferable=.80×blockedNormal. Alleen bike/swim met positive normal en safeCap>normal. Verdeel proportioneel normal-gewicht; vul capped ontvangers, herverdeel restant, laatste alfabetische ontvanger krijgt rekenrest.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Verwijderd100, ruimte bike10 →transfer10,rest70 niet toegewezen.

**Excel:** NOT IMPLEMENTED: injury allocation

**PDF hoofdstuk:** INJ

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## INJ-04 - High na blessure

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** _injury_adjusted_target

**Regels:** 438

**Inputs en types:** *, target: PlanningTarget, prior_loads: tuple[PlanLoadSample, ...], onboarding_baseline: StartingBaseline | None, blocked: frozenset[Discipline], goal_disciplines: frozenset[Discipline], eligible_recipients: frozenset[Discipline], cross_training_opt_ins: frozenset[Discipline], desired_high_fraction: Fraction

**Eenheden:** Belasting in interne eenheden; transferable en high als fracties; sportrestricties als labels/booleans.

**Voorwaarden en grenzen:** Replacement sport volledig low-only; highbudget krijgt geen extra transfer-high.

**Formule / algoritme:** NewTotal=unblockedNormal+redistributed. DesiredHigh=min(1,unblockedNormal×oldHigh/NewTotal), of0 bij NewTotal0.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Unblocked100,transfer10,oldHigh .20→highbudget20.

**Excel:** NOT IMPLEMENTED

**PDF hoofdstuk:** INJ

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('injury_discipline_basis_unavailable', 'A reviewed discipline load basis is required for this restriction.')

## INJ-05 - Rust-only en nulbasis

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** build_weekly_plan

**Regels:** 1342

**Inputs en types:** *, week_start: date, timezone_name: str, race_date: date, catalog: tuple[WorkoutTemplate, ...], prior_loads: tuple[PlanLoadSample, ...], goal_disciplines: frozenset[Discipline], confirmed_injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline]=frozenset(), cross_training_opt_ins: frozenset[Discipline]=frozenset(), zone_capabilities: Mapping[Discipline, ZoneCapability], available_dates: tuple[date, ...], selected_template_ids: Collection[UUID] | None=None, fixed_template_dates: Mapping[UUID, date] | None=None, selected_occurrence_ids: Collection[UUID] | None=None, fixed_occurrence_dates: Mapping[UUID, date] | None=None, maintenance_active: bool=False, onboarding_baseline: StartingBaseline | None=None

**Eenheden:** Belasting in interne eenheden; transferable en high als fracties; sportrestricties als labels/booleans.

**Voorwaarden en grenzen:** Rust-only is voorstel, niet automatisch actief. Oude apply_mvp_injury_policy zero-transfer is historisch, huidige v2 gebruikt nieuwe helper.

**Formule / algoritme:** Geen ongeblesseerde goalsport en geen historische veilige ontvanger→pending rest-only0. Restricted all-zero onboarding waar eerdere shortcut niet geldt→restricted_zero_base_allocation_unavailable.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** Alle doelsporten geblokkeerd zonder bike/swim-basis→rest-only.

**Excel:** NOT IMPLEMENTED: full precedence

**PDF hoofdstuk:** INJ

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('zero_history_discipline_baseline_unavailable', 'The catalog cannot fill this composition without an approved starting target for the untrained discipline.'); PlanningConstraintError('catalog_empty', 'No workout templates match the confirmed athlete configuration.'); PlanningConstraintError('catalog_coverage_unsatisfied', 'The current catalog cannot cover every uninjured goal discipline.'); PlanningConstraintError('catalog_phase_coverage_unavailable', f'No reviewed {target.phase.value} workout is available for: {missing_labels}.'); PlanningConstraintError('restricted_zero_base_allocation_unavailable', 'A reviewed starting allocation is required for this restricted introduction week.'); PlanningConstraintError('taper_catalog_coverage_unavailable', f'No reviewed taper workout is available for: {missing_labels}. This pre-race week cannot be generated yet.'); PlanningConstraintError('explicit_test_date_required', 'Every explicitly scheduled field test requires an exact date.')

## STATE-01 - Plan goedkeuren

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/service.py

**Functie:** approve_plan_proposal

**Regels:** 2727

**Inputs en types:** self, access_token: str, proposal_id: UUID, expected_base_revision: int

**Eenheden:** Plan/proposal/revision IDs en modelversies; weekstart als lokale datum; historische belasting in interne eenheden of NULL.

**Voorwaarden en grenzen:** Identieke applied retry geldig na base-match; andere terminalstate fout. SQL bron20260729140000:1214-1302 plus latere wrappers.

**Formule / algoritme:** Owner-scoped pending voorstel + expected base =proposal.base én huidige active revision, targetrevision pending_approval. Vorige active→superseded; target→active; proposal→applied atomair.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Pending selectie blijft niet actief tot approve.

**Excel:** 14_PLAN_APPROVAL: illustrative only

**PDF hoofdstuk:** STATE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## STATE-02 - Plan verwerpen

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/service.py

**Functie:** reject_plan_proposal

**Regels:** 2741

**Inputs en types:** self, access_token: str, proposal_id: UUID

**Eenheden:** Plan/proposal/revision IDs en modelversies; weekstart als lokale datum; historische belasting in interne eenheden of NULL.

**Voorwaarden en grenzen:** Applied kan niet verworpen. Databasevergrendeling en ownership geen Excel-emulatiebewijs.

**Formule / algoritme:** Owner pending→proposal rejected en targetrevision rejected; bestaande active_revision blijft. Rejected retry idempotent.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Active1 +pending2 rejected houdt active1.

**Excel:** 14_PLAN_APPROVAL: illustrative only

**PDF hoofdstuk:** STATE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## STATE-03 - Historische reader

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/repository.py

**Functie:** fetch_load_history

**Regels:** 75

**Inputs en types:** self, athlete_id: UUID, before_week: date

**Eenheden:** Plan/proposal/revision IDs en modelversies; weekstart als lokale datum; historische belasting in interne eenheden of NULL.

**Voorwaarden en grenzen:** Alleen huidig loadruleset telt; geen herberekening historische records. Sickfilter is downstream.

**Formule / algoritme:** v15 draagt expliciete actor-approvalbool per historyrow. v13 genereert maximaal6 complete weken vanaf vroegste plan/activity. Geen activiteiten→realized0; wel activiteiten maar geen current load→None.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Activity-only calendarweek met approvedflagFalse verandert eerste BASE niet.

**Excel:** 05_HISTORY: explicit manual snapshots

**PDF hoofdstuk:** STATE

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## WARN-01 - Waarschuwingen voorstel

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/planning/domain.py

**Functie:** build_weekly_plan

**Regels:** 1342

**Inputs en types:** *, week_start: date, timezone_name: str, race_date: date, catalog: tuple[WorkoutTemplate, ...], prior_loads: tuple[PlanLoadSample, ...], goal_disciplines: frozenset[Discipline], confirmed_injuries: frozenset[Discipline], low_only_disciplines: frozenset[Discipline]=frozenset(), cross_training_opt_ins: frozenset[Discipline]=frozenset(), zone_capabilities: Mapping[Discipline, ZoneCapability], available_dates: tuple[date, ...], selected_template_ids: Collection[UUID] | None=None, fixed_template_dates: Mapping[UUID, date] | None=None, selected_occurrence_ids: Collection[UUID] | None=None, fixed_occurrence_dates: Mapping[UUID, date] | None=None, maintenance_active: bool=False, onboarding_baseline: StartingBaseline | None=None

**Eenheden:** Belasting en minuten waar de waarschuwing daarop betrekking heeft; overige context als labels.

**Voorwaarden en grenzen:** Eerste fouten beëindigen vóór warnings. Empty rest-only eigen warning.

**Formule / algoritme:** Volgorde: distance-only,consolidated,intensity debt,manual review,target verschil,injury excluded,capacity limited,crosschoice,low-only.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Target194.1 versus gekozen194 geeft target_outside_catalog_capacity.

**Excel:** NOT IMPLEMENTED: 13_WEEK_PROPOSAL bevat alleen referentie of onvolledige proposalinformatie

**PDF hoofdstuk:** WARN

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** PlanningConstraintError('zero_history_discipline_baseline_unavailable', 'The catalog cannot fill this composition without an approved starting target for the untrained discipline.'); PlanningConstraintError('catalog_empty', 'No workout templates match the confirmed athlete configuration.'); PlanningConstraintError('catalog_coverage_unsatisfied', 'The current catalog cannot cover every uninjured goal discipline.'); PlanningConstraintError('catalog_phase_coverage_unavailable', f'No reviewed {target.phase.value} workout is available for: {missing_labels}.'); PlanningConstraintError('restricted_zero_base_allocation_unavailable', 'A reviewed starting allocation is required for this restricted introduction week.'); PlanningConstraintError('taper_catalog_coverage_unavailable', f'No reviewed taper workout is available for: {missing_labels}. This pre-race week cannot be generated yet.'); PlanningConstraintError('explicit_test_date_required', 'Every explicitly scheduled field test requires an exact date.')

## VAL-01 - Eindige domeinwaarden

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/models.py

**Functie:** InternalLoad.__post_init__

**Regels:** 88

**Inputs en types:** Zie broncontract

**Eenheden:** Interne belasting/duration niet-negatief en eindig; fractions 0–1; provenance en identifiers als niet-lege labels.

**Voorwaarden en grenzen:** Geen negatieve load clamp behalve expliciet debt exception. Pydantic transport heeft aanvullende ranges.

**Formule / algoritme:** Load/duration eindig en niet-negatief; fraction in[0,1]; identifiers en rulesetprovenance niet leeg.

**Afronding:** Geen extra afronding toevoegen; Decimal intern

**Voorbeeld:** NaN/negatief ongeldig; expliciet0 toegestaan in load.

**Excel:** input validations; detailed contracts NOT IMPLEMENTED

**PDF hoofdstuk:** VAL

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

## PREC-01 - Prioriteit en versie

**Categorie:** CURRENT IMPLEMENTATION

**Bron:** backend/app/modules/physiology/precedence.py

**Functie:** build_decision_run

**Regels:** 35

**Inputs en types:** *, run_id: UUID, specification: PhysiologySpecification, evaluations: Iterable[RuleEvaluation]

**Eenheden:** Regelstage als geordend label; versie en approvalstatus als provenance, zonder fysische eenheid.

**Voorwaarden en grenzen:** Pure helper-order onderscheid actual planning/domain flow. Historische waarden eigen versie behouden.

**Formule / algoritme:** Stable sort op stage; eerste conflict hoogste prioriteit. Iedere geëvalueerde regel moet approved zijn in versioned specification.

**Afronding:** Geen nieuwe numerieke afronding in deze beslis-/state-regel. Bewaar de aangeleverde modelprovenance.

**Voorbeeld:** Draft specification kan actieve beslissing niet produceren.

**Excel:** NOT IMPLEMENTED: 07_RULES_AND_FORMULAS bevat alleen referentie of onvolledige proposalinformatie

**PDF hoofdstuk:** PREC

**Bewerkbaarheid:** Zichtbare Excel-formule waar gekoppeld; structurele branchwijziging vereist port en nieuwe pariteit

**Tests:** Bestaande offline backendtests; geen volledige branchdekking bewezen

**Fout/no-result:** Zie functie en voorwaarden. Geen ontbrekend resultaat vervangen door nul.

# Review van roadmapfasen 10, 10.1 en 11

Reviewdatum: 2026-09-01

Dit document gebruikt de gevraagde bestandsnaam, maar volgt de inhoudelijke
opdracht: fase 10 en fase 11 uit `mvp-roadmap.md`. Fase 10.1 is meegenomen
omdat deze als afzonderlijke MVP-uitbreiding tussen beide fasen staat en
rechtstreeks bepaalt of fase 10 als volledige productflow kan worden beschouwd.
Fase 12 is niet inhoudelijk beoordeeld.

## Eindoordeel

- **Fase 10 is op codeniveau vrijwel volledig geïmplementeerd.** De
  datumcontracten, expliciete beschikbaarheid, lokale rustdatums,
  server-authoritatieve voorstelwijzigingen, BR-004, begrensde LLM-laag,
  bevestigingsflow en TSS-afscherming zijn aanwezig en getest.
- **Fase 10 is nog niet productie-afgerond.** Privacy/retentiegoedkeuring,
  hernieuwde fysiologische goedkeuring van BR-006, twee-echte-gebruikers-RLS en
  fysieke-devicevalidatie blijven open releasegates.
- **Fase 10.1 is nu lokaal geïmplementeerd.** Een persistente,
  server-authoritatieve swipe-draft ondersteunt accept/pass/undo/reset,
  recoverable exhaustion, een vast aantal en vaste disciplinecompositie,
  automatische of handmatige datumplaatsing en pending-only submission.
- **Fase 11 is geïmplementeerd binnen de expliciet goedgekeurde regels.** De
  onafhankelijke disciplinekeuzes, RPE-projectie, testplanning, bpm-observatie,
  profielhistorie en pending/confirm-boundaries zijn aanwezig.
- **Fase 11 voldoet niet aan alle eigen exitcriteria.** Automatische UC-05,
  Week-2-compleetheid, minimale steekproefregels en deterministische
  outlierbehandeling ontbreken bewust omdat de benodigde statistische en
  fysiologische besluiten niet zijn goedgekeurd. De code faalt hier veilig
  gesloten, maar de roadmapfase kan daarom niet als volledig afgerond worden
  aangemerkt.
- Na de gerichte correcties in deze review zijn de lokale applicatiecontroles
  groen: **390 backendtests**, Ruff check/format, strict mypy en Expo strict
  TypeScript.

Legenda: **Voldaan** = aantoonbaar aanwezig in code en lokale tests;
**Gedeeltelijk/gate** = veilig geïmplementeerd maar externe of nog niet
goedgekeurde verificatie ontbreekt; **Niet voldaan** = vereist gedrag ontbreekt.

## Beoordeling fase 10

| Roadmapvereiste | Status | Codebewijs en beoordeling |
|---|---|---|
| Beschikbaarheid bestaat uit lokale datums; hergebruik van de vorige week is expliciet | **Voldaan** | `WeeklyPlanProposalRequest` accepteert óf `available_dates` óf `reuse_previous_week` en weigert impliciet hergebruik (`backend/app/modules/planning/schemas.py`). De service zet de bron expliciet op `explicit`, `previous_week` of `checkin` (`backend/app/modules/planning/service.py`). |
| Planning en kalender schrijven een dag voor, geen trainingstijd | **Voldaan** | Publieke DTO's gebruiken `date`/`scheduled_date`. De oude interne timestamp blijft alleen een compatibiliteitsprojectie op lokale middag in `20260826085242_phase_10_date_only_planning.sql` en komt niet terug in de publieke planningcontracten. |
| 48 uur voor fiets/zwem betekent twee volledige lokale rustdatums; hardlopen blijft 72 verstreken uren | **Voldaan** | `backend/app/modules/physiology/anti_stack.py` gebruikt twee tussenliggende kalenderdatums voor de 48-uursdisciplines en UTC-verstreken tijd voor de 72-uursregel. `backend/tests/physiology/test_anti_stack.py` dekt woensdag-zaterdag en beide DST-overgangen. |
| Een pending voorstel kan alleen server-side en tegen de exacte revisie worden verwijderd/vervangen | **Voldaan** | De alternatives- en edit-routes zijn gebonden aan plan, workout en `expected_revision`. `PlanningService._pending_revision_edit_state`, `get_pending_workout_alternatives` en `edit_pending_workout` controleren pending state, stale state, selectie, beschikbaarheid, beperkingen en herplannen het volledige voorstel. |
| BR-004 blijft bij minder dan 80% op de beschikbare 42-dagenbaseline | **Voldaan** | De grens en baseline staan in `backend/app/modules/physiology/progression.py`; exacte 80%, onder 80% en ontbrekende baseline staan in `backend/tests/physiology/test_progression.py` en de plannerintegratie in `backend/tests/test_planning_domain.py`. |
| Vrije tekst wordt alleen een begrensde, inerte kandidaat met verduidelijkingsvragen | **Voldaan** | `backend/app/modules/coach/context.py` gebruikt een gesloten schema, geen tools en `store: false`. `backend/app/modules/checkins/service.py` valideert weekdatums en slaat de kandidaat niet op. De mobiele flow kopieert alleen gekozen velden en bevestigt de gestructureerde context afzonderlijk. |
| De LLM legt alleen een deterministisch genomen beslissing uit en kan niets muteren | **Voldaan** | `backend/app/modules/coach/weekly_plan.py` verstuurt alleen toegestane feiten, gebruikt strict Structured Outputs, `store: false`, geen tools en een deterministische fallback. De huidige officiële OpenAI-documentatie bevestigt dat het gebruikte model Responses en Structured Outputs ondersteunt en dat `store` en `text.format` geldige Responses-opties zijn. |
| Bevestiging is gebonden aan een exact voorstel | **Voldaan** | De bestaande immutable pending-revision/change-proposalflow blijft leidend; een edit expireert het vorige voorstel en maakt een nieuwe pending revisie. |
| Geen geplande of gerealiseerde TSS in API, UI, LLM-prompt of publieke logging | **Voldaan op codeniveau** | Publieke Pydantic-contracten bevatten geen loadvelden. `backend/tests/test_contracts.py` scant de volledige OpenAPI-structuur recursief. De coach-inputschema's kunnen deze velden niet representeren en mobiele types/schermen bevatten ze niet. Private berekeningen blijven in backendservice- en private-SQL-context. Productielogs zijn niet uitgevoerd en blijven onderdeel van operationele verificatie. |
| Privacy/retentie, fysiologiereview, twee-user-isolatie en fysieke devices | **Gedeeltelijk/gate** | `store: false` en dataminimalisatie zijn technisch aanwezig. De formele goedkeuringen en runtimecontroles zijn geen codefeit en staan terecht nog open in de roadmap. |

### Fase 10-correctie uit deze review

De deterministische Nederlandse fallback meldde dat “de tijden” de bevestigde
beschikbaarheid volgden. Dat botste met het expliciete dag-zonder-tijdcontract.
De tekst spreekt nu over “de trainingsdagen” en een regressietest voorkomt dat
dit opnieuw een voorgeschreven tijd suggereert.

## Beoordeling fase 10.1

De oorspronkelijke review vond hier terecht een zelfstandige productkloof. Die
verticale slice is op 2026-09-01 gebouwd; de bestaande editor voor een reeds
gegenereerd voorstel blijft als afzonderlijke revisieflow bestaan.

| Roadmapvereiste | Status | Codebewijs en beoordeling |
|---|---|---|
| Persistente server-authoritatieve swipe-draft, gebonden aan gebruiker, week, basisrevisie, context, beschikbaarheid en ruleset | **Voldaan op codeniveau** | `swipe_week_drafts`, contextfingerprints, forced RLS, owner-select en service-only invoker-RPC's staan in `20260901054333_phase_10_1_swipe_week_drafts.sql`; repository en service gebruiken deze state. |
| Vast doelaantal en compositie; pass telt niet, accept telt eenmaal | **Voldaan** | `planning/swipe.py` leidt de selectie uit decision history af. Service en databasetrigger bewaken het vaste target en de exacte disciplinecompositie; duplicate accept-retry is idempotent. |
| Elke rechtsswipe opnieuw valideren tegen alle deterministische voorwaarden | **Voldaan** | De service herbouwt en vergelijkt de contextfingerprint en zoekt alleen een kandidaat die samen met de accepted set nog door `build_weekly_plan` kan worden voltooid. |
| Passed card niet direct tonen; undo, reset en recoverable exhausted state | **Voldaan** | Passes worden uitgesloten tot reset, undo verwijdert exact de laatste beslissing en de response bevat `exhausted` plus herstelacties zonder loop. |
| Na selectie kiezen tussen automatische plaatsing en handmatige zevendaagse tijdlijn | **Voldaan** | De Expo-flow biedt automatische submit en een horizontale datumselector over uitsluitend bevestigde lokale datums, met radio/tikbediening naast het swipegebaar. |
| Volledige layout bij iedere plaatsing opnieuw server-side valideren | **Voldaan** | `place_swipe_workout` accepteert alleen een accepted template en beschikbare datum en voert na elke wijziging de volledige deterministische `build_weekly_plan` uit. |
| Alleen een immutable pending voorstel; expliciete activatie blijft nodig | **Voldaan** | `submit_swipe_draft` hergebruikt de bestaande pending revision/change-proposal-use-case. Selectie en plaatsing activeren niets; de aparte approvalroute blijft vereist. |
| Geen TSS in swipe-, kalender-, API- of mobiele state | **Voldaan op codeniveau** | Draftschema, API-DTO, mobiele types en pgTAP bevatten geen TSS; de bestaande recursieve OpenAPI-contracttest blijft groen. |

### Open releasegates voor fase 10.1

De implementatie is lokaal compleet, maar de nieuwe migratie en pgTAP-suite
zijn niet tegen een draaiende Supabase-stack uitgevoerd. Ook echte access
tokens en fysieke iOS/Android-gestures, herstarten en toegankelijkheidsbediening
zijn nog niet E2E gevalideerd. Er is niets naar hosted Supabase gepusht.

## Beoordeling fase 11

| Roadmapvereiste | Status | Codebewijs en beoordeling |
|---|---|---|
| Zwem, fiets en hardlopen kiezen onafhankelijk known/lab, veldtest, calibratie of RPE-only | **Voldaan** | `SetupRoute` en disciplinegebonden setups staan in `backend/app/modules/calibration/domain.py` en `service.py`. De profiel-UI bewaart en toont elke discipline afzonderlijk. |
| Calibration en RPE-only krijgen hetzelfde veilige RPE-trainingsgedrag | **Voldaan** | De planningcontext projecteert trainingen zonder actief profiel naar RPE-targets; calibration bewaart alleen aanvullende protocol/provenancecontext en fabriceert geen zone. De Phase 11-SQL-trigger verwijdert zonegetallen uit zonevrije snapshots en vult `rpe_target`. |
| Veldtest kan standalone of geïntegreerd, met exacte lokale datum en zonder uur | **Voldaan met gedocumenteerde fail-closed uitzondering** | `FieldTestSchedulingRequest`, calibrationrouter en -service ondersteunen beide routes. Run- en fietstests kunnen exact één same-discipline workout vervangen. Zwem-CSS blijft alleen standalone omdat geen goedgekeurde duur/private-loadregel bestaat. |
| RPE-workout heeft expected RPE; completion vereist actual RPE en gemiddelde hartslag in bpm | **Voldaan** | De RPE-projectie maakt segmenttargets. `ActivityRpeSubmission` en `ActivityService.submit_rpe` vereisen de bpm-observatie wanneer de toegewezen workout dat markeert. De repository schrijft via een service-only RPC. |
| Inclusieve ±10 bpm, alleen als observatie bij vertrouwde referentie | **Voldaan** | `assess_heart_rate_tolerance` in `backend/app/modules/physiology/zones.py` is pure deterministische Python, staat exact 10 bpm toe en retourneert geen zone-, drempel- of planbesluit. De tests dekken 89/90/91 en 109/110/111 bij referentie 100. |
| Actief, pending en immutable historie met provenance per discipline | **Voldaan** | `CalibrationService.zone_profile_state` bouwt disciplinegescheiden snapshots; `mobile/src/screens/ZoneProfileScreen.tsx` toont active, pending en prior versions met bron/status. Databaseconstraints en guarded critical writes beschermen lifecycle en provenance. |
| Calibrationzones tot na een complete Week-2-evaluatie verborgen; aparte bevestiging nodig | **Gedeeltelijk/gate, veilig gesloten** | De zichtbaarheidscode is correct fail-closed. `week_2_evaluation_completed` is bewust altijd `False` omdat geen goedgekeurde compleetheids-/sample-/outlierregels bestaan. Daardoor lekken of activeren geen numerieke calibrationzones, maar de positieve Week-2-route bestaat nog niet. |
| Later per discipline labwaarden of een veldtest starten via pending update | **Voldaan** | De profielpagina biedt beide routes; gemeten waarden behouden `measured_lab` provenance en blijven pending. Standalone testplanning maakt een apart `validation_test`-voorstel; geïntegreerde tests blijven aan het planvoorstel gebonden. |
| UC-05 pas na goedgekeurde statistische thresholds | **Niet geïmplementeerd, conform fail-closed besluit** | Er is geen automatische UC-05-evaluatie. Dit voorkomt verzonnen fysiologische logica, maar betekent ook dat dit roadmaponderdeel en de bijbehorende exitcriteria nog open zijn. |
| Minimum sample- en datakwaliteitstests; deterministisch outliergedrag | **Niet voldaan** | Protocolcompleetheid en invoerkwaliteit zijn getest, maar er is geen goedgekeurd minimum-sample- of outliermodel. De roadmap bevestigt dit zelf onder “Not implemented by design”. |
| Geen zonewijziging zonder pending voorstel en expliciete bevestiging | **Voldaan op codeniveau** | Zoneprofielen worden pending opgeslagen en approvalroutes gebruiken typed proposals/revisies. Testassignments zijn pending; planintegratie wordt door een database-trigger geweigerd als de exacte assignment ontbreekt. |
| RLS en least privilege op nieuwe testassignments/RPC's | **Statisch voldaan; runtimegate open** | De migration forceert RLS, gebruikt ownerpolicies, guarded writes en expliciete function/table grants. SECURITY DEFINER-functies voor private context controleren `service_role`; athlete-RPC's draaien als invoker. De lokale pgTAP-run kon niet verbinden en hosted verificatie is niet uitgevoerd. |
| TSS-vrije profiel- en testoppervlakken | **Voldaan op codeniveau** | Publieke calibration-, activity- en mobile-contracten geven geen geplande of gerealiseerde TSS terug. Private load blijft uitsluitend in server-side processingcontext. |

## Findings op prioriteit

### B-01 — Fase 10.1 ontbrak volledig — opgelost op codeniveau

De zelfstandige verticale slice bevat nu schema/RLS, pure domeintransities,
typed API, mobiele state machine, placementflow, pending-proposalintegratie en
gerichte tests. Alleen de hieronder genoemde database-, real-token- en
device-releasegates staan nog open.

### B-02 — Phase 11-exitcriteria voor Week 2/UC-05 zijn niet haalbaar zonder reviewbesluiten

Minimum sample, datakwaliteitsdrempels en outlierregels ontbreken. De huidige
hardcoded fail-closed status is de juiste veilige werking, maar “Phase 11
implemented” betekent hier niet “alle exitcriteria behaald”.

**Benodigde vervolgactie:** laat een bevoegde fysiologische/statistische review
de regels, evidenceversie, grensgevallen en rulesetversie vastleggen voordat
code wordt geschreven.

### H-01 — Phase 11-databasemigratie en pgTAP zijn nog niet runtime-gevalideerd

De officiële Supabase CLI 2.116.0 is tijdens deze review gebruikt. Uitvoering
van de drie relevante pgTAP-bestanden stopte read-only met
`ECONNREFUSED 127.0.0.1:54322`; er draait geen lokale Supabase/Postgres-stack en
Docker is niet beschikbaar. Er is niets naar hosted Supabase gepusht.

**Benodigde vervolgactie:** start een geïsoleerde lokale stack of gebruik de
goedgekeurde developmentomgeving, pas alleen de nog ontbrekende migration toe,
voer pgTAP/lint/advisors uit en herhaal daarna twee-real-token-isolatie.

### M-01 — Phase 11-pgTAP bewijst vooral structuur, niet ownergedrag

De 24 assertions controleren tabellen, kolomtype, forced RLS, triggers,
functies, privileges, constraints en seedvorm. Ze voeren geen echte athlete A /
athlete B create/read/update/approve-scenario's uit. De roadmap noemt
twee-real-user-isolatie terecht als gate.

**Aanbeveling:** voeg transactionele pgTAP-scenario's toe voor cross-user
create/read/update, stale standalone approval, integrated assignmentbinding en
direct-table-write rejection.

### M-02 — Known-values opslaan bestaat mobiel uit twee afzonderlijke requests

`ZoneProfileScreen.saveSetup` maakt eerst het pending calculated-zoneprofiel en
slaat daarna de discipline-setup op. Als de tweede request faalt, blijft een
geldig pending profiel bestaan terwijl de setup nog de oude route kan tonen.
Er ontstaat geen ongeautoriseerde actieve zone, maar de UI-state kan tijdelijk
inconsistent zijn.

**Aanbeveling:** voeg later een transactionele backend use-case/RPC toe die
setup en pending profiel atomair voorbereidt, of maak retry/reconciliation
expliciet. Dit is geen reden om de veilige pending boundary te omzeilen.

### M-03 — RPE-completion schrijft bpm vóór de activity-revisie

De gemiddelde hartslag wordt in een aparte service-only call opgeslagen en
daarna wordt de RPE-resultaatrevisie uitgevoerd. Bij een fout in de tweede stap
kan de observatie al bestaan. Dit verandert geen zones of plan en is veilig,
maar de use-case is niet atomair.

**Aanbeveling:** combineer beide writes in een begrensde transactionele
backend-RPC wanneer activity processing verder wordt gehard.

### L-01 — Dagcontract werd verkeerd verwoord in de fallback — opgelost

De fallbacktekst sprak over “tijden” terwijl alleen trainingsdatums worden
voorgeschreven. Dit is gewijzigd naar “trainingsdagen” en afgedekt met een
test.

### L-02 — Lokale kwaliteitsgate was door code-evolutie niet meer groen — opgelost

Strict mypy vond een verouderde in-memory calibrationrepository zonder de
Phase 11 integrated-testmethode en te smalle type-inferentie in een
configuratietest. Ruff vond twee lint- en vier formatverschillen. De mock,
types, imports en formattering zijn bijgewerkt; er is geen productiongedrag
verruimd.

## Uitgevoerde codewijzigingen

- `backend/app/modules/planning/swipe.py`, planningservice, repository, schema's
  en routes: persistente state machine, deterministische contextbinding,
  idempotente/stale-safe transities, placementvalidatie en pending submission.
- `supabase/migrations/20260901054333_phase_10_1_swipe_week_drafts.sql` en
  `supabase/tests/phase_10_1_swipe_week_drafts_test.sql`: TSS-vrije drafttabel,
  forced RLS, expliciete grants, guarded invoker-RPC's en owner/cross-user-tests.
- `mobile/src/api/client.ts`, `types.ts` en `PlanningScreen.tsx`: hervatbare
  one-card swipeflow, toegankelijke buttons, undo/reset/exhaustion en keuze
  tussen automatische en handmatige date-only plaatsing.
- `backend/tests/test_swipe_draft.py`, `test_planning.py` en
  `test_contracts.py`: tien-pass/drie-accept fixture, API-lifecycle,
  cross-owner/stale/idempotency/pending-only en OpenAPI-padcontrole.
- `backend/app/modules/coach/weekly_plan.py`: datumgerichte fallbacktekst en
  bestaande formatteringsafwijking gecorrigeerd.
- `backend/tests/test_weekly_plan_coach.py`: regressietest voor de
  dag-zonder-tijdformulering.
- `backend/tests/test_calibration.py`: in-memory repository weer volledig
  conform het actuele Phase 11-repositoryprotocol.
- `backend/tests/test_config.py`: expliciet breed testdata-type zodat strict
  mypy Pydantic-settings correct kan controleren.
- `backend/tests/test_workout_catalog.py`,
  `backend/tests/test_workout_catalog_repository.py` en
  `backend/tests/test_workout_catalog_seed_parity.py`: uitsluitend de door de
  repositoryformatter/linter vereiste mechanische opmaak/importvolgorde.

Er zijn geen ongoedgekeurde fysiologische regels bedacht, geen hosted
databasewijzigingen uitgevoerd en geen kritieke objecten buiten de bestaande
pending/confirmationflow aangepast.

## Reproduceerbare verificatie

Uitgevoerd op 2026-08-31:

```text
backend: python -m pytest
resultaat: 390 passed, 1 upstream Starlette/httpx-deprecationwarning

backend: python -m ruff check app tests
resultaat: All checks passed

backend: python -m ruff format --check app tests
resultaat: 115 files already formatted

backend: python -m mypy app tests
resultaat: Success: no issues found in 115 source files

mobile: npm run typecheck
resultaat: geslaagd (tsc --noEmit)

supabase: npx --yes supabase test db --local
resultaat: niet uitgevoerd; de lokale CLI-resolutie leverde zonder draaiende
stack geen resultaat en is veilig afgebroken; niets is naar hosted gepusht
```

De pgTAP-doelset bestaat uit:

- `supabase/tests/phase_10_ai_weekly_plan_explanation_test.sql`;
- `supabase/tests/phase_10_date_only_planning_test.sql`;
- `supabase/tests/phase_10_1_swipe_week_drafts_test.sql`;
- `supabase/tests/phase_11_discipline_zone_profiles_test.sql`.

## Actuele externe contractcontrole

- De [OpenAI gpt-5.6-luna modeldocumentatie](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
  vermeldt Responses en Structured Outputs als ondersteund. De
  [Responses create-reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
  ondersteunt de gebruikte `store: false`- en `text.format`-vorm.
- De [Supabase RLS-documentatie](https://supabase.com/docs/guides/database/postgres/row-level-security)
  vereist RLS plus passende policies/grants voor exposed tabellen. De Phase
  11-migration gebruikt forced RLS, ownerpolicies en expliciete grants. De
  [Supabase Data API-grantswijziging](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
  bevestigt de nieuwe least-privilege default voor Data API-exposure; de
  repositoryconfig laat auto-exposure uit en de migrations granten alleen de
  benodigde objecten.

## Go/no-go per beoordeelde fase

- **Fase 10 code:** GO.
- **Fase 10 productie:** NO-GO totdat privacy/retentie, named BR-006 review,
  twee-user-RLS en devicechecks zijn afgerond.
- **Fase 10.1 code:** GO.
- **Fase 10.1 productie:** migration, hosted pgTAP en ledger zijn afgerond;
  echte twee-user-tokenisolatie en fysieke iOS/Android-validatie blijven
  releasegates.
- **Fase 11 goedgekeurde subset:** conditionele GO na migration/pgTAP/lint/RLS
  en devicevalidatie.
- **Fase 11 volledige exitcriteria:** NO-GO totdat Week-2/UC-05
  sample- en outlierregels zijn goedgekeurd en geïmplementeerd.

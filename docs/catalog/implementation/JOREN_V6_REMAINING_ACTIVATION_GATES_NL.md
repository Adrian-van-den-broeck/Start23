# V6: resterende activatiepoorten

## Actuele opvolger: duurzame opslag — 7 november 2026

Branch `feat/joren-v6-persistence-hardening`, exacte basis
`4b3a76d9d764567e7bb438ad7493953faed6dea2`. De implementatie-SHA wordt na de
lokale commit in de opleverbijlage vastgelegd. Onderstaande oude sectie van
5 november beschrijft uitsluitend de eerdere automatische-selectielevering.
Deze opvolger vervangt haar uitspraken over de huidige opslagimplementatie.

De backend heeft nu een expliciet injecteerbare, inactieve Supabase-repository,
een verliesloze databasecataloguslezer en twee voorbereide voorwaartse migraties.
De bestaande eigenaars, voorstellen, revisies, fysieke workoutsnapshots,
privébelasting, bevestiging, afwijzing en occurrence-aware kaartconcepten worden
hergebruikt. Private extensies bewaren exacte bronrevisies, bevroren context,
logische voorkomens en onveranderlijke edit-ontvangstbewijzen. Het complete
weekresultaat blijft deterministische Python; de SQL-transactie controleert
onder dezelfde vergrendelingen de exacte revisie, context en bronidentiteiten.

**Geen database is benaderd. Beide migraties zijn niet uitgevoerd.**

| Poort | Actuele concrete grens |
| --- | --- |
| PostgreSQL/RLS/pgTAP | **NOT EXECUTED — DATABASE ENVIRONMENT UNAVAILABLE**. Geen lokale psql/PostgreSQL/Docker/Podman/Supabase CLI of geautoriseerde test-DSN beschikbaar. De volledige reproduceerbare SQL-fixtures en proces-/concurrentierunner staan klaar. Lokale mocks bewijzen geen PostgreSQL-beveiliging. |
| Numerieke opslag | Alle 77 officiële waarden, oorspronkelijke lexemen, rationale componenten en bronstructuren zijn exact voorbereid en lokaal rondgereisd. Onbegrensde numeric plus canonieke tekst voorkomt een gekozen vaste schaal. Werkelijke PostgreSQL-/JSON-rondreis en vergelijkingen moeten nog worden uitgevoerd. |
| Transacties en herstel | CAS, vergrendelvolgorde, onveranderlijke ontvangstbewijzen, rollback en nieuwe-procesherstel zijn geïmplementeerd/voorbereid. Werkelijke gelijktijdige SQL-swipes, bevestiging, afwijzing, verbindingsverlies en herstel moeten nog worden gemeten. |
| Geschatte zwemtijd | De referentieschatting blijft `ESTIMATED_FROM_APPROVED_REFERENCE_PACE`. Geen waargenomen of individueel voorgeschreven tijd. Operationeel vertrouwen op geschatte naleving blijft onder de bestaande reviewpoort. |
| Individuele lange duur | TR-BIKE-013 van 420 minuten blijft fail-closed zonder het bestaande bron-/atleet-/weekgebonden duurbewijs. Geen medische grens of ervaringsclassificatie toegevoegd; TSS-fit bewijst geen individuele duurgeschiktheid. |
| Planned/Realized V2 | `joren-v6-planned-if2-1` krijgt geen nieuwe Session-RPE-fallbackmapping. Historische V2, meetvoorrang en afwijzing van niet-ondersteunde provenance blijven behouden. |
| Toekomstige compatibiliteitsmapping | Vereist een afzonderlijk versiegebonden akkoord: exact toegestane planned-method/reference/source-revisies, welke uniforme segment-/disciplinegevallen in aanmerking komen, de rol van oorspronkelijke versus uitvoerings-RPE, de autoriteit van voorgeschreven/waargenomen duur, expliciete uitsluiting van ongedefinieerde afstand-/mixed-/rustgevallen, onveranderde meetvoorrang, exact numeriek beleid en een onafhankelijke regressiematrix. Geen extra formule of ruimere dispatch afleiden uit alleen de officiële planned-TSS-goedkeuring. |
| Mobile/device | Geen scherm/DTO/Android/iOS-releaseconfiguratie gewijzigd. Logische V6-voorkomens tegenover bestaande fysieke activity-/calendar-/registration-foreign keys vereisen expliciete consumentintegratie en devicebewijs vóór blootstelling. |
| Check-in/A5 | Historische A5 attachment/replay blijft ongewijzigd. V6 check-in-gedreven generatie weigert momenteel expliciet; er is geen alternatieve bevestigings- of attachmentconstructie bedacht. Eerst afzonderlijk de aansluiting toetsen vóór uitbreiding van deze preview. |
| Catalogus-/productievrijgave | Alle 77 revisies zijn INACTIVE. Geen actief logisch duplicaat, historische retirement, productieflag of startup-registratie. Exacte catalogus-/methode-/plannerrelease, migratie/rollback en activering vereisen afzonderlijke toestemming. |
| Verantwoordelijke review | Productgoedkeuring van de officiële methode is behouden; geen nieuwe wetenschappelijke aannames. Benoemde verantwoordelijke review en de bestaande onafhankelijke operationele/fysiologische poorten blijven afzonderlijk. |

Lokale softwarecontrole: **2.583 backendtests geslaagd**, Ruff lint/format en
strict mypy geslaagd. De uiteindelijke 40-scenarioregressie, 26 historische
referentieresultaten, bronhashes en exacte commando-uitkomsten worden vastgelegd
in `persistence/verification.json`. Geen computationele deadline of historische
verwachting is versoepeld. Dit sluit geen externe poort.

Zie [architectuur](JOREN_V6_PERSISTENCE_ARCHITECTURE.md),
[swipeverificatie](JOREN_V6_TRANSACTIONAL_SWIPE_VERIFICATION.md),
[database-resultaten](JOREN_V6_POSTGRES_RLS_TEST_RESULTS.md) en
[rollbackplan](JOREN_V6_PERSISTENCE_ROLLBACK_PLAN.md).

Productie/staging en de A5/A6-releaseworktree zijn onaangeraakt. Geen push,
merge, deployment, productie-migratie, activering of volgende releasefase.

**WOMBO V6 PERSISTENCE IMPLEMENTED — DATABASE VERIFICATION PENDING**

## Historische status: automatische selectie — 5 november 2026

5 november 2026, Europe/Amsterdam. Softwareversie
`joren-v6-automatic-selection-1`; besluit `joren-v6-official-tss-acceptance-1`.

## Nu geaccepteerd en geïmplementeerd

De eigenaar accepteert `joren-v6-planned-if2-1` inclusief de precieze IF²-invoer,
zwemreferenties, eenmalige sportfactor, exacte rationale tussenrekening en
50-cijferige HALF_EVEN-eindwaarde. De vroegere P01-keuze is hiermee gesloten.
Het oorspronkelijke voorstel en de eerdere onbesliste status blijven historisch
intact; de nieuwe goedkeuringsnotitie is een opvolger.

De backend kiest nu automatisch echte trainingen uit de 77 bronrevisies en maakt
een concreet pending voorstel. De bestaande kaartselectie en pending-workout-
alternatieven werken lokaal met volledige weekvalidatie, bewaren behouden
voorkomens en datums, en gebruiken dezelfde aparte atleetbevestiging. Deelweken,
geen HIGH-ondergrens, een harde weekgrens en de zachte 50/30/20-verdeling zijn
werkend softwaregedrag. Er zijn geen ervaringscategorieën toegevoegd.

L1 is de door de eigenaar toegestane engineeringkeuze, met geselecteerde totale
officiële belasting als noemer. Het is geen onafhankelijk door Joren ondertekend
wiskundig oordeel. De versiegebonden scope is maximaal één nieuwe training per
doelsport; bestaande/herhaalde voorkomens kunnen als complete selectie behouden
en gevalideerd worden. Buiten de eindige zoekgrens volgt een eerlijke incomplete-
zoekstatus, geen willekeurige aanbeveling.

## Nog nodig voor activatie

| Poort | Concrete grens |
| --- | --- |
| Operationele geschatte zwemtijd | Lokale preview gebruikt expliciet ESTIMATED referentietijd. Goedkeuring van die controle als operationele veiligheidspoort, inclusief onzekerheid/sensitiviteit en ontbrekende tijden, blijft nodig. Niets wordt VERIFIED of geobserveerd genoemd |
| Individuele lange duur | BIKE-013 van 420 minuten blijft automatisch uitgesloten zonder bronrevisie-/atleet-/weekgebonden duurbewijs. TSS-fit is geen fysieke gereedheid; geen verzonnen duurgrens of ervaringsklasse |
| Duurzame V6-opslag | De bestaande Supabase-writer ondersteunt nog geen volledige bevroren V6-bron/methode/rest-snapshots plus pending-revisie-CAS en edit-retrylookup. De adapter weigert zo'n writer. Het lokale in-memory contract is getest; dit is geen uitgevoerde SQL/C3/C8-uitrol |
| PostgreSQL/RLS/pgTAP | Externe transactietests, grants/RLS, twee echte atleten, snapshotretentie, idempotentie en migratie-/rollbackverificatie blijven open. Geen database is benaderd; geen migratie gemaakt of uitgevoerd |
| Planned/Realized V2 | De nieuwe geplande methode is nog niet toegelaten in de bestaande Session-RPE-fallback. Die blijft expliciet fail-closed; meetvoorrang en historische methoden blijven intact. Een afzonderlijk compatibiliteitsbesluit is nodig |
| Catalogusvrijgave | Exacte catalogus-/methode-/plannerrelease, actieve opvolgingsmapping, rollback en eventueel retirement apart goedkeuren. Alle nieuwe templates zijn INACTIVE; niets is automatisch uitgefaseerd |
| Verantwoordelijke review | De eigenaar geeft productgoedkeuring. Een benoemde verantwoordelijke fysiologische reviewer met identificeerbaar extern record blijft een afzonderlijke vrijgavepoort; geen handtekening of referentie is verzonnen |
| Mobile/device/A5/A6 | Bestaande DTO's en routes zijn behouden en via HTTP getest. Device-/mobiele vrijgave, weergave van nieuwe bronfocus versus bestaande uitvoering-RPE-guidance en huidige A5/A6-poorten blijven afzonderlijk te verifiëren. Geen mobile- of A5/A6-wijziging |

## Wat bewust niet is gedaan

Geen productieverbinding, push, merge, deployment, publicatie, migratie of
catalogusactivatie. De historische planner blijft de standaard. Geen herberekening
van historische TSS, nieuwe Realized V2-dispatch, wijziging van bestaande IDs of
stilzwijgende wijziging van oudere bronbestanden. Geen automatische C6–C8-vervolgstap.

De lokale eindresultaten, exacte SHAs en regressiebewijzen staan in het
[implementatierapport](JOREN_V6_AUTOMATIC_SELECTION_IMPLEMENTATION.md) en
`automatic-selection/verification.json`. Lokaal groen sluit geen externe poort.

WOMBO V6 AUTOMATIC SELECTION + SWIPE IMPLEMENTED — ACTIVATION GATES REMAIN

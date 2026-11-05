# V6: resterende activatiepoorten

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

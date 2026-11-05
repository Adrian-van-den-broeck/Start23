# WOMBO V6: resterende integratie- en releasepoorten

5 november 2026, Europe/Amsterdam. Versie `joren-v6-phase-tss-owner-intake-1`.
Deze levering is lokaal en inactief. Productie en A5/A6 blijven buiten scope.

## Besluiten die vaststaan

Jorens 77 nieuwe fasecellen zijn de bronwaarheid voor deze nieuwe revisie.
IF-waarden en zwemreferenties zijn bevestigd. De eigenaar meldt Jorens akkoord
op de eerder voorgestelde officiële TSS-aanpak; dat akkoord is vastgelegd en
wordt niet genegeerd vanwege oude rapporten.

De eigenaar kiest belastingcompatibiliteit op basis van geautoriseerd weekbudget
en officiële geplande TSS, zonder beginner/intermediate/advanced-indeling.
Deelweken zijn toegestaan, er is geen HIGH-ondergrens, maximaal 20% HIGH actieve
tijd geldt per sport per lokale week. Het weekbudget is een harde bovengrens;
50/30/20 is een zachte streefverdeling. Deze besluiten staan niet opnieuw ter discussie.

## Concrete open poorten

| Poort | Wat precies ontbreekt / gevolg |
| --- | --- |
| P01: numerieke autoriteit | De exacte binding van het gemelde akkoord aan bronweergave versus exact herberekende waarde en de opslag-/vergelijkingsconventie. De eigenaar antwoordde “Doe een voorstel zonder implenteren”. Het concrete voorstel staat in de TSS-notitie en is niet geïmplementeerd; officiële waarden blijven null |
| Selectie/rangschikking | Goedkeuring van de exacte 50/30/20-maat en resterende ties, inclusief concurrerende deelplannen. L1 is alleen expliciet gelabelde reviewdiagnostiek; er wordt geen winnaar gepubliceerd |
| Individuele duur/afstand | Geautoriseerd capaciteit-/geschiktheidsbewijs in concrete atleet/weekcontext, vooral voor BIKE-013 van zeven uur. TSS-fit en Taper-bronlabel bewijzen geen fysieke gereedheid; geen verzonnen duurgrens of ervaringsklasse |
| Bestaande waarborgen koppelen | Productie-adapter voor bestaande capability-, blessure-, herstel-, progressie-, herhalings- en planningsuitkomsten, gebonden aan exact atleet/revisie/week. De review kent uitsluitend expliciete bewijzen; testaannames zijn geen echte toestemming |
| Geschatte zwemtijd | Operationele acceptatie van de referentieschatting als veiligheidspoort, inclusief ontbrekende/onzekere tijd. Geschatte compliance blijft geschat; oorspronkelijke voorgeschreven en werkelijke tijden worden niet ingevuld |
| C3 duurzaamheid | Review van exact payload-/snapshotcontract met typed muurrust, bron-RPE/focus, aparte blokguidance, methode/bronversie en activatie-/rollbackrelaties; geen actieve vervangingsmapping of retirement geautoriseerd |
| Planned/Realized V2 | Expliciete methodecompatibiliteit voordat nieuwe P in nieuwe werkelijke-belastingsberekeningen mag worden gebruikt. Geen referentietijd als geobserveerde tijd; geen nieuwe mixed-session matrixbevoegdheid |
| PostgreSQL/RLS/pgTAP | Externe SQL-, grants-, RLS-, twee-echte-atleten-, snapshot- en migratietests blijven uitgesteld en onbewezen. Er is hier geen schemawijziging of migratie uitgevoerd |
| Wetenschappelijke/releasebeoordeling | Benoemde verantwoordelijke reviewer, identificeerbaar extern record en apart release-/activatiebesluit voor exacte catalogus/methode/policy-versies |
| A5/A6/mobile | Bestaande database/device/mobile/Android/iOS- en A5/A6-releasepoorten blijven afzonderlijk open waar eerder vereist; geen wijziging of verificatieclaim in deze backendlevering |

De acht precieze M-cel-exportverschillen staan in de broninname. Ze hebben gelijke
weergaven maar verschillende exacte lexemen; beide blijven behouden. Dit is geen
goedkeuring om de nieuwe afgeronde bronwaarde als officiële TSS te kiezen.

## Grens van deze levering

C3 is voorbereid als immutable inactief bron-/templaterevisie-artifact met 77
stabiele logische keys en nieuwe versie-IDs. C4 biedt een uitgeschakelde private
weekreview met hard budget, bronfasen, volledige weekinvoer, tijdmaxima en expliciete
veiligheidsbewijzen. C5 hergebruikt dezelfde versiegebonden schatter en houdt
gepland/geschat/geobserveerd gescheiden. Dit is geen voltooide actieve planner-
of database-integratie. Automatische selectie blijft geblokkeerd.

Alle lokale resultaten en regressiebewijzen staan in het
[integratierapport](JOREN_V6_C3_C5_INTEGRATION_REPORT.md). Lokaal groen sluit geen
externe poort. Geen push, merge, deployment, publicatie, migratie of activatie;
geen productieverbinding of wijziging van bestaande atleetplannen; geen C6–C8.

WOMBO V6 PHASE + TSS INTEGRATION PARTIAL — SPECIFIC APPROVAL GAPS DOCUMENTED

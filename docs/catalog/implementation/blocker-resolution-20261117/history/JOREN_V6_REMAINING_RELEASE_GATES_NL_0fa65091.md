# WOMBO V6: migratiegereedheid en resterende besluiten

16 november 2026, Europe/Amsterdam. Branch `release/joren-v6-hosted-migration-readiness`, vanaf exact **289280a5bddf6f0cc65eca1f562561e7df9a603c**. De definitieve commit staat in Git en het opleverbericht; deze tekst claimt geen zelfrefererende commit-SHA.

**WOMBO V6 PRODUCTION MIGRATION READINESS PARTIAL — EXACT RISKS DOCUMENTED**

## Bestuurlijke samenvatting

De hosted database bevat opnieuw bevestigd **47 van 63 geaccepteerde migraties**: precies 16 ontbreken, zonder extra of conflicterende versienummers. Alle bestandschecksums staan in de [migratieanalyse](JOREN_V6_HOSTED_MIGRATION_GAP_ANALYSIS.md). De huidige ledger en Auth-/schemametadata zijn voor en na deze beoordeling gelijk. Er zijn geen productiemigraties, deployments, activaties, roltoekenningen of echte-atleetmutaties uitgevoerd.

De zestien wijzigingen zijn concreet:

| # | Wijziging |
| --- | --- |
| 1 | A5: atomair aanmaken/koppelen en exact terughalen van een bestaand check-invoorstel |
| 2 | Private, prospectieve Realized V2-invoer en berekeningsprovenance |
| 3 | Expliciete registratie overgeslagen/onbekend, wekelijkse evidence en activiteitbewaking |
| 4 | Bevroren planevidence en controle bij aparte bevestiging |
| 5 | Nieuw Session-RPE-versieveld in de gedeelde activiteitprojectie |
| 6 | Inactieve V6-opslag, afgeschermde catalogus, snapshots, receipts en versiegebonden constraints |
| 7 | Exact 77 INACTIVE bron-/catalogusrevisies met officiële waarden; geen historische loadimport |
| 8 | Correcte V6-segmenten na de historische insert-trigger |
| 9 | Correctie van JSON-operatorvolgorde bij bewerken |
| 10 | Ownercontrole in de interne V2-goedkeuringsketen; directe history-RPC's blijven service-only |
| 11 | Bestaande zakelijke conflictsituaties terug naar niet automatisch herhaalbare PT409 |
| 12 | Bescherming tegen zelfgemaakte V6-revisies en wijzigingen aan bevroren snapshots |
| 13 | Mobiele logische/fysieke workoutidentiteit en leesprojecties |
| 14 | V6 binnen A5-koppeling/replay, verplaatsing en behoud van check-inbevestigingsprovenance |
| 15 | Append-only lidmaatschappen houden originele voltooide activiteit-/registratie-evidence in opvolgrevisies |
| 16 | Optionele frequentievoorkeuren, afzonderlijke bevoegdheid, intrekking/herbeoordeling en bewaakte swipe; niemand wordt aangesteld |

**Bestaande gebruikers kunnen worden geraakt terwijl V6 uitstaat.** Vooral activiteitprojectie, check-inherbevestiging, goedkeurings- en activiteittriggers worden gedeeld. Het historische strikte backendmodel weigert het nieuwe `session_rpe_version` met `extra_forbidden`; de publieke productiecontracten kennen dit veld nog niet. De exacte gedeployde commit en mobiele build zijn niet vastgesteld: Railway wijst de bestaande sessie af. De twee geconfigureerde backend-URL's zijn gezond, maar de lokale routing verschilt en één noemt zijn omgeving `local`. Gezondheid is geen compatibiliteitsbewijs.

**Alle zestien ongewijzigd veilig installeren is nu niet aangetoond.** De catalogus blijft technisch inactief en de historische planner blijft standaard, maar de keten verleent ook **13 nieuwe authenticated EXECUTE-signatures**. Dit voldoet niet aan de letterlijke eis dat gewone clients geen nieuwe uitvoerrechten krijgen. Owner-scoped lezen/voorkeuren is geen generatiebevoegdheid; toch wordt geen uitzondering aangenomen. De voorbereide uitvoerbundels blokkeren daarom commit op deze rechtenwijziging. Een algemene revoke van de private membership-helper zou historische leesfuncties breken.

**Herstel is nog niet productiegereed.** De echte backup-API geeft een lege backuplijst, lege recoverymetadata, `pitr_enabled=false` en `walg_enabled=true`. Er is geen beschikbaar herstelpunt of uitgevoerde hosted restoreproef aangetoond. Wel zijn lokaal een volledige G2-transactierollback en een uitgebreider forward-disablepad getest, met gelijkblijvende data. Dat vervangt geen backuprestore. [Herstelrapport](JOREN_V6_BACKUP_AND_RECOVERY_READINESS.md).

Aanbevolen volgorde, pas na het sluiten van de harde poorten: **G1 = 1; G2 = 2–12 atomair; G3 = 13–16 atomair**. G2 mag geen tussenstatus blootstellen waarin V2-goedkeuring/conflictclassificatie of V6-custody onvolledig is. G3 sluit lifecycle, fysieke evidence en frequentiebevoegdheid samen. Zie het [voorwaardelijke uitvoerplan](JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN.md); het is niet uitgevoerd en nog niet goedgekeurd.

## Nieuw geverifieerd lokaal bewijs

- **2.891 backendtests** geslaagd; één bestaande Starlette/httpx-deprecatiewaarschuwing. **935 mobiele tests in 89 suites** geslaagd. Ruff/format, strict mypy en strict TypeScript/unused-controles slagen; exacte resultaten staan in het [verificatieregister](migration-readiness-20261116/verification.json).
- Zowel de schone geaccepteerde 47-migratiegrens als een aparte grens met de twee werkelijk afwijkende hosted functiedefinities zijn met exact dezelfde zestien bestanden bijgewerkt: **722/722 pgTAP-asserties in 37 suites**, steeds met de expliciete A5-overlay. Alle 51 bestaande tabellen behouden na iedere groep dezelfde rijhashes, inclusief historische bron-, plan-, activiteit- en private evidence. Zes historische/A5-smokes slagen per groep.
- De **ongewijzigde A5-fixture faalt nog steeds**: acht assertions geslaagd, één gefaald, daarna abort vóór twintig resterende assertions. De onboarding-/fingerprintoverlay slaagt 29/29; dit is geen PASS van het origineel. De twee huidige final-schema-tests die vóór installatie niet uitvoerbaar zijn, blijven afzonderlijk gerapporteerd.
- **40/40 historische uitkomsten**, **26/26 geaccepteerde referentieresultaten** en volledige uitkomsthashes blijven gelijk. De bekende `current:build_4` achtseconden-timeout blijft bestaan. De exacte zoek-oracle blijft gelijk voor 15 contexten en **20.061.679** combinaties. Geen fysiologische regel of resourcegrens is verruimd.
- Echte portable SQL-lifecycle: negen A5/lifecyclegroepen, elf evidence-reschedulinggroepen en negen frequentiebeleidscontroles slagen, met procesherstart/nieuwe verbindingen. Dit gebruikt synthetische SQL-claims, **geen nieuwe GoTrue-/gateway- of apparaattest**.
- Het uitgebreidere lokale uitschakelpad bewaart alle 64 eindtabellen en bevestigde reads. Het eerdere vier-RPC-fixture dekt de latere frequentiewrappers en gedeelde A5-dispatch onvoldoende af. Ook de nieuwe fixture is uitsluitend lokaal; productieherstel vereist een afzonderlijk goedgekeurde forward migration.

## Exacte eigenaarbesluiten en open releasepoorten

| Besluit / poort | Nodige concrete sluiting |
| --- | --- |
| Backup en herstel | Werkelijk beschikbaar checkpoint; toegestane hosted herstelomgeving; geslaagde restoreproef; gemeten uitval/dataverlies; operator, kosten en retentie |
| Activiteitcompatibiliteit | Werkelijke deployed SHA vaststellen; compatibele backendbrug of nieuwe versiegebonden DB-projectie kiezen, afzonderlijk reviewen en repeteren vóór G2 |
| Geen nieuwe clientuitvoerrechten | Eis handhaven met een geteste forward ACL-/helperarchitectuur, of expliciet afzonderlijk de exacte owner-scoped uitzonderingen goedkeuren. Geen impliciete uitzondering of brede revoke |
| Bestaande drift | Twee functiedefinities, vier catalogus-service-ACL's en hosted default privileges beoordelen; geen ledgerreparatie. De downstream zone-trigger behoudt de relevante checks |
| Productiedoel en artifacts | Werkelijke service/omgeving/URL, backendcommit, Android/iOS-builds, flags, providers en geplande jobs vaststellen; Railway-sessie is nu ontoereikend |
| Hosted verificatie | Afzonderlijke officiële, geïsoleerde Supabase-omgeving met exact dezelfde keten en echte A/B-sessies; actuele ACL's/defaults en runtimepariteit aantonen |
| Verificatieadapter | Afzonderlijk de begrensde architectuur/code goedkeuren; bestaande local-only helper niet omzeilen. [Exact testplan](JOREN_V6_HOSTED_POST_MIGRATION_VERIFICATION_PLAN.md) |
| A5-foutnormalisatie | Alleen lokaal aangetoond; deployed foutgedrag/artefact afzonderlijk verifiëren. Geen migratiebewijs van deployment |
| Oorspronkelijke A5-fixture | Bestaande testcorrectie door A5-eigenaar accepteren; overlay-PASS gescheiden houden |
| Echte reviewer/operator | Benoemde bevoegde persoon, aanwijzings-/reviewreferentie en gecontroleerde databasebevoegdheid; niemand automatisch aanstellen |
| Individuele frequentiemaxima | Echt besluit per atleet, sport, lokale week en tijdzone; geen afleiding uit voorkeur, uren of belasting; geen synthetische REAL-autorisatie |
| Positieve multisessie | Blijft geblokkeerd zonder echte aanwijzing en individueel maximum; test-executor krijgt nooit productielidmaatschap |
| Wetenschappelijke verantwoordelijkheid | Onafhankelijke bevoegde reviewer met identificeerbaar record voor exacte bron-, fysiologie-, Planned IF²-, Realized V2- en beleidsversies. Productfrequentieakkoord vervangt dit niet |
| Zwemtijd / uitzonderlijke duur | Operationele acceptatie van bestaande estimates en vereist individueel bewijs; geen verzonnen algemene grens |
| Prestaties / hardware | Representatieve goedgekeurde contexten op doelhardware; bestaande grenzen en eerlijke `v6_search_incomplete` behouden |
| Security advisors / webhooks | Bestaande drie INFO en negen WARN inhoudelijk beoordelen; projectwebhookinventaris 403, Railway-jobs onbekend; geen ongeautoriseerde herstelwijziging |
| Sessierevocation | Bestaande uitgegeven JWT kan tot expiry geaccepteerd blijven; onmiddellijke universele intrekking is geen bewezen huidig contract |
| Echte apparaten | Android/iOS volledige flow, accountwissel, herstel en fysieke identiteit; Jest is geen apparaattest |
| Uitvoering / activatie | Pas na toepasselijke poorten afzonderlijk eigenaarakkoord voor migratievenster en operator. Catalogusactivatie, deployment en echte-atleetrelease blijven afzonderlijk |

De [vorige releasevoorwaarden](migration-readiness-20261116/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_289280a5.md) zijn ongewijzigd bewaard. Alle 77 geaccepteerde bronnen blijven INACTIVE; hosted zijn ze nog niet geïnstalleerd. De historische default, bestaande bevestigde plannen en officiële berekeningsversies zijn niet gewijzigd. Er is niet gepusht of gedeployed en geen beschermde worktree is aangepast.

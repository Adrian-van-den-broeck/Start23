# V6: resterende releasevoorwaarden na hosted Auth-verificatie

14 november 2026, Europe/Amsterdam. Branch `verify/joren-v6-hosted-supabase-auth`, vanaf exact `980e015b5e6546e1259c8585c3ca42c271add9f5`.

**WOMBO HOSTED AUTHENTICATION VERIFIED — V6 INTEGRATION GATES REMAIN**

Twee echte synthetische GoTrue-accounts zijn via de bestaande hosted Supabase-gateway getest. Password-login, ES256/JWKS, opaque mapping, refresh, API-keygrenzen, logout en daadwerkelijke tokenvervalcontrole zijn afzonderlijk vastgelegd in het [Auth-rapport](JOREN_V6_HOSTED_GOTRUE_GATEWAY_RESULTS.md) en [verificatieregister](hosted-auth-20261114/verification.json). De eigenaar heeft het aanvankelijk gepauzeerde project zelf hervat. De verifier heeft geen project, schema, globale bevoegdheden, Auth-instellingen of productiedependency aangepast.

De database bevat **47 van 63 migraties**. Zestien ontbreken, waaronder A5-proposalherstel en de V6-keten. Daarom zijn **nul V6-specifieke lifecyclecontroles geslaagd**: zij zijn geblokkeerd. Alle 77 geaccepteerde V6-catalogusrevisies blijven lokaal INACTIVE; de betreffende hosted tabellen ontbreken nog.

## Nieuw bewijs

- **2.891 backendtests** geslaagd, een bestaande deprecatiewaarschuwing; **935 mobiele tests in 89 suites** geslaagd. Ruff/formatting, strict mypy en strict TypeScript/unused-checks slagen; exacte opdrachten/resultaten staan in het register.
- **Alle 40 historische gevallen** hebben gelijke invoerfingerprints, uitkomsten en onafhankelijke controles. **Alle 26 geaccepteerde referentieresultaten** blijven gelijk. `current:build_4` behoudt de oorspronkelijke achtseconden-timeout; numerieke methoden en resourcegrenzen zijn niet verruimd.
- Beide echte accounts doorliepen normale onboarding, check-incontext, historische planvoorstellen en aparte bevestiging, kalender, synthetische activiteit met exacte retry, verplaatsing en herstel na opnieuw inloggen. A doorliep tevens historische swipe-indiening. Dit is geen V6-lifecyclebewijs.
- De uitgevoerde wederzijdse historische plan-/workout-/activiteit-/receipt-aanvallen zijn geweigerd. Private schema's en service-/Auth-adminfuncties zijn ontoegankelijk voor de geteste athlete-credentials. Niet aanwezige frequentie-/V6-contracten blijven open.
- De twee accounts zijn via de ondersteunde Auth-route verwijderd. **61 geinspecteerde tabellen: nul resterende testrecords**. Exacte private manifesten en beperkte queries zijn beschreven in het [opruimrapport](JOREN_V6_HOSTED_TEST_DATA_CLEANUP.md).
- De lokale A5-fix behoudt 422/`validation_failed` en voegt alleen `details.planning_code=v6_search_incomplete` toe. Replay, afwijzing zonder automatische retry en gegevensafscherming blijven getest. De fix is niet gedeployed; beschermde A5/A6-worktrees zijn niet gewijzigd.

Het [vorige releaseregister](hosted-auth-20261114/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_980e015.md) is als exacte geaccepteerde Git-blob bewaard. De **722 pgTAP-asserties in 37 suites** blijven historisch lokaal bewijs met de expliciete A5-overlay; de oorspronkelijke A5-fixture houdt haar bekende fout. Geen disposable databaseproef is tegen productie uitgevoerd.

## Open poorten

| Poort | Nog benodigd |
| --- | --- |
| Hosted migratie- en runtimepariteit | Afzonderlijk goedgekeurde geisoleerde officiele Supabase-omgeving, alle 63 migraties, volledige SQL/RLS-suite en echte V6 Auth/gateway-lifecycle. De [migratieanalyse](JOREN_V6_HOSTED_MIGRATION_READINESS.md) en het [niet-uitgevoerde voorstel](JOREN_V6_HOSTED_MIGRATION_DEPLOYMENT_PLAN.md) geven afhankelijkheden, kosten en herstelrisico's. |
| V6-accountisolatie | Beide richtingen voor voorkeuren, frequentiemachtiging, private evidence, fysieke occurrences, immutable receipts en frozen context. Geen test-only productiebevoegdheid gebruiken. |
| V6-lifecycle | Werkelijke A5-generatie, swipe, pending indiening, aparte bevestiging, kalender, activiteit, verplaatsing, herstel, retry en stale-versies met echte sessies. Geen V6-activatie om verificatie af te dwingen. |
| Historische fysieke identiteit | Activiteit bleef ongewijzigd, maar historische verplaatsing vervangt workout-ID's; de oude voltooide occurrence staat niet in de nieuwe actieve revisie. Dit is geen V6-identiteitsgarantie. |
| Sessierevocation | Refresh is ingetrokken; een reeds uitgegeven JWT bleef bij de Data API geldig tot expiry. Directe toegangsinvalidatie vergt een expliciet operationeel contract; de backend controleert geen sessiestore per verzoek. |
| Historische A5-SQL-fixture | Bestaande onboarding-/fingerprintcorrectie afzonderlijk door de A5-eigenaar laten accepteren. Overlay-PASS is geen ongewijzigde-suite-PASS. |
| Werkelijke reviewer/operator | Echte benoemde beoordelaar/operator met gecontroleerde bevoegdheids- en reviewreferenties. Niemand is aangemaakt of benoemd. |
| Individuele numerieke maxima | Werkelijk besluit per atleet, sport, lokale week en tijdzone op basis van de geaccepteerde onderbouwing. Geen afleiding uit voorkeur, uren, belasting of beschikbaarheid. |
| Positieve multisessie-autorisatie | Alleen met die echte bevoegdheid en een werkelijk individueel maximum; tot die tijd blijft de bestaande veilige standaard een sessie per sport gelden. |
| Wetenschappelijke acceptatie | Onafhankelijke bevoegde reviewer voor exacte bron-, methode- en beleidsversies; bestaande vijf frequentiebesluiten zijn geen persoonlijke machtiging. |
| Zwemtijd en uitzonderlijke duur | Operationele acceptatie van bestaande zwem-estimates en individueel duurbewijs waar vereist, zonder verzonnen algemene grens. |
| Planned versus Realized | Afzonderlijke acceptatie van Planned IF-squared en Realized V2-fallback, prioriteit voor meetgegevens en blokkering van niet-ondersteunde combinaties. |
| Prestaties en rekenbereik | Representatieve goedgekeurde contexten en doelhardware; de bekende 8/8/8-nodegrens blijft zichtbaar, zonder algemene voltooiingsgarantie. |
| Security advisors | Drie INFO en negen WARN laten beoordelen zonder ongeautoriseerde productieconfiguratie of grants te wijzigen. |
| Echte apparaten | Android/iOS: onboarding, voorkeur, check-in, swipe, review, bevestiging, activiteit, verplaatsing, herstel en accountwisseling. Jest vervangt geen apparaattest. |
| Deployment en catalogusactivatie | Afzonderlijke expliciete eigenaarstoestemming na alle toepasselijke poorten. Geen push, hosted migratie, deployment of activatie uitgevoerd. |

De exacte deterministische methoden, bestaande node-/resourcegrenzen en veilige frequentiestandaard blijven behouden. V6 blijft buiten de productiedependency.

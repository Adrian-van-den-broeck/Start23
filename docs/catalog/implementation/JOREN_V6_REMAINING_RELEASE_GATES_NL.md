# V6: resterende releasevoorwaarden na Auth-omgevingscontrole

14 november 2026, Europe/Amsterdam. Geisoleerde branch
`verify/joren-v6-real-supabase-auth`, vanaf exact
`dbeb9596f42f0504e428afbf5eddc75eaa7d20da`.

**WOMBO V6 AUTHENTICATION VERIFICATION BLOCKED ? EXACT ENVIRONMENT REQUIREMENTS DOCUMENTED**

Er zijn nul echte GoTrue-accounts/sessies en nul Supabase-gatewayverzoeken
uitgevoerd. Docker/Podman en een WSL-distributie ontbreken; een ondersteunde
complete lokale stack is niet beschikbaar. De beschikbare portable Windows
PostgreSQL en PostgREST sluiten deze poort niet. De
[omgevingsvereisten en herhaalstappen](JOREN_V6_REAL_AUTH_ENVIRONMENT.md) benoemen
het benodigde, door de eigenaar toegestane wegwerp-Linux-/containermilieu,
GoTrue ES256/JWKS, gateway, moderne API-sleutels en volledige Supabase-schema's.
Er is geen systeemsoftware geinstalleerd of hosted alternatief gebruikt.

Het [vorige releaseregister](real-auth-20261114/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_dbeb959.md)
is bytegelijk bewaard. De vijf eerder geaccepteerde frequentiebesluiten blijven
van kracht; zij vormen geen reviewerbenoeming of individuele numerieke machtiging.

## Nieuw uitgevoerd, met beperkte bewijskracht

- Backend: **2.876 tests geslaagd**, een bestaande deprecatiewaarschuwing.
- Mobiel: **929 tests in 88 suites geslaagd**; strict TypeScript en unused-checks slagen.
- Ruff/formatting en strict mypy slagen.
- Nieuwe eigen lokale PostgreSQL 17.11-cluster: **63 ongewijzigde migraties**;
  **722 pgTAP-asserties in 37 suites** met volledige TAP-plannen en de bestaande,
  expliciete A5-fixtureoverlay. De originele A5-fixture is afzonderlijk FAIL:
  8 geslaagd, 1 mislukt, 20 niet uitgevoerd na afbreken. Geen constraint versoepeld.
- Reguliere frequentie-/concurrentieproef: **9 SQL/ASGI-groepen slagen**, plus
  herstel in een nieuw Python-proces; geen echte Auth-identiteit of gateway.
- **Alle 40 historische gevallen** hebben gelijke invoerfingerprints, uitkomsten
  en onafhankelijke controles. **Alle 26 geaccepteerde referentieresultaten**
  blijven exact gelijk. `current:build_4` houdt zijn oorspronkelijke achtseconden-timeout.
- 325 historische catalogus-/loadrecords blijven gelijk; **77 V6-revisies, nul actief**.
  Geen reviewer of individueel besluit toegevoegd. Eigen databaseproces gestopt.

Het [verificatieregister](real-auth-20261114/verification.json) bevat exacte
resultaten, versies, bron-/artefacthashes en de grens tussen deze lokale proeven
en niet-uitgevoerde volledige-stacktests.

## Open poorten

| Poort | Nog benodigd |
| --- | --- |
| Werkelijke GoTrue en gateway | Ondersteunde geautoriseerde omgeving; echte signup/login, ES256/JWKS, issuer/audience/keychecks, API-keyrouting, refresh, werkelijke expiry en logout/revocation. Zie de [Auth-matrix](JOREN_V6_GOTRUE_GATEWAY_VERIFICATION.md). |
| Twee echte accounts | De volledige aanvalsmatrix in beide richtingen via FastAPI en de echte Data API; ook activiteitkoppeling, receipts, private evidence en concurrentie. Zie [isolatie](JOREN_V6_TWO_ACCOUNT_SECURITY_RESULTS.md). |
| Authenticated lifecycle | Alle dertien stappen met echte sessies, volledige onboarding, veilige een-per-sportstandaard, pending indiening, aparte bevestiging, kalender, activiteit, verplaatsing, herstel en stale/retry. Zie [lifecycle](JOREN_V6_AUTHENTICATED_LIFECYCLE.md). |
| Supabase-runtimepariteit | Alle 63 migraties en volledige SQL-suite op de echte Supabase-distributie; extensies, functies, grants, servicebevoegdheden en RLS tegen de gateway controleren. De lokale SQL-subset is onvoldoende. |
| Historische A5-testfixture | Bekende onboarding-/fingerprintcorrectie afzonderlijk door A5-eigenaar laten accepteren; originele SQL en beschermde worktrees zijn niet gewijzigd. Overlay-PASS is geen ongewijzigde-suite-PASS. |
| A5-foutnormalisatie | Additief voorstel: bestaande 422/validation_failed behouden, alleen details.planning_code=v6_search_incomplete toevoegen. Compatibiliteit en veiligheids-/replaychecks eerst bewijzen; niet geimplementeerd. |
| Sessierevocation | Logout maakt bestaande access-JWTs niet vanzelf onmiddellijk ongeldig. Meet refreshweigering en accessvenster apart. De huidige backend controleert geen auth.sessions per verzoek; een eis voor directe invalidatie vraagt een expliciet besluit. |
| Werkelijke reviewer/operator | Echte aangewezen beoordelaar, database-login en benoemings-/bevoegdheidsreferentie. Er is niemand aangemaakt. |
| Individuele numerieke maxima | Afzonderlijk werkelijk beoordeeld besluit per atleet, sport, lokale week en tijdzone met historie, volledigheid, actuele context en reviewreferenties. Geen afleiding uit voorkeur/uren/belasting/beschikbaarheid. |
| Positieve uitgifte/intrekking | Alleen uitvoeren met die echte bevoegdheid en besluiten. Tot die tijd blijft de veilige standaard gelden. |
| Onafhankelijke wetenschappelijke review | Aantoonbaar bevoegde verantwoordelijke reviewer en extern reviewrecord voor exacte bron-, methode- en beleidsversies. |
| Zwemtijd/uitzonderlijke duur | Operationele acceptatie van bestaande zwem-estimates en individueel duurbewijs waar vereist; geen verzonnen algemene grenzen. |
| Planned/Realized | Afzonderlijke acceptatie van Planned IF-squared versus Realized V2-fallback; meetgegevens houden prioriteit, niet-ondersteunde combinaties blokkeren. |
| Prestaties en groter rekenbereik | Representatieve privacygoedgekeurde contexten, doelhardware en expliciet geaccepteerde latency/resources. Eerdere 8/8/8-context bereikt nog de nodegrens; geen algemene voltooiingsgarantie. |
| Echte apparaten | Android/iOS met voorkeur, check-in, swipe, pending review, bevestiging, activiteit, verplaatsing, herstel en accountwisseling. Jest is geen apparaattest. |
| Hosted migratie/release | Afzonderlijke expliciete toestemming, pariteitscontrole, advisors en release-repetitie; niet uitgevoerd. |
| Catalogusactivatie | Afzonderlijke finale toestemming na alle toepasselijke poorten; alle 77 revisies blijven INACTIVE. |

V6 blijft buiten de productiedependency. De limieten blijven **200.000 gedeelde
worknodes**, **24 occurrences** en de oorspronkelijke historische corpusgrens
van **acht seconden**. Exacte numerieke methoden en eerlijke
`v6_search_incomplete` blijven behouden. Geen afgekapt voorstel, kleinere wens,
onbewezen winnaar of kunstmatige rustweek vervangt een onvolledige berekening.

Er is geen push, hosted migratie, deployment, activatie, fysiologische wijziging,
historische herinterpretatie of wijziging in beschermde A5/A6-worktrees uitgevoerd.
Alleen de nieuwe verificatierapporten en geclassificeerde bewijsbestanden zijn
lokaal gecommit. De echte authenticatiepoort blijft geblokkeerd.

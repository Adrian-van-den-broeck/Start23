# WOMBO V6 — technische oplossingen en eigenaarbesluiten

**WOMBO V6 TECHNICAL MIGRATION BLOCKERS RESOLVED — OWNER INFRASTRUCTURE AND EXECUTION APPROVAL REQUIRED**

17 november 2026. Branch `release/joren-v6-migration-blocker-resolution`, vanaf exact `0fa6509190d292d0c83e3076cda68c55624c202e`; volledige eind-SHA in Git en opleverbericht. Geen push, deployment, productiemigratie, activatie, billingwijziging, hosted accountcreatie of beschermde A5/A6-wijziging.

## Geïmplementeerd en lokaal bewezen

- **Activiteitcompatibiliteit:** forward C1 herstelt exacte historische projectie; versiegebonden V2-metadata is alleen server-side. Werkelijke PostgreSQL-responses slagen voor echte historische strikte model-/responsecode op 47 en gecorrigeerd 65; de oorspronkelijke 63-fout `extra_forbidden` blijft bewezen. Bestaande consumenten en optionele V2-presentatie zijn getest. Geen brede V6-deploy nodig voor deze incompatibiliteit. [Implementatie](JOREN_V6_ACTIVITY_COMPATIBILITY_IMPLEMENTATION.md).
- **Rechten:** exact 13 owner-scoped authenticated EXECUTE-signatures afzonderlijk gereviewd; machineallowlist en fail-closed offline generator. De private membership-helper blijft voor invoker-reads. Geen anonymous authority, athlete service writers, reviewer of test-executor. C2 sluit tevens een gereproduceerde NULL-revision-bypass bij voorkeuren. [Review en lijst](JOREN_V6_AUTHENTICATED_EXECUTE_ALLOWLIST.md).
- **Drift:** C2 verwijdert onnodige Dxtm-serviceprivileges op vier catalogustabellen en toepasselijke `postgres/public` defaults. `save_zone_profile` conditioneel geaccepteerd door actieve downstream guard; provider `rls_auto_enable` blijft ongewijzigd in afwachting van platformbewijs. Geen providernormalisatie of ledgerreparatie. [Disposition](JOREN_V6_HOSTED_DRIFT_DISPOSITION.md).
- **Adapter:** aparte factory/launcher, exact geïsoleerd target, twee gemanifesteerde subjects, echte JWT-verificatie, actuele owner-map, bestaande typed services, transportallowlist, redactie, mutatiejournal/reconciliatie en onafhankelijke kill switch. Geen productie-import, test-frequentiebypass of fake reviewer. Cleanup uitsluitend voor gemanifesteerde subjects na aparte toestemming. [Adapter](JOREN_V6_HOSTED_VERIFICATION_ADAPTER.md).

Finale regressie: **2.940 backendtests**, **935 mobiele tests/89 suites**, strict TypeScript, Ruff/format en strict mypy slagen. Beide echte PostgreSQL-upgrades (historisch schoon en gereproduceerde hosted drift) geven elk **752/752 assertions/38 suites**, met alle 51 historische tabelhashes gelijk na iedere groep. Beide bundelrepetities slagen in 14 guardgevallen. Negen lifecycle-, elf evidence- en negen frequentiegroepen slagen, inclusief nieuwe processen. De 40 historische planneruitkomsten, 26 referentiecompletions en multisessie-oracle (15 contexten, 20.061.679 combinaties) blijven exact. [Volledig bewijs](blocker-resolution-20261117/verification.json).

Oorspronkelijke A5-fixture: **8 pass/1 fail/abort vóór 20**. Alleen expliciete overlay 29/29; test-only patch niet overgenomen. Bekende achtseconden-timeout `current:build_4`, nodegrens en eerlijke incomplete-search blijven. Geen nieuwe fysiologische regel of workout.

## Minimale eigenaaracties

| Besluit | Actie |
|---|---|
| Exacte rechten/correcties | Review en keur uitsluitend [13-signature voorstel](blocker-resolution-20261117/authenticated-execute-allowlist.json), C1/C2 en driftkeuzes goed; dit is geen SQL-uitvoeringstoestemming |
| Railway/runtime | `npx --yes @railway/cli login` en browserlogin; daarna read-only werkelijke service/omgeving/URL, commit/artifact, flags, jobs en integraties vaststellen |
| Herstel/kosten | Vraag actuele Pro-/restore-/branchquote, kies RPO/RTO/operator; pas na aparte toestemming checkpoint en bewezen geïsoleerd herstel regelen |
| Hosted verificatie | Keur onafhankelijk synthetisch target en precies twee accounts, custody/cleanup goed; voer daarna genuine GoTrue/PostgREST/V6-verificatie uit |
| Productie-uitvoering | Na poorten: exacte bundelhashes beoordelen en apart operator/venster goedkeuren. G1=1; G2=2–12+C1 atomair; G3=13–16+C2 atomair; geen db push/auto-migrate-deploy |

[Backupopties/accountvoorwaarden](JOREN_V6_REMOTE_BACKUP_AND_RECOVERY_OPTIONS_NL.md): huidig Free heeft geen beschikbare backups/PITR. Eenvoudigste goedkope beheerde route: Pro vanaf USD25/maand plus afzonderlijk gequote tijdelijke restore en korte data-arme Micro-branch (USD0,01344/uur compute plus gebruik). Bestaande vertrouwde remote runner kan goedkoper zijn maar heeft nog geen custody/offerte/herstelbewijs. Schema-only is geen backup. Niets betaald of aangemaakt.

## Werkelijke artifacts: bewijs en ontbrekende identiteit

Railway CLI 5.63.1 geeft opnieuw Unauthorized. Lokale metadata noemt project `c0cf7bc7-abe8-4db5-857a-85cc39850640`, service `start23`, omgeving `production`; dit is geen onafhankelijk vastgesteld deploydoel. URL's `https://start23-production.up.railway.app` en `https://r6-api-r6-staging.up.railway.app` bewijzen geen SHA; eerste health noemde `local`. Gepubliceerde OpenAPI heeft 69 paden; readiness-bron en huidige normale startup hebben een identieke hash voor 73 paden. Geen deployed-runtimecompatibiliteit claimen.

Lokale `mobile/.env` wijst naar staging; lokale modefile noemt productie. Compiled API-configuratie is niet bewezen. Read-only EAS toont nieuwste FINISHED STORE Android **22**, app **1.0.0**, ID `0b1a3606-7476-4607-b4c7-a37e763249c0`, Git-metadata `ee229a9ac2b8de56a6b5bf69026921eab0ab5b56`, voltooid op 1 oktober 2026. Package `com.adrivdbs.wombo`; bronconfiguratie remote versioning/wombo-production autoIncrement. Geconfigureerde Play-track `internal` bewijst geen release. iOS EAS-query leeg sluit andere pipelines niet uit. Geen ADB-device aangesloten. [Geschoonde EAS-identiteit](blocker-resolution-20261117/eas-build-identities.json).

Eigenaar bevestigt in Play Console/App Store Connect actieve track/release/build, compiled routing en fysieke devices. Railway-flags, scheduled processes, Polar/providerconfiguratie en externe webhooks blijven onbekend; source-defaults bewijzen runtime niet. Eerdere webhookinventaris gaf 403. Bron bevat optionele Polar-retryjob en lokale maandagcheck-in; geen productieactiviteit daaruit afleiden.

## Onafhankelijke activatiepoorten

| Poort | Vereist |
|---|---|
| Wetenschappelijke verantwoordelijkheid | Benoemde bevoegde onafhankelijke reviewer en identificeerbaar record voor exacte bron-, Planned IF²-, Realized V2-, regels-/beleidsversies; productfrequentieakkoord vervangt dit niet |
| Reviewer/operator | Expliciete aanstelling/reviewreferentie en minimale bevoegdheid; niemand automatisch inschrijven |
| Individuele frequentie | Echt besluit per atleet/sport/lokale week/tijdzone, intrekking/herbeoordeling; voorkeuren/uren/load geven geen maxima of autorisatie |
| Positieve multisessie | Geen echte-atleetactivatie zonder aanstelling en individueel maximum; nooit productie-test-executor |
| Zwemtijd/uitzonderlijke duur | Operationele acceptatie bestaande estimates en individueel bewijs; geen verzonnen algemene grens |
| Hardware/prestaties | Representatieve goedgekeurde contexten op doelhardware met achtseconden-/200.000-nodegrenzen en eerlijke `v6_search_incomplete` |
| Security/integraties | Bestaande advisorbevindingen, providerobjecten, jobs/webhooks inhoudelijk beoordelen |
| Sessies/cleanup | JWT kan tot expiry geldig blijven; genuine hosted revocation, descendants en cleanup bewijzen |
| Apparaten | Android/iOS volledige flow, accountwissel, retry/herstel en logische/fysieke workoutidentiteit; Jest is geen apparaattest |
| A5-fixture | Alleen aparte goedkeuring kan oorspronkelijke test vervangen; overlaybewijs gescheiden |
| Activering | Aparte deployment-, generatie- en echte-atleetreleasegoedkeuring; 77 INACTIVE en historische default behouden |

[Oude voorwaarden](blocker-resolution-20261117/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_0fa65091.md) blijven bewaard. [Uitvoerplan](JOREN_V6_INACTIVE_PRODUCTION_ROLLOUT_PLAN.md) bevat bestanden/hashes, grenzen, stopvoorwaarden en unknown-commitreconciliatie. Lokale technische oplossingen zijn geverifieerd; echte hosted V6-uitvoering, backuprestore en deployed-runtimecompatibiliteit blijven open.

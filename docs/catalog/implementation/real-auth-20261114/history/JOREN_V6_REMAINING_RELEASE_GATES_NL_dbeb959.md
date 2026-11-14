# V6: resterende onafhankelijke releasevoorwaarden

14 november 2026, Europe/Amsterdam. Zoekoptimalisatiebranch
`perf/joren-v6-exact-multi-session-search`, exact uitgangspunt
`e85cbaa8b5e702c283186fc61fcadda74ad36faf`. Implementatie-SHA en bewijshashes
staan in [het verificatieregister](search-optimization/verification.json).

De drie bekende onvolledige zoekcontexten zijn nu exact opgelost onder de
bestaande limiet. Alle 15 oorspronkelijke synthetische contexten zijn volledig
gecontroleerd met een afzonderlijke exhaustive referentie die geen nieuwe
zoekgrenzen hergebruikt. Dit sluit de aangetoonde technische fout voor die
contexten; het geeft geen algemene garantie voor iedere frequentie of latency.

V6 blijft buiten de productiedependency. Alle 77 revisies blijven INACTIVE.
Het historische standaardalgoritme, de fysiologische regels, gegevenshistorie,
frequentieautorisatie en afzonderlijke atleetbevestiging zijn ongewijzigd.
Er is geen push, merge, hosted migratie, staging-/productieverbinding, deployment
of activatie uitgevoerd.

Het gemelde akkoord op alle vijf frequentievragen blijft vastgelegd in de
[goedkeuringsopvolger](../decisions/JOREN_V6_REAL_ATHLETE_FREQUENCY_APPROVAL.md).
Die beleidsbesluiten worden niet heropend. De voorgaande releasevoorwaarden zijn
[bytegelijk gearchiveerd](search-optimization/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_e85cbaa.md).

| Open poort | Benodigd bewijs of besluit |
| --- | --- |
| Werkelijke reviewer/operator | De daadwerkelijk aangewezen beoordelaar en database-login, met aanwijzings- en bevoegdheidsreferentie. Geen reviewer of bevoegdheid is aangemaakt voor deze optimalisatie. |
| Individuele numerieke maxima | Een echte beoordeling per atleet, sport, lokale week en bevestigde tijdzone, met gedateerde historie, volledigheid, actuele omstandigheden en reviewreferenties. Een voorkeur, uren, belasting of beschikbaarheid levert geen maximum op. |
| Positieve operationele uitgifte/intrekking | Het echte interne pad uitvoeren met die werkelijke bevoegdheid en afzonderlijke individuele besluiten. Zonder deze feiten blijft positieve uitgifte onbeschikbaar. TEST_ONLY-voorbeelden sluiten deze poort niet. |
| Onafhankelijke wetenschappelijke review | Een aantoonbaar bevoegde verantwoordelijke reviewer en extern reviewrecord voor de exacte bron-, methode- en beleidsversies. |
| Zwemtijd en uitzonderlijke duur | Operationele acceptatie van de bestaande zwem-estimates en het bestaande individuele duur-bewijs waar vereist; geen nieuwe algemene veiligheidsgrenzen. |
| Planned/Realized-compatibiliteit | Afzonderlijke officiële acceptatie van Planned IF² versus Realized V2-fallback. Meetgegevens houden prioriteit; niet-ondersteunde combinaties blijven geblokkeerd. |
| Representatieve prestaties en geaccepteerde latency | Beoordeel een privacygoedgekeurde representatieve contextset, doelhardware en expliciete latency-/resourcecriteria. De gemeten lokale verdelingen zijn geen SLA. Het voorstel in het benchmarkrapport vraagt afzonderlijk akkoord en wijzigt geen timeout. |
| Grotere zoekruimte | 3/3/2 en 4/4/4 voltooien in de extra synthetische meetset; 8/8/8 bereikt nog de bestaande nodegrens tijdens sportenumeratie. Geef nooit een afgekapt voorstel uit. Breder gebruik vraagt verdere exacte optimalisatie of expliciete beoordeling van het ondersteunde rekenbereik. |
| Gestructureerde A5-foutcode | De bestaande check-inadapter normaliseert een geforceerde rekenlimiet naar 422 `validation_failed`, terwijl domein/worker en de gewone planningsroute `v6_search_incomplete` behouden. De melding benoemt onvolledige berekening en schrijft niets. Beoordeel de bestaande codepariteit voor release; deze optimalisatie wijzigt de adapter niet. |
| Echte authenticatie/gateway | GoTrue-uitgegeven sessies en volledige Supabase-gatewaytests met twee accounts. Lokale JWT-GUCs en synthetisch ondertekende PostgREST-tokens bewijzen dit niet. |
| Echte apparaten | Android- en iOS-flows met voorkeur, check-in, meerdere occurrences, pending review, bevestiging, activiteitkoppeling, verplaatsing, herstel en accountwisseling. Mobiele bestanden/contracten zijn hier niet gewijzigd; eerdere Jest/APK-evidence is geen apparaattest. |
| Hosted migratie en release | Expliciete toestemming, Supabase-/extensie-/grant/RLS-pariteit, advisors en release-repetitie. Alleen eigen wegwerpdatabases op localhost zijn gebruikt. |
| Catalogusactivatie | Afzonderlijke finale toestemming nadat alle toepasselijke poorten zijn gesloten. Voorkeuren, maxima en deze optimalisatie activeren niets. |

Het plafond blijft 200.000 gedeelde worknodes en maximaal 24 occurrences.
Uitputting blijft `v6_search_incomplete`; geen kleinere wens, onbewezen winnaar
of kunstmatige rustweek vervangt de aanvraag. De oorspronkelijke historische
corpusgrens blijft acht seconden, met hetzelfde `current:build_4`-timeoutgeval.

Alle bestaande TSS-, HIGH-tijd-, fase-, herstel-, blessure-, capability-,
herhalings- en plaatsingsvoorwaarden blijven gelden. Behouden/voltooide
occurrences tellen eenmaal, met hun eigen identiteit en datum. Boven een
aangescherpt maximum volgt een conflict; bewijs wordt niet verwijderd of
gekloond. Ongeplande/onduidelijk gekoppelde activiteiten blijven uitbreiding
blokkeren zonder beoordeelde, ondersteunde complete-weekcontext.

De [integratieregressies](JOREN_V6_SEARCH_INTEGRATION_REGRESSIONS.md) onderscheiden
echte lokale SQL-/worker-/TCP-/herstartproeven van open releasepoorten. De
bestaande tijdelijke synthetische testrechten zijn na de afzonderlijke proeven
ingetrokken; het eindaudit vindt nul reviewers, nul besluiten en nul actieve
V6-revisies. Oorspronkelijke migraties, pgTAP-bronnen, gouden uitkomsten en
beschermde A5/A6-worktrees zijn ongewijzigd. De bekende A5-fixturecorrectie is
alleen als expliciete bestaande testoverlay gebruikt.

WOMBO V6 EXACT SEARCH OPTIMIZATION VERIFIED — RELEASE GATES REMAIN

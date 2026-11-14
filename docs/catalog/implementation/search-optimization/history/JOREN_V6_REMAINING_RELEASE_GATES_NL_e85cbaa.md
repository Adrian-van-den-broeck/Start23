# V6: resterende onafhankelijke releasevoorwaarden

13–14 november 2026, Europe/Amsterdam. Branch
`feat/joren-v6-approved-frequency-policy`; basis
`6745c903ae045b3c3215e928fb53c36cb119a741`.

Het gemelde akkoord op alle vijf beleidsvragen is vastgelegd in de
[goedkeuringsopvolger](../decisions/JOREN_V6_REAL_ATHLETE_FREQUENCY_APPROVAL.md).
De vijf productbesluiten zijn daarmee gesloten. De oorspronkelijke PROPOSED
tekst blijft exact behouden; het eerdere releaseregister is als
[historisch document](frequency-policy/history/JOREN_V6_REMAINING_RELEASE_GATES_NL_20261112.md)
bewaard. Historische passages over een nog ontbrekend productbesluit heropenen
het nu gemelde akkoord niet.

Optionele blijvende voorkeuren, afzonderlijke private weekbesluiten, schorsing,
herbevestiging en databasebewaking zijn lokaal geïmplementeerd. Een voorkeur is
geen maximum. Uren, belasting, beschikbare dagen en voltooide trainingen leveren
geen nieuwe frequentietoestemming op. V6 blijft uit de productiedependency;
alle 77 bronrevisies blijven INACTIVE. Geen bevestigde week of historische
berekening is stil herschreven.

| Open poort | Wat nog nodig is |
| --- | --- |
| **Volgende onafhankelijke technische prioriteit: zoekprestaties** | Los de aangetoonde uitval op met bewezen exacte selectie, representatieve worker/HTTP-, geheugen-, admission- en annuleringstests. Behoud alle veiligheidsvoorwaarden en onafhankelijke exhaustive-oracles. |
| Werkelijke reviewer/operator | Benoem de daadwerkelijk aangewezen beoordelaar en database-login, leg de aanwijzings-/bevoegdheidsreferentie vast en ken pas daarna de beperkte interne registratierechten toe. De migratie maakt geen reviewer aan. |
| Individuele numerieke maxima | Ieder maximum vraagt een echte beoordeling voor de exacte atleet, sport, lokale week en bevestigde tijdzone, met gedateerde historie, volledigheid, actuele context en reviewreferenties. Het beleidsakkoord geeft geen enkel getal af. |
| Positieve operationele uitgifte-/intrekkingsverificatie | Voer het echte interne pad uit met die daadwerkelijke bevoegdheid en afzonderlijk beoordeelde besluiten. Hypothetische Python-invoer en TEST_ONLY-lifecycleproeven sluiten deze poort niet. Zonder die feiten blijft uitgifte onbeschikbaar. |
| Onafhankelijke wetenschappelijke review | Een aantoonbaar bevoegde, verantwoordelijke reviewer en extern reviewrecord voor de exacte bron-, methode- en beleidsversies. Geen credentials of externe review worden uit het gemelde akkoord afgeleid. |
| Zwemtijd en uitzonderlijke duur | Operationele acceptatie van geschatte actieve zwemtijd en het bestaande individuele duur-bewijs waar vereist. Geen nieuwe algemene duur- of veiligheidsgrenzen. |
| Planned/Realized-compatibiliteit | Afzonderlijke officiële acceptatie van Planned IF² versus Realized V2-fallback. Meetgegevens behouden prioriteit; niet-ondersteunde combinaties blijven geblokkeerd. |
| Echte authenticatie/gateway | GoTrue-uitgegeven sessies en volledige Supabase-gatewaytests met twee accounts, inclusief voorkeur, private autorisatie, snapshot en bevestiging. Lokale SQL-claims/HS256-tokens zijn hiervoor geen bewijs. |
| Echte apparaten | Android- en iOS-flows voor optionele onboarding, profielwijziging, check-in, meerdere occurrences, pending review, expliciete bevestiging, activiteitkoppeling, verplaatsing, herstel, herstart en accountwisseling. De geslaagde debugbuild is geen apparaattest. |
| Hosted migratie en release | Expliciete autorisatie, volledige Supabase-/extensie-/grant/RLS-pariteit, advisors en releaserepetitie. De kandidaat is uitsluitend op eigen wegwerpdatabases op localhost uitgevoerd. |
| Catalogusactivatie | Afzonderlijke finale toestemming nadat alle toepasselijke poorten zijn gesloten. Geen activatie via voorkeuren of een handmatig maximum. |

De 15 oorspronkelijke synthetische zoekcontexten zijn herhaald. BASE 2/2/1 bij
het oorspronkelijke budget-300-geval, BASE 2/2/2 bij 200 en de normale
onboardingcontext met 105 minuten per sport blijven `v6_search_incomplete`.
Ook gewone aanvragen kunnen dus vastlopen. Een kleiner geldig voorstel bewijst
geen optimum voor de oorspronkelijke aanvraag.

Het plafond blijft **200.000 gedeelde worknodes** en maximaal 24 occurrences.
Geen hogere limiet/deadline, stil verlaagde wens, greedy winnaar of opgeslagen
onbewezen optimum is toegestaan. Een nieuwe, door de atleet bewust gewijzigde
voorkeur vormt een nieuwe context. De ongewijzigde historische corpusgrens is
acht seconden, met het bestaande diagnostische timeoutgeval `current:build_4`.
Dit werk bevat geen afzonderlijke grote zoekoptimalisatie.

De bestaande TSS-, HIGH-tijd-, fase-, herstel-, blessure-, capability-,
herhalings- en planningsvoorwaarden blijven onafhankelijk gelden. Behouden en
voltooide occurrences tellen eenmaal. Boven een aangescherpt plafond volgt een
conflict voor beoordeling; bewijs wordt niet verwijderd of gekloond. Ongeplande
of onduidelijk gekoppelde activiteiten blokkeren uitbreiding tot een beoordeelde,
ondersteunde complete-weekcontext bestaat. De ongeschikte legacy correctieve
writer blijft geblokkeerd bij opgenomen activiteitbewijs.

De [verificatie](JOREN_V6_FREQUENCY_VERIFICATION.md) onderscheidt uitgevoerde
lokale proeven van open poorten. De originele A5-fixture en beschermde
A5/A6-bronnen zijn ongewijzigd; de bekende fixturecorrectie is alleen als
expliciete geïsoleerde testoverlay uitgevoerd. Er is geen push, merge, hosted
migratie, staging-/productieverbinding, deployment of V6-activatie uitgevoerd.

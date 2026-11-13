# V6: sessiewens en frequentieautorisatie voor echte atleten

**Ter besluitvorming door eigenaar en Joren — niets in dit document is al goedgekeurd.**

Datum: 13 november 2026, Europe/Amsterdam. Gecontroleerde implementatie:
`feat/joren-v6-multi-session-planning`,
`6745c903ae045b3c3215e928fb53c36cb119a741`.
Voorgestelde beleidsidentiteit: `joren-v6-real-athlete-frequency-policy-1`,
status **PROPOSED**. Goedkeuring moet naar deze exacte tekst/versie verwijzen;
wijzigingen in de voorwaarden vragen een nieuwe besluitversie.

## 1. Aanbevolen besluit

Voeg een **optionele, blijvende sessiewens per doelsport** toe, bijvoorbeeld
RUN 2 / BIKE 2 / SWIM 1. Gebruik die uitsluitend als zacht selectiedoel binnen
een **afzonderlijk, expliciet beoordeeld maximum per atleet, sport en week**.
Een wens is geen voorschrift, minimum, bewijs van belastbaarheid of toestemming
om extra belasting toe te voegen.

Start voor echte atleten met **individuele weekautorisatie door Joren** of een
door hem en de eigenaar expliciet aangewezen bevoegde beoordelaar. Leg elk
numeriek maximum en de onderbouwing vast. Bouw nu geen automatische vertaling
van historie naar een maximum: daarvoor ontbreekt een goedgekeurde regel.
Dit is een begrensde eerste productroute met beoordelingswerk per week, geen
schaalbare automatische frequentiebepaling.

Zonder voldoende beoordeeld bewijs blijft de bestaande automatische standaard
van één sessie per geschikte doelsport gelden, onder alle bestaande beperkingen.
Ook die standaard garandeert geen geschikte training: minder sessies of rust
blijven mogelijk. Ontbrekende bevoegdheid of gegevens blokkeren uitbreiding;
ze bewijzen geen medische ongeschiktheid.

Een groter geautoriseerd weekbudget, meer beschikbare dagen, veel historische
uren, veel voltooide sessies of een hoge sessiewens leveren afzonderlijk geen
frequentieautorisatie op. Gebruik geen beginner/intermediate/advanced-categorieën.

**Behouden:** officiële methode `joren-v6-planned-if2-1`, de 77 brontrainingen,
bronfasen, bestaande selectierangschikking en historische planner. Alle
blessure-, herstel-, progressie-, capability-, beschikbaarheids-, herhalings-,
HIGH-actieve-tijd- en planningsvoorwaarden blijven onafhankelijk verplicht.
Goedkeuring van dit voorstel sluit de overige V6-releasepoorten niet.

## 2. Vijf afzonderlijke begrippen

| Begrip | Voorgestelde representatie en betekenis | Bevoegdheid |
| --- | --- | --- |
| Atleetwens `P` | Per sport een nullable geheel aantal sessies per week, eigen revisie en bevestigingstijdstip. `null` = geen voorkeur; `0` = geen nieuwe sessies voor deze sport gevraagd. | Atleet mag de eigen wens wijzigen; geen wijziging van een veiligheidsmaximum. |
| Geautoriseerd maximum `M` | Afzonderlijk intern record met atleet, sport, exacte lokale week, numeriek maximum, beleidsversie, beoordelaar, bewijsreferenties, revisie en geldigheidsstatus. Plafond voor de **hele week**, inclusief behouden en voltooide occurrences. | Alleen een vertrouwde serverprocedure mag een goedgekeurd beoordelingsbesluit registreren. |
| Bestaande week `C` | Volledige behouden occurrence-prefix uit de server, met logische én fysieke identiteit, datums, bronrevisies en eventuele activiteitkoppelingen. Een voltooid lid telt eenmaal, ook bij hergebruik van hetzelfde template. | Werkelijke plan-/activiteitregistratie; geen cliënttelling en geen bewijs van een nieuw maximum. |
| Weekbelasting `B` | Bestaande intern geautoriseerde weekgrens en sportcaps, met eigen bron/ruleset. | Ongewijzigde resolver voor historie, onboarding, herstel, progressie en blessurecontext. `P` en `M` mogen `B` niet verhogen. |
| Geen geldige autorisatie | Expliciete toestand: ontbrekend, nog te beoordelen, geschorst, ingetrokken, verlopen of door een nieuw besluit vervangen. Bewaar historische versies en intrekkingsreden. | De resolver onderscheidt een bewezen afwezig record van een mislukte database-opvraag. Bij opvraagfouten geen oude toestemming aannemen. |

### Vertaling naar de bestaande selector

Voor een geldige autorisatie krijgt de selector `maximum=M` en
`target=min(P,M)` als een wens bestaat; de oorspronkelijke, eventueel hogere
wens blijft apart bewaard voor uitleg. Zonder wens blijft `target=None`:
het bestaande contract vraagt dan `min(1,M)`. Een maximum van vijf vraagt dus
niet automatisch vijf sessies. Een maximum van nul staat geen sessies toe.

Zonder extra autorisatie wordt een wens boven één voor nieuwe generatie tot
de bestaande standaard begrensd. Dit is geen nieuw universeel fysiologisch
maximum. `P=0` vraagt geen toevoeging; behouden sessies verdwijnen daardoor niet.
Een nieuw opgeslagen nulvoorkeur is ook geen annulering van een actief plan.

De automatische selector stopt bij het effectieve zachte doel, maar accepteert
een grotere behouden prefix zolang die onder alle harde grenzen valt. Bij
`P=2`, `M=3`, `C=1` is het doel twee **totaal**, dus hoogstens één toevoeging.
Bij `C=3` zijn geen toevoegingen nodig. Bij `C=4 > M=3` mag geen geldig nieuw
voorstel worden geclaimd en mag de prefix niet stil worden ingekort.

De bestaande fallback laat behouden herhalingen intact en voegt zonder
frequentiecontract niets toe aan een al vertegenwoordigde sport. Zet deze
historische eigenschap niet om in een retroactief hard maximum van één voor
een eerder bevestigde week. Een oude multi-sessieweek is evenmin toestemming
voor een nieuwe week of voor verdere uitbreiding.

Dit maximum begrenst de complete plannerweek. Activiteiten die bij die
occurrences horen tellen niet nogmaals als extra sessie. Ongeplande of niet
eenduidig gekoppelde activiteiten in de betrokken week kunnen niet zomaar als
V6-template aan de prefix worden toegevoegd: daarvoor bestaat dit contract niet.
Voorgesteld is dan uitbreiding te blokkeren tot beoordeling van de volledige
weekcontext. Geen afgeronde activiteit negeren om ruimte te creëren, geen
synthetische occurrence maken en geen nieuwe sessiedefinitie uit meetfragmenten
afleiden. De registratie van zo'n activiteit blijft gewoon mogelijk.

Rangschikking blijft: haalbare sportdekking, vervolgens totale afgedekte zachte
sessiewens, daarna bestaande 50/30/20-allocatieafstand waar van toepassing,
budgetbenutting en stabiele template-UUIDs. Er komt geen prioriteit bij om
bijvoorbeeld eerst RUN volledig te vullen. Een zachte wens kan dus gedeeltelijk
worden vervuld; veiligheid en alle harde grenzen gaan altijd voor.

`SessionFrequency` kan uitsluitend gehele aantallen 0–24 representeren; 24 is
een rekentechnische grens, geen advies. Voorgesteld voor de invoer: 0–24 per
sport en maximaal 24 gevraagde sessies samen; toon bij overschrijding een
technische invoermelding. Ook een toegelaten invoer kan buiten het praktische
zoekbereik vallen. Een autorisatiemaximum is nooit een capaciteitstoezegging.

## 3. Herkomst en bewijs van het maximum

**Aanbevolen eerste bron:** een gecontroleerd intern beoordelingsrecord,
geregistreerd na een expliciet besluit van Joren/de aangewezen beoordelaar.
Geen nieuwe coachportal, cliëntveld voor maxima, vrije LLM-beslissing of
globale configuratie voor alle accounts. Een gecontroleerde interne invoerroute
volstaat voor deze eerste release; benoem de verantwoordelijke operator.

Elke beslissing bevat ten minste:

- Exacte atleetidentiteit, sport, lokale maandag–zondagweek en bevestigde IANA-
  tijdzone; aanmaak-/beoordelingstijd, numeriek maximum en besluitversie.
- Werkelijke sessiehistorie per sport over een **expliciet gedateerde** beoordeelde
  periode, met bron en volledigheid. Maak geregistreerde activiteiten,
  atleetrapportage en ontbrekende registratie onderscheidbaar; ontbrekend is
  geen nul. Oude afstand/frequentie-onboarding wordt niet automatisch hergebruikt.
- Beoordeling van de actuele blessure-, ziekte-, herstel-/onderbrekingscontext,
  sportcapability en beoogde fase. Een sensor of bevestigde zone is geen bewijs
  dat meerdere sessies geschikt zijn. Individueel duur-bewijs blijft apart nodig
  waar de bestaande V6-regels dat vragen.
- Onderbouwing waarom dit maximum in juist deze week wordt toegestaan; naam en
  bevoegdheid van de beoordelaar, herleidbaar goedkeurings-/reviewrecord en
  eventuele voorwaarden. Een lege referentie of alleen `TEST_ONLY` volstaat niet.
- Geldigheid voor uitsluitend de genoemde week, plus expliciete opschortings-,
  intrekkings- en vervangingsstatus. Geen automatische verlenging naar volgende
  weken. Een besluit voor meerdere weken moet elke week afzonderlijk benoemen
  en bij gebruik opnieuw op actualiteit worden gecontroleerd.

Er is geen goedgekeurde universele observatieduur, minimale datadekking,
verhogingsstap of veilige tabel met sessieaantallen. Dit voorstel verzint die
niet: de beoordelaar moet de gekozen periode, beperkingen en voldoende bewijs
per individueel besluit verantwoorden. Kan hij dat niet, dan geen uitbreiding.
Dit maakt handmatige beoordeling mogelijk zonder een onbewezen rekenregel.

**Joren moet beide goedkeuren:** de regels voor vaststelling, geldigheid en
intrekking én de concrete individuele maxima die via deze eerste route worden
afgegeven. De eigenaar keurt productsemantiek, invoer, operationele capaciteit
en verantwoordelijke rollen goed. Een bevoegde verantwoordelijke wetenschappelijke
reviewer en extern reviewrecord blijven vereist; Jorens rol mag niet zonder
bevestigde bevoegdheid gelijk worden gesteld aan die afzonderlijke releasepoort.

Een latere automatische resolver vereist eerst een afzonderlijk versioneerd
besluit over meetperiode, bronkwaliteit, ontbrekende gegevens, terugkeer na
uitval, frequentieverandering, contra-indicaties en grensgevallen, met valideerbare
fixtures. Daarna hoeven individuele besluiten niet handmatig te blijven als die
goedgekeurde regel dat expliciet toestaat. Dit document autoriseert die stap niet.

## 4. Kleinste voorgestelde productinteractie

Voeg één kaart **‘Gewenste sessies per week (optioneel)’** toe aan het bestaande
profiel, met dezelfde kaart als optioneel onderdeel van de onboarding-
eindcontrole. Per huidige doelsport: ‘Geen voorkeur’ of een geheel aantal;
bijvoorbeeld Hardlopen 2, Fietsen 2, Zwemmen 1. Geen vooringevulde 2/2/1 en geen
nieuwe verplichte onboardingstap. Sla dit apart van trainingshistorie op.

Voorgestelde toelichting:

> Dit is je voorkeur. Je weekvoorstel kan minder sessies bevatten door je herstel,
> geschiktheid en beschikbare dagen. Je beoordeelt en bevestigt elk weekplan apart.

De uren over de vorige maand, profielgegevens, hartslagmeterbevestiging,
bevestigde tijdzone, concrete wedstrijd en vereiste bevestigde zones/kalibratie
blijven de bestaande onboardingvoorwaarden. Herintroduceer geen historische
frequentievragen als vervanging van uren en geen RPE-only onboardingroute.

| Situatie | Voorgestelde interactie |
| --- | --- |
| Overslaan/bestaand account zonder wens | Laat `null` staan en gebruik de bestaande standaard. Geen nieuwe onboardingblokkade, geen afleiding uit uren of TSS. |
| Later wijzigen | Via dezelfde profielkaart, met opslaan, revisiecontrole en duidelijke opgeslagen status. Nieuwe wens geldt voor volgende nieuw gegenereerde voorstellen, ook in de huidige week als de atleet expliciet opnieuw laat plannen. |
| Geldigheidsduur | De wens blijft staan tot wijziging/verwijdering; geen aparte weekoverride in deze minimale UI. Het autorisatiemaximum blijft exact weekgebonden. |
| Lopend concept/pending plan | Wens- of autorisatierevisie wijzigt de context; laat herladen en een nieuw beoordeelbaar voorstel maken via bestaande revisiepaden. Geen stil herschikken of ophogen van het oude voorstel. |
| Actief bevestigd plan | Alleen een voorkeur opslaan verandert niets aan dat plan. Een noodzakelijke planwijziging blijft een afzonderlijke pending wijziging met atleetbevestiging en behoud van activiteitbewijs. |
| Wens boven toegestaan maximum | Bewaar de wens, maar toon kwalitatief ‘Je voorkeur is opgeslagen. Extra sessies zijn voor deze week nog niet vrijgegeven.’ Geen hogere frequentie of medische geschiktheid suggereren. |
| Minder sessies in het voorstel | Toon gevraagd versus voorgesteld aantal per sport en ‘We stellen deze week minder sessies voor binnen je huidige trainingsvoorwaarden.’ Voeg alleen een specifieke reden toe als de server die aantoonbaar kent. Geen verzonnen medische uitleg. |
| Zoekwerk niet voltooid | ‘Het weekvoorstel kon niet volledig worden berekend. Er is geen nieuw voorstel opgeslagen.’ Bied aanpassen van de wens of ondersteuning aan; geen rustweek/onhaalbaarheid claimen en geen eindeloze automatische retry. |

Een frequentiewens opslaan is geen goedkeuring van een maximum en geen
voorafgaande goedkeuring van daadwerkelijke trainingen. Behoud de huidige
swipe-, accept/pass/undo-, datumplaatsings-, voorstelreview- en expliciete
planbevestigingsflow. Herhaalde templates blijven aparte kaarten/occurrences.

## 5. Ontbrekende gegevens, uitval en herbevestiging

Voorgestelde governance voor uitbreiding, zonder de bestaande fysiologische
resolver te veranderen:

- Bij een nieuw gemelde blessure wordt de extra autorisatie voor de betrokken
  sport geschorst; bestaande blessure-uitsluiting, low-only en toegestane
  herverdelingsregels blijven leidend. Geen nieuwe herverdeling wegens een
  onvervulde frequentiewens.
- Bij gemelde ziekte of expliciet gemelde trainingsonderbreking worden extra
  frequentieautorisaties voor de betrokken planningscontext geschorst tot een
  nieuwe beoordeling. Bij ziekte geldt dit voor alle sporten. Introduceer geen
  eigen aantal gemiste dagen of sessies dat een onderbreking definieert.
  Ontbrekende registraties alleen zijn geen diagnose; onzekere bewijsactualiteit
  verhindert wel een nieuwe uitbreiding.
- Na herstel blijft de oude wens als wens zichtbaar, met ‘Controleer je voorkeur
  na je onderbreking’. Atleet herbevestigt die vóór hernieuwde uitbreiding en de
  beoordelaar geeft een nieuwe weekautorisatie. Een verklaring ‘weer beter’
  herstelt het oude maximum niet automatisch. De bestaande workload-resolver
  blijft verantwoordelijk voor ziekte-, vermoeidheids- en gemiste-trainingregels.
- Een wijziging van doelsport, relevante capability of tijdzone/weekbinding, of
  een gewijzigde beoordelingsgrond maakt de betrokken autorisatie opnieuw te
  beoordelen. Een materiële wijziging markeert ook de wens ter herbevestiging.
  Een andere datum binnen dezelfde bevestigde beschikbaarheid vraagt op zichzelf
  geen nieuwe blijvende wens, maar wel de bestaande weekvalidatie.
- Een normale volgende week vraagt geen nieuwe profielinvoer: toon de geldende
  wens bij voorstelreview. Wel is voor extra sessies opnieuw een geldige exacte
  weekautorisatie nodig. Een hogere wens vraagt geen herkalibratie van zones en
  kan nooit op zichzelf een hoger maximum afdwingen.

Bij verlopen/ingetrokken autorisatie mag een oud pending multi-sessievoorstel
niet alsnog worden bevestigd. Behoud het oude snapshot als historisch bewijs;
blokkeer nieuw gebruik en maak alleen met actuele context een nieuw voorstel.
Als behouden/voltooide occurrences een nieuw plafond overschrijden, meld een
conflict voor beoordeling. Wis, kloon of verplaats die bewijsrecords niet om een
nieuwe week passend te laten lijken. Een bevestigd actief plan wordt niet
automatisch herschreven; toon de gewijzigde voorwaarden en gebruik het bestaande
beoordelings-/pending pad. Een daarvoor ongeschikte correctieve writer blijft
geblokkeerd. Geen claim dat intrekking via de huidige software al operationeel is.

## 6. Inspectie van het bestaande servercontract

De volgende bevindingen gelden voor de gecontroleerde SHA, niet voor een nieuw
geïmplementeerde autorisatieroute.

| Onderdeel | Bestaand gedrag | Minimale voorgestelde aansluiting na goedkeuring |
| --- | --- | --- |
| `v6_frequency.py:SessionFrequency` | `sport`, `maximum`, niet-lege `reference`, optioneel `target`, uitsluitend `status="soft_target"`; gehele aantallen 0–24 en `target <= maximum`. | Houd dit rekencontract. Een aparte serverresolver valideert echte besluitstatus, bewijs en revisie; een niet-lege string bewijst nu nog geen bevoegdheid. |
| `v6_selection.py:V6Controls` | Frequentie vereist `athlete_scope` en `week_scope`; dubbele sporten worden geweigerd. Andere controls blijven afzonderlijk. | Vul controls per verzoek met exact geverifieerde actor/week. Geen procesbrede atleetautorisatie of publieke maximum-/budgetoverride. |
| `v6_service.py` | `_assert_individual_scope` controleert actor/week; `_scoped_service` maakt request-local controls en occurrence-namespace. | Los eerst de token-actor naar de bestaande interne identiteit op, laad diens besluit voor exact die lokale week en controleer ook de tijdzonebinding. Geen `user_id` uit de cliënt vertrouwen. |
| `app/local_v6.py` | Alleen expliciete test-injectie; weigert niet-test en niet-loopback Supabase. Normale startup activeert V6 niet. | Maak later een afzonderlijk beoordeelde reguliere dependency-aansluiting; schakel deze testbeveiliging niet uit. Frequentieopslag alleen maakt V6 niet releaseklaar. |
| `controls_json`, frozen snapshot | Exacte controls, referenties en `selection_version` worden privé opgeslagen; oude snapshots krijgen backward defaults. | Voeg blijvende wensrevisie en autorisatie-ID/revisie/status-/bewijsversie toe aan de private context/snapshot-envelope en fingerprints. Bewaar zowel de oorspronkelijke wens als het begrensde doel. |
| `frozen_controls` / `effective_controls` | Herstel na restart; actuele expliciete maxima kunnen aanscherpen. Een groter huidig doel of maximum vergroot het opgeslagen generatieverzoek niet. | Behoud deze monotonie bij vervanging; een hogere toestemming vraagt nieuwe generatie/review. Leg ook de actuele beperkende bron vast, naast de oude frozen referentie. |
| Intrekking | Een ontbrekend record in `current.session_frequency` verwijdert een oud frozen record **niet**. `status` is geen lifecycle-statusveld. | Gebruik expliciete intrekkings-/schorsingsrecords en controleer die vóór generatie, hervatten, bewerking, submit en bevestiging. Alleen een leeg tuple doorgeven is onvoldoende. Een harde nul kan een complete behouden week ongeldig maken; dat is een conflict, geen opdracht tot verwijderen. |
| Opslag en approval | `InactiveSupabaseV6Repository` bestaat; private V6-writer valideert scope/fingerprints. Bevestiging gebruikt de bestaande `approve_plan_proposal` RPC; er bestaat geen echte frequentiebron om daar live te controleren. | Controleer dezelfde autorisatie-/wensrevisie en actuele status atomair bij nieuwe opslag én bevestiging. Een voorafgaande Python-check alleen voorkomt geen intrekking tussen lezen en commit. |
| Behouden prefix en replacements | Volledige week telt mee voor maxima, budget, templategebruik en HIGH-tijd. Pending vervanging wijzigt één occurrence en optimaliseert siblings niet. | Lever alle bestaande occurrences inclusief voltooid bewijs; behoud logische/fysieke IDs, datums, receipt- en lidmaatschapscontracten. |

### Voorgestelde opslag en transacties

Twee gescheiden concepten volstaan: een owner-scoped, versioneerde
voorkeurregistratie met historie en een server-private, append-only
frequentiebesluitregistratie met actuele status/revisie. Concrete tabel-/RPC-namen
zijn implementatiewerk na besluit; geen nieuw framework of algemene policy-engine.
Wijzigingen komen via forward-only migraties, nooit via herschrijven van de 62
bestaande migraties of terugrekenen van historische plannen.

Sta geen twee tegenstrijdige actuele besluiten voor dezelfde atleet/sport/week
toe. Vereis expliciete vervanging met een verwachte revisie; geen ‘laatste
timestamp wint’. De resolver onderscheidt ‘geen besluit’ van ‘ingetrokken’ en
controleert een toegestane beleidsversie en echte beoordelaar. TEST_ONLY moet
voor de echte route expliciet worden afgewezen; de bestaande dataclass doet dit
nog niet zelf. Een ingetrokken besluit mag via oude snapshots of caches niet
opnieuw toestemming opleveren.

Bind voorkeur-, autorisatie- en restrictierevisies aan de bestaande
input-/context-/generation-fingerprints, ook in onboarding-initiële verzoeken,
swipedrafts, A5/check-in en pending vervangingen. Controleer die bij commit onder
de bestaande lock/CAS-volgorde, inclusief concurrerende intrekking. Introduceer
geen losse lockvolgorde die approval, move of A5 kan deadlocken. Databaseguards
moeten ook directe writes en bevestiging afdekken.

Behoud exacte idempotente receipts en terminale attachment-status. Een retry
van een al gecommitteerde operatie retourneert het bestaande resultaat en voert
geen nieuwe generatie of activatie uit. Intrekking mag dat historische receipt
niet veranderen; een nieuwe mutatie of latere bevestiging controleert wél de
actuele autorisatie. Als nog niets gecommit is, moet een intrekking een late
workerwrite verhinderen. Geen nieuw verzoek-ID fabriceren om een stale context
of bestaande A5-uitkomst te omzeilen. Na herladen verloopt een werkelijk nieuwe
aanvraag via de bestaande toegestane revisie-/verzoekpaden.

### Privacy en accountisolatie

Alleen eigen wensen, kwalitatieve beschikbaarheidsstatus en sessieaantallen zijn
nodig in publieke Pydantic-contracten. Maxima/besluitbewijs blijven server-private
in dit minimale voorstel. TSS, gerealiseerde/geplande private belasting, interne
budgetten en bewijsinhoud blijven uit API-responses, fouten, logs, analytics,
toegankelijkheidslabels en mobiele opslag. Geen secret/servicekeys naar Expo.
Voorkeur wijzigen loopt via een smalle owner-afgeleide operatie; de atleet kan
geen autorisatiebesluit schrijven of de eigenaar van een record wijzigen.

Behoud bestaande RLS/grants; nieuwe voorkeurdata krijgt ownerisolatie en private
autorisatiedata geen cliëntgrant. Controleer bij vertrouwde serverwrites de actor
ook expliciet; een servicekey is geen ownercheck. Gebruik geen user-editable
JWT-metadata als frequentiebevoegdheid. Dit sluit aan op de officiële
[Supabase RLS-documentatie](https://supabase.com/docs/guides/database/postgres/row-level-security).
De [changelog](https://supabase.com/changelog.md) is op 13 november geraadpleegd;
er is geen SDK-/CLI-upgrade, databaseverbinding of infrastructuurwijziging gedaan.

## 7. Zoekruimte: reëel capaciteitsrisico bij gewone wensen

De huidige grenzen zijn **24 complete-week-occurrences** en **200.000 gedeelde
worknodes** voor sport-multisetuitbreiding, samenvoegen en schedulerrecursie.
De caller kan de nodegrens verlagen, niet verhogen. Dit zijn engineeringgrenzen,
geen fysiologische maxima. De selector materialiseert en rangschikt complete
combinaties vóór plaatsing. Daardoor kan hij vastlopen terwijl er passende
kleinere weken bestaan. Ook rangschikken kost tijd zonder extra worknodes.

Bij de hieronder gebruikte BASE-context waren 22 RUN-, 22 BIKE- en 16 SWIM-
templates eligible vóór de complete-sport HIGH-toets. Zonder budget/HIGH-pruning
zijn er bij 2/2/1 maximaal `C(24,2) × C(24,2) × 17 = 1.294.992`
multisetcombinaties; bij 2/2/2 is dit `276 × 276 × 153 = 11.654.928`.
Dat zijn bovengrenzen vóór de bestaande noodzakelijke pruning, geen aantallen
veilige of werkelijk onderzochte weken. Vijf of zes gevraagde sessies kunnen dus
de nodegrens raken, ruim onder 24 occurrences.

### Werkelijk uitgevoerde lokale meting op de ongewijzigde code

Op 13 november zijn 15 synthetische contexten uitgevoerd met `build_v6_plan` en
`official_catalog()` van de genoemde SHA. Alle frequenties hadden expliciet
`TEST_ONLY`-authority, `maximum=target`; geen echte atleet is geautoriseerd.
Week 26 oktober–1 november 2026, Europe/Amsterdam, zeven beschikbare datums,
wedstrijd twaalf weken later, volledige testcapabilities, geen blessure, prefix,
individueel duur-bewijs of extra `maximum_uses`. Zwemtijd gebruikte de bestaande
preview-estimate. Bronfasen, exacte officiële belasting en HIGH-/schedulerregels
zijn ongewijzigd. BUILD gebruikt expliciet `build_week=4` in het synthetische
target; dit is geen uit een werkelijk wedstrijdschema afgeleide BUILD-claim.

De bedragen hieronder zijn uitsluitend private ontwikkelcontext, nooit UI-copy.

| Context; wens RUN/BIKE/SWIM | Weekgrens | Worknodes incl. plaatsing | Uitkomst |
| --- | ---: | ---: | --- |
| BASE 2/2/1 | 100 | 21.040 | Voltooid; vijf sessies |
| BASE 2/2/1 | 150 | 60.789 | Voltooid; vijf sessies |
| BASE 2/2/1 | 200 | 117.838 | Voltooid; vijf sessies |
| BASE 2/2/1 | 250 | 189.609 | Voltooid; vijf sessies, weinig noderuimte over |
| BASE 2/2/1 | 300 | Grens overschreden | `v6_search_incomplete`; geen winnaar |
| BASE 2/1/1 | 300 | 43.005 | Voltooid; vier sessies |
| BASE 3/2/1 | 150 | 191.519 | Voltooid; zes sessies, weinig noderuimte over |
| BASE 2/2/2 | 100 | 79.141 | Voltooid; zes sessies |
| BASE 2/2/2 | 200 | Grens overschreden | `v6_search_incomplete`; geen winnaar |
| RUN-only 3/0/0 | 200 | 2.800 | Voltooid; drie sessies |
| RUN-only 4/0/0 | 300 | 20.513 | Voltooid; vier sessies |
| BUILD-4 2/2/1 | 100 | 21.374 | Voltooid; vijf sessies |
| BUILD-4 2/2/1 | 150 | 66.640 | Voltooid; vijf sessies |
| Normale onboardingresolver, 35 min/week/sport; 2/2/1 | 100,1 | 21.076 | Voltooid; vijf sessies |
| Normale onboardingresolver, 105 min/week/sport; 2/2/1 | 300,2 | Grens overschreden | `v6_search_incomplete`; geen winnaar |

De laatste twee gebruiken `starting_baseline({sport: Decimal(minutes)})`,
`prior_loads=()` en **geen** `authorized_target`-override. De overige dertien
gebruiken een synthetisch `PlanningTarget` met de vermelde grens en fase.
De reguliere berekening bij 105 minuten per sport toont dat het probleem niet
alleen door een willekeurige budgetoverride kan ontstaan. De ingevoerde uren
zijn synthetisch; ze bewijzen geen geschikte frequentie. Een werkelijke
autorisatie zou nog steeds het afzonderlijke beoordelingsbesluit vereisen.

Conclusie: **structurele uitval bij plausibele aanvragen is aangetoond**. Hoe
vaak dit bij echte goedgekeurde atleten voorkomt, is onbekend zonder een
representatieve, privacygoedgekeurde contextset. Niet claimen dat alle 2/2/1-
weken werken of dat uitval zeldzaam is. De 250-case duurde lokaal circa 10,8 s;
een noderesultaat onder de cap garandeert dus geen acceptabele latency. Dat is
een directe domeinmeting, geen spawned-worker/HTTP/deadlinetest. De bestaande
8-seconden performancecorpusgrens en A9-worker/admission/cancellation blijven
ongewijzigd; die grens is niet als bestaande worker-timeout verondersteld.

### Concrete weken met echte V6-brontrainingen

Alle onderstaande frequentietoestemmingen zijn synthetisch. De training-ID's
en geselecteerde bronrevisies zijn werkelijk V6; dit zijn geen voorschriften
voor een echte atleet en geen nieuw akkoord op zwem-estimates of geschiktheid.

| Demonstratie | Daadwerkelijk geselecteerde workouts in de voorbeeldweek |
| --- | --- |
| BASE 2/2/1, grens 100; ook bij normale baseline 100,1 | Ma TR-BIKE-022; di TR-RUN-025; do TR-BIKE-023; vr TR-RUN-025; za TR-SWIM-022. De twee RUN-025 zijn verschillende occurrences. |
| BASE 2/2/1, grens 150 | Ma TR-BIKE-024; di TR-RUN-026; do TR-BIKE-026; vr TR-RUN-027; za TR-SWIM-002. |
| BASE 2/1/1, grens 300 | Ma TR-RUN-027; di TR-SWIM-003; do TR-BIKE-004; vr TR-RUN-003. Dit is een afzonderlijke aanvraag, geen automatisch verlaagde fallback voor het mislukte 2/2/1-geval. |
| BASE 2/2/2, grens 100 | Ma TR-BIKE-025; di TR-RUN-025; wo TR-SWIM-021; do TR-BIKE-022; vr TR-RUN-026; za TR-SWIM-021. |
| Beperkt budget 45, 2/2/1; bestaand bewijs | Ma TR-RUN-025; do TR-BIKE-023; vr TR-SWIM-021: drie sessies, gedeeltelijke vervulling. Bij grens nul volgt rust. |

De laatste rij komt uit het bestaande
[machinebewijs](../implementation/multi-session/examples.json) en
[selectorrapport](../implementation/JOREN_V6_MULTI_SESSION_SELECTOR.md), niet
uit de 15 nieuwe metingen. Het bestaande bewijs is reproduceerbaar met
`python -B -m benchmarks.v6_multi_session_evidence --private-output <nieuw-lokaal-bestand>`
vanuit `backend`. Voor de nieuwe meetmatrix zijn de volledige invoerparameters
hierboven vastgelegd; de lokale meetrunner en JSON staan alleen in genegeerde
`.runtime/frequency_review_probe.py` en `.runtime/frequency-review-probe.json`.
Geen broncode, testfixture of eerder bewijsbestand is daarvoor gewijzigd.

### Voorgestelde verbetering, apart technisch werk

Een optimalisatieonderzoek is gerechtvaardigd vóór brede real-athlete-vrijgave.
Aanbevolen volgorde:

1. Meet dezelfde aanvragen via de echte worker/HTTP-flow, inclusief beperkte
   beschikbaarheid, behouden/voltooide herhalingen, maximale templategebruiken,
   alle fasen en relevante sportcombinaties. Rapporteer ook sorteer-/geheugenkosten,
   wachtrijgedrag en het stadium van uitputting; geen private load in normale logs.
2. Onderzoek exacte branch-and-bound met bewezen optimistische grenzen op de
   **volledige bestaande rangtuple**, plus hergebruik van exacte load-/tijdgegevens.
   Sla een tak alleen over als geen completion de beste reeds volledig geplaatste
   geldige week kan verbeteren. Voor de allocatieratio zijn eerst geldige grenzen
   nodig; grotere belasting of minder losse HIGH-tijd bewijst geen dominantie.
3. Onderzoek lazy samenvoegen/rangschikken of exacte deelzoekruimten om niet alle
   contenders tegelijk te materialiseren. Een vroeg gevonden week is pas winnaar
   na uitputting of een sluitend certificaat dat geen betere plaatsbare week
   bestaat. Behoud template-identiteit, multipliciteit, vaste datums, occurrence-
   identiteit en planningsverschillen; geen ongefundeerde DP-state-merge.
4. Toets elke optimalisatie met onafhankelijke exhaustive-oracles en de bestaande
   regressies, Decimal-grenzen en schedulinggevallen. Behoud harde beperkingen,
   node-/memorybegrenzing, procesownership en annulering. Verhoog niet alleen
   deadlines of grenzen als vervanging voor bewijs en meting.

Bij uitputting blijft `v6_search_incomplete` zonder nieuwe opslag gelden. Geen
top-N-templatefilter, greedy winnaar, willekeurig incumbent, stil verlaagde wens
of bypass van veiligheid. Een door de atleet bewust verlaagde wens vormt een
nieuwe context; meld die keuze expliciet en geef haar geen claim van optimum
voor de eerdere wens. De bekende falende contexten zijn open releasegevallen,
geen reden om een onbewezen optimum te publiceren.

## 8. Alternatieven en afweging

| Optie | Voordeel | Nadeel / besluit |
| --- | --- | --- |
| **Aanbevolen: zachte wens + individueel beoordeeld weekmaximum** | Past op het bestaande contract; maximum en wens blijven onafhankelijk; geen onbewezen algemene drempels. | Beoordelaar en gecontroleerde registratie nodig per week; beperkte operationele schaal. |
| Alleen bestaande één-per-sport-standaard | Geen nieuwe frequentieautorisatie nodig; bruikbare fallback. | Maakt de geïmplementeerde multi-sessiecapaciteit niet voor extra sessies beschikbaar. Kies dit zolang de beoordelingsroute niet gereed is. |
| Later automatische, wetenschappelijk beoordeelde regel op werkelijke historie | Kan opschalen met herleidbare beslissingen. | Meetperiode, kwaliteit, grenzen en terugkeerregels ontbreken; afzonderlijke goedkeuring en implementatie vereist. |
| Wens zelf als maximum of maximum afleiden uit uren/TSS | Minder invoer-/reviewwerk. | Verwisselt intentie/budget met geschiktheid; afwijzen als productbeleid. |
| Universeel maximum per sport of ervaringscategorie | Eenvoudige configuratie. | Geen goedgekeurde onderbouwing; categorieën zijn uitgesloten. Geen getallen voorstellen alsof ze medisch gezag hebben. |

## 9. Minimaal integratieplan na besluit

1. Leg eigenaar-/Jorenbesluit met exacte documentversie, verantwoordelijke
   beoordelaar, operator en extern reviewrecord vast. Laat de eerste concrete
   maxima afzonderlijk goedkeuren; een akkoord op UI is geen frequentietoestemming.
2. Voeg de gescheiden voorkeur-/besluitopslag en smalle typed contracten toe,
   inclusief revisies, audit, exacte weekbinding en intrekking. Maak een
   forward-only migratie en RLS/grant-tests. Geen hergebruik van oude onboarding-
   frequentievelden of backfill van veronderstelde toestemming.
3. Voeg een server-side resolver toe aan bestaande services/repositories; laat
   de Python-domainselector uitsluitend gevalideerde `SessionFrequency` ontvangen.
   Leg voorkeur en toestemming afzonderlijk vast in actuele en frozen context.
   Houd FastAPI-routes dun; geen fysiologische logica in mobiel of LLM.
4. Sluit generatie, swipedraft, A5/check-in, pending vervanging, submit en atomic
   approval aan op actuele autorisatierevisies. Behoud CAS, receipts, rollback,
   stale rejection en fysieke activiteitkoppelingen. Pas alleen toekomstige
   records toe; historische snapshots blijven onder hun eigen versies leesbaar.
5. Voeg de kleine optionele profiel/onboardingkaart en kwalitatieve uitleg toe.
   Los de zoekruimtepoort op met apart bewezen technisch werk of houd de
   getroffen real-athlete-route gesloten. Daarna pas de reguliere V6-wiring en
   release afzonderlijk beoordelen; de loopback-testseam blijft beveiligd.

## 10. Test- en releasevoorwaarden

| Verificatie voor latere implementatie | Vereiste dekking |
| --- | --- |
| Domein-/resolvercontract | `null`, nul, wens onder/boven maximum, maximum zonder doel, verschillende sporten/weken, dubbele/ongeldige records, TEST_ONLY-afwijzing, verval, schorsing, intrekking, vervanging en onbekende beleidsversie. Geen afleiding uit uren/TSS. |
| Complete week | Behouden/voltooid telt eenmaal; boven zachte wens behouden, boven hard maximum conflict; ongeplande/onduidelijk gekoppelde activiteiten blokkeren uitbreiding tot beoordeling; templateherhalingen, capability, fase, injury/recovery/progression, sportcaps, exact budget en per-sport HIGH exact 20%/net erboven. Geen extra budget na meerdere sessies. |
| Lifecycle en concurrency | Hervatten na restart, voorkeurswijziging tijdens swipe, intrekking tijdens workerwerk/opslag/approval, aangescherpt maximum, geen uitbreiding van frozen verzoek, exact replay na verloren acknowledgement, stale CAS, A5-attachment en concurrente edits/moves. Een retry activeert geen ingetrokken plan. |
| Behoud van bewijs | Voltooide siblings/activiteit-FKs en meet-/berekenrecords bytegetrouw behouden bij verandering; onverenigbare correctieve schrijver blijft geblokkeerd. |
| Privacy en isolatie | OpenAPI/public-contracttests, recursieve TSS/private-load-lektests inclusief fouten/logging/accessibility; pgTAP/RLS/grants en twee echte GoTrue-accounts via volledige gateway, inclusief voorkeur, autorisatie, snapshot, edit en approval. |
| Mobiel | Strikte TypeScript, relevante Jest/controller-/transporttests; optioneel overslaan, wijzigen, nul/geen voorkeur, conflict, gedeeltelijke week en `search_incomplete` apart. Echte Android/iOS-tests voor onboarding, check-in, voorstelbevestiging, meerdere occurrences, herstart en accountwisseling. |
| Performance en regressie | De 15 meetcontexten, bekende falende aanvragen, onafhankelijke kleine-space-oracles, retained/date-constrained contexts en volledige historische corpuspariteit. Bewijs latency/memory/admission/cancellation met ongewijzigde afgesproken grenzen. Geen claims op basis van alleen een directe domeinmeting. |
| Projectchecks | Volledige backendtests, Ruff/format, strict mypy, relevante contract-/privacychecks, strict TypeScript/mobile en migratie-/pgTAP/RLS-checks vóór release. Niet-beschikbare omgevingen blijven expliciete open poorten. |

Ook na frequentiegoedkeuring blijven de onafhankelijke voorwaarden uit het
[laatste releaseregister](../implementation/JOREN_V6_REMAINING_RELEASE_GATES_NL.md)
staan: operationele acceptatie van geschatte zwemtijd, individueel duur-bewijs
waar vereist, officiële Planned IF²/Realized V2-fallbackcompatibiliteit,
bevoegde wetenschappelijke review, echte tokens/gateway, echte apparaten,
hosted migratie-/releaseautorisatie en aparte catalogusactivatie. Geen hiervan
wordt door een zachte sessiewens, een handmatig maximum of lokale tests vervangen.

### Verificatie van deze documenttaak

Dit is uitsluitend een voorstel plus read-only inspectie/lokale simulatie.
De bestaande `tests/test_v6_multi_session.py` is opnieuw uitgevoerd:
**51 geslaagd**, 3,34 s. Daarnaast zijn de 15 hierboven vermelde domeinmetingen
uitgevoerd. De eerdere 2.727 backendtests, 911 mobiele tests en 680 pgTAP-
asserties zijn **eerder gerapporteerd bewijs**, geen in deze taak herhaalde runs.
Volledige backend/mobile/database- en apparaattests zijn voor deze documentwijziging
niet opnieuw uitgevoerd; de toekomstige integratie- en releasepoorten blijven open.
Documentlinks en `git diff --check` zijn gecontroleerd.

Alleen dit nieuwe beslisdocument is als projectbestand toegevoegd; de meetrunner
en ruwe uitvoer staan lokaal genegeerd. Geen plannerimplementatie, bronnen,
fasetoewijzingen, historische berekeningen, migraties of publieke schema's
gewijzigd. Geen push, merge, deployment, productiegegevens, activatie of wijziging
aan beschermde A5/A6-worktrees.

## 11. Gelezen besluitbasis en implementatiereferenties

- Root `AGENTS.md`, mobiele `AGENTS.md` en
  [actuele MVP-roadmap](../../implementation/mvp-roadmap.md), in het bijzonder
  de actuele onboarding en de expliciete supersessie van oudere besluiten.
- [Phase 13 onboarding/baseline](../../requirements/phase-13-joren-ruleset-1.md),
  [open frequentievraag](../../requirements/workout-distribution-decision.md) en
  [goedgekeurde templateherhaling](../../requirements/joren-workout-selection-phase-2026-09-28.md).
- [Officiële TSS-acceptatie](../implementation/JOREN_V6_OFFICIAL_TSS_ACCEPTANCE.md),
  [automatische selectie](../implementation/JOREN_V6_AUTOMATIC_SELECTION_IMPLEMENTATION.md),
  [partial-week/no-HIGH-minimum-besluit](../implementation/JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md)
  en [precieze HIGH-supersessie](../implementation/JOREN_V6_NO_HIGH_MINIMUM_BUILD_POLICY.md).
  Hun latere opvolgers bepalen de actuele status; eerdere ‘nog niet goedgekeurd’-
  passages blijven historisch en heropenen geen inmiddels genomen besluit.
- Alle vijf gevraagde laatste rapporten:
  [beleid](../implementation/JOREN_V6_MULTI_SESSION_POLICY.md),
  [selector](../implementation/JOREN_V6_MULTI_SESSION_SELECTOR.md),
  [swipe/opslag](../implementation/JOREN_V6_MULTI_SESSION_SWIPE_AND_PERSISTENCE.md),
  [verificatie](../implementation/JOREN_V6_MULTI_SESSION_VERIFICATION.md) en
  [releasepoorten](../implementation/JOREN_V6_REMAINING_RELEASE_GATES_NL.md).
- Geïnspecteerde code: `v6_frequency.py`, `v6_search.py`, `v6_selection.py`,
  `v6_service.py`, `v6_repository.py`, `service.py`, `repository.py`, `execution.py`
  onder `backend/app/modules/planning`; `backend/app/local_v6.py`; de bestaande
  V6-persistence/lifecycle/membership-migraties; `OnboardingScreen.tsx`,
  `ProfileScreen.tsx` en de bestaande multi-sessiontests/benchmark.

## 12. Vijf concrete goedkeuringsvragen

1. **Eigenaar + Joren:** akkoord met optionele blijvende sessiewensen als zachte doelen, inclusief nul, afzonderlijk van een hard weekmaximum en planbevestiging?
2. **Joren:** akkoord met individueel beoordeelde maxima per exacte week en de bewijsvereisten uit §3; wie mag ze beoordelen?
3. **Eigenaar + Joren:** akkoord met de schorsing en herbevestiging na blessure, ziekte of gemelde onderbreking uit §5?
4. **Eigenaar:** akkoord met de minimale profiel/onboardingkaart uit §4 en gecontroleerde interne registratie; wie wordt de operator?
5. **Eigenaar + Joren:** akkoord dat echte multi-sessieplanning pas wordt vrijgegeven na bewezen afhandeling van de bekende zoekuitval én de overige bestaande releasepoorten?

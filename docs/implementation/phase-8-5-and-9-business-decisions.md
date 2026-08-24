# Fase 8.5 en fase 9: openstaande bedrijfsbeslissingen

Laatst bijgewerkt: 2026-08-24

Doelgroep: stakeholders van Start23 op het gebied van bedrijfsvoering, product,
klinische zaken/fysiologie, privacy, beveiliging en engineering.

## Samenvatting

De functionele kernen van fase 8.5 en fase 9 zijn geïmplementeerd. Op
2026-08-24 is ook `Voorstel Start23 Zone 1-5 rekenmodel v1.0` technisch
vastgelegd en geïmplementeerd als `start23-zone-model-1.0`. De oorspronkelijke
fase-8.5- en fase-9-migraties zijn toegepast en hun gehoste pgTAP-testsuites
slagen. De forward-only zone-modelmigratie is op dezelfde datum op de gekoppelde
database toegepast; de 19-assertion rollback-only pgTAP-suite slaagt en remote
error-level lint is schoon. Lokale database-uitvoering blijft geblokkeerd
doordat Docker en Podman in de ontwikkelomgeving ontbreken.

De gekwalificeerde fysiologische review en productieondertekening van de
actieve fysiologieregels en `start23-zone-model-1.0` zijn op 2026-08-24 door de
product owner als afgerond bevestigd. De identiteit en het bewijsdossier van de
beoordelaar worden in het externe product-governanceregister beheerd en niet in
de broncode gedupliceerd. Nieuwe of gewijzigde fysiologische regels blijven een
nieuwe review vereisen.

Het resterende werk bestaat voornamelijk uit productbeleid,
operationele keuzes en live verificatie. Het systeem faalt bewust gesloten
wanneer een klinische regel of productregel niet is goedgekeurd. Start23 kan nu
een volledig zone 1-5-voorstel berekenen, maar zet dit altijd in afwachting en
activeert het pas na een afzonderlijke bevestiging van de atleet. Start23
koppelt geïmporteerde activiteiten niet stilzwijgend en activeert de verwerking
door Polar niet voordat de relevante beslissingen zijn genomen.

De aanbevelingen in dit document zijn voorstellen ter bespreking, behalve
8.5-D1 en 8.5-D5: het model is technisch geïmplementeerd en de fysiologische
productiereview is afgerond.

## Wat al is besloten

- Geplande en gerealiseerde TSS blijven intern en worden nooit aan de mobiele
  applicatie teruggegeven.
- Fysiologische berekeningen blijven deterministische Python-regels; een LLM
  kan plannen of zones niet zelfstandig wijzigen.
- Wijzigingen aan drempelwaarden en zones blijven in afwachting totdat de
  atleet ze bevestigt.
- Een bevestigde veldtestdrempel en de daarop berekende zones zijn twee aparte
  beslissingen: drempelbevestiging maakt uitsluitend een nieuw zonevoorstel;
  zonebevestiging activeert dat voorstel pas daarna.
- Het Zone 1-5-rekenmodel is geversioneerd als `start23-zone-model-1.0` en
  gebruikt canonieke hele watt-, bpm- en secondengrenzen met één afronding
  volgens `ROUND_HALF_UP`.
- De feedbackschaal voor kalibratie is de canonieke sessie-RPE van 1 tot en
  met 10.
- Submaximale kalibratie kan bruikbare observaties verzamelen, maar kan geen
  drempelwaarde fabriceren.
- Polar is voorlopig de eerste wearable-adapter, maar is niet goedgekeurd als
  verwerker voor productie.
- Inloggegevens en tokens van providers blijven uitsluitend in de backend.
- Redis, Celery, microservices en een tweede workerservice vallen buiten de
  MVP.

## Fase 8.5: zone-invoer, veldtesten en kalibratie in week 1

### 8.5-D1 — Zone 1-5-rekenmodel v1.0 vastgesteld en geïmplementeerd

**Besluit en status:** `Voorstel Start23 Zone 1-5 rekenmodel v1.0` is op
2026-08-24 technisch vastgesteld als `start23-zone-model-1.0`. De berekening is
deterministische Python-code; de database bewaart de kandidaten, versie en
herkomst, maar berekent de fysiologische grenzen niet zelf.

**Vastgelegde conversies:**

- Fietsvermogen uit FTP: Z1 `<56%`, Z2 `56–<76%`, Z3 `76–<91%`, Z4
  `91–<106%`, Z5 `>=106%`. Waarden boven `120%` FTP krijgen daarnaast het
  kenmerk `supramaximal`; dit maakt geen zesde zone.
- Fietsdrempelhartslag en hardloop-LTHR: Z1 `<85%`, Z2 `85–<90%`, Z3
  `90–<95%`, Z4 `95–<103%`, Z5 `>=103%`.
- Hardloopdrempeltempo en zwem-CSS worden eerst als snelheid geïnterpreteerd:
  Z1 `<78%`, Z2 `78–<88%`, Z3 `88–<95%`, Z4 `95–<102%`, Z5 `>=102%` van de
  drempelsnelheid. In opgeslagen seconden betekent een lagere waarde een
  hogere intensiteit.
- Bereken eerst met volledige precisie en rond iedere canonieke grens precies
  één keer af op hele watt, bpm of seconde met `ROUND_HALF_UP`. Een exact
  gedeelde grens hoort bij de zone met de hogere intensiteit. De buitenrand van
  Z1 of Z5 blijft open waar het model geen fysiek maximum definieert.

**Profielen en herkomst:** Fietsvermogen is primair boven fietshartslag;
hardlooptempo is primair boven hardloophartslag; zwem-CSS is primair. Eén
disciplineprofiel mag een primaire en secundaire metriek bewaren. Minimaal
worden bronmetriek en -waarde, bronmethode en -kwaliteit, model- en
bewijsversie, berekentijdstip, reviewstatus/-actor/-tijd en de gekoppelde
kalibratie-evaluatie opgeslagen. Eerdere actieve versies blijven onveranderlijk
en worden alleen bij bevestiging opgevolgd. Bij zwemmen blijft RPE een
secundaire uitvoerings- en contextindicator; v1.0 definieert geen numerieke
RPE-naar-zonegrenzen, zodat engineering die niet afleidt of verzint.

**Bevestigingscontract:** Een bekende, door de atleet bevestigde drempel maakt
een berekend zonevoorstel. Bij een veldtest bevestigt of verwerpt de atleet
eerst de drempel. Bevestigen maakt daarna een nog steeds `pending` zoneversie;
pas de bestaande stale-safe zonegoedkeuring maakt deze actief. Afwijzen van de
drempel maakt geen zoneprofiel. Geen van deze routes geeft geplande of
gerealiseerde TSS aan de mobiele applicatie door.

**Resterende verificatie:** De fysiologische ondertekening onder 8.5-D5,
gekoppelde migratie en rollback-only pgTAP-suite zijn afgerond. Twee echte
Supabase-sessies en mobiele builds moeten nog in de doelomgevingen worden
geverifieerd.

### 8.5-D2 — Kalibratiesessies integreren in de normale planner voor week 1

**Benodigde beslissing:** Definieer een zone-onafhankelijk contract voor
segmenten van geplande trainingen en een goedgekeurde interne belastingsregel
voor kalibratieprotocollen.

**Waarom dit belangrijk is:** De bestaande normale planner verwacht doelen in
zone 1-5. De goedgekeurde kalibratiefixtures gebruiken in plaats daarvan
protocolinstructies en RPE, waardoor ze momenteel als expliciete zelfstandige
sessies worden uitgevoerd.

**Gebruikssituatie:** Een nieuwe wielrenner kent zijn FTP niet. In week 1 moet
een veilige kalibratietraining worden gepland zonder vermogenszones te
verzinnen, TSS vrij te geven of te doen alsof de training een normale
zonegebaseerde catalogussessie is.

**Aanbevolen richting:** Voeg een afzonderlijk segmenttype voor protocoldoelen
toe met beoordeelde RPE-/instructiedoelen. Houd de belastingsberekening privé en
voeg het segment pas aan de normale planning toe nadat de belastingsregel is
beoordeeld.

### 8.5-D3 — Beslissen of zachte plausibiliteitswaarschuwingen worden ingesteld

**Benodigde beslissing:** Beslis of de MVP op bewijs gebaseerde zachte bereiken
voor handmatig ingevoerde drempelwaarden en zones nodig heeft. Keur, als dat zo
is, de waarden, bronnen, beoordelaar en versie goed.

**Waarom dit belangrijk is:** Structureel geldige waarden worden momenteel
geaccepteerd met `soft_range_not_configured`. Ze worden niet afgewezen enkel
omdat er geen goedgekeurd plausibiliteitsbereik bestaat.

**Gebruikssituatie:** Een atleet voert een FTP van 600 watt in. De waarde is
technisch geldig, maar Start23 kan zonder een goedgekeurd bereik dat bij de
atleet en discipline past niet aangeven of deze ongebruikelijk of waarschijnlijk
verkeerd ingevoerd is.

**Aanbevolen richting:** Laat de waarschuwing ongeconfigureerd totdat er bewijs
en duidelijk eigenaarschap van de beoordeling bestaan. Zet een zachte
waarschuwing nooit om in een automatische afwijzing.

### 8.5-D4 — Beslissen of de HR-terugvaloptie op basis van fysiologisch geslacht wordt toegevoegd

**Benodigde beslissing:** Beslis of de optionele terugvalmethode voor de
maximale hartslag waardevol genoeg is voor de MVP om het verzamelen van een
afzonderlijk gevoelig veld voor fysiologisch geslacht te rechtvaardigen. Keur
bij opname de formules, toestemmingstekst, privacybehandeling, regelset en
voorwaartse migratie goed.

**Waarom dit belangrijk is:** Het huidige profiel verzamelt dit veld niet.
Genderidentiteit mag niet als vervanging worden gebruikt en de voorgestelde
terugvalmethode is geen FTP-schatter.

**Gebruikssituatie:** Een atleet heeft geen gemeten hardloopdrempel en vraagt om
begeleiding op basis van hartslag. Start23 mag de fysiologie niet stilzwijgend
afleiden en geen geslachtsspecifieke formule toepassen zonder expliciete invoer
van de atleet en beoordeelde regels.

**Aanbevolen richting:** Stel deze optionele terugvalmethode voor de MVP uit,
tenzij onderzoek en klantvalidatie een duidelijk voordeel ten opzichte van
uitsluitend RPE-begeleiding aantonen.

### 8.5-D5 — De verantwoordelijke fysiologische beoordelaar aanstellen

**Besluit en status:** afgerond op 2026-08-24. De product owner heeft bevestigd
dat de gekwalificeerde fysiologische beoordelaar de actieve regels en
`start23-zone-model-1.0` voor productie heeft beoordeeld en ondertekend. De
persoons- en dossiergegevens blijven in het externe governanceregister; iedere
inhoudelijke ruleset- of modelwijziging opent opnieuw een reviewpoort.

**Waarom dit belangrijk is:** Geautomatiseerde tests bewijzen dat code met een
regel overeenkomt; ze bewijzen niet dat de fysiologische regel zelf klinisch
geschikt is.

**Controle:** Geautomatiseerde tests blijven alleen de implementatie bewijzen;
de nu vastgelegde menselijke review geldt uitsluitend voor de daarbij
beoordeelde versies.

## Vervroegde fase-10-levering: AI-uitleg bij weekschema's

Op 2026-08-24 is een afgebakend deel van de latere fase 10 vervroegd
geïmplementeerd. De bestaande deterministische planner maakt nog altijd het
weekschema en slaat dit als `pending` voorstel op. Daarna kan de backend via de
OpenAI Responses API een korte Nederlandstalige coachuitleg genereren uit een
gesloten Pydantic-schema met alleen week, tijdzone, fase, openbare
trainingsnamen, discipline, tijdstip, duur, kwalitatieve intensiteit en
rustdagen. Geplande/gerealiseerde TSS, interne belastingswaarden, vrije
atleetstekst en mutatietools worden niet meegestuurd.

De response gebruikt een strikt JSON-schema, `store: false`, een server-only
API-sleutel en een begrensde timeout. Weigering, ongeldige output,
provideruitval of een ontbrekende sleutel levert een deterministische lokale
uitleg op. Alleen de uitleg van een nog openstaand planvoorstel kan via een
service-only RPC eenmaal worden ingevuld; de AI kan geen workout, datum, zone,
planstatus of goedkeuring wijzigen. De mobiele planningsweergave toont deze
uitleg naast de bestaande expliciete knoppen voor goedkeuren en afwijzen. De
niet-persoonlijke live provider-smoketest is op 2026-08-24 geslaagd met
`gpt-5.6-luna` en `store: false`. De gekoppelde migratie, remote error-level
lint, rollback-only pgTAP-suite en RPC-rechtencontrole zijn eveneens afgerond.
Goedkeuring van DPA, regio en bewaarbeleid blijft een productiepoort voor deze
AI-laag. Voor een volledige lokale FastAPI-E2E-test moet daarnaast nog
`START23_SUPABASE_SECRET_KEY` in de backendomgeving worden geconfigureerd.

### 8.5-D6 — De strategie voor mobiele dependency-advisories kiezen

**Benodigde beslissing:** Blijf compatibele patches voor Expo SDK 57 volgen of
financier een afzonderlijk beoordeelde SDK-upgrade. Gebruik de momenteel
voorgestelde geforceerde auditfix niet, omdat deze de vastgelegde versies van
Expo en React Native doorkruist.

**Waarom dit belangrijk is:** Expo Doctor slaagt momenteel voor 20 van 21
controles. Het verwacht nieuwere compatibele patches voor `expo` (`~57.0.16`),
`expo-dev-client` (`~57.0.15`) en `expo-splash-screen` (`~57.0.8`) dan de nu
vastgelegde versies. De laatste audit rapporteerde daarnaast 8 bevindingen met
gemiddelde ernst en 11 bevindingen met hoge ernst in upstream/transitieve
afhankelijkheden, zonder kritieke bevindingen.

**Gebruikssituatie:** Een releasechecklist vereist een heldere beslissing over
afhankelijkheden. De automatische geforceerde fix zou de werkende SDK-stack
downgraden of anderszins breken. De organisatie moet daarom de gemonitorde
blootstelling tijdelijk accepteren of een upgradeproject goedkeuren.

**Aanbevolen richting:** Leg een tijdgebonden risicoacceptatie vast, monitor
compatibele patches en beoordeel dit bij iedere release opnieuw. Escaleer
onmiddellijk als een bevinding kritiek wordt of aantoonbaar invloed heeft op
het uitgeleverde runtimepad.

### 8.5-G1 — Verificatie met echte sessies en apparaten voltooien

**Resterende poort:** Test twee echt geauthenticeerde atleten en Android- en
iOS-developmentbuilds tijdens zone-instelling, protocoluitvoering, RPE-invoer,
evaluatie, onderbreking en hervatting.

**Gebruikssituatie:** Atleet B meldt zich aan nadat atleet A een kalibratietest
heeft voltooid. Atleet B mag niets zien van de instellingen, observaties of het
resultaat in afwachting van atleet A. Een onderbroken mobiele flow moet tevens
kunnen worden hervat zonder dubbele records.

**Aanbevolen richting:** Behandel dit als een releasepoort en niet als een
optionele QA-taak. Gebruik echte Supabase-sessies en voer per ondersteund mobiel
platform ten minste één test op een fysiek apparaat uit.

## Fase 9: eerste wearable-integratie

### 9-D1 — Een go/no-go-beslissing voor productie met Polar nemen

**Benodigde beslissing:** Keur Polar AccessLink goed als eerste provider voor
productie, of stop en selecteer een andere provider na beoordeling door
product, juridische zaken, privacy en commercie en na toetsing van de
voorwaarden van de provider.

**Waarom dit belangrijk is:** De adapter is technisch geïmplementeerd, maar er
zijn geen echte client, webhook, inloggegevens of atleetverbinding aanwezig en
er is geen verwerking door de provider actief.

**Gebruikssituatie:** Een triatleet geeft Start23 toestemming om GPS- en
hartslaggegevens te ontvangen. Start23 heeft een goedgekeurde relatie met de
verwerker en een rechtmatig doel nodig voordat deze gezondheids- en
locatiegegevens worden verwerkt.

**Aanbevolen richting:** Houd de connector uitgeschakeld totdat één
gedocumenteerde go/no-go-beoordeling de providervoorwaarden, commerciële
geschiktheid, ondersteunde regio's, gegevenscategorieën en uitstaprisico's
omvat.

### 9-D2 — Beleid voor toestemming, bewaartermijnen, verwijdering en regionale verwerking goedkeuren

**Benodigde beslissing:** Keur de toestemmingstekst voor atleten en de regels
voor ruwe bestanden, canonieke samenvattingen, ontkoppeling,
verwijderings-/exportverzoeken, regionale verwerking en merkvermelding van de
provider goed.

**Waarom dit belangrijk is:** Een account ontkoppelen, een providertoken
verwijderen en reeds geïmporteerde gezondheids- en locatiegegevens verwijderen
zijn verschillende handelingen.

**Gebruikssituatie:** Een atleet ontkoppelt Polar en vraagt Start23 vervolgens
om alle geïmporteerde FIT-bestanden te verwijderen, maar wil handmatig
ingevoerde trainingshistorie behouden. Product en support hebben hiervoor
eenduidig beleid nodig.

**Aanbevolen richting:** Definieer vóór livegebruik een gegevensinventaris en
bewaartermijnentabel. Maak onderscheid tussen accountontkoppeling en
gegevensverwijdering en maak beide keuzes begrijpelijk in de mobiele UI.

### 9-D3 — Het callbackdomein voor productie kiezen en de integratie registreren

**Benodigde beslissing:** Kies het OAuth-callbackdomein voor productie,
registreer de Polar-client en webhook, sla inloggegevens op in de
deploymentvariabelen van de backend en leg het eigenaarschap van
inloggegevensrotatie vast.

**Waarom dit belangrijk is:** OAuth kan niet end-to-end met productiegedrag
worden getest totdat de redirect- en webhookendpoints bij de provider zijn
geregistreerd.

**Gebruikssituatie:** Een atleet tikt op **Polar koppelen**, keurt de toegang in
de browser goed en moet terugkeren naar een goedgekeurde Start23-callback in
plaats van naar een ontwikkelaars-URL.

**Aanbevolen richting:** Gebruik het definitieve HTTPS-domein van de backend,
houd ieder geheim uitsluitend aan de serverzijde en wijs één operationele
eigenaar aan voor registratie en rotatie.

### 9-D4 — De ervaring rond historische import goedkeuren

**Benodigde beslissing:** Bepaal de standaardwaarde en uitleg voor de atleet
binnen het geïmplementeerde aanvraagbereik van 1 tot en met 30 dagen. Bepaal hoe
wordt gecommuniceerd dat oudere backfill via deze adapter niet beschikbaar is.

**Waarom dit belangrijk is:** De implementatie handhaaft de limiet van de
provider voor recente historie en verzint geen ouder archief.

**Gebruikssituatie:** Een nieuwe gebruiker verwacht zes maanden Polar-historie.
Start23 kan alleen de ondersteunde recente periode importeren en mag niet de
indruk wekken dat de oudere historie later nog binnenkomt.

**Aanbevolen richting:** Laat de atleet een ondersteund bereik selecteren,
vermeld de limiet vóór bevestiging en kies niet stilzwijgend voor maximale
gegevensverzameling totdat de privacybeoordeling dit goedkeurt.

### 9-D5 — De herstelprocedure voor mislukte imports kiezen

**Benodigde beslissing:** Kies een geïmplementeerd retrymechanisme, het aantal
nieuwe pogingen/de back-off, een definitieve foutstatus, alarmering en het
eigenaarschap van support.

**Waarom dit belangrijk is:** Webhookwerk wordt vóór verwerking veilig
opgeslagen en een fout wordt vastgelegd, maar er is momenteel geen
productieschema dat mislukt werk opnieuw oppakt.

**Gebruikssituatie:** Polar accepteert de webhook, maar geeft HTTP 503 terug
wanneer Start23 de training ophaalt. De atleet zou de verbinding niet hoeven te
verbreken en opnieuw te leggen om de activiteit te herstellen.

**Aanbevolen richting:** Gebruik één begrensde geplande Railway-opdracht tegen
de bestaande modulaire monoliet, met back-off, een definitieve status en een
alarm. Introduceer voor de MVP geen Redis, Celery of andere service.

### 9-D6 — Gedrag bij ingetrokken tokens en opnieuw verbinden definiëren

**Benodigde beslissing:** Bepaal hoe ingetrokken of ongeldige langlevende
Polar-toegang wordt gedetecteerd, weergegeven, opnieuw geprobeerd en opnieuw
verbonden, terwijl geldige bestaande activiteiten behouden blijven.

**Waarom dit belangrijk is:** Het geïmplementeerde Polar-model gebruikt een
langlevend toegangstoken tot uitschrijving, en geen verzonnen flow voor het
verversen van tokens.

**Gebruikssituatie:** De atleet trekt de toegang van Start23 in via het
Polar-accountdashboard. De volgende import moet **Opnieuw verbinden vereist**
tonen en mag niet herhaaldelijk mislukken of eerder geïmporteerde canonieke
activiteiten verwijderen.

**Aanbevolen richting:** Behoud bestaande activiteiten, markeer de verbinding
als ingetrokken/opnieuw-verbinden-vereist, verwijder onbruikbare inloggegevens
veilig en vereis een nieuwe expliciete OAuth-bevestiging.

### 9-D7 — De minimale mobiele connectorervaring goedkeuren

**Benodigde beslissing:** Definieer de kleinste productie-UI voor verbinden,
verbindingsstatus, importbereik, voortgang, fout/hernieuwde poging,
ontkoppeling en privacylinks.

**Waarom dit belangrijk is:** De backend-API's bestaan, maar er is geen
verbindings- of importscherm voor fase 9 aan Expo toegevoegd.

**Gebruikssituatie:** Een import mislukt nadat drie activiteiten zijn ontdekt.
De atleet moet begrijpen of er iets is geïmporteerd, of opnieuw proberen veilig
is en of Polar nog steeds gekoppeld is.

**Aanbevolen richting:** Bouw na goedkeuring van de provider één klein scherm
voor instellingen/integraties. Toon kwalitatieve status en aantallen, maar
nooit TSS.

### 9-D8 — De productscope van ruwe FIT-bestanden bepalen

**Benodigde beslissing:** Beslis of ruwe FIT-bestanden voor de MVP uitsluitend
backendarchieven blijven of dat ondertekende downloads, zichtbaar
bestandsbeheer voor atleten en een UI voor bewaren/verwijderen nodig zijn.

**Waarom dit belangrijk is:** FIT-bestanden worden, wanneer beschikbaar, privé
opgeslagen. Een ontbrekend FIT-bestand maakt de canonieke
activiteitssamenvatting echter niet ongeldig. Er bestaat geen download-API of
UI voor ruwe bestanden.

**Gebruikssituatie:** Een atleet vraagt om het oorspronkelijke FIT-bestand voor
gebruik in een andere dienst. Start23 heeft een veilige exportflow nodig of
moet duidelijk aangeven dat downloads van ruwe bestanden niet tot de MVP
behoren.

**Aanbevolen richting:** Houd ruwe bestanden voor de MVP uitsluitend in de
backend, tenzij vereisten voor gegevensportabiliteit downloads noodzakelijk
maken. Regels voor bewaartermijnen en verwijdering zijn ook vereist als er geen
download voor atleten wordt gebouwd.

### 9-D9 — Het beleid voor koppeling van geïmporteerde activiteiten goedkeuren

**Benodigde beslissing:** Beslis of wearable-activiteiten expliciet
ongekoppeld blijven, aan de atleet worden voorgesteld of onder strikte
deterministische regels automatisch mogen worden gekoppeld.

**Waarom dit belangrijk is:** Er bestaat geen beoordeelde regel voor koppeling
op basis van nabijheid, bricktrainingen, multisportsessies of dubbelzinnige
trainingen binnen dezelfde discipline. Huidige Polar-imports komen daarom als
ongekoppeld in het canonieke activiteitspad terecht.

**Gebruikssituatie:** Een Polar-hardloopactiviteit begint 20 minuten na een
geplande hardlooptraining en heeft een vergelijkbare duur. Start23 moet bepalen
of die training als suggestie wordt getoond of handmatige selectie vereist is;
het stilzwijgend koppelen van de verkeerde training zou de feedback
beschadigen.

**Aanbevolen richting:** Begin met alleen suggesties en expliciete bevestiging
door de atleet. Automatische koppeling moet een afzonderlijke beoordeelde
regeltabel met tests voor dubbelzinnigheid vereisen.

### 9-D10 — De geauthenticeerde grens voor geprivilegieerde RPC's accepteren of refactoren

**Benodigde beslissing:** Beveiliging moet het huidige eigenaarsgebonden
`SECURITY DEFINER`-ontwerp formeel accepteren of om een refactor vragen, met
name voor de alleen-lezen-RPC's voor verbindingen en importlijsten.

**Waarom dit belangrijk is:** Supabase Security Advisor meldt waarschuwingen
voor `start_polar_oauth`, `get_polar_connection` en `list_polar_imports`.
Uitvoering door `public` en `anon` is ingetrokken, iedere handeling leidt
`auth.uid()` af en gehoste eigendomstests slagen, maar de waarschuwing vereist
nog steeds een expliciete uitkomst van de beoordeling.

**Gebruikssituatie:** Een aangemelde aanvaller wijzigt aanvraagparameters in
een poging de importhistorie van een andere atleet op te vragen. De beoordeling
moet bewijzen dat de identiteit uit de geverifieerde sessie wordt afgeleid en
niet door de aanroeper kan worden geselecteerd.

**Aanbevolen richting:** Refactor de alleen-lezen-RPC's naar invoker-/RLS-paden
als dit privileges vermindert zonder het contract ingewikkelder te maken.
Behoud alleen waar de private OAuth-status dit vereist een nauw begrensde en
beoordeelde geprivilegieerde schrijfgrens.

### 9-D11 — Bescherming tegen gelekte wachtwoorden inschakelen

**Benodigde beslissing:** Beslis wanneer de bescherming van Supabase Auth tegen
gelekte wachtwoorden wordt ingeschakeld en werk waar nodig de authenticatie- en
supportteksten bij.

**Waarom dit belangrijk is:** Security Advisor meldt op projectniveau nog
steeds dat deze bescherming is uitgeschakeld. Dit is een gezamenlijke
beveiligingspoort voor productie die tijdens de beoordeling van fase 9 is
ontdekt.

**Gebruikssituatie:** Een klant probeert zich te registreren met een wachtwoord
dat al voorkomt in een bekend openbaar datalek. Zonder deze instelling mist
Start23 een beschikbare beveiligingsmaatregel die dat wachtwoord kan
afwijzen.

**Aanbevolen richting:** Schakel de bescherming vóór productie in, tenzij
producttests een concreet onboardingprobleem aantonen dat niet met duidelijke
communicatie kan worden opgelost.

### 9-G1 — Live end-to-endverificatie van de integratie voltooien

**Resterende poort:** Verifieer echte OAuth, aflevering en replayafhandeling van
webhooks, historische import, FIT-overdracht, eigendomsisolatie tussen twee
sessies, achtergronduitvoering op Railway, ontkoppeling/intrekking en
runtimegedrag op Android en iOS.

**Gebruikssituatie:** Een echte Polar-training moet precies één canonieke
activiteit aanmaken die uitsluitend voor de eigenaar zichtbaar is, privé
blijven voor een tweede atleet, herstellen van een tijdelijke providerfout en
na bevestigde ontkoppeling geen actief token behouden.

**Aanbevolen richting:** Voer dit pas uit na de go/no-go-beslissingen over de
provider en privacy, met speciaal daarvoor bestemde testatleten en een
schriftelijke checklist voor bewijsvoering.

## Aanbevolen beslisvolgorde

1. Keur het contract voor de zone-onafhankelijke kalibratieplanner goed.
2. Beslis of zachte bereiken en de terugvaloptie op basis van fysiologisch
   geslacht tot de MVP behoren.
3. Neem een go/no-go-beslissing voor productie over Polar en het bijbehorende
   gegevensverwerkingspakket.
4. Keur regels goed voor toestemming, bewaartermijnen, verwijdering,
   historische import en koppeling.
5. Leg het callbackdomein, de retryprocedure, het gedrag bij opnieuw verbinden
   en de minimale mobiele UI vast.
6. Rond de beveiligingsbeslissingen en liveverificatie met twee
   atleten/apparaten af.

## Checklist voor besluitvorming en ondertekening

- [x] Aangewezen fysiologische beoordelaar aangesteld; afronding door de
      product owner bevestigd op 2026-08-24.
- [x] Formules, grensbezit, inverse-tempoafhandeling en afronding voor Zone 1-5
      technisch vastgelegd en geïmplementeerd als `start23-zone-model-1.0`.
- [x] Productieondertekening van het zone-model door de aangewezen
      fysiologische beoordelaar vastgelegd.
- [ ] Planner-/belastingscontract voor kalibratie in week 1 goedgekeurd.
- [ ] Scope van zachte bereiken en terugval op basis van fysiologisch geslacht
      vastgesteld.
- [ ] Risico van mobiele afhankelijkheden geaccepteerd of upgrade gefinancierd.
- [ ] Polar als productieprovider goedgekeurd of afgewezen.
- [ ] Beleid voor toestemming, bewaartermijnen, verwijdering, regionale
      verwerking en attributie goedgekeurd.
- [ ] Eigenaar voor productiecallback, inloggegevens, webhook en rotatie
      toegewezen.
- [ ] Beleid voor historische import, retry, opnieuw verbinden, ruwe FIT en
      koppeling goedgekeurd.
- [ ] Beoordeling van geprivilegieerde RPC's en instelling voor gelekte
      wachtwoorden afgerond.
- [ ] Bewijs voor echte sessies, gehoste integratie, Android en iOS geaccepteerd.

## Referenties

- [MVP-roadmap](mvp-roadmap.md)
- [Backend-zoneberekening en kalibratie](backend-zone-calculation.md)
- [Voorstel Start23 Zone 1-5 rekenmodel v1.0](Voorstel%20Start23%20Zone%201%E2%80%935%20rekenmodel%20v1.0.pdf)
- [API-contracten](../architecture/api-contracts.md)
- [Beveiligingsmodel](../architecture/security-model.md)
- [Workflow voor Supabase-databasemigraties](https://supabase.com/docs/guides/deployment/database-migrations)
- [Wijziging in expliciete toekenning voor de Supabase Data API](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)
- [Supabase-changelog met belangrijke wijzigingen](https://supabase.com/changelog?types=breaking-change)

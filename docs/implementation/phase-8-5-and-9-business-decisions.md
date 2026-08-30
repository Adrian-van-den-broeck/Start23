# Fase 8.5 en fase 9: vastgelegde bedrijfsbeslissingen

Laatst bijgewerkt: 2026-08-26

Doelgroep: stakeholders van Start23 op het gebied van bedrijfsvoering, product,
fysiologie, privacy, beveiliging en engineering.

## Samenvatting

De besluiten 8.5-D2 tot en met 8.5-D6, 8.5-G1 en 9-D1 tot en met
9-D11 en 9-G1 zijn op 2026-08-26 vastgelegd. De in software uitvoerbare delen
zijn geïmplementeerd in de bestaande Expo/FastAPI/Supabase-monoliet. Besluiten
die menselijke goedkeuring, een dashboardinstelling, providerregistratie of
testen met echte personen en apparaten vereisen, blijven expliciete
productiepoorten en worden niet door een codewijziging als voltooid beschouwd.

De belangrijkste uitkomsten zijn:

- week-1-kalibratie past zonder verzonnen zones in de normale planner via een
  exclusieve keuze tussen `zone_target` en `protocol_target`;
- zachte plausibiliteitsbereiken en een HR-fallback op basis van fysiologisch
  geslacht vallen niet in de MVP;
- één gekwalificeerde fysiologische eindverantwoordelijke en echte
  apparaat-/sessietests zijn harde productiepoorten;
- Polar blijft voorwaardelijk de eerste provider, maar kan in productie niet
  starten zonder juridische, privacy- en provider-termsgoedkeuring;
- de mobiele Polar-flow is klein, toont geen TSS en laat koppeling van een
  activiteit alleen na expliciete bevestiging toe;
- imports gebruiken een begrensde retryopdracht in de Railway-monoliet en
  ingetrokken credentials leiden tot `reconnect_required`;
- alleen-lezen Polar-RPC's gebruiken invokerrechten/RLS waar mogelijk;
- Supabase-bescherming tegen gelekte wachtwoorden en de Polar-E2E met twee echte
  gebruikers blijven open releasepoorten.

## Reeds geldende uitgangspunten

- Geplande en gerealiseerde TSS blijven intern en worden nooit aan de mobiele
  applicatie teruggegeven.
- Fysiologische berekeningen blijven deterministische Python-regels. Een LLM
  kan plannen, drempels of zones niet zelfstandig wijzigen.
- Kritieke wijzigingen worden eerst als `pending` opgeslagen en pas na een
  afzonderlijke bevestiging van de atleet toegepast.
- Het Zone 1-5-model is geversioneerd als `start23-zone-model-1.0`.
- De feedbackschaal voor kalibratie is sessie-RPE 1–10.
- Providercredentials en -secrets blijven uitsluitend in de backend.
- Redis, Celery, microservices en een tweede workerservice vallen buiten de
  MVP.

## Fase 8.5: zone-invoer, veldtesten en kalibratie

### 8.5-D1 — Zone 1-5-rekenmodel

**Status:** eerder vastgesteld en geïmplementeerd als
`start23-zone-model-1.0`. De bestaande deterministische conversies,
afrondingsregels, provenance en dubbele bevestigingscyclus blijven ongewijzigd.
Dit besluit geeft geen toestemming om fysiologische regels zonder review te
wijzigen.

### 8.5-D2 — Kalibratie in week 1

**Besluit:** goedgekeurd. Een gepland segment heeft precies één doel:
`zone_target` of `protocol_target`. Een kalibratietest gebruikt
`protocol_target` en krijgt nooit een kunstmatige Zone 1-5 toegewezen.

**Contract:** een `protocol_target` bevat een versieerbaar `protocol_id`, een
`segment_id`, het beoordeelde minimum en maximum voor RPE, een expliciete
kwalitatieve intensiteitscategorie (`low` of `high`) en de aanduiding of het
segment optioneel is. De kwalitatieve categorie is nodig voor de bestaande
deterministische planner; deze is geen verborgen zoneconversie. Beide
doeltypen tegelijk, of geen van beide, is ongeldig. Publieke segmenten bevatten
geen TSS of interne belastingswaarde.

**Implementatie:** de workoutcatalogus, planner, API-modellen, mobiele typen en
databaseopslag ondersteunen deze tagged union. Als de fietssetup nog
`test_pending` of `calibration_pending` is, kan de planner de beoordeelde
`start23_week1_bike_calibration_v1` als normale week-1-catalogussessie kiezen.
De catalogusentry gebruikt uitsluitend de goedgekeurde protocolsegmenten en
RPE-doelen. Het bestaande interne planningsmodel mag de expliciete
intensiteitscategorie gebruiken, maar retourneert de interne belasting nooit
aan de mobiele app.

Nieuwe protocoltemplates mogen alleen worden toegevoegd wanneer duur,
segmenten, RPE en intensiteitsclassificatie inhoudelijk zijn beoordeeld. Voor
de bestaande afstandgestuurde zwemfixture is geen planningsduur verzonnen; die
blijft buiten normale selectie totdat zo'n beoordeelde duur bestaat.

### 8.5-D3 — Plausibiliteitswaarschuwingen

**Besluit:** uitgesteld tot na de MVP. `soft_range_not_configured` blijft de
canonieke uitkomst wanneer geen goedgekeurd zacht bereik bestaat. Een
structureel geldige invoer wordt nooit automatisch geweigerd uitsluitend
omdat deze ongewoon lijkt.

**Gevolg:** er komen nu geen grenswaarden, waarschuwingsteksten of
atleetsegmentatie bij. Een toekomstige waarschuwing vereist bewijsbron,
versie, eigenaar, fysiologische review en tests die aantonen dat de melding
zacht blijft. Structurele validatie van type, eenheid en positieve waarde
blijft wel gelden.

### 8.5-D4 — HR-fallback op basis van fysiologisch geslacht

**Besluit:** uitgesteld tot na de MVP. De beperkte verwachte meerwaarde
rechtvaardigt het verzamelen van dit extra gevoelige gegeven niet.

**Gevolg:** profiel, onboarding, database en API krijgen geen veld voor
fysiologisch geslacht en er wordt geen geslachtsspecifieke formule toegepast.
Start23 leidt fysiologisch geslacht ook niet af uit genderidentiteit of andere
gegevens. De bestaande niet-geslachtsspecifieke, als fallback gemarkeerde
methoden en RPE-begeleiding blijven beschikbaar binnen hun huidige
beperkingen.

### 8.5-D5 — Fysiologisch reviewer

**Besluit:** vóór productie is één gekwalificeerde fysiologische
eindverantwoordelijke verplicht. De reviewer moet de exact actieve ruleset,
het zone-model en iedere nieuwe protocoltemplate aan een extern bewaard
reviewrecord koppelen. Materiële wijzigingen openen de poort opnieuw.

**Productiepoort:** productieconfiguratie vereist een reviewrecord-id en een
verantwoordelijke eigenaar. De naam en kwalificatie zijn in deze beslissing
niet aangeleverd en worden niet in broncode verzonnen; het externe
governanceregister blijft de bron van waarheid. Een eerdere algemene
product-ownerbevestiging vervangt dit aantoonbare eindverantwoordelijke record
niet. Totdat dit record is ingevuld en geaccepteerd, blijft deze poort open.

### 8.5-D6 — Dependency-advisories

**Besluit:** tijdelijke risicoacceptatie voor de MVP. Er wordt geen geforceerde
`npm audit fix` uitgevoerd wanneer die Expo of React Native buiten de
ondersteunde SDK-combinatie zet.

**Releaseproces:** iedere release beoordeelt `npm audit`, Expo Doctor, de
bereikbaarheid van het kwetsbare runtimepad, beschikbare compatibele patches
en eventuele kritieke bevindingen opnieuw. De release-eigenaar legt datum,
bevindingen en acceptatie of mitigerende actie vast. Een kritieke of aantoonbaar
uitbuitbare bevinding is geen stilzwijgend geaccepteerd risico.

### 8.5-G1 — Echte apparaten en sessies

**Besluit:** harde releasepoort voor elk officieel ondersteund platform.

**Bewijs:** minimaal twee echte geauthenticeerde Supabase-sessies bewijzen
eigenaarsisolatie en per ondersteund platform doorloopt een fysieke devicebuild
zone-instelling, protocolplanning/-uitvoering, RPE, evaluatie, onderbreking en
hervatting. Een platform mag pas als ondersteund worden gecommuniceerd nadat
zijn bewijs is geaccepteerd. Deze poort is nog niet voltooid.

## Vervroegde fase-10-levering: AI-uitleg

De bestaande afgebakende AI-uitleg bij een deterministisch gemaakt, nog
`pending` weekschema blijft ongewijzigd. De provider ontvangt geen TSS,
mutatietools of vrije atleetstekst; fouten vallen terug op lokale
deterministische tekst. Dit verandert geen besluit in dit document.

## Fase 9: eerste wearable-integratie

### 9-D1 — Polar

**Besluit:** voorwaardelijke GO. Polar AccessLink blijft de eerste provider.
Technische ontwikkeling en testomgevingen mogen doorgaan, maar verwerking in
productie blijft uit totdat juridische/privacybeoordeling én de voorwaarden
van de provider expliciet zijn goedgekeurd.

**Handhaving:** wanneer Polarcredentials in een productieomgeving zijn
geconfigureerd, weigert de backend te starten zonder de drie afzonderlijke
goedkeuringsvlaggen. Dit is een technische guardrail; de bijbehorende dossiers
blijven extern bewijs.

### 9-D2 — Privacy en retentie

**Besluit:** beleid moet vóór productie zijn vastgelegd. Ontkoppelen verwijdert
credentials en stopt nieuwe verwerking, maar verwijdert niet automatisch reeds
geïmporteerde activiteiten of bestanden. Een verwijderings- of
portabiliteitsverzoek blijft een afzonderlijke privacyflow.

**Richting:** ruwe FIT-bestanden worden korter bewaard dan canonieke
activiteiten. Exacte termijnen, rechtsgrond, regio, consenttekst,
verwijderings-SLA en uitzonderingen zijn nog niet aangeleverd en mogen niet
door engineering worden verzonnen. Productieconfiguratie met Polar vereist
positieve termijnen waarbij `raw_fit_retention_days` kleiner is dan
`canonical_activity_retention_days`.

### 9-D3 — Callback en operationeel eigenaarschap

**Besluit:** gebruik het definitieve publieke HTTPS-backenddomein voor de
OAuth-callback en webhookregistratie. Client secret, webhooksecret en tokens
staan uitsluitend in backend-/Railway-secrets. Eén operationele eigenaar is
verantwoordelijk voor providerregistratie, secretrotatie, incidenten en
callbackwijzigingen.

**Handhaving:** een productieconfiguratie met Polar accepteert geen localhost,
HTTP-callback of ontbrekende operationele eigenaar.

### 9-D4 — Historische import

**Besluit:** 14 dagen is de standaard. De atleet kan uitsluitend 7, 14 of 30
dagen kiezen. De UI meldt vóór import dat meer dan 30 dagen via deze koppeling
niet beschikbaar is.

**Implementatie:** API-validatie en mobiele selectie gebruiken exact deze drie
waarden; een willekeurig aantal dagen wordt afgewezen. Dit is geen toezegging
dat de provider oudere of vóór registratie ontstane gegevens levert.

### 9-D5 — Retry van imports

**Besluit:** gebruik een Railway scheduled job in dezelfde FastAPI-monoliet.
Geen Redis, Celery, microservice of tweede worker voor de MVP.

**Implementatie:** de opdracht `start23-retry-polar-imports` claimt in beperkte
batches alleen vervallen retries. Iedere import heeft maximaal vier pogingen
(de eerste poging plus drie retries). De huidige begrensde exponentiële
back-off is 5, 10 en 20 minuten; het generieke plafond is zes uur. Succes wist
de retryplanning, een definitieve fout blijft zichtbaar voor support en een
atleet kan een mislukte, nog retrybare import ook handmatig opnieuw starten.
Railway moet de opdracht nog daadwerkelijk volgens het operationele runbook
inplannen en monitoren.

### 9-D6 — Ingetrokken token

**Besluit:** een door Polar geweigerde of ingetrokken autorisatie zet de
verbinding op `reconnect_required`. Onbruikbare credentials worden veilig
verwijderd en er worden geen zinloze automatische retries gepland.

Bestaande canonieke activiteiten en, onder het geldende retentiebeleid, ruwe
bestanden blijven behouden. De atleet moet een volledig nieuwe expliciete
OAuth-toestemming geven; Start23 simuleert geen niet-bestaande refreshflow.

### 9-D7 — Mobiele UI

**Besluit:** één minimalistisch Integrations-scherm voor Polar. Het scherm
ondersteunt verbinden, verbindingsstatus, 7/14/30-dagenimport, importstatus,
handmatige retry, ontkoppelen en een korte privacy-uitleg.

De UI maakt expliciet dat ontkoppelen geen gegevensverwijdering is, toont
`reconnect_required` en bevat geen geplande of gerealiseerde TSS.

### 9-D8 — FIT-bestanden

**Besluit:** backend-only voor de MVP. Er komt geen filemanager of
downloadscherm, tenzij de definitieve privacy-/portabiliteitsanalyse dit
vereist. FIT-opslag blijft privé, owner-scoped en servergeschreven; een
ontbrekende FIT-export maakt de canonieke activiteit niet ongeldig.

### 9-D9 — Activiteit koppelen

**Besluit:** alleen een suggestie plus expliciete bevestiging door de atleet.
Geen automatische koppeling in de MVP.

**Implementatie:** de mobiele app kan de dichtstbijzijnde geplande training van
dezelfde discipline binnen 24 uur voorstellen. Alleen een expliciete actie
roept de eigenaargebonden bevestigingsroute aan. De backend controleert
eigenaarschap, discipline, geldige planstatus en dat de activiteit nog niet is
gekoppeld. De suggestie zelf wijzigt niets en een LLM is niet betrokken.

### 9-D10 — `SECURITY DEFINER`

**Besluit:** refactor alleen-lezen RPC's waar mogelijk naar invokerrechten en
RLS vóór productie.

**Implementatie:** `get_polar_connection` en `list_polar_imports` zijn
`SECURITY INVOKER` en vertrouwen op expliciete grants plus owner-RLS.
Schrijvende of private-credentialoperaties blijven alleen waar nodig nauw
begrensde `SECURITY DEFINER`-functies, met ingetrokken `public`/`anon`-rechten,
een vaste `search_path`, service-rolecontrole of een identiteit uit
`auth.uid()`. De nieuwe expliciete activiteitskoppeling controleert de eigenaar
ook server-side.

### 9-D11 — Bescherming tegen gelekte wachtwoorden

**Besluit:** Supabase Auth-bescherming tegen gelekte wachtwoorden moet vóór
productie zijn ingeschakeld.

Dit is een projectdashboard-/Auth-instelling en wordt niet via een SQL-migratie
gefingeerd. Het releasebewijs moet een geaccepteerde dashboardcontrole en een
authenticatietest bevatten. De poort blijft open totdat dit bewijs bestaat.

### 9-G1 — Polar end-to-end

**Besluit:** harde releasepoort. Test met twee echte gebruikers, echte
OAuth-toestemming en webhooks, een tijdelijke providerfout met retry,
ontkoppeling en `reconnect_required` gevolgd door nieuwe toestemming, en
fysieke apparaten voor ieder officieel ondersteund platform.

Het bewijs moet tevens aantonen dat precies één canonieke activiteit wordt
gemaakt, de andere gebruiker geen verbinding/import/bestand kan zien, en
disconnect geen actief credential achterlaat. Deze poort is nog niet voltooid.

## Releasepoorten na deze besluitronde

- [x] Contract `zone_target`/`protocol_target` en eerste beoordeelde
  week-1-fietskalibratie geïmplementeerd.
- [x] MVP-scope voor plausibiliteit en fysiologisch geslacht vastgelegd.
- [x] Tijdelijke dependency-risicoacceptatie en herbeoordeling per release
  vastgelegd.
- [x] Polar-keuzes voor import, retry, reconnect, UI, FIT, koppeling en
  invoker-RPC's geïmplementeerd.
- [ ] Eén gekwalificeerde fysiologische eindverantwoordelijke en extern
  reviewrecord formeel invullen en accepteren.
- [ ] Juridische, privacy- en provider-termsgoedkeuring voor Polar vastleggen.
- [ ] Exact retentie-/verwijderings-/regiobeleid en consenttekst vastleggen.
- [ ] Definitief HTTPS-domein registreren, backendsecrets plaatsen en één
  operationele eigenaar aanwijzen.
- [ ] Railway scheduled job configureren, monitoren en alarmering beleggen.
- [ ] Supabase-bescherming tegen gelekte wachtwoorden inschakelen en testen.
- [ ] 8.5-G1 en 9-G1 met twee echte gebruikers en fysieke apparaten afronden.

## Referenties

- [MVP-roadmap](mvp-roadmap.md)
- [Backend-zoneberekening en kalibratie](backend-zone-calculation.md)
- [API-contracten](../architecture/api-contracts.md)
- [Beveiligingsmodel](../architecture/security-model.md)
- [Supabase-databasemigraties](https://supabase.com/docs/guides/deployment/database-migrations)
- [Supabase Data API en expliciete grants](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)

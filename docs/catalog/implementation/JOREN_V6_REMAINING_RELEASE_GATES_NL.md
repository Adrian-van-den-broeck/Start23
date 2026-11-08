# V6: resterende onafhankelijke releasevoorwaarden

8 november 2026, Europe/Amsterdam. Branch `feat/joren-v6-lifecycle-completion`.
Implementatie `bb4ac2c917780740551443380ef6fde7a4db4e09`; gecontroleerde basis
`31a8ed0cfad831780b405030121817df50e8fa2c`.

De A5-koppeling en bevestigde datumwijzigingen zijn lokaal ge?mplementeerd en
geverifieerd. V6 blijft uitgeschakeld voor productie. Alle 77 bronrevisies blijven
INACTIVE; de normale applicatie kiest nog de historische implementatie. Er is geen
push, merge, deployment, staging-/productieverbinding, hosted migratie of
catalogusactivatie uitgevoerd. De beschermde A5/A6-releasebranch is ongewijzigd.

De vaststaande V6-keuzes blijven ongewijzigd: offici?le methode
`joren-v6-planned-if2-1`, harde geautoriseerde weekgrens, zachte 50/30/20-verdeling,
maximaal 20% HIGH actieve tijd per sport en geen HIGH-ondergrens. Er zijn geen
ervaringscategorie?n of nieuwe fysiologische regels toegevoegd.

De bestaande check-in-herbevestiging is transactioneel hersteld: de oude context
wordt superseded met behoud van zijn oorspronkelijke bevestigingstijd. Een nieuwe
onbevestigde revisie kan geen planning vanuit een oudere bevestiging autoriseren.

Voor vrijgave blijven afzonderlijk nodig:

- Operationele acceptatie van geschatte actieve zwemtijd. Referentietijd is geen
  gemeten uitgevoerde tijd en vult geen activiteitduur in.
- Individuele geschiktheid van uitzonderlijk lange trainingen, inclusief bestaand
  vereist duur-bewijs. Er is geen nieuwe algemene duurgrens verzonnen.
- Offici?le compatibiliteitsbeslissing voor Planned IF? versus Realized V2
  Session-RPE fallback. Niet-ondersteunde combinaties blijven geblokkeerd;
  meetgegevens behouden prioriteit.
- Een aantoonbaar bevoegde, verantwoordelijke wetenschappelijke beoordelaar en
  een extern reviewrecord voor de exacte bron-, methode- en beleidsversies.
- GoTrue-uitgegeven sessies en volledige Supabase gateway-/accountisolatietests.
  SQL-claims en lokaal ondertekende PostgREST-tokens vervangen die tests niet.
- Echte Android- en iOS-apparaattests: onboarding, check-in, voorstelbeoordeling,
  bevestiging, datumwijziging, refresh/herstart, conflicten en activiteitkoppeling.
  Een geslaagde APK-build is daarvoor geen bewijs; iOS-build/signing is hier niet
  uitgevoerd.
- Expliciete autorisatie voor hosted migraties en release. De nieuwe forward-only
  migratie is uitsluitend op wegwerpdatabases op localhost uitgevoerd.
- Afzonderlijke definitieve catalogusactivatie na acceptatie van alle voorwaarden.

Functionele begrenzing: een V6-week met bestaande activiteitkoppelingen, voltooide
of expliciet geregistreerde trainingen wordt bij een datumwijziging geweigerd,
ook wanneer een andere nog geplande training wordt gekozen. Er is geen goedgekeurd
contract om bestaand bewijs naar nieuwe fysieke revisierijen over te dragen.
Een vervolg moet eerst dat identiteits-/chronologiecontract vastleggen; bestaande
bijlagen of historische voorschriften worden nooit stilzwijgend herschreven.
Bestaande pending voorstellen blokkeren eveneens een actieve datumwijziging.

De originele A5 SQL-fixture is niet aangepast. De bekende onboarding- en
fingerprintcorrectie is alleen als expliciete ge?soleerde test-overlay gebruikt.
Permanente overname blijft een afzonderlijk te beoordelen voorstel.

De exacte controles, aantallen, bronhashes en bewijsgrenzen staan in
[JOREN_V6_LIFECYCLE_TRANSACTION_TESTS.md](JOREN_V6_LIFECYCLE_TRANSACTION_TESTS.md)
en [verification.json](lifecycle-completion/verification.json).

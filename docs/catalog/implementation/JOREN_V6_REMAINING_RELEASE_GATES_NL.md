# V6: resterende onafhankelijke releasevoorwaarden

8 november 2026, Europe/Amsterdam.
Branch `feat/joren-v6-evidence-safe-rescheduling`; gecontroleerde basis
`1dbe10b1a419c689f189faf077f4178eaa4f6310`.
De exacte implementatie-SHA en controlehashes staan in
[verification.json](evidence-rescheduling/verification.json).

Een onvoltooide V6-training kan lokaal veilig worden verplaatst nadat een andere
training in dezelfde bevestigde week is geregistreerd. Voltooide en gekoppelde
trainingen behouden hun oorspronkelijke fysieke record en activiteitbewijs.
Alleen het verplaatste, geschikte doel krijgt een nieuwe fysieke voorschriftrij.
Een onveranderlijke lidmaatschapstabel neemt de overige oorspronkelijke records
op in de nieuwe weekrevisie. Er wordt geen activiteitbewijs gekopieerd, verplaatst,
losgekoppeld of opnieuw berekend. De oorspronkelijke bron en methode blijven
leidend. Eerdere bevestigde voorschriften en bronmomentopnamen blijven intact.

V6 blijft uitgeschakeld voor productie. Alle 77 bronrevisies blijven INACTIVE;
de normale applicatie kiest nog de historische implementatie. Er is geen push,
merge, deployment, staging-/productieverbinding, hosted migratie of
catalogusactivatie uitgevoerd. De beschermde A5/A6-releasebranch en bestaande
historische worktrees zijn niet gewijzigd.

De officiële methode `joren-v6-planned-if2-1`, harde geautoriseerde weekgrens,
zachte 50/30/20-verdeling, maximaal 20% HIGH actieve tijd per sport, afwezigheid
van een HIGH-ondergrens, trainingsfasen, selectievolgorde en zwemreferenties zijn
ongewijzigd. Er zijn geen ervaringscategorieën of nieuwe fysiologische regels.
Meetgegevens behouden prioriteit. Niet-ondersteunde Planned/Realized V2
fallbackcombinaties blijven geblokkeerd; referentiezwemtijd wordt geen gemeten tijd.

Voor vrijgave blijven afzonderlijk nodig:

- Operationele acceptatie van geschatte actieve zwemtijd.
- Individuele geschiktheid van uitzonderlijk lange trainingen, inclusief bestaand
  vereist duur-bewijs. Er is geen nieuwe algemene duurgrens verzonnen.
- Officiële compatibiliteitsbeslissing voor Planned IF² versus Realized V2
  Session-RPE fallback. Dit werk wijzigt de fallbackdispatch niet.
- Een aantoonbaar bevoegde, verantwoordelijke wetenschappelijke beoordelaar en
  een extern reviewrecord voor de exacte bron-, methode- en beleidsversies.
- GoTrue-uitgegeven sessies en volledige Supabase gateway-/accountisolatietests.
  SQL-claims en lokaal ondertekende PostgREST-tokens vervangen die tests niet.
- Echte Android- en iOS-apparaattests: onboarding, check-in, voorstelbeoordeling,
  bevestiging, datumwijziging na activiteit, refresh/herstart, conflicten en
  activiteitkoppeling. Componenttests en een APK-build zijn geen apparaattests.
  iOS-build/signing is hier niet uitgevoerd.
- Expliciete autorisatie voor hosted migraties en release. De nieuwe forward-only
  migratiekandidaat is uitsluitend op wegwerpdatabases op localhost uitgevoerd.
- Afzonderlijke definitieve catalogusactivatie na acceptatie van alle voorwaarden.

Resterende functionele begrenzingen:

- De automatische selector maakt maximaal één nieuwe training per doelsport.
  Uitbreiding naar meerdere nieuwe trainingen per sport vergt toekomstig werk.
- Een voltooid/geannuleerd doel, ieder doel met gekoppelde activiteit en ieder
  expliciet geregistreerd doel blijft onverplaatsbaar. Ook een koppeling die nog
  op RPE wacht geeft geen toestemming om het fysieke record te vervangen.
- Een wijziging buiten de week, buiten bevestigde beschikbaarheid of tegen
  bestaande herstel-/planningsregels wordt geweigerd, evenals vreemde of
  verouderde identifiers en revisies.
- Een pending voorstel blokkeert een actieve datumwijziging. Bevestiging van een
  vervangend voorstel dat inmiddels geregistreerde fysieke records zou verliezen
  wordt eveneens geweigerd. Verwerp het onverenigbare voorstel, laad opnieuw en
  verplaats vervolgens een geschikte onvoltooide training.
- Legacy correctieve generatie zonder een V6-lidmaatschapscontract blijft
  geblokkeerd op een actief V6-plan. Dit werk verleent geen toestemming om
  voltooide trainingen te herschrijven of bewijs over te dragen.

De originele A5 SQL-fixture is niet aangepast. De bekende onboarding- en
fingerprintcorrectie is alleen als expliciete geïsoleerde test-overlay gebruikt.
Permanente overname blijft een afzonderlijk te beoordelen voorstel.

De bewijsgrenzen, werkelijk uitgevoerde SQL/HTTP-controles, mobiele resultaten en
historische regressies staan in
[JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md](JOREN_V6_ACTIVITY_IDENTITY_REGRESSIONS.md)
en het [eigenaarschapcontract](JOREN_V6_EVIDENCE_CARRY_FORWARD_CONTRACT.md).

Implementation commit: `057d88bb41aa8f73c1e1e66b0e7d0059754ca527`.
Evidence reviewed 2026-11-12; the documentation-only successor records the
verification manifest and source hashes. V6 remains inactive.

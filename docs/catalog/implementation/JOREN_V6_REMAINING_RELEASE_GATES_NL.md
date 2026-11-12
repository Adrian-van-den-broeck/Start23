# V6: resterende onafhankelijke releasevoorwaarden

12 november 2026, Europe/Amsterdam.
Branch `feat/joren-v6-multi-session-planning`; gecontroleerde basis
`b87d0e4f82702e168ec16441bbe7661fd0d10cb2`.
De exacte implementatie-SHA en controlehashes staan in
[verification.json](multi-session/verification.json).

De inactieve planner ondersteunt nu meerdere nieuwe sessies per sport wanneer
een expliciet, intern, atleet- en weekgebonden frequentiecontract dat vraagt.
Zonder zo'n contract blijft maximaal één nieuwe sessie per doelsport de veilige
standaard. Een maximum is geen doel; een zachte aanvraag is geen verplicht
minimum. Alle nieuwe frequentievoorbeelden zijn TEST_ONLY. De huidige goedgekeurde
onboarding verzamelt uren, geen geautoriseerde sessiefrequentie. Product moet de
bron, meetperiode, ontbrekende gegevens, herstel-/blessurebehandeling en
bevestiging/intrekking van frequentieautorisatie nog vastleggen.

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
van een HIGH-ondergrens, trainingsfasen en zwemreferenties zijn ongewijzigd.
Expliciet gevraagde sessiedekking komt na sportdekking en vóór de bestaande
allocatie-/belastingrangschikking; zonder frequentiecontract verandert de keuze
niet. Er zijn geen ervaringscategorieën of nieuwe fysiologische regels.
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
- Een productbesluit over echte frequentieautorisatie voordat automatische
  herhaalde sportsessies buiten expliciete testcontexten worden aangeboden.
- Operationele beoordeling van de begrensde zoekruimte: maximaal 24 occurrences
  en 200.000 gedeelde zoek-/planningsstappen. Het getoonde budget-300-geval geeft
  eerlijk `v6_search_incomplete`; een afgekapt resultaat wordt niet opgeslagen.

Resterende functionele begrenzingen:

- Zonder expliciete frequentieautorisatie maakt de automatische selector maximaal
  één nieuwe training per doelsport. De multi-sessiecapaciteit is lokaal bewezen
  met synthetische aanvragen; uren of TSS worden niet tot frequentiebeleid verheven.
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
[JOREN_V6_MULTI_SESSION_VERIFICATION.md](JOREN_V6_MULTI_SESSION_VERIFICATION.md),
het [frequentiebeleid](JOREN_V6_MULTI_SESSION_POLICY.md) en het
[eigenaarschapcontract](JOREN_V6_EVIDENCE_CARRY_FORWARD_CONTRACT.md).

De bestaande 62 migraties zijn op een nieuwe lokale wegwerpdatabase afgespeeld;
voor deze uitbreiding is geen nieuwe migratie nodig. De lokale implementatie-SHA
en bewijs-hashes staan in het nieuwe verificatiemanifest. De uiteindelijke
documentatiecommit wordt apart in de oplevering vermeld. V6 blijft inactief.

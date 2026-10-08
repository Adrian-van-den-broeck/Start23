# Bekende gaten en vragen

WOMBO DETERMINISTIC ENGINE REVIEW PACKAGE INCOMPLETE — SEE PARITY AND COVERAGE GAPS

## Technische gaten

1. Native-formula XLSX implementeert geen exacte begrensde multisetsearch/backtracking. Er wordt geen vereenvoudigde selector als equivalent voorgesteld.
2. Er is geen functionele XLSM en geen authored VBA. Excel COM geeft hier een null VBProject terug. Macrotrust is niet aangepast. Dit blokkeert programmatische VBA-installatie; het verklaart niet dat de algoritmen al geschreven of geverifieerd zouden zijn.
3. De 154 v2 catalogus-ID's worden met gen_random_uuid() aangemaakt (20260929210000:10-13). De lokale bronprojectie behoudt v1 fixture-ID's bij v2 eigenschappen. De exacte deployed-ID/tie-breaker-volgorde is onbekend. Geen staging/production is gelezen.
4. 66 beschreven groepen zijn geen complete human-reviewed all-rule inventaris. 676 discoveryrecords en 1250 syntactische beslispunten moeten op reachability, contracten en tests worden beoordeeld. SQL/mobile-conditiondekking ontbreekt.
5. Weektargets gebruiken expliciete autoritatieve previous-state-inputs. De zesweekse SQL-historyreader en zijn NULL/zero/provenance-aggregatie worden niet volledig geëmuleerd. In het model blokkeert een ontbrekende approved snapshot verdere terugkerende berekening.
6. Complete planvalidation ontbreekt: juiste targetfit, vaste composition, eligible prefixes, protocoldata, stale context, exacte restspreiding en cross-week interacties zijn geen complete simulatorpoort.
7. Blessures en sick-historyfiltering geven waar nodig NOT IMPLEMENTED/expliciete-input-gate. De huidige waterfill wordt beschreven, niet nagebootst met onbeoordeelde eenvoudiger formule.
8. Intensiteitschuld en manual-review-recovery/escalatie worden niet downstream gesimuleerd. De .20 highfraction-parameter is geen bewezen volledige branchimplementatie.
9. Actuele Phase13-zones zijn berekenbaar. Legacy model1.0, handmatige grenzen, fieldtestkwaliteit, setup/onboarding/zoneapproval-events en RPE-correctie-immutability zijn niet volledig geport.
10. Calendar spacing is alleen voor Europe/Amsterdam (huidige EU-regel) en UTC uitgewerkt. Arbitrary IANA-zones/historische DST-wetten blijven open.
11. Origineel en Joren rekenen zij-aan-zij met dezelfde expliciete vorige inputs. Eigen volledige divergerende approved multieweek-state per ruleset ontbreekt.
12. Excel Double is geen Python Decimal. Een tolerantie van 1e-9 voor numerieke asserties is geen bewijs van volledige precisiematch. Boundaries en rounding moeten afzonderlijk gecontroleerd worden.
14. Broncatalogus bevat U+FFFD replacementtekens in namen/beschrijvingen. De Excel-display markeert [bronteken ontbreekt]; exacte ongewijzigde brontekst staat in fixtures/catalog.json en extra bronkolommen. Geen oorspronkelijke punctuatie/letter wordt geraden.
13. De 40 scenariotitels op het werkblad zijn reviewtargets. Ze zijn niet automatisch 40 uitgevoerde volledige engineflows. De executable parity JSON en het rapport zijn de testbron.

## Brondiscrepanties en bereik

- Oud roadmap-/Phase3-gedrag noemt zero injury redistribution. De nieuwe actuele planning v2 gebruikt bounded 80% transfer met recipientcaps. De historische helper blijft aanwezig, maar is niet de nieuwe proposalregel.
- srpe_formula en legacy RPE-hours zijn aanwezig; actuele activiteitprocessing gebruikt ze niet als missing-datafallback. Een formule kunnen vinden bewijst niet dat de MVP haar activeert.
- Joren HR/CSS-zones hebben inclusieve gehele grenzen; bestaande fieldtest/known-value model1.0 heeft gedeelde grens met hogere-intensiteitseigendom. Beide provenanceversies blijven onderscheiden.
- Whole-workout 80/20-minuten en private high-load-budget zijn verschillende grootheden. Een geselecteerde week kan andere minuutpercentages krijgen dan de high-loadband suggereert.
- Swim-brontrainingen op afstand hebben bronload-provenance, maar current planned load=None. Dat is een echt catalogusgat en geen reden om duur te gokken.
- Eén week zonder activiteiten is door SQL gerealiseerde load0. Activiteiten met ontbrekende actuele load kunnen NULL geven. SQL SUM negeert NULL naast bekende waarden; het model neemt bij bepaalde gemengde cases conservatiever unavailable aan. Dat is een expliciete mismatch, geen parity-pass.

## Wat Joren inhoudelijk moet beoordelen

- Is 56.25 belasting/uur met sportmultipliers .90/1/1.15 de juiste vorige-maandbaseline?
- Is totale nulhistorie45 bruikbaar terwijl componenten nul blijven en restricted/partial-historycases kunnen blokkeren?
- Zijn .80 completiondrempel, +10% growth, >110% debt en >115% sessionovershoot passend?
- Is high-load70-90% van nominaal20%-budget de gewenste intensiteitsverdeling tegenover whole-workoutminuten?
- Zijn 72/48 elapsed uren passend rondom DST en consolidated low workouts?
- Is 80% injury-transfer met recipientbasis/caps verantwoord, en hoort bestaande positieve bike/swim-basis zonder nieuwe opt-in replacement toe te staan?
- Is volledige maandag-race-taper35% en partial-week fail-closed de gewenste productuitkomst?
- Welke onafhankelijke reviewprovenance ondersteunt HR/RPE-ankers en discrete zonegrenzen?
- Hoe moeten mean-HR estimates, die geen complete match opleveren, in feedback en progression worden beoordeeld?

Geen inhoudelijk voorstel wordt automatisch in de app verwerkt.

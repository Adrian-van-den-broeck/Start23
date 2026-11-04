# Correctieverzoek aan Joren - zes zwemtrainingen

## C2.1 correctie bevestigd en afgeleide bron geverifieerd

2026-11-04: de eigenaar heeft Jorens eerdere expliciete bevestiging herhaald:
voor TR-SWIM-015 t/m TR-SWIM-020 moet het geordende blok **300m Z3 naar 300m Z2**.
Besluit **C2.1-SWIM-1**, met [scope en herkomst](JOREN_C2_UPDATED_DECISIONS.md#c21-approval).
Het historische verzoek hieronder blijft bewaard en is niet verzonden.
Deze keuze hoeft niet opnieuw te worden gevraagd.

De geaccepteerde C2-SHA bevatte alleen de conflicterende oorspronkelijke bron en
een inactief conceptregister; geen gecorrigeerde afgeleide versie. C2.1 levert
`joren_c21_swim_corrections_v1.json`, revisie
`joren-swim-if2-approved-prescription-overlay-1`, SHA-256
`a850a745e2170a3024f00ca201116880f8ba66de46d73e6b40ef8dbd380a948a`.
Dit is een volledig reproduceerbaar correctiemanifest, geen herschreven workbook.
De volledige oorspronkelijke document/cel-XML, alle twintig originele rijen en
hun events blijven naast de afgeleide voorschriften bewaard. Alleen N19–N24
veranderen, telkens precies het eerste 300m-blok; rust, afstand, focus, overige
blokken, aggregaten en opgeslagen bronwaarden blijven gelijk.

**A. Origineel:** 7405 bytes, oorspronkelijke SHA-256
`7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`;
de zes conflicten blijven historische feiten. Ook de oudere bron/PDF blijven intact.

**B. Afgeleide kandidaat:** alle twintig voorschriften zijn structureel consistent;
de zes gecorrigeerde rijen hebben Z2/Z3 = 600m/0m en ieder zonetotaal en totaalaantal
meters klopt. IF² is opnieuw berekend, zie [reconciliatie](JOREN_SWIMMING_IF2_TSS_RECONCILIATION.md).
De zes hebben geen resterende structuur- of rekenafwijking bij de expliciete
verificatieparameters. De overige drie Z3-rijen missen nog de IF-coëfficiënt.

**C. Operationeel:** INACTIVE; geen catalogusentries, methodetoelating, planwijziging
of activatie. Referentietempo's, normalisatie, afronding/precisie/opslag,
operationele P, V2-compatibiliteit en releasegoedkeuring blijven aparte poorten.
Actieve zwemtijd ontbreekt nog voor alle twintig rijen: tijdscompliance UNVERIFIED.

Reproductie vanuit backend:
`python -B -m app.jobs.joren_c2_dry_run --dry-run --approved-corrections --private-output NEW_PATH`.
Identieke herhaling is alleen-lezen; afwijkende bestaande uitvoer wordt geweigerd.

## Historisch onverzonden correctieverzoek

Datum intake: 2026-11-04. Concept om te verzenden; niet verzonden. Alleen intern.

Beste Joren, dank voor de IF²-herziening. We bewaren het originele bestand ongewijzigd. In precies onderstaande zes regels wijken de zonekolommen af van de voorgeschreven uitvoering. Daardoor houden we deze zes trainingen buiten iedere operationele catalogus. Wil je **per regel** bevestigen of de zonekolommen of de uitvoering leidend zijn, of een eigen volledige correctie leveren? We kiezen dat niet op basis van welke variant de TSS-weergave verklaart.

Bron: `Zwemtrainingen_IF2.xlsx`, 7405 bytes, SHA-256 `7c2ee58f719036d41d15e4446727a7144b46b600df4a9ea26f78c82f7093f6cb`, werkblad `Zwemtrainingen`. Alle waarden hieronder zijn exact uit de bron; de uitvoering is niet aangepast.

| ID / Excel-rij | Titel | F totale meters | H/I/J/K/L meters (bron) | N uitvoering, totalen Z2/Z3 | M exacte bronwaarde | Gevraagde keuze |
| --- | --- | --- | --- | --- | --- | --- |
| TR-SWIM-015 / 19 | Snelheid 10x100m | 1600 | 0 / 600 / 0 / 0 / 1000 | 300 / 300 | 39.9 | kolommen / uitvoering / eigen correctie |
| TR-SWIM-016 / 20 | Snelheid 15x100m | 2100 | 0 / 600 / 0 / 0 / 1500 | 300 / 300 | 54.8 | kolommen / uitvoering / eigen correctie |
| TR-SWIM-017 / 21 | Snelheid 20x100m | 2600 | 0 / 600 / 0 / 0 / 2000 | 300 / 300 | 69.59999999999999 | kolommen / uitvoering / eigen correctie |
| TR-SWIM-018 / 22 | Weerstand 10x100m | 1600 | 0 / 600 / 0 / 0 / 1000 | 300 / 300 | 39.9 | kolommen / uitvoering / eigen correctie |
| TR-SWIM-019 / 23 | Weerstand 15x100m | 2100 | 0 / 600 / 0 / 0 / 1500 | 300 / 300 | 54.8 | kolommen / uitvoering / eigen correctie |
| TR-SWIM-020 / 24 | Weerstand 20x100m | 2600 | 0 / 600 / 0 / 0 / 2000 | 300 / 300 | 69.59999999999999 | kolommen / uitvoering / eigen correctie |

Als de kolommen leidend zijn, moet je expliciet bevestigen of het eerste `300m Z3` in N `300m Z2` wordt. Als de huidige uitvoering leidend is, moeten I/J expliciet600/0 -> 300/300 worden bevestigd. Geef in beide gevallen ook de bijbehorende geverifieerde nieuwe TSS en de volledige formule. Dit zijn alternatieven ter goedkeuring, geen uitgevoerde correcties.

Bevestig daarnaast de referentietempo's per zone, de ontbrekende Z3-IF, de factor100/60, .90 precies eenmaal, eventuele afronding van tempo naar minuten, en eindafronding/opslag. .88 voor Z3 en afgeronde tempo-minuten verklaren de getoonde aggregaatwaarden, maar zijn uitsluitend GERECONSTRUEERD. Met die kandidaat geeft de ongewijzigde uitvoering circa41.2/56.1/71.0 in plaats van39.9/54.8/69.6; we vervangen niets. Lever de correctie als nieuwe bronversie met beslissingreferentie; oude bytes/historie blijven bewaard.

Exacte huidige N-cellen:

**TR-SWIM-015 - N19**

```text
300m Z3 | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 300m Z2
```

**TR-SWIM-016 - N20**

```text
300m Z3 | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 300m Z2
```

**TR-SWIM-017 - N21**

```text
300m Z3 | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 100m Z5 | 30s Rust | 300m Z2
```

**TR-SWIM-018 - N22**

```text
300m Z3 | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 300m Z2
```

**TR-SWIM-019 - N23**

```text
300m Z3 | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 300m Z2
```

**TR-SWIM-020 - N24**

```text
300m Z3 | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 100m Z5 | 15s Rust | 300m Z2
```

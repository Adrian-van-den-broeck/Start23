# Specificatie fysiologische formules
## Status
Draft - goedkeuring vereist vóór berekeningscode
Dit document is de veiligheidspoort ("safety gate") van Fase 3. Het scheidt vereisten die al expliciet zijn van keuzes die een technische aanname anders tot fysiologisch beleid zouden maken. Zolang dit document niet is goedgekeurd en er geen stabiele ruleset-versie aan is toegewezen, faalt de backend gesloten ("fails closed") en evalueert hij geen enkele fysiologische regel.
De regelvoorrang uit Fase 0, de vereiste van een openstaand voorstel ("pending proposal") en de vertrouwelijkheid van de TSS blijven leidend.
## Regeloverschrijdende beslissingen die goedkeuring vereisen
De volgende conventies moeten voor elke opgenomen berekening worden goedgekeurd:

gebruik Decimal-rekenkunde voor interne belasting en verhoudingen;
definieer canonieke invoereenheden per regel;
definieer precisie en eindafronding los van de tussentijdse precisie;
specificeer het exacte gelijkheidsgedrag bij elke drempelwaarde;
specificeer het onder- en bovengrens-clamping-gedrag;
verwerp ongeldige waarden in plaats van ze stilzwijgend om te zetten ("coercing");
definieer het gedrag bij ontbrekende, nul- en onvolledige-historiekwaarden;
sla de ruleset-versie op bij elke beslissingsrun;
geef uitsluitend kwalitatieve, atleetgerichte toelichtingen terug.

## BR-002: volume- en intensiteitsschuld
Expliciet brongedrag:

volumeschuld is gebaseerd op gerealiseerde belasting boven de eerder geplande belasting;
het voorbeeld 600 gepland / 680 gerealiseerd creëert een interne schuld van 80;
de reguliere projectie voor de volgende week vertrekt vanuit de eerder geplande belasting;
hoge-intensiteitsschuld is gebaseerd op tijdspercentage;
de normale ondergrens voor hoge intensiteit is 5%, met een uitzondering bij een bevestigde blessure.

Goedkeuringsbeslissingen:

Wordt schuld geactiveerd bij elke gerealiseerd > gepland, enkel boven 10%, of enkel na herhaalde/"structurele" overschrijding?
Is gelijkheid op exact 110% een overschrijding?
Wordt alle schuld toegepast op precies één volgende week, of doorgeschoven tot ze is afgelost?
Mag de resulterende doelwaarde voor de volgende week nul bereiken, en wat is de bovengrens-clamp?
Staat de blessure-uitzondering 0% hoge intensiteit toe bij elke bevestigde blessure, of enkel voor een geblesseerde discipline?

## BR-003: tijdgebaseerde intensiteitsverdeling
Expliciet brongedrag:

Zone 1, Zone 2 en zwemtechniek zijn lage intensiteit;
Zone 3, Zone 4 en Zone 5 zijn hoge intensiteit;
de verhouding wordt berekend op basis van duur, niet TSS;
het standaard wedstrijdgerichte doel is 80/20.

Goedkeuringsbeslissingen:

Gemengde trainingen toewijzen op basis van segmentduur, dominante categorie, of trainingsclassificatie?
not_evaluated of 0/0 teruggeven voor een week met nul duur?
Welke afwijking van de verhouding levert een waarschuwing op, inclusief exacte gelijkheid?
Worden de niet-wedstrijddoelen 90/10 en swimrun-doelen 75/25 uitgesteld ten opzichte van de MVP?
Met welke precisie worden percentages weergegeven terwijl de exacte duur intern wordt behouden?

## BR-004: progressieve belasting
Expliciet brongedrag:

de eerder geplande belasting, niet de gerealiseerde overschrijding, is het groei-ankerpunt;
de reguliere groei bedraagt 10%;
gerealiseerde belasting van 80% tot en met 100% van het geplande volgt de reguliere groei;
onder 80% wordt een baseline-fallback geactiveerd.

Goedkeuringsbeslissingen:

Is exact 80% regulier of fallback? De tekst impliceert regulier.
Is de baseline het rekenkundig gemiddelde van vier actieve weken, een 42-daags model, of een andere gedefinieerde CTL-formule?
Worden weken met nul belasting meegenomen in die baseline?
Wat gebeurt er bij minder dan het vereiste aantal historieksamples?
Welke afronding en maximum/minimum-clamps zijn van toepassing?
Hoe wordt de geplande belasting van een ingekorte of gepersonaliseerde training vastgelegd ("snapshotted")?

## BR-006: anti-stack-intervallen
Expliciet brongedrag:

hoge-intensiteitshardlopen vereist 72 uur tussentijd;
hoge-intensiteitsfietsen en -zwemmen vereisen 48 uur;
een handmatige kalenderverplaatsing geeft een waarschuwing maar wordt niet geblokkeerd.

Goedkeuringsbeslissingen:

Meten vanaf de start of het einde van de vorige training tot de volgende start?
Het interval enkel binnen dezelfde discipline of over disciplines heen toepassen?
Nemen gemengde/brick-trainingen deel aan meer dan één discipline?
Absolute UTC-tijdstippen vergelijken terwijl atleet-lokale tijden worden getoond?
Gebruikt de filtering van gegenereerde decks hetzelfde interval als de planning?

## BR-007: berekening van herstelweek
Expliciet brongedrag:

weken 1 tot en met 4 zijn opbouwweken;
week 5 is een herstelweek;
het hersteldoel is 60% van de geplande belasting van week 4.

Goedkeuringsbeslissingen:

Hoe worden gedeeltelijke blokken van vijf weken afgestemd op een A-wedstrijd?
Vervangt de taper het herstel wanneer beide in dezelfde week vallen?
Wat gebeurt er wanneer week 4 geen geldige geplande belasting heeft?
Welke precisie en afronding zijn van toepassing op het resultaat van 60%?

## BR-008: taperberekening
Expliciet brongedrag:

A-wedstrijd T-2 is 60% van de gemiddelde opbouwbelasting;
A-wedstrijd T-1 is 35% van de gemiddelde opbouwbelasting;
B-wedstrijd gebruikt een reductie van 15% over vier dagen;
C-wedstrijd heeft geen taper.

Goedkeuringsbeslissingen:

Welke weken vormen de "gemiddelde opbouwbelasting", en hoe worden ontbrekende weken behandeld?
Lopen wedstrijdweken van maandag tot zondag in de tijdzone van de atleet?
Wat is de reductiebasis voor de B-wedstrijd en hoe wordt deze over vier dagen verdeeld?
Hoe worden overlappende wedstrijden opgelost?
Welke afronding en clamps zijn van toepassing?

## BR-009: validatie van discipline-zones
Canonieke eenheden voorgesteld door de architectuur:

zwem-CSS: seconden per 100 meter;
fiets-FTP: watt;
fiets-drempelhartslag: slagen per minuut;
hardloop-drempeltempo: seconden per kilometer;
hardloop-LTHR: slagen per minuut.

Goedkeuringsbeslissingen:

Beoordeel klinisch de minimum- en maximumwaarden voor elke metriek.
Definieer de ordening van zonegrenzen en of gelijkheid tussen aangrenzende zones is toegestaan.
Definieer de invoerconversie en de opgeslagen precisie.
Keur de fallback-formules en de vereiste fysiologie-inputs goed.
Bevestig dat berekende vervangingen altijd in afwachting ("pending") blijven.

Er wordt door engineering geen enkel numeriek bereik afgeleid.
## BR-010: herverdeling bij blessure
Expliciet brongedrag:

een bevestigde blessure verwijdert trainingen van de betrokken discipline uit de voorgestelde scope van de huidige en de volgende week;
de bron noemt een herverdelingscoëfficiënt van 0,8;
gegenereerde wijzigingen blijven in afwachting ("pending").

Goedkeuringsbeslissingen:

Is automatische cardiovasculaire herverdeling medisch aanvaardbaar voor de MVP?
Indien aanvaard, wordt het resterende deel van 0,8 gelijk verdeeld of naar rato van de bestaande disciplineverhoudingen en -capaciteit?
Wat gebeurt er wanneer twee of alle drie de disciplines geblokkeerd zijn?
Welke ernst/status activeert de verwijdering en wat zijn de vervalregels?
Volstaat een expliciete vrijgave door de atleet, of is een andere beoordeling vereist?
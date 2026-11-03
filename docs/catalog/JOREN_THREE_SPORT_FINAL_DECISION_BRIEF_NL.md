# Joren — beslisbrief nieuwe trainingscatalogus

Datum: 2026-11-03, Europe/Amsterdam. Alleen beoordeling; geen activatie.
Geaccepteerde code: `feat/joren-realized-tss-v2`, exacte SHA `cef4d0adfb09f5f1937528a98c594a6442816f20`.
Bestaande reviewbranch `review/joren-new-workout-catalog`; worktree
`F:\Projecten Business\Start23\Code\.worktrees\joren-new-workout-catalog`.
Private belastingwaarden zijn uitsluitend technisch beoordelingsmateriaal, geen atleetweergave.


Deze brief bundelt **zes beslissingen**. Alle drie bestanden zijn aanwezig en 61
trainingen zijn structureel gecontroleerd. De IF²-reconstructie voor lopen/fietsen
is nog geen formeel of wetenschappelijk goedgekeurde methode. De zwemformule staat
wel expliciet in de meegeleverde PDF. De zes bestaande sportreviews blijven intact.
**Er is voor A–F nog geen nieuw akkoord ontvangen. Stilte geldt niet als akkoord.**
Er wordt nu niets geïmporteerd, geactiveerd of uitgerold.

## A. Geplande TSS en afronding

**Bron en code:** RUN 20/BIKE 21 passen op een IF²-hypothese met Z1=.55, Z2=.75,
Z4=.98, Z5=1.15; Z3 is niet aangeleverd. HALF_EVEN op één decimaal reproduceert
alle 41 weergaven. Dit bewijst de oorspronkelijke bedoeling niet. De bestaande
zone-minuutberekening blijft een andere methode. Zwemmen gebruikt de gepubliceerde
vaste afstandsmatrix; geen extra 0.90. De huidige broncatalogus kan P bewaren zonder
P opnieuw met zonecoëfficiënten te berekenen.

**Advies/besluitvraag:** bevestig of corrigeer de IF²-methode voor RUN/BIKE en keur
per sport een methodeversie goed. Advies voor toekomstige operationele P: exact
berekenen onder een expliciet Decimal-precisiebeleid, oorspronkelijke bron-P apart
bewaren; afronding alleen aan de vastgelegde presentatiegrens. Bevestig HALF_EVEN
voor de gereconstrueerde bronweergave. Alternatieven zijn afgeronde bron-P als
operationele autoriteit, of een door Joren expliciet herziene zone-minutenbron.
Die keuze mag niet impliciet door de importer worden gemaakt.

**Voorbeeld/gevolg:** TR-BIKE-004 heeft bron 84.4, hypothese84.375 en huidige
zone-referentie72.0. Een echte gemeten72.0 blijft72.0. Een andere goedgekeurde
geplande P verandert selectie en mogelijk de volgende weekbasis; historisch
vastgelegde P blijft gelijk. **Bevoegdheid:** Joren voor trainingsmethode, eigenaar
voor productacceptatie, engineering voor reproduceerbare precisie en provenance;
vereiste onafhankelijke wetenschappelijke/releasebeoordeling blijft open.

## B. Bronversie en vervanging

**Bron en code:**61 nieuwe TR-IDs; geen formele catalogusversie of vervangingstabel.
Oude templates en goedgekeurde voorkomens zijn onveranderlijk. Gelijke titel,
getalsuffix of duur bewijst geen identiteit. De technische UUID5-mapping, hashes
en rijherkomst zijn een uitgewerkt engineeringvoorstel zonder fysiologische regel.

**Advies/besluitvraag:** accepteer één nieuwe catalogusrelease met afzonderlijke
sport-/methodeversies en 61 nieuwe logische TR-identiteiten. Leg expliciet vast
welke oude templates alleen voor toekomstige selectie worden opgevolgd; behoud
alle historie. Alternatief: uitsluitend expliciet bevestigde logische opvolgers
krijgen een nieuwe versie van een bestaande key. Er wordt nooit automatisch
samengevoegd. **Voorbeeld/gevolg:** oude BIK-001 en TR-BIKE-001 hebben beide 60minZ1,
maar P 36 versus30.2. Historische P 36 blijft36 en wordt niet door een nieuwe
weekberekening herinterpreteerd. **Bevoegdheid:** eigenaar/Joren voor bronrelaties;
engineering voor de botsingsvrije technische mapping.

## C. Intensiteit, fasen en geschiktheid

**Bron en code:** Expected Zone is sessiefocus. Bronbestanden missen complete
selectiemetadata. De planner bewaakt de bestaande hoge-belastingbudgetten,
blessurecaps, herhalingen en rustafstand; dat geeft nog geen individuele
beginnersgeschiktheid. De volledige voorgestelde61-rijentabel staat in de finale
reconciliatie: alleen Z1/Z2→laag/base-build-herstel-taper; gemengde Z3+→hoog/build;
Z5 alleen op de bestaande toegestane buildpositie4. Dit is **VOORGESTELD**.

**Advies/besluitvraag:** keur die rijmapping goed of pas haar expliciet aan,
inclusief doelgroep/automatische selectie van lange sessies. Houd TR-BIKE-013
voorlopig uit automatische beginnersselectie; bepaal de bedoelde individuele scope.
Er wordt geen nieuwe duurgrens verzonnen. Alternatief: alleen een door Joren
benoemde deelset mag automatisch deelnemen. **Voorbeeld/gevolg:** met alleen deze
kaart geeft de huidige selector bij beginnersdoel45 een pending420min/P 393.8-draft
met waarschuwing. Rekenbaarheid is dus geen geschiktheid. Een verkeerde scope kan
zowel weekcapaciteit als de volgende geplande basis sterk verhogen.
**Bevoegdheid:** Joren voor trainingsindeling/doelgroep; eigenaar voor productscope.

## D. RPE per intervalblok

**Bron en code:** bron-RPE 9–10 beschrijft de Z5-focus, niet elk Z2-herstelblok.
De huidige validator verwacht dat blok-RPE binnen een totale template-range valt;
die range is niet hetzelfde als de smallere bronfocus. Oud RPE 3 blijft historischZ1;
de nieuwe mapping geeft3–4=Z2. Rust aan de zwemmuur is geen zone/RPE-blok.

**Advies/besluitvraag:** behoud bronfocus apart en bevestig blokbereiken volgens
de nieuwe mapping per expliciete zone, met sessiefeedback als apart veld. Laat
engineering de versiegebonden representatie/aggregate-validatie aanpassen zonder
bronwaarden te overschrijven. Alternatief: lever eigen expliciete blok-RPE's aan.
**Voorbeeld/gevolg:** TR-BIKE-020 bevat6×30sZ5=3min plus Z2/Z1. Z2 krijgt voorgesteld
RPE 3–4, niet9–10. De sessie blijft gemengd en krijgt geen hele-sessie-RPE-correctie;
zonder geschikte meting blijft automatische weekbelasting onbeschikbaar.
**Bevoegdheid:** Joren voor uitvoeringsintentie, engineering voor het datacontract.

## E. Afstandsgebaseerd zwemmen

**Bron en code:** de PDF geeft vaste TSS per 100m en stilstaande rust0; de CSS1:55
is geen uitgewerkte persoonsafhankelijke schaalmethode. De huidige projectie zet
P van afstands-only zwemmen op onbekend. De planner kan zulke afstanden/dagen wel
representeren, maar kent dan geen volledige tijd-/80/20-dekking. V2 heeft echt
gepland T en bevestigd werkelijk A nodig.

**Advies/besluitvraag:** accepteer de vaste gepubliceerde matrix als versiegebonden
geplande afstand-P, met T onbekend, expliciete rustevents en zichtbare onvolledige
tijddekking. Houd afstands-RPE-realisatie en CSS-schaling uitgeschakeld; vraag alleen
een aparte wetenschappelijke specificatie als die gewenst zijn. Bepaal afzonderlijk
hoe aangetoonde muurrust en actieve/verstreken tijd meetcompleetheid beïnvloeden.
Alternatief: zwemselectie blijft uitgesloten totdat een onafhankelijk goedgekeurd
voorschrift echte geplande tijd bevat; nooit tijd uit afstand verzinnen.

**Voorbeeld/gevolg:** TR-SWIM-010=6×1.44+10×1.98=28.44, bron 28.4;150s muurrust0.
Een afgeronde bron-P is geen gemeten prestatie. Bij35min verstreken tijd en 30min
Z2-meting blijft het huidige resultaat21.6 met gedeeltelijke dekking. Onbekende/
gedeeltelijke voltooiing houdt de volgende week tegen; een afstandsratio vervangt
A/T niet. **Bevoegdheid:** Joren voor methodiek/bewijssemantiek, eigenaar voor scope,
engineering voor expliciete onbekende tijd en behoud van meetvoorrang.

## F. Activatiebereik en vrijgave

**Bron en code:** alle 61 bronnen zijn aanwezig;439 gerichte tests slagen. Enkele
automatische build-zoekacties overschreden het8s-reviewbudget, terwijl expliciete
combinaties de echte planner wel doorstaan. Zwemtijddekking en doelgroep zijn nog
geen volledige haalbaarheidstoets. PostgreSQL/pgTAP blijft door de eigenaar
uitgesteld tot pre-beta; productie/staging is niet gewijzigd.

**Advies/besluitvraag:** geef pas na A–E, slicesC1–C8 en de open verificatiepoorten
een apart prospectief activatiebesluit met de exacte release/hashset en rollback.
Alternatief: een expliciet goedgekeurde deelset eerst; geen stilzwijgende invoering
van 61 rijen. **Voorbeeld/gevolg:** een nieuwe release verandert0 historische
voorkomens. In de test met vorige P 150 geeft volledige bruikbare week 133.6 een
volgend doel 165; een onbekende sessie houdt150 vast. Activatie mag die historie
niet herschrijven of onbekende gegevens als nul behandelen. **Bevoegdheid:**
eigenaar voor vrijgave; vereiste wetenschappelijke/database/releasepoorten blijven
afzonderlijk gelden. Deze brief is geen activatietoestemming.

## Antwoordregistratie

Graag één expliciet antwoord per letterA–F, met eventuele aangepaste rijmapping.
Alle daadwerkelijke antwoorden worden apart met datum, eigenaar, bronreferentie,
versie en exacte acceptatievoorwaarden vastgelegd. Huidige status: **A–F OPEN**.
Technische voorstellen tellen niet als Joren-akkoord.

Onderbouwing: [alle 61 resultaten](JOREN_THREE_SPORT_FINAL_RECONCILIATION.md),
[planningssimulatie](JOREN_THREE_SPORT_PLANNING_SIMULATION.md),
[implementatievolgorde](JOREN_THREE_SPORT_INTEGRATION_SEQUENCE.md).
| Bron | Oorspronkelijk bestand | Bytes | SHA-256 |
| --- | --- | --- | --- |
| RUN | Looptrainingen_Definitief_Optie1.xlsx | 7198 | dd93449eba8ad88e7a8d430897c4ec3034a9d92229ae42b675984243ed4360a3 |
| BIKE | Fietstrainingen_Definitief_Optie1.xlsx | 7376 | 5e327e48ce6d83cd3e61397ad062f77e6017b36289167c4aaf33e28a0b4f95df |
| SWIM | Zwemtrainingen_Definitief_Optie1.xlsx | 7333 | bd7d62439d77a0730f2b0eed6ab10b3d7c4d03bdc1645089024184b0b43e2674 |
| SWIM spec | Specificatie Zwem TSS.pdf | 149021 | ec1d141f60925628ca78b45801fedf8074c71adf57d9c877ada2e34199f5a59a |

Het originele loopbestand staat in `F:\Projecten Business\Start23\Code\docs\trainings`.
De originele fiets- en zwembronnen staan in
`F:\Projecten Business\Start23\Code\.worktrees\joren-realized-tss-v2\docs\trainings`.
Alle vier originele bestanden zijn ongewijzigd op deze locaties. Aanlevering is
bevestigd; catalogusversies en methodische acceptatie zijn afzonderlijke besluiten.

Ja — ik zou die vragen veel concreter maken en telkens **“wat staat er nu / wat geeft jouw document / wat moet jij bevestigen”** erbij zetten. Belangrijk: bij het zogenaamde “roadmap-model” bestaat voor de nieuwe 2-maandenbaseline **nog géén definitieve formule**. De roadmap definieert alleen de inputs en zegt expliciet dat Joren de formule nog moet vastleggen. Het oude model `reported hours × 40` is juist vervangen/superseded. 

Je kunt dit ongeveer zo naar Joren sturen:

### Vragen voor definitieve Phase 13-specificatie

**1. Startbaseline / onboarding: welk model is definitief?**

In de huidige roadmap staat dat we voor de nieuwe baseline **2 maanden trainingshistoriek** willen gebruiken, per discipline:

* zwemmen: gemiddeld **meter/week + sessies/week**
* fietsen: gemiddeld **km/week + sessies/week**
* lopen: gemiddeld **km/week + sessies/week**

De beoogde formule is daar nog niet ingevuld; conceptueel staat er dus alleen:

`Baseline_swim = f(gemiddelde meter/week, sessies/week, Z2-aanname)`

`Baseline_bike = f(gemiddelde km/week, sessies/week, Z2-aanname)`

`Baseline_run = f(gemiddelde km/week, sessies/week, Z2-aanname)`

`Totale baseline = combinatie van de drie discipline-baselines`

De exacte `f(...)`, combinatie, afronding, minimum/maximum en onvoldoende-historiek-regels ontbreken nog. De oudere geïmplementeerde richting `reported hours × 40` is inmiddels expliciet superseded. 

In jouw nieuwe onboarding-PDF staat echter een ander model: **gemiddelde uren/week van de afgelopen maand**, met RPE 4 / IF 0,75 als vaste intensiteit. 

Daar is de formule:

`Start-TSS = uren/week × (IF² × 100) × sport-multiplier`

met `IF = 0,75`, dus:

* zwemmen: `uren × (0,75² × 100) × 0,9 = uren × 50,625`
* fietsen: `uren × (0,75² × 100) × 1,0 = uren × 56,25`
* lopen: `uren × (0,75² × 100) × 1,15 = uren × 64,6875`

Dus concreet: **welk model moet definitief gebruikt worden?**

**A.** 2 maanden + afstand/week + sessiefrequentie
of
**B.** 1 maand + uren/week × vaste IF 0,75?

Als A de bedoeling is, hebben we nog de exacte formule nodig om afstand + frequentie naar start-TSS/private load om te zetten.

Ook graag exact bepalen wat bij **0 trainingshistoriek** gebeurt. In jouw document staat nu bijvoorbeeld 40–50 TSS voor een volledige beginner, maar voor de code moeten we één deterministische regel hebben. 

---

**2. Calibratie voor lopen en fietsen: is deze formule definitief?**

Zoals ik je document begrijp:

`LTHR = gemiddelde HR / RPE-ankerfactor`

Met:

| RPE | factor t.o.v. LTHR |
| --: | -----------------: |
|   1 |               0,70 |
|   2 |               0,78 |
|   3 |               0,84 |
|   4 |               0,88 |
|   5 |               0,91 |
|   6 |               0,94 |
|   7 |               0,97 |
|   8 |               1,00 |
|   9 |               1,03 |
|  10 |               1,06 |

Bijvoorbeeld uit jouw PDF:

`145 bpm / 0,88 = 164,77 → 165 bpm LTHR`

Daarna:

* Z1 `<82% LTHR`
* Z2 `82–89%`
* Z3 `90–95%`
* Z4 `96–100%`
* Z5 `>100%` 

**Is dit exact het definitieve algoritme voor zowel lopen als fietsen?**

En hoe moeten we afronden?

Bijvoorbeeld als:

`LTHR × 0,82 = 135,3 bpm`

wordt de grens dan 135 of 136 bpm?

We moeten uiteindelijk voor **iedere gehele bpm exact één zone** hebben zonder overlap of gaten.

---

**3. Wat moet gebeuren bij een verdachte calibratie-uitkomst?**

In het voorbeeld staat:

`gemiddelde HR = 125`
`RPE = 6`
`LTHR = 125 / 0,94 ≈ 133 bpm`

Daar staat vervolgens dat bij bijvoorbeeld `<140 bpm` de app kan waarschuwen **of** kan wachten op een tweede training. 

Voor de implementatie moeten we dit exact weten.

Is `<140 bpm`:

* een echte vaste grens;
* enkel een voorbeeld;
* leeftijds-/disciplineafhankelijk?

En wat doet de app exact?

**Optie A:** zones berekenen en als pending tonen met waarschuwing.
**Optie B:** geen zones berekenen en tweede calibratiesessie eisen.
**Optie C:** iets anders.

Ook graag eventuele andere invalid/outlier-regels vastleggen.

---

**4. Zwemcalibratie: is CSS/tempo?**

Voor zwemmen staat in jouw document:

`CSS = gemiddelde pace / RPE-multiplier`

waarbij pace in seconden/100 m wordt gebruikt.

De RPE-multipliers zijn:

| RPE | multiplier |
| --: | ---------: |
|   1 |       1,25 |
|   2 |       1,18 |
|   3 |       1,12 |
|   4 |       1,08 |
|   5 |       1,06 |
|   6 |       1,04 |
|   7 |       1,01 |
|   8 |       1,00 |
|   9 |       0,96 |
|  10 |       0,92 |

Bijvoorbeeld:

`120 sec/100m / 1,12 = 107,14 sec ≈ 1:47/100m CSS`

Daarna:

* Z1 `>115% CSS`
* Z2 `108–114%`
* Z3 `103–107%`
* Z4 `98–102%`
* Z5 `<98%` 



Ook hier graag de exacte afrondings- en boundaryregels.

---



**6. Wat doen we als time-in-zone-data onvolledig is?**

Voorbeeld:

Totale looptraining = 60 minuten.

Maar door slechte sensorverbinding hebben we slechts:

* 10 min Z1
* 20 min Z2
* 8 min Z3
* 3 min Z4

Dus maar **41 van de 60 minuten** heeft betrouwbare HR-zone-data.

Met de nieuwe formule kunnen we voor die 41 minuten berekenen:

`10×0,58 + 20×0,92 + 8×1,38 + 3×1,84`

maar wat doen we met de ontbrekende 19 minuten?

Moeten we:

* alleen de 41 minuten meetellen;
* de 41 minuten extrapoleren naar 60 minuten;
* de volledige load ongeldig/onvoldoende betrouwbaar verklaren;
* een fallback gebruiken;
* een minimum coverage eisen, bijvoorbeeld X%?

De roadmap vraagt expliciet dat ontbrekende/partiële zone-tijd deterministisch behandeld wordt. 

Ook graag aangeven wat we doen bij **distance-only zwemmen** wanneer er geen bruikbare duration/time-in-zone beschikbaar is.

---

**7. De sRPE-formule zonder zones: moet die nog gebruikt worden in de MVP?**

In jouw document staat voor onbekende zones:

`TSS = (duur in uren × IF² × 100) × sport-multiplier`

met:

RPE 1 → IF 0,45
RPE 2 → 0,55
RPE 3 → 0,65
RPE 4 → 0,75
RPE 5 → 0,82
RPE 6 → 0,88
RPE 7 → 0,94
RPE 8 → 1,00
RPE 9 → 1,05
RPE 10 → 1,15

Bijvoorbeeld 60 min lopen, RPE 4:

`1 × 0,75² × 100 × 1,15`
`= 64,69 TSS` 

Maar onze huidige MVP-beslissing is dat een HR-monitor verplicht wordt en dat RPE-only niet meer als normale trainingsroute beschikbaar is. De roadmap zegt ook dat de huidige RPE-duration-load wordt vervangen door time-in-zone multipliers. 

Daarom graag expliciet bevestigen:

**Moet deze sRPE-formule nog bestaan als fallback?**

Zo ja:

* exact wanneer mag die gebruikt worden?
* alleen wanneer zones nog niet gekend zijn?
* ook wanneer HR tijdens een training ontbreekt?
* geldt ze ook voor zwemmen?
* krijgt zo'n load een lagere reliability/status?

Of is deze volledige sectie enkel historische context en **niet bedoeld voor de nieuwe MVP-ruleset**?

---

**8. Fatigue, missed training en sickness: exacte formule**

De huidige Phase 13-richting is:

* **sick week:** bewaren voor history/audit, maar uitsluiten uit load/planningberekeningen;
* **fatigue/missed training:** vertrekken van de lagere werkelijk gerealiseerde private load;
* daarna daarop progressie toepassen.

Conceptueel:

`Target_next = Realized_load_current × (1 + p)`

waar `p` de progressiefactor is.

Bij bijvoorbeeld `p = 10%` en 300 gerealiseerde TSS:

`300 × 1,10 = 330 TSS`

Maar in de roadmap staat expliciet dat **10% momenteel slechts een voorbeeld is en nog geen definitief vastgelegde boundary**. 

Kun je dus aangeven:

* exacte `p`;
* geldt dezelfde `p` na fatigue en missed training?
* wanneer wordt géén progressie toegepast?
* wat is exact de bron/marker waarmee een week als `sick` wordt beschouwd?
* blijft de huidige 42-day baseline enkel als fallback bestaan voor normale ontbrekende historie, of vervalt die volledig?

De huidige implementatie gebruikt nog een beschikbare 42-day realized baseline in BR-004 en een historische progression-regel; die moet dus bewust behouden of vervangen worden. 

---

**9. Taper: graag de volledige deterministische formule**

We hebben nu beslist dat taper **niet meer per volledige week** werkt, maar in de **7–10 dagen onmiddellijk vóór race day**. 

Wat nog nodig is:

**Hoe kiezen we 7, 8, 9 of 10 dagen?**

Bijvoorbeeld:

`Taper_start = race_date - N dagen`

waar `N ∈ {7,8,9,10}`.

Maar wat bepaalt N?

* raceafstand?
* discipline?
* trainingsbelasting?
* raceprioriteit?
* altijd dezelfde waarde?

En hoe verlagen we de load tijdens taper?

Bijvoorbeeld moet het iets zijn zoals:

`Taper_target_day = normal_target × reduction_factor(day)`

of:

`Taper_total = normal_load × factor`

We hebben dus de exacte reduction factors/curve nodig.

Ook graag bepalen:

* hoe partial Monday–Sunday weeks behandeld worden;
* wat er op race day zelf gebeurt;
* hoe overlaps met recovery behandeld worden;
* wat gebeurt bij meerdere races dicht bij elkaar;
* of swim/bike/run dezelfde reductie krijgen.



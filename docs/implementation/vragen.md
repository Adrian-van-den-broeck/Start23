

### 2. Calibratie: het concept is er, maar ik zou nog verduidelijking vragen vóór dit de definitieve Phase 13-regel wordt

Voor lopen en fietsen definieert Joren een mapping van RPE naar % van LTHR. Bijvoorbeeld: RPE 4 = 88%, dus een gemiddelde hartslag van 145 bpm leidt tot een geschatte LTHR van ongeveer 165 bpm. Daarna worden daar de vijf hartslagzones van afgeleid. 

Voor zwemmen gebruikt hij in plaats daarvan **tempo/CSS** en reverse-engineert hij CSS vanuit de RPE-multiplier. 

Dat is op zich een bruikbaar deterministisch concept, maar je Phase 13-specificatie vraagt meer: exacte afronding, zonegrenzen, geldige inputs, gedrag bij ontbrekende data, outliers/data-quality-regels enzovoort. 

Het duidelijkste voorbeeld is de lage-LTHR-situatie. Joren schrijft dat als het berekende omslagpunt verdacht laag is, bijvoorbeeld `<140`, de app **een waarschuwing kan geven of op een tweede training kan wachten**. 

Voor software is dat niet precies genoeg.

Er moet vastgelegd worden:

**Is `<140 bpm` effectief de regel, of enkel een voorbeeld? En wat gebeurt er dan exact: waarschuwing + pending voorstel, of volledig blokkeren en een tweede sessie eisen?**

Ook is er een belangrijk punt rond zwemmen: je roadmap beschrijft de nieuwe calibratie rond tekstuele RPE + **gemiddelde hartslag**, terwijl Joren voor zwemmen **pace/CSS** gebruikt.  

Dat kan perfect de bedoeling zijn, maar het moet expliciet bevestigd worden zodat Astra niet zelf beslist welk document voorrang krijgt.

### 3. Zone-load-berekening: de kern is aanwezig

Dit is waarschijnlijk het tweede sterkste onderdeel.

Joren geeft vaste TSS/min-coëfficiënten:

| Zone | Zwemmen | Fietsen | Lopen |
| ---- | ------: | ------: | ----: |
| Z1   |    0,45 |    0,50 |  0,58 |
| Z2   |    0,72 |    0,80 |  0,92 |
| Z3   |    1,08 |    1,20 |  1,38 |
| Z4   |    1,44 |    1,60 |  1,84 |
| Z5   |    1,80 |    2,00 |  2,30 |

En de load wordt berekend als de som van:

**tijd in zone × zonecoëfficiënt**. 

Dat past mooi bij de nieuwe Phase 13-richting.

Maar één vereist punt ontbreekt nog: wat doe je als HR-zone-data **onvolledig** is?

Bijvoorbeeld:

60 minuten lopen
maar slechts 41 minuten geldige HR-zone-data.

Moet Wombo dan:

* enkel die 41 minuten gebruiken?
* extrapoleren naar 60?
* de load weigeren?
* markeren als incomplete data?
* een fallback gebruiken?

Astra mag dat niet zelf verzinnen.

Daarnaast heb je nog het speciale geval van **distance-only swimming**, waar de roadmap expliciet zegt dat je geen load mag verzinnen zonder gedefinieerde regel.

### 4. De onboarding baseline is het grootste probleem

Hier zit de grootste mismatch met je huidige roadmap.

De roadmap verwacht een **twee-maanden discipline-specifieke geschiedenis** met:

* zwemmen: gemiddelde meter/week + sessies/week
* fietsen: gemiddelde km/week + sessies/week
* lopen: gemiddelde km/week + sessies/week

en Joren zou moeten bepalen hoe dat naar de startbaseline vertaald wordt. 

Maar de pdf vraagt in plaats daarvan:

> gemiddeld aantal **uren per week van de afgelopen maand**

voor elke discipline. 

Daarna wordt RPE 4 / IF 0,75 aangenomen en wordt een vaste start-TSS per uur berekend. 

Dus dit is niet gewoon “nog wat detail ontbreekt”.

Dit is eigenlijk **een ander baseline-model** dan wat nu in je roadmap staat.

Ook bij zero-base is er nog iets vaags: daar staat dat een beginner bijvoorbeeld **40–50 TSS** krijgt. 

“Bijvoorbeeld 40–50” is geen deterministische regel die je rechtstreeks in code kunt gieten.

### 5. Er is ook een conflict rond RPE-only load

Dit is belangrijk.

Het TSS-document bevat een volledig alternatief:

> **TSS-berekening zonder zones (sRPE)**

met RPE → IF-waarden en de formule:

`duur × IF² × 100 × sport multiplier`. 

Maar de huidige MVP-richting heeft RPE-only juist grotendeels verlaten, met HR-monitor als vereiste en Phase 13 gericht op time-in-zone load.

Dus ik zou **niet zomaar toestaan dat Astra dit sRPE-gedeelte implementeert omdat het in Jorens pdf staat**.

Er moet eerst bevestigd worden of dit:

**A. verouderd is en niet meer voor de MVP geldt**, of
**B. nog als specifieke fallback bedoeld is.**

Als B klopt, dan moet de roadmap eerst aangepast worden.

### Er zijn daarnaast nog Phase 13-beslissingen die deze drie pdf’s niet afdekken

Je roadmap vraagt nog steeds exacte regels voor sickness/fatigue/missed training en taper.

Zo moet nog exact bepaald worden:

* welke progressiefactor na fatigue/missed training geldt;
* hoe 7 versus 8 versus 9 versus 10 dagen taper gekozen wordt;
* welke reductiefactoren/curve gelden;
* hoe partial weeks en race-day boundaries werken. 

### Wat ik Joren nog zou vragen

Ik zou hem niet alles opnieuw laten schrijven. Gewoon deze punten laten verduidelijken:

1. **Baseline:** gebruiken we definitief het roadmap-model met 2 maanden + meters/km + sessies/week, of zijn pdf-model met 1 maand + uren/week? Geef één definitieve formule met afronding, zero-base-regel en min/max-guards.
2. **Zwemcalibratie:** is zwemmen bewust een uitzondering waarbij pace/CSS gebruikt wordt in plaats van gemiddelde HR?
3. **Calibratie-validiteit:** wat zijn exact de invalid/suspicious-result-regels? Is `<140 bpm` echt een grens? Warning of blokkering? Wanneer is een tweede sessie verplicht?
4. **Boundary/rounding:** exact vastleggen hoe zonegrenzen en afronding werken zodat elke bpm/pace precies in één zone valt.
5. **Onvolledige HR-data:** exact bepalen wat er gebeurt als slechts een deel van de training geldige time-in-zone-data heeft, inclusief distance-only swims.
6. **sRPE-TSS:** bevestigen of “TSS zonder zones” voor de MVP vervalt of nog als specifieke fallback moet blijven bestaan.
7. **Fatigue/missed training:** exacte progressiefactor vastleggen.
8. **Taper:** exact bepalen hoe 7–10 dagen gekozen wordt en welke load-reductie toegepast wordt.

Daarna zou ik Phase 13 pas als **echt implementation-ready** beschouwen.

Het goede nieuws is wel dat je al dicht zit: de RPE-tabel en de time-in-zone-coëfficiënten zijn bruikbaar en ook de calibratiebasis is grotendeels aanwezig. **De grootste blocker is het conflict rond de onboarding baseline plus enkele ontbrekende deterministische edge rules.**

Ik zou dus voorlopig nog **geen Astra-credits verbranden aan volledige Phase 13-implementatie**. Eerst deze punten sluiten, daarna Astra High gebruiken om de nieuwe Phase 13-regels correct in de bestaande codebase te integreren.

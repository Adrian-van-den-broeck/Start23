# V6 beleidsbesluiten en goedkeuringspoorten

2026-11-05, Europe/Amsterdam. Privé ontwikkelrapport; uitsluitend offline.

De sandbox rekent toekomstige beleidskeuzes door. Geslaagde simulaties zijn geen
wetenschappelijke goedkeuring van Joren en maken geen enkele training actief.

## Wat de labels betekenen

| Label | Status |
| --- | --- |
| CONFIRMED JOREN RULE | Triatlon 50/30/20 als zachte streefverdeling; maximaal 20% HOGE actieve tijd per sport en lokale maandag-zondagweek; nul hoog mag; Z1/Z2 laag en Z3-Z5 hoog; stilstaande zwemrust telt niet mee; waar haalbaar één geschikte training per sport. Door eigenaar doorgegeven; geen verzonnen handtekening/reviewreferentie. |
| PROPOSED PRODUCT POLICY | Hard expliciet weekbudget, selectievolgorde, vergelijkingsmaat, metadata-contract en eventuele omgang met UNVERIFIED. Niet operationeel goedgekeurd. |
| NUMERICALLY RECONSTRUCTED METHOD | Exacte hypothetische Decimal-invoer uit weergegeven bron-P. Geen akkoord op bronprecisie, Z3-IF, zwemreferenties of operationele P. |
| UNAPPROVED ATHLETE METADATA | Voor alle 77 echte trainingen ontbreekt goedgekeurde individuele geschiktheid. Een HR-sensor/zwempace bewijst geen belastbaarheid. |
| TESTED OFFLINE BEHAVIOR | 33 rekenkundige combinaties binnen 45; 23 daarvan voldoen ook aan de oude doelpassing; echte automatische 45,1 en handmatige 43,1 apart gereproduceerd; 40 regressies vergeleken. |
| ACTIVE PRODUCTION BEHAVIOR | Oude plannerdoelstellingen/toleranties blijven gelijk. Geen nieuw budgetbeleid, tijdcontrole of 50/30/20-rangschikking geactiveerd. |

## Concrete besluiten

| Poort | Benodigd besluit/evidence | Wie | Tot die tijd |
| --- | --- | --- | --- |
| Bronmethode/precisie | Autoritatieve operationele P, volledige IF²/Z3/zwemreferentie- en afrondingsconventie, versie en Realized V2-compatibiliteit. Weergegeven 15,1 is alleen exacte hypothetische invoer onder de benoemde experimentmethode. | Joren + eigenaar, verantwoordelijke reviewer waar vereist | SOURCE_METHOD_UNAPPROVED; operationele P blijft geblokkeerd. |
| Weekbudget | Scope van strikt geautoriseerd plafond en versie; geen algemene 45-grens voor ervaren atleten of historie. | Eigenaar/Joren | Automatisch 45,1 blijft LEGACY_VALID, maar prospectief 0,1 te hoog. Geen runtimewijziging. |
| Selectievolgorde | Veiligheid/geschiktheid, bestaande restricties, budget, haalbare sportdekking, verdeling, benutting, bestaande tie-breaks: expliciet goedkeuren of aanpassen. | Eigenaar/Joren | Geen nieuwe standaardrangschikking. |
| Verdeling versus benutting | Keuze maat/denominator en prioriteit; eventuele oude minimumvulling behouden of vervangen. Geen willekeurige tolerantie of sportcaps. | Eigenaar/Joren | 40,2 verdelingsgericht en 44,8 benuttingsgericht blijven vergelijkbare offline getuigen. |
| Individuele geschiktheid | Beginner, sportspecifieke ervaring, bevestigde capabilities, duur/afstand, lange sessies, blessure, herstel/taper, herhaling/frequentie en fase/intensiteit; herleidbaar naar atleet/templateversie/week/context. | Joren/verantwoordelijke reviewer; eigenaar voor contract/inname | ATHLETE_SUITABILITY_UNAPPROVED; 7 uur fietsen wordt nooit automatisch beginnersgeschikt. Geen vaste duurgrens of medische regel verzonnen. |
| Zwemtijd | Betrouwbaar voorgeschreven actieve duur waar numerieke controle nodig is; apart besluit welke consumenten expliciet UNVERIFIED mogen verwerken. | Joren + eigenaar | Geen numeriek zwem-/totaalweekakkoord, ook niet bij volledig Z2. Geen CSS/afstand/referentiepace als minuten. |
| Onhaalbare sportdekking | Veilig gedrag als geen geschikte drie-sportcombinatie onder budget past; betekenis van deelplan/rust/uitstellen. | Eigenaar/Joren | Bestaande restricties blijven leidend; geen extra belasting, herschaling of blessureherverdeling. |
| BUILD/intensiteit | Bestaande hoog-load/session-minima versus maximaal 20% actieve tijd, inclusief nul hoog: versieer expliciete toekomstige integratie/supersessie. | Joren + eigenaar/reviewer | Beide worden apart gerapporteerd; planner blijft gelijk. |
| Activatie/release | Catalogusopvolging/retirement, wetenschappelijke review, identiteit/provenance, latere technische/database/devicepoorten en apart releasebesluit. | Eigenaar/verantwoordelijke reviewers | Geen C3-C8, migratie, activatie of publicatie. |

## Wat kan onafhankelijk worden onderzocht?

Een expliciet UNVERIFIED zwemresultaat verhindert niet dat de sandbox exact
budget, structurele sportdekking, aandelen en bekende loop-/fietstijd berekent.
Die resultaten blijven hypothetisch. Het verhindert wél een numerieke claim dat
de zwemweek aan de tijdgrens voldoet of in beschikbare minuten past. Of later
een atleetgericht concept met dat onbekende resultaat mag doorgaan, is nog een
product-/Joren-besluit; de sandbox keurt dat niet goed en voegt geen uitzondering toe.
Progressie/Realized V2 blijven afhankelijk van hun eigen registratie-evidence.

De handmatige 43,1-getuige is geen automatisch gekozen plan. De echte automatische
combinatie BIKE-022/RUN-027/SWIM-021 is 45,1; de expliciete handmatige
BIKE-023/RUN-024/SWIM-021 is 43,1. Beide missen goedgekeurde geschiktheid en
zwemtijd. De laagste drie-sportcombinatie is 29,3, maar voldoet niet aan de oude
doelpassing. Bij herstel 25,86 en taper 15,085 bestaat binnen de geteste volledige
één-per-sportcombinaties geen oplossing. Er wordt geen uitzondering uit afgeleid.

Ontbrekende metadata is een kennisgat, geen bewijs van lichamelijke onmogelijkheid.
Een afzonderlijke synthetische blessurecasus toont dat sportdekking niet mag worden
afgedwongen door restricties te versoepelen. Synthetische toestemming in tests
is nooit op de 77 echte workouts toegepast.

## Grenzen van levering

Alle bestaande planneroptimalisaties, A3-A9, C1/C2/C2.1/V6 en Realized TSS V2
blijven behouden. De bekende `current:build_4`-timeout blijft een performancepoort:
acht seconden, voortgaande toestand-/geheugengroei, geen bewijs van onhaalbaarheid.
Geen hogere deadline, nieuwe zoekcap of scorewijziging is geprobeerd.

Backendtests, lint/format/strict mypy en de 40-casusregressie worden met exacte
resultaten en Git-verwijzingen in het [leverrapport](JOREN_V6_PROSPECTIVE_POLICY_SANDBOX.md)
vastgelegd. Database/pgTAP/RLS en device/releasepoorten blijven extern open; deze
offline taak heeft ze niet uitgevoerd of gesloten. Geen productiebenadering,
bronwerkboekwijziging, historische herberekening, actieve configuratie/catalogus,
migratie, push, merge, deployment of Play Store-publicatie.

Exact geverifieerde implementatie/evidence Git SHA:
`ad8a327d0d50ddc2e2e91c48c799f2f3d27d962c`. De daaropvolgende documentatiecommit
legt deze onveranderlijke verwijzing vast. De uiteindelijke levertip staat in het
afleverbericht en is opvraagbaar via `git rev-parse experiment/joren-v6-policy-sandbox`.

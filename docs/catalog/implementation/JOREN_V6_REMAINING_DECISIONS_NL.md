# Joren V6 resterende besluiten

2026-11-05, Europe/Amsterdam. Private developer validation; no activation.

De 77 bronstructuren zijn gevalideerd. De kleinere trainingen lossen het
rekenkundige tekort voor de eerste 45-TSS-week op: er bestaan 33 rustige
combinaties met één training per sport onder 45. De echte planner accepteert
de expliciete 43,1-combinatie als concept. Dit is geen geaccepteerd standaardplan
en geen bewijs dat iedere beginnende atleet deze trainingen aankan.

## Besluiten die al vaststaan

- IF² als methoderichting en Z1=.55/Z2=.75/Z4=.98/Z5=1.15 uit de C2-besluiten.
- Z3-Z5 zijn hoog en Z1-Z2 laag volgens de bestaande intensiteitsclassificatie.
- Maximaal 20% hoge **actieve tijd per sport per week**. Nul procent hoog mag.
- Voor triatlon is BIKE/RUN/SWIM 50/30/20 van geplande belasting een **streefverdeling**.
  Dit verhoogt geen weekbudget en vervangt geen enkelvoudig sportdoel.
- De zes 300m Z3-blokken moeten Z2 zijn. V6 bevat dit al, inclusief 600m Z2/0m Z3.
- Stilstaande zwemrust heeft geen belasting en geen actieve zwemtijd.
- Eén geschikte training per sport voor de gewenste eerste beginnersweek; de
  nulhistorie-basis blijft 45. Geen generieke verhoging of verkorting is toegestaan.

De huidige opdracht van de eigenaar geeft deze Joren-besluiten door. Intake:
5 november 2026. Oorspronkelijke beslisdatum, handtekening of onafhankelijke
wetenschappelijke reviewreferentie is niet aangeleverd en wordt niet verzonnen.

## Nog benodigde besluiten en implementatiepoorten

| Onderwerp | Concreet ontbrekend besluit / gevolg |
| --- | --- |
| Z3-IF en zwemreferentie | Bevestig of corrigeer .88 en 2.17/2.00/1.83/1.67/1.50 minuten per 100m. Dit is nu een passende reconstructie, geen formeel akkoord. |
| Volledige bronformule en precisie | Leg normalisatie, factor eenmaal, eventuele tussentijdse afronding, HALF_EVEN-weergave en opslag vast. Exact seconden/60 wijkt bij SWIM-011–014 af. |
| Operationele geplande P | Kies per versie expliciet tussen bronwaarde/weergave en exact berekende P, met methode-, precisie- en Realized V2-compatibiliteit. Tot dan blijft P operationeel geblokkeerd. |
| Persoonlijke geschiktheid | Accepteer rijmetadata/fasen, benodigde capabilities, beginners- en lange-sessiescope, herhalingen en blokbegeleiding. Een beschikbare HR-/pacecapability bewijst geen belastbaarheid; 10 minuten lopen is niet universeel geschikt. |
| Selectie bij streefverdeling | Leg prioriteiten en tie-breaks vast tussen persoonlijke geschiktheid, één per sport, weekbudgetbenutting en nabijheid tot 50/30/20. De 40,2- en 43,1-voorbeelden illustreren verschillende afwegingen. Geen nieuwe harde tolerantie verzonnen. |
| Ontbrekende zwemduur | Bepaal welke consumenten/plannen met expliciet UNVERIFIED mogen doorgaan. Een geheel Z2-voorschrift is rustig, maar heeft geen numeriek geverifieerde actieve-tijdnoemer. Lever alleen echte betrouwbare voorgeschreven tijd als tijd vereist is. |
| Bestaande planner tegenover nieuw beleid | De selector laat nog kleine budgetoverschrijdingen en een lange-sessie-fallback toe, gebruikt oude hoog-loadfilters en handhaaft de nieuwe streefverdeling/tijdgrens nog niet. Latere afzonderlijke integratie moet dit oplossen zonder veiligheid te verzwakken. |
| Lage recovery/taper-budgetten | De 43,1-combinatie past niet bij 25,86/15,085. Geen automatische verhoging, extra herstel-/taperfactor of planplicht afleiden. Fail-closed blijft gelden waar geschikte combinaties ontbreken. |
| Automatische zoektijd | Acht historische timeoutslots blijven reproduceerbaar; V6 heeft zes automatische timeouts, inclusief build4. Een expliciet passend concept sluit deze poort niet. Geen timeoutverhoging toegepast. |
| Identiteit en release | De voorgestelde bronopvolging is volledig traceerbaar; formele vervanging/retirement van bestaande actieve templates, wetenschappelijke acceptatie en latere activatie blijven apart. |

Geen formule, veiligheidslimiet, atleetminuut of nieuw productbeleid is ingevuld om
een geslaagd resultaat af te dwingen. Historische bronmethoden en voorkomens
blijven onveranderd. PostgreSQL/pgTAP voor Realized V2 blijft uitgesteld conform
opdracht; er is geen productie-database benaderd en geen migratie gemaakt.

Het resultaat blijft **gedeeltelijke validatie**: bronstructuren en getoonde
rekenwaarden zijn compleet geverifieerd, maar operationele methode, persoonlijke
geschiktheid, zwemduurdekking, beleidsintegratie en automatische planning zijn
geen gesloten poorten. Er is niets geactiveerd, gepusht, gemerged of uitgerold.

Verification and immutable delivery commits: [integration report](JOREN_V6_CATALOG_INTEGRATION_REPORT.md).

# Joren V6: resterende operationele goedkeuringen

5 november 2026, Europe/Amsterdam. Versie:
`joren-v6-final-prospective-policy-1`. Privé ontwikkelrapport, uitsluitend offline.

## Twee besluiten zijn nu bevestigd

Joren verduidelijkte deelweken met: **“Ja een gedeeltelijk schema met een of twee
soorten inderdaad”**. Een geschikt en veilig deelplan mag prospectief als drie
sporten niet binnen het geautoriseerde budget passen. De exacte keuze tussen
veilige alternatieven blijft open. Geen verplichte sportvolgorde, hogere belasting
of nieuwe herstel-/taperfactor volgt hieruit.

Joren antwoordde over intensiteitsminima: **“We zullen het zonder ondergrens
doen.”** Ook BUILD mag 0% hoge actieve tijd bevatten. Maximaal 20% per sport per
atleetlokale week blijft gelden; Z1/Z2 laag, Z3–Z5 hoog, stilstaande zwemrust
uitgesloten. Dit maakt niet ieder rustig BUILD-schema geschikt.

De exacte oorspronkelijke vragen, eerdere antwoorden en statuswijzigingen staan
in het [nieuwe register](JOREN_V6_FINAL_POLICY_DECISION_UPDATE.md). Het oude
deelgoedkeuringsregister blijft historisch intact. De oude openstaande vraag over
deelplan versus geen plan en de vraag naar een BUILD-ondergrens zijn hiermee
afgehandeld als prospectief beleid; zij zijn geen open besluit meer.

## Wat bevestigd blijft

IF Z1–Z5 = .55/.75/.88/.98/1.15. Zwemreferenties =
2.17/2.00/1.83/1.67/1.50 min/100m. Geplande actieve zwemtijd mag daarmee offline
worden geschat met `ESTIMATED_FROM_APPROVED_REFERENCE_PACE`; uitgevoerde tijd
wordt nooit afgeleid. Bevestigde getallen keuren niet de volledige TSS-methode goed.

Veiligheid en individuele geschiktheid komen eerst, met behoud van blessure-,
herstel-, taper-, progressie- en beschikbaarheidsregels. Het expliciete weekbudget
is een maximum. Geschikte sportdekking geldt waar haalbaar; 50/30/20 BIKE/RUN/SWIM
is een zachte streefverdeling van geplande belasting, geen verplichte dekking van
afwezige sporten. Nabijheid tot die verdeling komt vóór budgetbenutting.
Uiteindelijke keuzes moeten deterministisch zijn.

## Nog expliciet nodig

| Onderwerp | Ontbrekend akkoord / gevolg |
| --- | --- |
| Volledige IF²-methode | Formule, normalisatie, toepassing bronfactoren, tussen-/eindafronding en opslagprecisie; parameterbevestiging is onvoldoende |
| Officiële geplande P | Bronwaarde of exact herberekende waarde, met exacte operationele methodeversie |
| Planned-P / Realized TSS V2 | Expliciete compatibiliteit en gebruiksgrenzen; historische gegevens behouden hun eigen methode |
| Persoonlijke geschiktheid | Jorens antwoord blijft afwachtend: beginner/intermediate/advanced, ervaring, individuele belastbaarheid en capabilities |
| Training- en fasegegevens | Goedgekeurde fase-, lange-sessie-, herstel/taper- en herhalingsmetadata per training/categorie en concrete atleet/weekcontext |
| Geschatte zwemcontrole | Operationele acceptatie, ontbrekende dekking, onzekerheid en grensgevallen; offline schatting is geen operationele veiligheidspoort |
| Selectiealgoritme | Exacte maat voor 50/30/20, gelijke standen en rangschikking van concurrerende veilige deelplannen; geen sport-omissievolgorde goedgekeurd |
| Historische plannerintegratie | Expliciet versiegebonden vervangingsbesluit voor oude BUILD-minima/Z5-selectieplicht en nieuwe selectie/controles, zonder overige waarborgen te wijzigen |
| Catalogus en release | Formele vervanging/retirement, activatie, verantwoordelijke wetenschappelijke review met identificeerbaar record en afzonderlijke productieautorisatie |

De historische minimumvulling en oude hoog-loadscore zijn niet stilzwijgend
vervangen. De nieuwe prioriteiten zijn bevestigd, maar vormen nog geen volledig
operationeel selectiealgoritme. Geen automatisch gekozen standaard volgt uit de
simulaties. Als geen geschikte training bestaat, blijft geen plan/rust/fail-closed
mogelijk. Ontbrekend bewijs wordt niet omgezet in toestemming.

## Wat de simulaties aantonen en wat open blijft

Alle 18.675 niet-lege combinaties met maximaal één sessie per aanwezige sport zijn
offline onderzocht. Er bestaan rekenkundige deelweken bij 25,86 en 15,085, zonder
budgetoverschrijding. De [haalbaarheidsrapportage](JOREN_V6_PARTIAL_WEEK_FEASIBILITY.md)
onderscheidt die uitkomsten van expliciete TEST_ONLY-geschiktheidsaannames en van
echte goedkeuring. De 77 echte trainingen hebben nog geen goedgekeurde individuele
geschiktheid. Hun ondersteunde uitkomst blijft onbeslist/fail-closed.

De [BUILD-rapportage](JOREN_V6_NO_HIGH_MINIMUM_BUILD_POLICY.md) legt de exacte
toekomstige supersessiegrens vast. De actieve planner, BUILD-zoekoptimalisaties,
A3–A9 en Realized V2 zijn behouden. De bestaande `current:build_4`-timeout bij acht
seconden blijft een performancebeperking, geen bewijs van onhaalbaarheid; geen
nieuwe optimalisatie of hogere deadline is geprobeerd.

Database/pgTAP/RLS-, device- en operationele releasepoorten zijn hier niet
uitgevoerd of gesloten. Er zijn geen schema-, API-, mobile- of runtimewijzigingen.
Pending/atleetbevestiging, stale-safe versievoorwaarden en idempotentie blijven
vereist bij latere integratie. Niets gepusht, gemerged, gemigreerd, geactiveerd of
uitgerold; A5/A6 en C3–C8 zijn niet gewijzigd of gestart.

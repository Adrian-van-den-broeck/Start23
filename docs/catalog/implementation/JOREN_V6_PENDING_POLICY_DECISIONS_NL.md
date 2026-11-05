# Joren V6: nog openstaande beleidsbesluiten

2026-11-05, Europe/Amsterdam. Versie `joren-v6-partial-approval-1`.
Privé ontwikkelrapport, uitsluitend offline. Zie het
[letterlijke vragen- en antwoordenregister](JOREN_V6_PARTIAL_APPROVAL_REGISTER.md).

## Wat nu vaststaat

Z3 IF is 0,88; de eerder bevestigde IF-waarden blijven gelijk. Zwemreferenties
Z1–Z5 zijn 2,17 / 2,00 / 1,83 / 1,67 / 1,50 min/100m. Die mogen worden gebruikt
om geplande actieve zwemtijd te **schatten**. De nieuwe offline schatter bewaart
afstand, broncellen, blokvolgorde en ontbrekende individuele voorgeschreven tijden.
Stilstaande rust telt niet mee. Een geschat 80/20-resultaat blijft expliciet geschat.

Voor toekomstig beginnersbeleid is de volgorde bevestigd: veiligheid en
geschiktheid; blessure/herstel/progressie; expliciet weekbudget als maximum;
waar haalbaar één geschikte training per sport; nabijheid tot 50/30/20;
budgetbenutting; deterministische gelijke-standkeuzes. Dit activeert geen nieuwe
planner. De automatische 45,1 overschrijdt het toekomstige plafond van 45;
40,2/43,1/44,8 blijven hypothetische voorbeelden, geen goedgekeurde voorschriften.

Drie sporten mogen niet worden afgedwongen door veilige grenzen te overschrijden.
Het antwoord op vraag 3 kiest echter geen exact terugvalgedrag.

## Gerichte verduidelijking van vraag 3

Nieuwe verduidelijkingsvraag, nog niet beantwoord:

> Als drie geschikte trainingen niet binnen het veilige weekbudget en alle
> restricties passen, wil je dan (A) geen plan voorstellen, of (B) een veilig
> deelplan? Als B: welke expliciete sport-/sessieprioriteit bepaalt wat wegvalt,
> en in welke herstel-/tapersituaties geldt dit?

Tot dit besluit: geen sport automatisch laten vallen, geen onvolledig
atleetgericht plan genereren en geen budget of reductiefactor verhogen.

## Vragen 5 en 6 blijven onbeantwoord

De exacte oorspronkelijke vragen staan ongewijzigd in het register. Nodig:

- **BUILD:** bepaal of de oude intensiteitsminima verdwijnen of voor expliciete
  gevorderde fases afzonderlijk blijven gelden. Leg versie, bereik en verhouding
  tot het maximum van 20% hoge actieve tijd vast.
- **Geschiktheid:** lever goedgekeurd niveau/fase/capability- en
  geschiktheidsbewijs per training of categorie, inclusief lange sessies,
  herstel/taper, beginners en herhaling. Leg de koppeling met atleet,
  templateversie en weekcontext vast.

Geen wijziging aan BUILD-minima, fasegeschiktheid, beginnerscriteria, lange-sessie-
of herhalingsrestricties, of capability-/geschiktheidsmetadata zolang dit openstaat.

## Bronmethode en operationele integratie blijven aparte poorten

De eerste vraag bevatte meer dan parameterwaarden. Nog nodig zijn de volledige
IF²-formule en normalisatie, verwerking sportfactor, eventuele tussenafronding,
eindafronding, ruwe opslagprecisie, officiële geplande P (bronwaarde of exacte
herberekening) en expliciete Realized TSS V2-compatibiliteit. "Ja, de waarden
kloppen." sluit die onderdelen niet. Nieuwe rekenfixtures zijn offline bewijs;
historische waarden en methodes blijven intact.

Voor latere selectie-integratie moeten ook de exacte nabijheidsmaat voor
50/30/20, de gelijke-standvolgorde en behoud/vervanging van de oude minimumvulling
worden vastgelegd. De prioriteiten zijn bevestigd; de eerdere L1/UUID-diagnostiek
is daarmee niet automatisch het goedgekeurde algoritme.

De geschatte zwemduur is geen individueel voorschrift. Er is geen empirische
onzekerheidsband aangeleverd; de onderzochte ±0,005 min/100m is uitsluitend een
illustratief gevoeligheidsscenario. Voor gebruik als operationele veiligheidspoort
zijn expliciete acceptatie van die schattingsbasis, omgang met grensgevallen en
een apart integratie-/releasebesluit nodig. Geen CSS-schaal, uitgevoerde duur of
Realized TSS wordt afgeleid.

Catalogusopvolging/retirement, benoemde verantwoordelijke wetenschappelijke review,
historiebehoud, stale-safe pending/atleetbevestiging en latere database-/device-
en releaseverificatie blijven vereist waar van toepassing. De bestaande
`current:build_4`-diagnostische timeout is geen bewijs van onhaalbaarheid en blijft
een performancepoort. Dit werk verandert geen van die poorten en wijzigt A5/A6 niet.

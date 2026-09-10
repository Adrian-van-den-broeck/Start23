# Meeting Notulen: Wombo MVP Afstemming

**Datum:** 5 november
**Aanwezigen:**
* **Adrian** (Speaker 1 – Tech Lead / Software Development)
* **Joren** (Speaker 2 – Sportwetenschappelijk adviseur / Product)

---

## 1. Strategische & Algemene Beslissingen

* **Focus MVP:** Volledige focus op racetype-doelen (marathon, triatlon, etc.). Persoonlijke subdoelen (zoals gewichtsverlies of ABC-doelen) worden tijdelijk vergrendeld met een "Coming Soon / slotje".
* **Minimale vereiste (Hardware):** Een hartslagmeter is een **harde vereiste**. Trainen enkel op RPE/tempo zonder hartslagdata wordt niet ondersteund (te inaccuraat).
  * *Business opportunity:* Overwegen om een hartslagmeter aan te bieden bij een jaarabonnement (kostprijs ca. € 20 - € 25).
* **AI-rol in MVP:** De AI mag **niet** zelfstandig hartslagzones herschalen bij vermoeidheid of ziekte. AI past enkel volume/intensiteit van de trainingen aan binnen de bestaande zones.

---

## 2. Fysiologische Modellen, Zones & Belasting (TSS / RPE)

### Trainingshistoriek (Onboarding)
* Het veld "aantal jaren ervaring" verdwijnt.
* **Nieuwe input onboarding (afgelopen 2 maanden):**
  * **Zwemmen:** Gemiddeld aantal meters per week + frequentie (aantal sessies).
  * **Fietsen:** Gemiddeld aantal kilometers per week + frequentie.
  * **Lopen:** Gemiddeld aantal kilometers per week + frequentie.
  * *Doel:* Hieruit een initiële baseline TSS schatten (aanname: Zone 2 duurtraining).

### Zones & TSS Bepaling (Zonder vermogensmeter / labotests)
* **Fietsen:** Omdat veel gebruikers geen wattagemeter bezitten, wordt fietsen net als lopen gebaseerd op **hartslag**.
* **RPE-schaal:** Vervangen van abstracte cijfers door **10 duidelijke tekstuele opties/gevoelsbeschrijvingen** (bijv. "babbeltempo", "verzuren", "buiten adem/uitputting") om foute data-invoer te voorkomen. Dit moet discipline-specifiek worden uitgewerkt.
* **Initiële zone-ijking (Dirk-case):**
  1. Gebruiker krijgt opdracht voor een eerste training (bijv. "1 uur lopen op babbeltempo").
  2. Gebruiker geeft achteraf RPE (beschrijving) en gemiddelde hartslag in.
  3. Formule berekent de initiële zones rondom dit ankerpunt (bijv. zone 3B afleiden met staffel $\pm$ slagen).
* **TSS-berekening:** TSS wordt per zone berekend met een vermenigvuldigingsfactor op basis van tijd (bijv. Zone 1 = tijd $\times$ factor, Zone 2 = tijd $\times$ factor).
* **Ziekte & Vermoeidheid:**
  * **Ziek:** Week wordt volledig genegeerd in de berekeningen; zones blijven ongewijzigd.
  * **Moe / training overgeslagen:** TSS daalt automatisch. Volgende week bouwt voort op de *gerealiseerde* (lagere) TSS (bijv. +10% regel).

### Taper-periode
* De taper duurt **7 tot 10 dagen** direct voorafgaand aan de racedag (niet een willekeurige week ervoor). In deze periode daalt de geplande TSS drastisch.

---

## 3. Doel- en Race-instellingen (App Flow)

* **Veld "Wat wil je bereiken":** Wordt verwijderd als los tekstveld en geïntegreerd in het concrete doel.
* **Veld "Haalbaarheid":** Wordt definitief verwijderd.
* **Doelconfiguratie:**
  * Keuze uit disciplines: **Lopen, Fietsen, Zwemmen, Triatlon, Duatlon**.
  * **Verplichte velden:** Racenaam (voor tracking/historiek), Datum, Afstand per discipline, Richttijd totaal.
  * **Optionele velden:** Richttijd per individuele discipline, specifieke focus (bijv. "focus op zwemonderdeel").

---

## 4. UI/UX & Applicatie Feedback

* **Profiel & Tijdzone:**
  * Automatische bepaling o.b.v. locatie.
  * Toevoegen van een dropdown-selectie voor tijdzones indien locatie geweigerd wordt (bijv. Europe/Amsterdam).
  * Naam, voornaam, geboortedatum en rusthartslag blijven in profiel. Lengte en gewicht worden voorlopig weggelaten.
* **Schermen & Navigatie:**
  * Tussenschermen verwijderen (o.a. het tussenscherm na onboarding en bij het starten van basistesten).
  * Tijdzone-melding weghalen bij de test-flows.
  * Waarschuwing/disclaimer toevoegen: **"Stop bij pijn"**.
* **Weekplanning view:**
  * De trainingsblokken moeten **versleepbaar (drag-and-drop)** worden in de week ipv een statische lijst onderaan.
  * Mogelijkheid behouden om ongeplande trainingen toe te voegen ("unplanned workout").

---

## 5. Geïdentificeerde Bugs (Tijdens Live Test)

* [ ] **Crash bij navigeren naar Profiel:** App crasht bij openen profielpagina vanuit weekplanning.
* [ ] **Activiteit logging conflict:** Foutmelding *"This activity state changed, refresh and try again"* bij het opslaan van RPE.
* [ ] **Duplicaat logging:** Dezelfde activiteit kan per ongeluk twee keer opgeslagen worden via dezelfde knop.
* [ ] **Veldtest inplannen:** Geeft een foutmelding (*"Wombo service tijdelijk niet beschikbaar"*).
* [ ] **Navigatiefout bij testen:** 'Testen' switcht soms naar het verkeerde scherm.

---

## 6. Actiepunten

### Joren (Sportwetenschap & Content) — *Deadline: zaterdagochtend 09:00*
- [ ] **RPE-tekstschaal uitwerken:** 10 concrete definities/beschrijvingen per sportdiscipline (babbeltempo, verzuring, etc.) i.p.v. enkel getallen.
- [ ] **Zone-kalibratie formule:** De mathematische staffel uitwerken om vanuit 1 kalibratietraining (RPE + hartslag) de 5 hartslagzones te berekenen (incl. spreiding boven/onder).
- [ ] **TSS Multipliers:** Factoren per hartslagzone definiëren (tijd in zone $\times$ factor = TSS) gebaseerd op de standaarden (o.a. TrainingPeaks).
- [ ] **Baseline berekening:** Formule opleveren om de 2-maands historiek (meters/km + frequentie) om te zetten naar een start-TSS voor week 1.

### Adrian (Techniek & Implementatie)
- [ ] **GDPR-structuur:** Database-inrichting aanpassen zodat medische data (zoals rusthartslag) via identifiers losgekoppeld blijft van persoonsgegevens.
- [ ] **Onboarding aanpassen:**
  * Velden 'lengte', 'gewicht', 'haalbaarheid' en 'wat wil je bereiken' verwijderen.
  * Vragenlijst toevoegen voor trainingsvolume laatste 2 maanden (lopen, fietsen, zwemmen).
  * Doelenselectie herstructureren (opties voor triatlon/duatlon/losse sporten met verplichte datum/afstand/richttijd).
  * Persoonlijke subdoelen vergrendelen ("Coming Soon").
- [ ] **UI-aanpassingen:**
  * Tussenschermen weghalen (direct doorstromen).
  * Tijdzone handmatige dropdown toevoegen als fallback.
  * Trainingsblokken in weekoverzicht versleepbaar maken (drag-and-drop).
- [ ] **Bugfixes:**
  * Profiel crash oplossen.
  * Field test planningsbug herstellen.
  * RPE activity state concurrency/refresh error fixen.
- [ ] **Website/Beta funnel:** Generieke toegangscode-functionaliteit afronden via Supabase voor bèta-testers (Pioniers).
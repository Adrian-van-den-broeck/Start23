# Backup en herstel zonder lokale Docker

Status: read-only onderzocht op 17 november 2026; niets aangezet, betaald, geëxporteerd of hersteld. Er is nog **geen bewezen herstelbaar productiecheckpoint**. Een geïsoleerd schema, preview branch of synthetisch testproject is geen productiebackup.

## Werkelijke accountstatus

De geautoriseerde Management API geeft voor organisatie Start23 (`dhgozxsnsszssxkwjewa`) plan `free` en één zichtbaar actief project: `start23-dev`, referentie `isfumhgqphieoayqahjv`. De projectlijst heeft count 1 bij limit 100; dit bewijst niet dat het gehele account elders geen projecten heeft.

De vernieuwde backuprespons geeft `backups: []`, `pitr_enabled: false`, `walg_enabled: true` en lege `physical_backup_data`. WAL-G ingeschakeld is geen bewijs van een beschikbaar herstelpunt. De branchlijst is leeg. Entitlements tonen nul/false voor backupretentie, restore-to-new-project, cloning en branching. Beschikbare PITR-varianten zijn leeg. De restore-point-read gaf HTTP 400; zonder aanvullende platforminformatie is de precieze oorzaak onbekend. De backup-schedule-read gaf 402; de officiële API betreft Enterprise-aanpassing van het schema, niet de beschikbaarheid van Pro-dagbackups.

Project-, backup-, addon-, organisatie- en entitlementreads zijn toegestaan. Bevoegdheid om billing te wijzigen, een project/branch te creëren of herstel uit te voeren is bewust niet getest. Zie [accountbewijs](blocker-resolution-20261117/recovery-account-options-resumed.json) en [projecttelling](blocker-resolution-20261117/organization-project-count-current.json). Een eigenaar moet in Dashboard de feitelijke offerte, betaalrechten en alle overige quota controleren.

## Opties en kosten

| Optie | Wat het oplevert | Huidige voorwaarden/kosten | Besluit |
|---|---|---|---|
| Huidig Free-project | Geen nu aantoonbaar checkpoint | API retourneert geen backups en retentie 0 | Geen herstelbasis; WAL-G-status niet als backup behandelen |
| Pro met dagelijkse backup | Beheerde productiebackup, zeven dagen retentie | Vanaf USD 25/maand; USD 10 computecredit dekt één Micro-project volgens huidige prijspagina | Eerst eigenaarsofferte; na upgrade wachten op aantoonbaar succesvol checkpoint en herstelbaarheid bewijzen |
| Geïsoleerde hosted restore/clone | Bewijs dat het echte checkpoint herstelt, inclusief database/Auth | Betaald plan en beschikbare fysieke backup; extra projectcompute/resources; Dashboard toont kosten vóór aanmaak | Tijdelijk herstelproject afzonderlijk goedkeuren; bevat productiegegevens en vereist streng toegangsbeheer |
| Data-arme preview branch | Echte hosted schema/Auth/PostgREST-verificatie met twee synthetische gebruikers | Branching nu niet toegestaan; betaalde toegang vereist. Micro USD 0,01344/uur, circa USD 0,32256 voor 24 uur compute, plus gebruik | Geen productiebackup. Geen productiegegevens includeren, geen merge/automatische productiedeploy |
| Afzonderlijk synthetisch project | Hosted V6-verificatie met aparte credentials | Free-slot mogelijk als accountquota dat toelaten; anders compute en planquote in Dashboard | Geen backup; geen accounts/projecten aangemaakt |
| Eigen externe recovery runner en versleutelde opslag | Native `pg_dump`/herstel zonder lokale Docker of grote lokale opslag | Bestaande vertrouwde runner/opslag kan goedkoop zijn; feitelijke offerte hangt af van opslag, egress, runtime en beheer | Eerst eigenaar kiest beheerder, regio, toegangsmodel, bewaartermijn en offerte; geen data geëxporteerd |

De actuele officiële [prijzen](https://supabase.com/pricing), [backupvoorwaarden](https://supabase.com/docs/guides/platform/backups), [clonevoorwaarden](https://supabase.com/docs/guides/platform/clone-project), [branchkosten](https://supabase.com/docs/guides/platform/manage-your-usage/branching) en [branchgedrag](https://supabase.com/docs/guides/deployment/branching) onderbouwen bovenstaande indicaties. Bedragen zijn USD, exclusief belasting en extra verbruik; het zijn geen accountgebonden offertes. Branches krijgen geen computecredit en vallen niet onder de gewone spend cap. Branches zijn standaard zonder productiedata; kopieeropties voor data moeten uit blijven. Controleer meegekopieerde instellingen, Edge Functions en webhooks voordat een geïsoleerde omgeving actief wordt.

PITR is optioneel voor een strakker herstelvenster: zeven dagen circa USD 100/maand (USD 0,137/uur), veertien circa USD 200 en 28 circa USD 400, bovenop plan/compute. De huidige documentatie noemt beschikbaarheid op alle computeformaten; een oude verplichting om naar Small te upgraden is hier niet overgenomen. De zichtbare account-addonlijst is geen bewijs van actieve entitlement. Zie [PITR-prijzen](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery). De eigenaar moet in Dashboard de daadwerkelijke minimale looptijd, belastingen en herstelquote bevestigen.

## Laagste praktische route

1. Laat de eigenaar de Pro-upgradeofferte voor de bestaande organisatie openen, plus de kostenpreview voor één tijdelijke restore en een kortlevende data-arme Micro-branch. Activeer nog niets. Een tweede project of branch kan additionele compute kosten; de bestaande credit mag niet dubbel worden gerekend.
2. Keur gewenste RPO/RTO en het verliesvenster sinds de laatste dagbackup expliciet goed. Zonder geaccepteerd checkpoint-age/write-loss-venster is een dagbackup onvoldoende. Kies PITR of een goedgekeurde aanvullende remote backup als dat venster te groot is.
3. Na afzonderlijke infrastructuurgoedkeuring: wacht op een daadwerkelijk beschikbaar checkpoint, noteer ID/tijd/schema/ledger en voer een beveiligde geïsoleerde herstelrepetitie uit. Bewijs historische reads/writes, Auth/owner-mapping, ledger en benodigde secrets/configuratie. Verifieer wie herstel mag starten en hoe de oorspronkelijke productieomgeving behouden blijft.
4. Gebruik een aparte data-arme branch of synthetisch project voor de V6-adapter en twee expliciet goedgekeurde synthetische accounts. Een restore met echte atleetgegevens is hiervoor niet automatisch een toegestaan testdoel. Verifieer schema/ACL/RLS en genuine GoTrue daar voordat productie-uitvoering wordt besproken.

Dit is de goedkoopste eenvoudige beheerde route bij de waargenomen Free-status. Een reeds beschikbare, vertrouwde remote runner kan goedkoper zijn; zonder gekozen eigenaar/opslag/regio en hersteltest kan die route niet als operationeel of geprijsd worden aangemerkt.

## Scope van herstel en alternatief remote runner

Een databasebackup bevat niet automatisch Storage-objecten, externe integratiestatus of alle platforminstellingen. Een clone kan database, Auth, rollen en Vault-root meenemen, maar onder meer Storage-objecten, Auth/API-configuratie, Edge Functions en Realtime moeten volgens de providerinstructies afzonderlijk worden gecontroleerd. Aangepaste rolwachtwoorden worden niet vanzelf hersteld. Herstelcredentials, encryptiesleutels, bucketobjecten en Railway-configuratie behoren daarom tot het herstelplan. Zie de officiële backup- en clonedocumentatie hierboven.

Voor een eigen runner: gebruik een eigenaarbeheerde, gepatchte host met geschikte native PostgreSQL-tools, een geverifieerde DB-verbinding en versleutelde opslag met beperkte toegangsrechten. Stream/comprimeer op de externe host; geen lokale Docker en geen productie-export naar deze workspace. Leg database-, rollen-, Auth-, private-schema- en Storage-scope vast; gebruik geen onbeoordeelde one-size-fits-all dump als herstelbewijs. Maak checksums, bewaartermijn en sleutelherstel expliciet en herstel daadwerkelijk naar een goedgekeurde geïsoleerde host. Export, opslag en restore vragen elk afzonderlijke eigenaarstoestemming vanwege echte atleetgegevens.

De eigenaar kan de exacte quote verkrijgen via Supabase Dashboard → organisatie → Billing/Subscription, project → Database → Backups en de kostenpreview van Restore/Branch. Controleer benodigde organisatie-/projectrechten met [Access Control](https://supabase.com/docs/guides/platform/access-control); token-readtoegang bewijst geen billing- of restorebevoegdheid. De [backup-schedule API](https://supabase.com/docs/reference/api/v1-get-backup-schedule) is Enterprise-specifiek. Geen betaalde dienst of configuratie is in deze taak gewijzigd.

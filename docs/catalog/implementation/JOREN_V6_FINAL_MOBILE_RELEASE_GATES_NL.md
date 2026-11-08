# WOMBO V6 mobiele releasepoorten

8 november 2026. Branch `feat/joren-v6-mobile-lifecycle`.
Bron-SHA `3d54615e6635cd662f5e3dfa246bedee924b9b06`.
Geteste implementatie f09941d405d25cdbb587b662fe1f5fe17c1c14eb; de laatste rapportcommit volgt daarna.

**WOMBO V6 MOBILE LIFECYCLE PARTIAL — EXACT BLOCKERS DOCUMENTED**

De bestaande app kan lokaal echte V6-kaarten verwerken, keuzes en datums behouden,
een pending voorstel indienen, apart bevestigen en de bevestigde trainingen tonen.
Kalender en activiteit gebruiken de expliciete koppeling tussen logische occurrence
en fysieke revisierij. Gemeten activiteitverwerking en registratie zijn in echte
lokale PostgreSQL-transacties gecontroleerd. Dit is geen productieautorisatie.

| Poort | Status en vereist vervolg |
| --- | --- |
| Lokale software | Backend-, mobiele en type/lint/contractcontroles en exacte resultaten staan in verification.json. |
| Database | 60 migraties; 34 suites / 654 assertions lokaal geslaagd; 14 aanvullende kalender/activiteit-checkgroepen. JWT-claims zijn gesimuleerd. Hosted migraties/advisors zijn niet uitgevoerd. |
| A5 V6 check-in | OPEN: de V6-writer moet aansluiten op A5's bestaande atomische attachment/replay-transactie; geen tweede replay- of goedkeuringssysteem. Tot die tijd fail-closed. |
| A5-fixture en A5/A6-adoptie | OPEN: de afzonderlijke fixturecorrectie is niet aangenomen. Originele A5-test en beschermde release-worktree zijn ongewijzigd. Geen productie-onboarding aangepast. |
| Datum wijzigen na bevestiging | OPEN: een nieuwe V6-revisie moet bron/context/mapping behouden. Het legacy move-pad wordt vóór schrijven geweigerd. Pending datumplaatsing werkt wel. |
| Realized V2 Session-RPE | OPEN voor deze geplande methode: geen goedgekeurde fallbackmapping. Waarnemingen blijven bruikbaar; onondersteunde fallback blijft zonder waarde en niet planner-eligible. |
| Operationele zwemtijd | OPEN: `ESTIMATED_FROM_APPROVED_REFERENCE_PACE` is een schatting; individuele voorgeschreven/gemeten tijd en operationele veiligheidsacceptatie zijn niet bewezen. |
| Supabase Auth/gateway | BLOCKED — ENVIRONMENT: geen GoTrue-stack/gateway of echte sessies. Signup/login, refresh/revocation, issuer/audience/JWKS, key-routing en twee echte accounts blijven vereist. |
| Android | Hermes-export en lokale x86_64-debugbuild geslaagd. Geen aangesloten apparaat/emulator; geen installatie, echte login, TalkBack- of kill/relaunch-verificatie. |
| iOS | OPEN: geen Xcode/signing/deviceomgeving op deze Windows-host. |
| Onafhankelijke review, catalogus en release | OPEN: verantwoordelijke fysiologische review, vereiste operationele acceptatie, expliciete catalogusactivering en releaseautorisatie blijven nodig. |

Alle 77 V6-revisies blijven INACTIVE. De historische planner blijft de standaard.
Geen TSS/private load in mobiele UI, a11y-labels of publieke responses; geen nieuwe
fysiologische formules, ervaringscategorieën of lokale budgetautorisatie.

Productie en staging zijn niet benaderd of gewijzigd. Geen push, merge, deployment,
hosted migratie, activering of wijziging aan de A5/A6-releasebranch.

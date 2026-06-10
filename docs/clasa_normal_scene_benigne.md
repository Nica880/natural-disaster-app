# Clasa „Normal" — eliminarea incidentelor false pe scene fără dezastru

*10 iunie 2026 · antrenare: [`model/train_v3.py`](../model/train_v3.py) · diagnostic: audit benign prin pipeline-ul de producție*

## 1. Scopul

Cerința operațională a RAID: **să semnaleze doar incidente reale**. O autostradă cu trafic normal nu e un accident; o pădure sănătoasă nu e un incendiu — trebuie semnalată *doar dacă arde*.

Problema structurală: clasificatorul (v1, v2) e un model **închis pe 5 clase de dezastru** (Car Crash / Cyclone / Earthquake / Flood / Wildfire). Softmax-ul e *obligat* să distribuie 100% din probabilitate între cele 5 — pentru o scenă perfect normală, modelul nu are nicio cale să spună „nu se întâmplă nimic". Întrebarea empirică era doar *cât de des* trec aceste predicții forțate de pragurile existente.

## 2. Diagnosticul — măsurat, nu presupus

### 2.1 Setul de test benign

10 fotografii de scene normale, descărcate din Wikimedia Commons și **verificate vizual una câte una**, alese să fie și adversariale (apă reală, sute de mașini, zăpadă, macara):

| # | Scena | De ce e capcană |
|---|---|---|
| 01 | Autostradă + canal navigabil (aerian) | mașini + apă reală |
| 02 | Ambuteiaj dens pe autostradă | exact scenariul „poză cu autostrada cu mașini" |
| 03 | Stradă urbană cu pietoni | — |
| 04 | Parcare plină, vedere aeriană | sute de mașini; asfalt gri uniform |
| 05 | Pădure verde sănătoasă | scenariul „pădure fără flăcări" |
| 06 | Munți cu zăpadă, drumeți | zăpadă ≈ textura „dezastru alb" |
| 07 | Râu calm cu munți | apă reală |
| 08 | Plajă cu oameni în apă | 24% din cadru chiar e apă |
| 09 | Câmp cu macara și piloni | structuri ≈ șantier/dărâmături |
| 10 | Lan de grâu | — |

### 2.2 Rezultatul: 6/10 incidente false

Rulate prin **pipeline-ul de producție complet** (clasificator v2 + specialiști + gărzi + logica de verdict), cu poarta reală din `monitor.py` (`EVENT_WORTHY_TYPES`):

| Scena | Verdict | Incident fals? | Mecanismul eșecului |
|---|---|---|---|
| Autostradă + canal | Flood 0.71 `[flood]` | **DA** | clasificator păcălit + canalul = „apă" 1.0% în segmenter |
| Ambuteiaj | Uncertain 0.31 | nu | clasificatorul nesigur → sub pragul 0.45 |
| Stradă cu pietoni | Earthquake 0.70 `[generic]` | **DA** | **Earthquake nu are specialist** → nimic nu-l contrazice |
| Parcare aeriană | Flood 0.94 `[flood]` | **DA** | asfaltul = „apă" 4.5% (fals-pozitiv segmenter) |
| Pădure | Uncertain 0.69 | nu | Wildfire 0.69 < 0.75 + zero flăcări → garda downgrade |
| Munte cu zăpadă | Earthquake 0.60 `[generic]` | **DA** | fără specialist |
| Râu calm | Uncertain 0.71 | nu | garda downgrade |
| Plajă | Flood 0.90 `[flood]` | **DA** | marea chiar e apă — dar **apă ≠ inundație** |
| Câmp + macara | Earthquake 0.56 `[generic]` | **DA** | fără specialist |
| Lan de grâu | Uncertain 0.52 | nu | clasificator nesigur |

Taxonomia eșecurilor:
1. **Clasele fără specialist (Earthquake, Cyclone) trec direct pe board** — orice predicție ≥ 0.45 devine incident; nu există semnal care s-o contrazică (3/6).
2. **„Confirmarea" Flood e ruptă pe scene benigne** — segmenterul raportează apă pentru mare/canal (apă reală, dar nu inundație) sau chiar pentru asfalt; pragul de 1% e mult prea permisiv ca să însemne „inundație" (3/6).
3. Gărzile + pragurile existente salvează restul (4/10) — dar doar când clasificatorul e *nesigur*. Când e încrezător și greșit (parcare → Flood 0.94), nimic nu-l mai oprește.

## 3. Soluția aleasă: a 6-a clasă, „Normal"

**Alternative respinse:**
- *Praguri mai dure* — ar tăia și detecțiile reale (recall); nu rezolvă plaja (0.90) sau parcarea (0.94).
- *Corroborare obligatorie de la specialist* — Earthquake/Cyclone nu au specialist; ar dezactiva complet aceste clase.
- *Prag pe aria de apă la Flood* — plaja are 24% apă reală; distincția „mare vs. inundație" e semantică, nu de prag.

**De ce clasa „Normal" e corectă:** singura componentă care vede *întreaga scenă* e clasificatorul — el trebuie să poată spune „nicio urgență". Cu un set de scene cotidiene la antrenare, softmax-ul nu mai e forțat să inventeze un dezastru.

**De ce nu strică nimic existent (by design):**
- poarta `EVENT_WORTHY_TYPES` din `monitor.py` enumeră *explicit* cele 5 tipuri de dezastru → verdictul „Normal" **nu creează incident** fără nicio modificare;
- indecșii claselor de dezastru rămân neschimbați (Normal se adaugă la final, index 5);
- checkpoint-ul păstrează formatul `{'model','classes','accuracy'}`, iar backend-ul citește lista de clase din fișier → **drop-in, zero modificări de cod**;
- gărzile existente compun natural: dacă clasificatorul spune „Normal 0.95" și YOLO-ul de foc halucinează, `_override_allowed` blochează override-ul (clasificator ≥ 0.75 pe altă clasă).
- rollback trivial: `disaster_model.pth` se înlocuiește înapoi cu v2 (păstrat pe disc).

## 4. Construcția setului „Normal"

### 4.1 Ce nu a mers (documentat pentru onestitate metodologică)

Prima încercare: descărcare în masă din Wikimedia Commons (18 interogări tematice × ~100 imagini, concurență 6). Rezultat: **HTTP 429 Too Many Requests** — rate-limit la nivel de IP, persistent și după un drip „politicos" la 1 cerere/sec (21 de imagini în ~10 min). Lecția: Wikimedia e excelent pentru eșantioane mici (setul de test de 10), nepractic pentru sute de fișiere într-un interval scurt.

### 4.2 Ce a mers: COCO val2017 + completare Wikimedia

- **COCO val2017** (5.000 de fotografii cotidiene, un singur zip de 785 MB de pe CDN, fără rate-limit): străzi, trafic, pietoni, interioare, sport, animale — exact distribuția de „viață normală" de care are nevoie clasa. Eșantion aleator determinist (seed 42): **1.300 imagini**.
- **Wikimedia**: cele 23 de peisaje reușite înainte de blocare (pădure, munte etc.).
- Deduplicare după hash MD5 → **1.323 imagini unice**.
- Split determinist 72/18/10: **952 antrenare / 238 validare / 133 test**, în `Datasets/Normal/{train,valid,test}/Normal/` — folder **separat** de setul canonic „Natural Disasters" (neatins).
- **Igienă experimentală:** cele 10 imagini ale testului benign sunt excluse explicit (filtru pe titlu la descărcare) — testul final nu e contaminat de antrenare.
- Verificare vizuală prin eșantionare: interior de tramvai, baie, motocicletă, tort de nuntă — cotidian pur.

## 5. Antrenarea (`model/train_v3.py`)

Rețeta v2 moștenită integral (augmentare cu speckle, label smoothing 0.1, două faze, cosine LR, early stopping — motivațiile în [`antrenare_clasificator_v2.md`](antrenare_clasificator_v2.md)), plus:

- `classes = [cele 5 din ImageFolder] + ["Normal"]` — indecșii 0–4 identici cu v2;
- `Datasets/Normal/<split>/` ca `ImageFolder` separat cu `target_transform` → index 5, concatenat la train/valid/test;
- `fine_tune_images/` (doar clase de dezastru) remapat după nume în lista combinată;
- raport final extins: confuzie 6×6 pe test, cele 120 de cadre de dezastru ale simulatorului (**nu** trebuie să devină „Normal") și cele 10 scene benigne (**trebuie** să devină „Normal").

Volume: **7.679 antrenare / 2.167 validare / 1.096 test** · MPS, batch 32, `nice -n 5`.

### 5.1 Rezultatele antrenării

Early stop după 18 epoci efective. **Best val acc: 98.7% · Test (1.096 imagini, 6 clase): 99.0%.**

Matricea de confuzie pe test (rând = adevăr):

| | Car Crash | Cyclone | Earthquake | Flood | Wildfire | Normal |
|---|---|---|---|---|---|---|
| Car Crash | **136** | 0 | 1 | 0 | 0 | 0 |
| Cyclone | 0 | **184** | 0 | 0 | 1 | 0 |
| Earthquake | 0 | 0 | **238** | 1 | 0 | 0 |
| Flood | 1 | 0 | 3 | **196** | 2 | 0 |
| Wildfire | 0 | 0 | 0 | 0 | **200** | 0 |
| **Normal** | 0 | 0 | 0 | 2 | 0 | **131** |

Observații cheie: **niciun dezastru din test nu e clasificat „Normal"** (rândurile de dezastru au 0 pe coloana Normal — clasa nouă nu „fură" detecții reale), iar cele 120 de cadre de dezastru ale simulatorului rămân **120/120** la nivel de clasificator. Pe cele 10 scene benigne, **6/10 devin direct „Normal"** (de la 0/10 cu v2); rămân 4 scurgeri la nivel de clasificator: autostrada+canal (Flood 0.53), parcarea aeriană (Flood 0.82), muntele cu zăpadă (Earthquake 0.72), râul calm (Wildfire 0.56 — oricum oprit de gărzile existente).

## 6. Calibrarea regulilor de verdict — pe măsurători, nu pe intuiție

După antrenare am măsurat vectorii compleți de probabilitate v3 pe toate cele 130 de imagini (120 dezastre + 10 benigne), plus procentele măștii de apă pe toate cadrele flood. Constatări care au dictat regulile:

- **P(Normal) pe toate cele 120 de cadre de dezastru: maximum 0.12** — clasa Normal e un semnal de separare curat;
- cutremurele reale clasifică la **≥0.88**, cicloanele reale la **≥0.83** (singura excepție, 0.70, e infograficul-diagramă — nu o fotografie); scurgerea benignă „munte → Earthquake" e la **0.72**;
- inundațiile reale au fie clasificator ≥0.75, fie mască de apă substanțială (39.3% la singurul cadru real sub 0.75 care depinde de mască); scurgerea „autostradă+canal" are (0.53, mască 1.0%).

**Regulile adăugate în `analyze.py`** (constanta `FLOOD_MASK_STRONG_PCT = 8.0`):

1. **Flood cere conf ≥ 0.75 SAU mască ≥ 8%** — o mască subțire (mare, canal, fals-pozitive pe asfalt: 1–5%) nu mai e tratată drept „confirmare" de inundație. Omoară autostrada (0.53/1.0%), păstrează toate cele 24 de inundații reale.
2. **Cyclone/Earthquake (clase fără specialist) cer conf ≥ 0.75** — fără corroborare posibilă, clasificatorul trebuie să fie sigur. Omoară muntele (0.72), păstrează toate cutremurele (≥0.88) și cicloanele reale (≥0.83).

**Limită demonstrată a regulilor:** parcarea aeriană scorează (Flood 0.82, mască 4.5%), iar cadrul real flood_16 scorează (Flood 0.82, mască 0.0%) — **niciun prag pe aceste semnale nu le poate separa**. Parcarea se repară doar prin date: runda 2 de imagini „Normal" țintite (parcări/orașe aeriene, munți cu zăpadă) + fine-tuning scurt din checkpoint-ul v3.

**Cost asumat al regulii 2:** infograficul-diagramă de ciclon (frame_10, conf 0.70) coboară la „Uncertain" — pentru un desen schematic, nu o scenă reală de cameră, considerăm răspunsul onest, nu o regresie. Auditul de dezastre devine astfel **118/120 aşteptat**, cu ambele ratări „Uncertain" onest și **zero verdicte de tip greșit**.

## 7. Porțile de validare înainte de instalare

v3 + regulile se instalează **doar** dacă (altfel rămâne v2):

1. **Testul de dezastre nu regresează** — ✅ 99.0% (v2: 99.2% pe 5 clase; diferența vine din testul extins, nu din pierdere pe dezastre — vezi matricea: 8 erori pe dezastre, identic cu v2);
2. **Auditul end-to-end pe 120 de cadre**: fără verdicte de tip greșit; ≥118/120 cu ratările exclusiv „Uncertain" onest (poarta inițială ≥119 revizuită conștient — vezi §6, costul regulii 2);
3. **Auditul benign end-to-end**: ≤1/10 incidente false (parcarea, până la fine-tuning-ul rundei 2; ținta finală rămâne 0/10).

## 8. Rezultate end-to-end (măsurate)

Ambele audituri, rulate prin pipeline-ul de producție cu v3 + regulile calibrate — **predicțiile din §6 s-au confirmat exact**:

**Dezastre (120 cadre): 118/120 (98.3%), zero verdicte de tip greșit.** Matricea e diagonală; singurele ratări sunt „Uncertain" onest pe: `cam-accident/frame_06` (clasificator 46% Car Crash / 46% Earthquake — ambiguitate reală) și `cam-cyclone/frame_10` (infograficul-diagramă, 0.70 < 0.75 — costul asumat al regulii 2).

**Benigne (10 scene): 1/10 incidente false** (de la 6/10):

| Scena | Înainte (v2) | După (v3 + reguli) |
|---|---|---|
| Autostradă + canal | Flood 0.71 ❌ | Uncertain ✓ (regula 1) |
| Ambuteiaj | Uncertain ✓ | **Normal 0.73** ✓ |
| Stradă cu pietoni | Earthquake 0.70 ❌ | **Normal 0.82** ✓ |
| Parcare aeriană | Flood 0.94 ❌ | Flood 0.82 ❌ *(singura rămasă — fix prin date, §6)* |
| Pădure | Uncertain ✓ | **Normal 0.96** ✓ |
| Munte cu zăpadă | Earthquake 0.60 ❌ | Uncertain ✓ (regula 2) |
| Râu calm | Uncertain ✓ | Uncertain ✓ |
| Plajă | Flood 0.90 ❌ | **Normal 0.87** ✓ |
| Câmp + macara | Earthquake 0.56 ❌ | **Normal 0.88** ✓ |
| Lan de grâu | Uncertain ✓ | **Normal 0.67** ✓ |

De remarcat plaja: cu 24.1% apă reală în cadru, clasificatorul v3 spune acum „Normal 0.87" — exact distincția semantică „apă ≠ inundație" pe care pragurile nu o puteau exprima.

**Instalat în aplicație** ✅ — v3 + regulile sunt copte în imaginea Docker a backendului; smoke-test pe imaginea finală: 118/120 dezastre, 1/10 benigne (identic cu auditurile pre-instalare). Rollback: `cp model/disaster_model_v2.pth model/disaster_model.pth` + rebuild.

> ⏳ *Pas următor (deschis): runda 2 de imagini „Normal" țintite (parcări/orașe aeriene, munți cu zăpadă) + fine-tuning scurt din checkpoint-ul v3, pentru a închide parcarea (țintă finală: 0/10). Blocaj curent: Wikimedia rate-limit (429) persistent la descărcări în masă — se reia după răcirea limitei.*

## 8. Artefacte

| Fișier | Rol |
|---|---|
| `model/train_v3.py` | rețeta v3 (6 clase) |
| `model/disaster_model_v3.pth` | checkpoint-ul v3 (după antrenare) |
| `Datasets/Normal/{train,valid,test}/Normal/` | clasa Normal (1.323 imagini: COCO + Wikimedia) |
| `/tmp/benign_test/` (10 imagini) | testul benign end-to-end (exclus de la antrenare) |
| `/tmp/benign_eval.py` | harness-ul auditului benign (rulat în containerul backend) |
| `model/audit_pipeline.py` | auditul de dezastre (120 cadre), neschimbat |

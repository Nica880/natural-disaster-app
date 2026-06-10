# Reantrenarea clasificatorului de dezastre (v2) — local, pe Apple Silicon

*10 iunie 2026 · scriptul: [`model/train_v2.py`](../model/train_v2.py) · auditul: [`model/audit_pipeline.py`](../model/audit_pipeline.py)*

## 1. Contextul și problema

RAID decide tipul de dezastru în două trepte: un **clasificator de scenă** (ResNet18, 5 clase: Car Crash / Cyclone / Earthquake / Flood / Wildfire) dă verdictul de bază, peste care **detectoarele specializate** (YOLO foc / inundație / accident) adaugă severitate, arie afectată și resurse recomandate, iar logica de verdict din `app/api/routes/analyze.py` le arbitrează.

În utilizare reală au apărut incidente etichetat greșit — exemplul-semnal: o scenă evidentă de **inundație** (familie traversând apa până la brâu, camera `cam-flood`, Dunăre · Galați Port) raportată ca **„Car Crash · minor"** cu 68% încredere și o cutie falsă „Accident 0.43" desenată pe o persoană.

### Auditul care a cuantificat problema

Am construit un harness care rulează **pipeline-ul de producție complet** peste cele **120 de cadre ale simulatorului de camere** (`camera_sim/samples/`, 24 cadre × 5 camere, numele folderului = adevărul) și am inspectat vizual fiecare cadru ratat. Rezultatul inițial:

- **98/120 (81.7%)** verdicte corecte, din care **16 de tip greșit** (periculoase operațional);
- clasificatorul v1 era **categoric și încrezător greșit**: piață inundată → „Earthquake **0.99**", casă scufundată cu barcă → „Earthquake 0.97", salvatori pe plăci de beton → „Car Crash **0.99–1.00**" (fără nicio mașină în cadru);
- tipar clar: modelul învățase *textură/culoare grosieră* („moloz împrăștiat = accident", „maro = pământ"), nu structura scenei.

### De ce era v1 slab

Rețeta originală (`model/train.py`) era minimală:

| Aspect | v1 |
|---|---|
| Epoci | 5, fixe |
| Augmentare | **niciuna** (doar Resize + Normalize) |
| Calibrare | niciuna → greșeli raportate cu încredere 1.00 |
| LR schedule | constant 1e-3, Adam |
| Fine-tuning | tot modelul de la început, fără warm-up |

Două gărzi adăugate în logica de verdict (detaliate în §5) au urcat scorul la 103/120, dar **cele 10 erori rămase de tip greșit erau toate ale clasificatorului, la încredere 0.95–1.00** — nereparabile prin praguri. Singura soluție: reantrenarea.

## 2. Datele

Setul existent era deja bun — problema nu era volumul, ci rețeta:

| Split | Total | Car Crash | Cyclone | Earthquake | Flood | Wildfire |
|---|---|---|---|---|---|---|
| train | 6 707 | 1 019 | 1 233 | 1 748 | 1 404 | 1 303 |
| valid | 1 929 | 263 | 341 | 530 | 421 | 374 |
| test  |   963 | 137 | 185 | 239 | 202 | 200 |

La antrenare s-au adăugat și cele **20 de cazuri grele** colectate manual în `fine_tune_images/` (train efectiv: **6 727**). Splitul de test a rămas neatins — folosit o singură dată, la final.

## 3. Rețeta v2 (ce s-a schimbat și de ce)

Arhitectura a rămas **același ResNet18** (pornit din ponderile ImageNet), iar checkpoint-ul păstrează formatul `{'model','classes','accuracy'}` — **drop-in**: zero modificări în backend (`app/services/classifier.py`).

**Augmentare** (inexistentă în v1) — fiecare alegere țintește un mod de eșec observat în audit:

| Transformare | Motivația concretă |
|---|---|
| `RandomResizedCrop(224, scale 0.6–1.0)` | forțează învățarea structurii, nu a compoziției globale |
| `RandomHorizontalFlip` | invarianță stânga-dreapta |
| `ColorJitter(0.3, 0.3, 0.3, 0.05)` | apa maro vs. molozul maro nu se mai disting prin nuanță |
| `RandomGrayscale(p=0.05)` | cadrele de arhivă alb-negru din feed (ex. `cam-earthquake/frame_09`) |
| `GaussianBlur(p=0.15)` | cadre defocalizate / comprimate |
| **`Speckle(p=0.3, amount=2%)`** — transformare custom | simulatorul de camere adaugă zgomot „sare-și-piper" peste cadre; modelul îl vede acum și la antrenare (domain match) |

**Optimizare:**

- **Label smoothing 0.1** în CrossEntropyLoss → calibrare: v1 greșea cu 1.00; v2 raportează încredere realistă (corectele se grupează la 0.80–0.98).
- **Două faze**: (1) backbone înghețat, doar capul `fc`, 2 epoci, AdamW lr 1e-3 — capul nou nu mai „trage" în jos ponderile pre-antrenate; (2) toată rețeaua, AdamW lr 1e-4, weight decay 1e-4, **CosineAnnealingLR** (T_max=18, η_min=1e-6).
- **Early stopping** cu răbdare 6 pe acuratețea de validare; checkpoint salvat la **fiecare** îmbunătățire (întreruperea nu pierde nimic).

**Mediu de rulare:** local, Apple Silicon (**MPS**), batch 32, `nice -n 5` ca să nu deranjeze lucrul curent; fără caffeinate (sesiune activă). Durata: **~40 de minute** — 18 epoci efective (2 + 16) dintr-un maxim de 20, oprit de early stopping.

## 4. Rezultate

**Traiectoria validării:** 91.5% → 92.8% (warm-up cap) → 97.5% la prima epocă de fine-tuning complet → vârf **99.2%** (epoca 13), apoi platou și early stop.

**Pe testul independent (963 imagini, folosit o singură dată): 99.2%** — 8 erori în total:

| adevăr \ predicție | Car Crash | Cyclone | Earthquake | Flood | Wildfire |
|---|---|---|---|---|---|
| Car Crash | **137** | 0 | 0 | 0 | 0 |
| Cyclone | 0 | **183** | 0 | 0 | 2 |
| Earthquake | 0 | 0 | **237** | 1 | 1 |
| Flood | 1 | 0 | 1 | **199** | 1 |
| Wildfire | 0 | 0 | 0 | 1 | **199** |

**Pe cele 120 de cadre ale simulatorului (doar clasificatorul): 120/120** — inclusiv cadrele „grele" pe care v1 le rata cu 0.97–1.00 și cele atipice (infografic de ciclon, hartă radar, transmisiune TV cu grafică).

## 5. Efectul în sistemul complet (end-to-end)

Acuratețea verdictului final (clasificator + specialiști + arbitraj), măsurată cu `model/audit_pipeline.py` pe aceleași 120 de cadre:

| Etapă | Corecte | Verdicte de tip greșit |
|---|---|---|
| v1, logica originală | 98/120 (81.7%) | 16 |
| + gărzi în logica de verdict¹ | 103/120 (85.8%) | 10 |
| + **clasificatorul v2** | 115/120 (95.8%) | **0** |
| + prag recalibrat² | **119/120 (99.2%)** | **0** |

¹ *Gărzile (motivate tot de audit): un specialist poate **contrazice** clasificatorul doar dacă acesta nu e aproape-sigur pe altă clasă și doar cu o cutie ≥ 0.55 (YOLO-urile de foc/accident halucinau detecții „puternice" de 0.26–0.52 pe imagini satelitare de ciclon, deturnând clasificări corecte de 1.00); iar „clasificator slab + cutie slabă" nu mai pot încheia împreună un verdict de accident (cazul-semnal: 0.68 + 0.43).*

² *`HIGH_CONFIDENCE_THRESHOLD` coborât 0.85 → 0.75: pragul fusese dimensionat pentru v1 cel necalibrat; v2, antrenat cu label smoothing, plasează corectele la 0.80–0.95, iar 0.85 le retrograda inutil la „Uncertain".*

Singura „ratare" rămasă: un accident real clasificat corect dar cu 0.60, raportat onest ca *„Uncertain — best guess Car Crash 60%"*. **Matricea finală e perfect diagonală: sistemul nu mai dă niciun verdict de tip greșit pe acest set; când nu e sigur, spune.**

## 6. Artefacte și reproducere

| Fișier | Rol |
|---|---|
| `model/train_v2.py` | rețeta completă; rulare: `python model/train_v2.py` |
| `model/disaster_model.pth` | **modelul activ = v2** (copt în imaginea Docker a backendului) |
| `model/disaster_model_v2.pth` | originalul v2 (val acc 0.992 în checkpoint) |
| `model/disaster_model_v1.pth` | v1, păstrat pentru comparație |
| `model/audit_pipeline.py` | auditul end-to-end pe cele 120 de cadre (istoricul măsurat e în antet) |
| `app/api/routes/analyze.py` | gărzile + pragul recalibrat, cu motivația în comentarii |

După orice schimbare de model sau de logică: `docker compose build backend && docker compose up -d backend`, apoi re-rulează auditul (instrucțiuni în antetul scriptului).

## 7. Limite și pași următori

- Cifrele end-to-end sunt pe setul demo de 120 de cadre; garanția independentă rămâne testul de 963 imagini (99.2%). Cifrele sunt consistente între ele.
- Bucla de feedback a operatorului („Correct / False alarm" în UI) poate alimenta periodic `fine_tune_images/` — scriptul le include automat la următoarea reantrenare.
- Notebook-urile `notebooks/train_cyclone_yolo.ipynb` / `train_earthquake_yolo.ipynb` ar adăuga specialiști și pentru Cyclone/Earthquake (azi acoperite doar de clasificator + detectorul generic) — ar îmbogăți severitatea/aria, tipul fiind deja la 100% pe setul demo.

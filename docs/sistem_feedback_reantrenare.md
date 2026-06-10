# Sistemul de feedback cu corecție — bucla operator → reantrenare

*10 iunie 2026 · ~60 de linii de cod în total · fără tabele noi, fără endpoint-uri noi*

## 1. Scopul

Operatorul care vede un incident **catalogat greșit** trebuie să poată: (a) semnala greșeala și (b) spune **ce este de fapt** în imagine, dintr-un dropdown. Pe baza corecției, cadrul ajunge automat într-un folder de reantrenare, astfel încât fiecare greșeală raportată devine material de antrenament la următoarea rulare — o buclă de îmbunătățire continuă închisă, fără pași manuali.

## 2. Ce exista deja (și a fost refolosit)

Sistemul fusese proiectat pe jumătate — am completat jumătatea lipsă în loc să construiesc paralel:

| Componentă existentă | Rol |
|---|---|
| `FeedbackCreate.actual_type` (schema Pydantic) | câmpul „ce e de fapt" exista deja în payload |
| Tabela `feedback` (coloana `actual_type`) | persistența exista deja |
| `POST /incidents/{id}/feedback` | endpoint-ul exista; alimentează și panoul „Detection accuracy" |
| `fine_tune_images/<clasă>/` | folderele pe clase existau (lowercase) |
| `train_v2.py` / `train_v3.py` | **includ deja automat** `fine_tune_images/` la antrenare |
| Butoanele „Correct / False alarm" în `IncidentDetail` | UI-ul de feedback exista, fără corecția de tip |

Ce lipsea: dropdown-ul în UI, copierea imaginii în folderul clasei corecte și calea fișierelor către host.

## 3. Modificările (4 fișiere)

### 3.1 `app/services/repository.py` — `export_for_retraining()` (~30 linii)

La un feedback cu `actual_type`, funcția:
1. **validează eticheta** împotriva listei de clase cunoscute (`car crash / cyclone / earthquake / flood / wildfire / normal`) — orice altceva e ignorat cu warning (apărare la input arbitrar);
2. ia **analiza cu încrederea maximă** a incidentului (cel mai reprezentativ cadru);
3. citește **imaginea originală** din blob-store — `original_image_path`, NU varianta adnotată: boxele și măștile desenate ar otrăvi antrenarea;
4. o scrie în `fine_tune_images/<clasă>/<incident_id>.jpg` (id-ul ca nume previne duplicatele la feedback repetat).

### 3.2 `app/api/routes/monitor.py` — 2 linii în ruta existentă

```python
if payload.actual_type:
    repository.export_for_retraining(db, incident_id, payload.actual_type)
```

### 3.3 `docker-compose.yml` — 1 linie (mount)

```yaml
- ./fine_tune_images:/app/fine_tune_images
```

Backend-ul rulează în Docker; fără mount, fișierele ar fi murit în containerul efemer. Cu el, aterizează direct în repo-ul de pe host, unde scripturile de antrenare (rulate pe Mac, pe MPS) le găsesc.

### 3.4 `frontend/src/components/monitor/IncidentDetail.jsx` (~30 linii)

- „**Correct**" → neschimbat (trimite `{verdict_correct: true}`).
- „**False alarm**" → nu mai trimite direct; deschide un `<select>` nativ: *„What is actually in the image?"* cu cele 5 dezastre + **„Normal — no incident"**.
- Alegerea → `{verdict_correct: false, actual_type: <alegerea>}` → confirmare: *„Recorded — saved for retraining as Flood."*
- Stările noi (`pickingType`, `correctedType`) urmează tiparul existent al componentei; fără librării noi, fără componente noi.

## 4. Fluxul cap-coadă

```
Operator: click incident → „False alarm" → alege „Flood"
   │
   ▼
POST /incidents/{id}/feedback  {verdict_correct: false, actual_type: "Flood"}
   │                                   │
   ▼                                   ▼
tabela feedback                 export_for_retraining()
(panoul Detection accuracy)     → fine_tune_images/flood/{id}.jpg  (originalul, pe host)
                                        │
                                        ▼
                       următorul  python model/train_v3.py
                       → imaginea intră automat în setul de antrenare
```

Decizie de design: opțiunea **„Normal — no incident"** alimentează direct clasa „Normal" (v. [clasa_normal_scene_benigne.md](clasa_normal_scene_benigne.md)) — alarmele false pe scene liniștite devin, prin chiar gestul de respingere al operatorului, datele care întăresc clasa ce le previne.

## 5. Verificare (efectuată, cu dovezi)

1. **API real:** am creat un incident de test prin `/ingest` (cadru de foc), am trimis feedback `{verdict_correct: false, actual_type: "Flood"}` → fișierul a apărut pe host în `fine_tune_images/flood/65edb96b5c8a.jpg`; verificat vizual că e **originalul curat** (fără boxe de adnotare).
2. **UI real (browser, server de dev pe portul 5173):** modal deschis → „False alarm" → dropdown vizibil cu toate cele 6 opțiuni → screenshot. (Notă CORS: backend-ul permite doar originile 5173/5174 — serverul de dev trebuie pornit pe 5173, cu nginx-ul Docker oprit temporar.)
3. **Curățenie post-test:** incidentul de test dismissed; rândurile lui șterse din `feedback`/`analyses`/`incidents`/`cameras`; imaginea-test ștearsă din `fine_tune_images/flood/` (un cadru de **foc** etichetat „flood" ar fi otrăvit setul); nginx repornit.

## 6. Cum se folosește bucla, periodic

1. Operatorii corectează incidente greșite din UI (zero efort suplimentar — un click + o alegere).
2. Când s-au strâns suficiente corecții (orientativ: zeci), rulezi `python model/train_v3.py`.
3. Porțile de validare standard înainte de instalare: `model/audit_pipeline.py` (120 cadre) + auditul benign; dacă trec, copiezi checkpoint-ul peste `model/disaster_model.pth` și `docker compose build backend && docker compose up -d backend`.

## 7. Limite cunoscute

- Se exportă **un singur cadru** per incident (cel cu încrederea maximă) — suficient și curat; toate cadrele ar dilua setul cu near-duplicate.
- Eticheta corectată nu e re-verificată de nimeni (operatorul e sursa de adevăr); pentru dizertație e modelul de încredere corect — într-un sistem multi-operator s-ar adăuga o coadă de revizuire.
- `feedback` pentru incidente din istoric funcționează identic (endpoint-ul nu cere incident activ).

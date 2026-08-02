# Chicago Risk Score API

Final Project MLOps SISTECH 2026. Repository ini berisi sistem prediksi Risk Score untuk lokasi dan waktu tertentu, disajikan sebagai REST API berbasis FastAPI.

Dokumentasi ini ditulis dari sudut pandang developer: apa yang sudah dibangun untuk CP2, bagaimana alur sistemnya, artefak apa yang dipakai, dan apa yang perlu ditunjukkan saat demo atau submit.

## Ringkasan Singkat

Risk Score adalah estimasi 0-100 yang merangkum tiga dimensi:

1. Tingkat keparahan kejadian kriminal.
2. Seberapa baru kejadian tersebut.
3. Seberapa dekat kejadian tersebut dengan titik yang ditanyakan.

Sistem ini tidak memprediksi kepastian kejadian, melainkan menghasilkan estimasi berbasis pola historis. Data serving dibangun dari hasil pipeline sebelumnya, lalu dipakai oleh API untuk menjawab request real-time.

## Status CP2

Pada checkpoint CP2, fokus utama repository ini adalah:

- Model Training & Baseline Comparison.
- REST API Serving.

Artinya, deliverable CP2 yang paling penting bukan raw data mentah, melainkan hasil training, artefak model, dan API yang bisa dipanggil secara lokal.

### Yang sudah siap untuk CP2

- Notebook training tersedia di [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb).
- Artefak model tersimpan di [models/risk_model_v1.joblib](models/risk_model_v1.joblib).
- Lookup table serving tersedia di [data/processed/risk_lookup_table.csv](data/processed/risk_lookup_table.csv).
- Feature reference untuk fallback model tersedia di [data/processed/grid_feature_reference.csv](data/processed/grid_feature_reference.csv).
- API utama sudah tersedia dan tervalidasi lewat test suite.

## Arsitektur Runtime

Alur runtime sistem sederhana:

1. Request masuk ke FastAPI.
2. Router memvalidasi parameter dan parsing datetime.
3. Sistem mencari hasil exact match di lookup table.
4. Jika tidak ada, sistem memakai fallback model.
5. Response dikembalikan dalam format JSON yang konsisten.

### File inti runtime

- [app/main.py](app/main.py) menjadi entry point FastAPI.
- [app/routers/risk_score.py](app/routers/risk_score.py) menangani endpoint utama scoring.
- [app/routers/heatmap.py](app/routers/heatmap.py) menghasilkan sebaran skor per grid.
- [app/routers/safe_commute.py](app/routers/safe_commute.py) menghitung opsi waktu/rute sederhana.
- [app/routers/locations.py](app/routers/locations.py) menyediakan lokasi statis untuk UI.
- [app/routers/health.py](app/routers/health.py) menyediakan health check.
- [app/routers/monitoring.py](app/routers/monitoring.py) menyediakan metadata model.
- [app/utils.py](app/utils.py) berisi helper parsing, scoring, prediksi fallback, dan logging.
- [app/loader.py](app/loader.py) memuat model dan dataset processed saat aplikasi start.

## Notebook Training

Notebook [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb) adalah bukti utama CP2 untuk sisi modeling.

Notebook ini dipakai untuk:

- memuat data hasil feature engineering,
- membuat baseline sederhana,
- melatih model machine learning,
- membandingkan performa baseline vs model,
- menyimpan artefak model dan feature reference.

### Hasil yang perlu ditunjukkan

Output yang paling penting dari notebook adalah perbandingan metrik berikut:

```text
Baseline   | MAE= 9.546 | RMSE=12.391 | R2=-0.000
Model      | MAE= 3.082 | RMSE= 4.338 | R2= 0.877
Perbaikan MAE terhadap baseline: 67.71 persen
```

Interpretasi singkat:

- Baseline hanya menjadi pembanding sederhana.
- Model memberi error jauh lebih rendah dari baseline.
- R2 model positif dan tinggi, sedangkan baseline mendekati nol.

### Artefak yang dihasilkan

- [models/risk_model_v1.joblib](models/risk_model_v1.joblib)
- [data/processed/grid_feature_reference.csv](data/processed/grid_feature_reference.csv)

Jika diminta penjelasan teknis, jelaskan bahwa file-file tersebut adalah hasil training yang dipakai langsung oleh API.

## REST API

API dijalankan dengan FastAPI dan secara default menyediakan Swagger UI di `/docs`.

### Endpoint utama

#### `GET /risk-score`

Parameter:

- `lat`
- `lon`
- `datetime`

Contoh:

```text
GET /risk-score?lat=41.86&lon=-87.67&datetime=2026-07-30T00:00:00
```

Response berisi:

- `risk_score`
- `level`
- `model_version`
- `last_updated`
- `source`

#### `GET /heatmap`

Parameter:

- `datetime`

Contoh:

```text
GET /heatmap?datetime=2026-07-30T14:00:00
```

Response berisi titik grid yang relevan untuk waktu tersebut.

#### `GET /safe-commute`

Parameter:

- `lat_start`
- `lon_start`
- `lat_end`
- `lon_end`
- `datetime`
- `window_hours` opsional

Contoh:

```text
GET /safe-commute?lat_start=41.88&lon_start=-87.63&lat_end=41.90&lon_end=-87.60&datetime=2026-07-30T14:00:00
```

Endpoint ini membandingkan beberapa opsi waktu keberangkatan dan memilih rekomendasi dengan risk score rata-rata terendah.

#### `GET /locations`

Mengembalikan daftar lokasi statis untuk kebutuhan dropdown atau pemetaan UI.

#### `GET /health`

Health check sederhana untuk memastikan service hidup.

#### `GET /model-metrics`

Endpoint monitoring ringan untuk melihat metadata model versioning.

### Cara menjalankan API lokal

Aktifkan virtual environment lalu jalankan:

```bash
python -m uvicorn app.main:app --reload
```

Jika ingin spesifik ke port tertentu:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Lalu buka:

```text
http://127.0.0.1:8000/docs
```

## Monitoring dan Logging

CP2 sudah memiliki monitoring dasar.

### Logging prediksi

Setiap request ke `/risk-score` dicatat ke:

- [logs/prediction_log.csv](logs/prediction_log.csv)

Kolom yang dicatat:

- timestamp
- lat
- lon
- datetime
- risk_score
- source

### Metadata model

Riwayat model disiapkan lewat:

- [models/model_versions.json](models/model_versions.json)

Untuk CP2, file ini berfungsi sebagai placeholder versioning ringan dan dasar observabilitas model.

## Validation

Hal yang bisa dijadikan bukti teknis saat submit:

```bash
pytest tests -q
```

Hasil yang diharapkan:

```text
15 passed
```

Ini menunjukkan endpoint utama, validasi input, dan helper logic berjalan.

### A. Urutan Demo

1. Buka [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb).
2. Tunjukkan output perbandingan baseline vs model.
3. Tunjukkan bahwa model disimpan sebagai artefak training.
4. Buka Swagger UI di `/docs`.
5. Demo endpoint `/risk-score`.
6. Demo endpoint `/heatmap`.
7. Demo endpoint `/safe-commute`.
8. Demo endpoint `/locations`.
9. Tunjukkan hasil `pytest tests -q`.

### B. Output Notebook 

```text
Baseline   | MAE= 9.546 | RMSE=12.391 | R2=-0.000
Model      | MAE= 3.082 | RMSE= 4.338 | R2= 0.877
Perbaikan MAE terhadap baseline: 67.71 persen
```

- Baseline hanyalah pembanding sederhana.
- Model memberi performa yang jauh lebih baik.
- Risk Score sudah siap dipakai sebagai service, bukan hanya eksperimen notebook.

### C. Artefak 

- [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb)
- [models/risk_model_v1.joblib](models/risk_model_v1.joblib)
- [data/processed/risk_lookup_table.csv](data/processed/risk_lookup_table.csv)
- [data/processed/grid_feature_reference.csv](data/processed/grid_feature_reference.csv)
- [data/processed/features_labels_events.csv](data/processed/features_labels_events.csv)
- [tests/test_api_endpoints.py](tests/test_api_endpoints.py)


### D. Bukti Teknis 

Hasil test suite

```bash
pytest tests -q
```

Target output:

```text
15 passed
```

Ini membuktikan endpoint utama, validasi input, dan helper logic berjalan dengan baik.


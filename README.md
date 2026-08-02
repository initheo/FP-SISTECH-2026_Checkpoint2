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

### Yang perlu ditunjukkan saat demo CP2

- Output notebook yang membandingkan baseline vs model.
- Swagger UI di `/docs`.
- Endpoint `/risk-score`, `/heatmap`, `/safe-commute`, dan `/locations`.
- Hasil `pytest tests -q`.

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

## CP2 Submission Package

Bagian ini adalah format yang sebaiknya dipakai saat mengumpulkan CP2. Fokusnya adalah membuktikan dua hal: proses training sudah selesai dan REST API benar-benar bisa dipakai.

### A. Yang Harus Ditunjukkan Saat Demo

Urutan demo yang paling aman:

1. Buka [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb).
2. Tunjukkan output perbandingan baseline vs model.
3. Tunjukkan bahwa model disimpan sebagai artefak training.
4. Buka Swagger UI di `/docs`.
5. Demo endpoint `/risk-score`.
6. Demo endpoint `/heatmap`.
7. Demo endpoint `/safe-commute`.
8. Demo endpoint `/locations`.
9. Tunjukkan hasil `pytest tests -q`.

### B. Output Notebook yang Wajib Masuk Bukti

Ambil screenshot atau cuplikan output dari notebook training yang menampilkan metrik berikut:

```text
Baseline   | MAE= 9.546 | RMSE=12.391 | R2=-0.000
Model      | MAE= 3.082 | RMSE= 4.338 | R2= 0.877
Perbaikan MAE terhadap baseline: 67.71 persen
```

Makna yang perlu kamu sampaikan:

- Baseline hanyalah pembanding sederhana.
- Model memberi performa yang jauh lebih baik.
- Risk Score sudah siap dipakai sebagai service, bukan hanya eksperimen notebook.

### C. Artefak yang Harus Disertakan

File yang paling relevan untuk disubmit:

- [notebooks/model_training_baseline_comparison.ipynb](notebooks/model_training_baseline_comparison.ipynb)
- [models/risk_model_v1.joblib](models/risk_model_v1.joblib)
- [data/processed/risk_lookup_table.csv](data/processed/risk_lookup_table.csv)
- [data/processed/grid_feature_reference.csv](data/processed/grid_feature_reference.csv)
- [data/processed/features_labels_events.csv](data/processed/features_labels_events.csv)
- [tests/test_api_endpoints.py](tests/test_api_endpoints.py)

Kalau dikumpulkan dalam zip, pastikan isi utamanya adalah source code, model/artifacts, dan bukti presentasi/hasil, bukan raw data mentah.

### D. Bukti Teknis yang Bisa Ditampilkan

Sertakan hasil test suite berikut sebagai verifikasi:

```bash
pytest tests -q
```

Target output:

```text
15 passed
```

Ini membuktikan endpoint utama, validasi input, dan helper logic berjalan dengan baik.

### E. Paket Submission yang Rapi

Jika ingin menyusun folder submit, struktur yang paling masuk akal adalah:

- source code repository,
- model dan processed artifacts,
- screenshot atau PDF hasil demo,
- notebook training sebagai bukti proses,
- hasil test suite.

### F. Ringkasan Narasi Saat Submit

Kalimat inti yang aman dipakai saat presentasi:

"Saya membangun sistem Risk Score end-to-end: mulai dari pseudo-labeling dan training, lalu membandingkannya dengan baseline, kemudian men-deploy hasilnya sebagai REST API yang bisa dikonsumsi front-end."

"Hasil model menunjukkan peningkatan yang signifikan dibanding baseline, dan API sudah tervalidasi lewat test suite serta Swagger UI."

## Catatan Penting

- Repository ini sudah fokus pada serving hasil pipeline, bukan menjalankan raw notebook saat runtime.
- Swagger UI aktif lewat FastAPI, jadi demo paling cepat adalah lewat `/docs`.
- Jika port 8000 sedang dipakai proses lain, matikan proses tersebut sebelum menjalankan Uvicorn lagi.
- Risk Score adalah estimasi berbasis pola historis, bukan kepastian kejadian.

## Next Step Setelah CP2

Setelah CP2 selesai, pengembangan berikutnya adalah:

- continual learning yang lebih lengkap,
- versioning model yang lebih formal,
- monitoring yang lebih kaya,
- dokumentasi final dan presentasi.

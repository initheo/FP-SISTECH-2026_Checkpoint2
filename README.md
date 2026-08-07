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

#### `GET /api`

Ini adalah endpoint pintu masuk yang paling cocok dibagikan ke FE kalau mereka minta model "satu link lalu bercabang".

Contoh response:

```json
{
	"message": "Chicago Risk Score API",
	"description": "Read-only geospatial risk API for Chicago reporting and commute analysis.",
	"scope": "Chicago only",
	"endpoints": [
		"GET /health",
		"GET /api",
		"GET /docs",
		"GET /openapi.json",
		"GET /risk-score",
		"GET /heatmap",
		"GET /safe-commute",
		"GET /locations",
		"GET /coverage",
		"GET /model-metrics",
		"GET /prediction-stats"
	]
}
```

Kalau FE butuh satu base URL, formatnya seperti ini:

```text
https://domain-api-kamu.com
```

Lalu cabangnya tinggal:

- `https://domain-api-kamu.com/api`
- `https://domain-api-kamu.com/risk-score`
- `https://domain-api-kamu.com/heatmap`
- `https://domain-api-kamu.com/locations`
- `https://domain-api-kamu.com/safe-commute`

Untuk report lokasi, FE bisa mengambil data titik dari `GET /locations` lalu render sebagai marker atau daftar titik di UI.

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
- `source` — `lookup_table` atau `model_fallback`
- `disclaimer` — pernyataan etis bahwa skor adalah estimasi, bukan prediksi kepastian kejadian

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

## CP3 Implementation

CP3 menambahkan alur continual learning yang bisa dijalankan dari data processed yang sudah ada. Implementasinya dibuat di [app/continual_learning.py](app/continual_learning.py) dan dapat dieksekusi lewat [scripts/continual_learning.py](scripts/continual_learning.py).

### Tujuan CP3

- mensimulasikan data baru yang datang bertahap,
- mendeteksi drift berdasarkan kenaikan MAE,
- melatih ulang model hanya ketika drift terdeteksi,
- menerima checkpoint baru hanya jika kualitas membaik,
- mencatat versi model beserta konteks evaluasinya.

### Alur Implementasi

1. Dataset [data/processed/features_labels_events.csv](data/processed/features_labels_events.csv) dibaca dan diurutkan berdasarkan `Date`.
2. Data dipecah menjadi beberapa batch temporal.
3. Model serving aktif dipakai sebagai baseline awal.
4. Setiap batch baru dievaluasi untuk melihat apakah MAE naik lebih dari ambang drift.
5. Jika drift terdeteksi, model kandidat dilatih ulang dari seluruh data yang sudah terlihat.
6. Kandidat dievaluasi pada holdout tetap.
7. Kandidat hanya dipromosikan jika holdout MAE turun dan RMSE tidak memburuk.
8. Jika promosi berhasil, versi baru disimpan ke folder [models](models) dan metadata ditambahkan ke [models/model_versions.json](models/model_versions.json).

### Parameter Penting

- `CP3_BATCH_COUNT = 4`
- `CP3_DRIFT_THRESHOLD = 0.15`
- `CP3_QUALITY_GATE = 0.05`
- `CP3_RANDOM_STATE = 42`

### Cara Menjalankan Simulasi CP3

Jalankan pipeline penuh:

```bash
python scripts/continual_learning.py
```

Untuk run lebih cepat saat development:

```bash
python scripts/continual_learning.py --max-rows 200000 --no-persist
```

Output script berupa JSON summary berisi:

- daftar batch temporal,
- event drift,
- checkpoint yang diterima atau ditolak,
- metrik holdout sebelum dan sesudah retraining.

### Monitoring CP3

Endpoint [GET /model-metrics](app/routers/monitoring.py) membaca isi [models/model_versions.json](models/model_versions.json), sehingga histori model dapat ditampilkan di API tanpa menjalankan notebook.

### Deliverable CP3 yang Perlu Disiapkan

- notebook continual learning,
- model version history yang terisi,
- hasil simulasi drift/retraining,
- laporan atau slide yang menjelaskan keputusan update model.

## Validation

Hal yang bisa dijadikan bukti teknis saat submit:

```bash
pytest tests -q
```

Hasil yang diharapkan:

```text
18 passed
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

## Deployment untuk Website

Bagian ini menjelaskan cara men-deploy project supaya API bisa dipakai oleh frontend website. Karena repository ini berisi backend FastAPI, maka yang dideploy ke server publik adalah API + model artifact + processed data. Frontend akan mengonsumsi API tersebut lewat base URL.

### 1. Yang harus ikut ter-deploy

- Kode aplikasi di [app](app).
- Model artifact di [models/risk_model_v1.joblib](models/risk_model_v1.joblib).
- File metadata model di [models/model_versions.json](models/model_versions.json).
- Data processed di [data/processed](data/processed).
- Folder [logs](logs) akan dibuat saat runtime jika belum ada.

### 2. Cara deploy backend

Paling simpel adalah menjalankan FastAPI dengan `uvicorn` di environment server. Contoh command produksi:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Kalau ingin deployment yang lebih rapi, pakai Docker:

```bash
docker build -t chicago-risk-score-api .
docker run --env-file .env -p 8000:8000 chicago-risk-score-api
```

Atau dengan Docker Compose:

```bash
docker compose up --build -d
```

Kalau memakai platform seperti Render, Railway, atau VPS, pastikan:

- dependency dari [requirements.txt](requirements.txt) sudah ter-install,
- working directory mengarah ke root repository,
- file model dan data processed ikut tersedia di server,
- file `.env` berisi `CORS_ALLOW_ORIGINS` sudah disiapkan,
- port dibuka sesuai konfigurasi platform.

### 3. Konfigurasi frontend

Frontend cukup diarahkan ke base URL API yang sudah dideploy. Contoh:

```text
VITE_API_BASE_URL=https://your-api-domain.com
```

Lalu service FE memanggil endpoint seperti:

- `GET /risk-score?lat=...&lon=...&datetime=...`
- `GET /heatmap?datetime=...`
- `GET /safe-commute?...`
- `GET /locations`
- `GET /health`
- `GET /model-metrics`

Jika FE berada di domain berbeda, backend perlu mengaktifkan CORS agar browser mengizinkan request dari website frontend.

Untuk environment production, set variabel berikut di server:

```text
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
```

### 4. Checklist sebelum go-live

- Jalankan `pytest tests -q` dan pastikan semua test lulus.
- Buka `/docs` dan pastikan Swagger UI bisa diakses.
- Pastikan endpoint `/risk-score` hanya dipakai untuk koordinat Chicago agar hasil tetap valid.
- Pastikan FE memakai base URL production, bukan `localhost`.
- Pastikan response `Unavailable` ditangani dengan benar di UI jika lokasi di luar coverage.

### 5. Rekomendasi alur deploy

1. Deploy backend FastAPI ke server publik.
2. Verifikasi endpoint lewat Swagger atau Postman.
3. Update FE agar memakai API base URL production.
4. Uji integrasi FE dengan endpoint `/risk-score` dan `/heatmap`.
5. Kalau semuanya stabil, baru publish website.


### D. Bukti Teknis 

Hasil test suite

```bash
pytest tests -q
```

Target output:

```text
18 passed
```

Ini membuktikan endpoint utama, validasi input, dan helper logic berjalan dengan baik.


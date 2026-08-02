# Ringkasan Project: Chicago Risk Score System

Final Project — Machine Learning Operations
Sisters in Tech (SISTECH) by RISTEK Fasilkom UI 2026

---

## 1. Tujuan Project

Membangun sebuah sistem end-to-end yang memperkirakan **tingkat risiko kejahatan (Risk Score, skala 0-100)** pada suatu lokasi dan waktu tertentu, berdasarkan pola kejahatan historis di Kota Chicago, lalu menyajikan hasilnya melalui **REST API** yang dapat dikonsumsi oleh aplikasi lain (dalam hal ini, tim Front-End SISTECH).

Risk Score dirancang mencerminkan tiga dimensi sekaligus:

1. **Tingkat keparahan** kejahatan yang pernah terjadi di sekitar lokasi
2. **Seberapa baru** kejadian itu terjadi (semakin lama, semakin kecil pengaruhnya)
3. **Seberapa dekat** kejadian itu dengan lokasi yang ditanyakan

Karena dataset Chicago Crimes tidak menyediakan label Risk Score secara langsung, sistem ini membentuknya sendiri lewat proses **pseudo-labeling** berbasis domain knowledge (bukan data yang sudah berlabel dari awal).

Sistem juga dirancang untuk **beradaptasi terhadap data baru** (continual learning): mensimulasikan datangnya data secara bertahap, mendeteksi apakah pola berubah (drift), lalu memperbarui model secara terkendali kualitas — bukan retraining membabi buta.

### Disclaimer Penting

Risk Score adalah **estimasi berbasis pola historis**, bukan prediksi kepastian suatu kejadian. Dataset yang dipakai (Chicago) berkonteks Amerika Serikat, berbeda dengan konteks lokal Indonesia — ini perlu ditegaskan di setiap penyajian hasil agar tidak menyesatkan pengguna akhir.

---

## 2. Arsitektur Sistem Secara Keseluruhan

```
Dataset Chicago Crimes (mentah)
        |
        v
[ Notebook 01 ] Pseudo-Labeling & Feature Engineering
        |
        | menghasilkan
        v
features_labels_events.csv   risk_lookup_table.csv
        |                           |
        v                           |
[ Notebook 02 ] Model Training      |
  & Baseline Comparison             |
        |                           |
        v                           |
risk_model_v1.joblib                |
grid_feature_reference.csv          |
model_versions.json                 |
        |                           |
        +------------+--------------+
                     |
                     v
            [ REST API (FastAPI) ]
        /risk-score   /heatmap   /safe-commute
        /locations    /health    /model-metrics
                     |
                     v
        Dikonsumsi oleh Front-End
        (heatmap interaktif, safe commute, dropdown lokasi)
```

Prinsip desain utama: **notebook adalah pabrik data/model** (dijalankan sesekali, saat data atau parameter berubah), sedangkan **API adalah konsumen hasil pabrik** (dijalankan terus-menerus, hanya membaca file CSV/model yang sudah jadi — tidak pernah menjalankan ulang notebook).

---

## 3. Tahapan Pengerjaan (Checkpoint)

| Checkpoint | Komponen | Bobot Penilaian |
|---|---|---|
| CP1 | Pseudo-Labeling & Feature Engineering | 12.5% |
| CP2 | Model Training & Baseline Comparison | 17.5% |
| CP2 | Fungsionalitas API (FastAPI) | 15% |
| CP3 | Continual Learning (drift, retraining, versioning) | 25% |
| CP3 | Monitoring & Logging | 10% |
| CP3 | Laporan Akhir & Presentasi | 20% |

### CP1 — Pseudo-Labeling & Feature Engineering

Notebook: `notebooks/Final_PseudoLabeling_FeatureEngineering.ipynb`

- **Data cleaning**: parsing tanggal, filter koordinat dalam bounding box Chicago, pelaporan retention rate
- **Feature engineering temporal**: cyclical encoding (sin/cos) untuk jam, hari, bulan — bukan encoding linear, karena jam 23 dan jam 0 sebenarnya berdekatan secara siklis
- **Feature engineering spasial**: agregat historis per grid (jumlah kejahatan, tingkat penangkapan, komposisi jenis kejahatan)
- **Severity Scoring Engine**: skor dasar 0-100 mengikuti hierarki lima tingkat (merujuk NIBRS/FBI), ditambah modifier deskripsi (bonus senjata dipilih berdasarkan prioritas, bukan dijumlahkan, agar tidak double-count)
- **Validasi wajib**: fungsi severity dan decay diuji langsung terhadap contoh perilaku yang diberikan pada instruksi soal, sebelum dipakai ke seluruh dataset
- **Space-Time Decay**: peluruhan temporal (exponential, half-life dikalibrasi 260 hari agar kejadian 2 tahun lalu bernilai ~0.14 sesuai instruksi soal) dan peluruhan spasial (kernel Gaussian berbasis jarak riil Haversine, dihitung lewat `BallTree` secara tervektorisasi)
- **Normalisasi**: `log1p` → clip persentil 99 → min-max ke skala 0-100
- **Output**: dua tabel yang saling konsisten — `features_labels_events.csv` (per kejadian, auditable) dan `risk_lookup_table.csv` (per grid-hari-jam, siap untuk API)

### CP2 — Model Training & Baseline Comparison, REST API Serving

Notebook: `notebooks/model_training_baseline_comparison.ipynb`

- **Baseline**: menebak rata-rata risk_score dari data latih, tanpa melihat fitur apapun
- **Model**: `RandomForestRegressor`, dilatih pada fitur temporal dan spasial untuk memprediksi risk_score
- **Split**: random split (bukan split berdasarkan waktu), karena label bergeser seiring waktu akibat temporal decay yang berpusat pada satu tanggal referensi tetap — split waktu baru dipakai khusus untuk simulasi continual learning di CP3
- **Evaluasi**: MAE, RMSE, R2, dibandingkan eksplisit antara baseline dan model
- **Output**: `risk_model_v1.joblib`, `grid_feature_reference.csv` (fitur historis per grid untuk fallback prediksi), `model_versions.json`

REST API: folder `app/`

| Endpoint | Fungsi | Sumber data |
|---|---|---|
| `GET /risk-score` | Endpoint wajib sesuai instruksi soal — skor risiko untuk satu titik lokasi dan waktu | `risk_lookup_table.csv`, fallback ke model jika kombinasi grid-waktu belum ada |
| `GET /heatmap` | Sebaran skor risiko di seluruh grid untuk satu waktu tertentu — dikonsumsi fitur heatmap interaktif FE | `risk_lookup_table.csv` |
| `GET /safe-commute` | Membandingkan skor risiko di beberapa titik sepanjang rute dan beberapa pilihan waktu keberangkatan | `risk_lookup_table.csv` + fallback model |
| `GET /locations` | Daftar lokasi (nama + koordinat) untuk dropdown Anonymous Report di FE | Data statis, koordinat konsisten dengan sistem grid |
| `GET /health` | Health check untuk platform hosting | - |
| `GET /model-metrics` | Riwayat metrik tiap versi model, untuk pemantauan performa | `model_versions.json` |

### CP3 — Continual Learning, Monitoring & Logging, Laporan Akhir

- **Continual learning**: data dibagi jadi batch berurutan waktu (simulasi "data baru datang"), tiap batch dicek drift (MAE pada data baru naik >15% dibanding referensi), jika drift terdeteksi maka model dilatih ulang tapi **hanya dipakai jika benar-benar lebih baik** pada data holdout tetap (quality gate) — bukan asal replace
- **Monitoring & logging**: setiap pemanggilan `/risk-score` dicatat ke `logs/prediction_log.csv` (timestamp, lokasi, waktu diminta, hasil skor, sumber prediksi); riwayat metrik antar versi model dapat dipantau lewat `/model-metrics`
- **Laporan akhir**: `reports/FP_MLOps_[FullName]_Report.pdf`, merangkum seluruh proses, justifikasi keputusan (parameter, algoritma, kriteria drift), dan refleksi

---

## 4. Struktur Folder

```
FP_MLOps_[FullName]/
├── README.md
├── requirements.txt
├── .gitignore
├── Procfile
├── Dockerfile
│
├── notebooks/
│   ├── Final_PseudoLabeling_FeatureEngineering.ipynb
│   ├── model_training_baseline_comparison.ipynb
│   └── 03_continual_learning.ipynb
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── loader.py
│   ├── utils.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       ├── risk_score.py
│       ├── heatmap.py
│       ├── safe_commute.py
│       ├── locations.py
│       ├── health.py
│       └── monitoring.py
│
├── data/
│   ├── raw/                      (dataset mentah, tidak di-commit)
│   └── processed/
│       ├── features_labels_events.csv
│       ├── risk_lookup_table.csv
│       └── grid_feature_reference.csv
│
├── models/
│   ├── risk_model_v1.joblib
│   └── model_versions.json
│
├── logs/
│   └── prediction_log.csv        (dihasilkan otomatis saat API berjalan)
│
├── outputs/
│   └── FP_MLOps_[FullName]_Output.json
│
├── reports/
│   └── FP_MLOps_[FullName]_Report.pdf
│
└── tests/
    ├── test_severity_validation.py
    ├── test_decay_validation.py
    └── test_api_endpoints.py
```

---

## 5. Cara Menjalankan Project

### 5.1. Instalasi

```bash
git clone <url-repository-ini>
cd FP_MLOps_[FullName]

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 5.2. Menghasilkan Data dan Model (hanya sekali, atau saat data/parameter berubah)

Jika folder `data/processed/` dan `models/` **sudah berisi file**, langkah ini boleh dilewati — notebook hanya perlu dijalankan ulang saat:

- dataset mentah diganti (misalnya dari data sintetis ke dataset Chicago Crimes asli),
- atau parameter penting diubah (half-life, bandwidth spasial, struktur fitur, dsb).

```bash
jupyter execute notebooks/Final_PseudoLabeling_FeatureEngineering.ipynb
jupyter execute notebooks/model_training_baseline_comparison.ipynb
```

Setelah dijalankan, pastikan file berikut benar-benar terisi:

```bash
ls data/processed/    # features_labels_events.csv, risk_lookup_table.csv, grid_feature_reference.csv
ls models/            # risk_model_v1.joblib, model_versions.json
```

### 5.3. Menjalankan API Secara Lokal

```bash
uvicorn app.main:app --reload --port 8000
```

Buka `http://127.0.0.1:8000/docs` untuk dokumentasi interaktif (Swagger UI), tempat semua endpoint bisa dicoba langsung dari browser.

Contoh pemanggilan manual:

```
GET http://127.0.0.1:8000/risk-score?lat=41.86&lon=-87.67&datetime=2026-08-03T00:00:00
GET http://127.0.0.1:8000/heatmap?datetime=2026-08-03T00:00:00
GET http://127.0.0.1:8000/safe-commute?lat_start=41.88&lon_start=-87.63&lat_end=41.90&lon_end=-87.60&datetime=2026-08-03T00:00:00
GET http://127.0.0.1:8000/locations
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/model-metrics
```

### 5.4. Menjalankan Pengujian Otomatis

```bash
pytest tests/ -v
```

Pengujian mencakup: severity scoring cocok dengan contoh anchor pada instruksi soal, perilaku space-time decay sesuai tabel instruksi, dan kelima endpoint API merespons dengan benar (termasuk penanganan input tidak valid).

### 5.5. Continual Learning (CP3)

```bash
jupyter execute notebooks/03_continual_learning.ipynb
```

Notebook ini mensimulasikan data baru datang secara bertahap, mendeteksi drift, melatih ulang model bila diperlukan, dan memperbarui `models/model_versions.json` dengan entri versi baru — hanya jika model baru terbukti lebih baik pada data holdout tetap.

### 5.6. Deploy ke Hosting Eksternal (opsional, sesuai instruksi soal)

```bash
git push origin main
```

Lalu di Railway (atau Render):

1. New Project → Deploy from GitHub repo → pilih repository ini
2. Platform otomatis mendeteksi `requirements.txt` dan `Procfile`
3. Tambahkan health check dengan path `/health`
4. Setelah build selesai, API dapat diakses lewat URL publik, contoh: `https://fp-mlops-risk-score.up.railway.app/docs`

---

## 6. Batasan yang Diketahui

- Rute pada `/safe-commute` disederhanakan sebagai garis lurus antara titik awal dan akhir, bukan rute jalan sungguhan (butuh routing engine terpisah seperti OSRM/Google Directions API, di luar cakupan project ini)
- `/locations` memakai daftar lokasi statis karena dataset Chicago Crimes tidak menyediakan nama lokasi manusiawi, hanya koordinat
- Data `contacts`, `report-activity`, dan riwayat laporan pengguna berada di luar cakupan sistem ini — tidak melibatkan Risk Score sama sekali, sehingga menjadi tanggung jawab tim Back-End aplikasi, bukan bagian dari pipeline MLOps ini

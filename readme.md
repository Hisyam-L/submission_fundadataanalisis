# Proyek Analisis Data: Bike Sharing

Analisis data penyewaan sepeda Capital Bikeshare (Washington D.C., 1 Januari 2011 - 31 Desember 2012) beserta dashboard interaktifnya dengan Streamlit.

## Pertanyaan Bisnis

1. Pada jam berapa penyewaan mencapai puncak pada hari kerja vs akhir pekan/libur, dan berapa selisihnya?
2. Seberapa besar cuaca menurunkan penyewaan, dan musim apa yang tertinggi/terendah?

## Struktur Folder

```
submission
├── dashboard
│   ├── dashboard.py
│   └── main_data.csv
├── data
│   ├── day.csv
│   └── hour.csv
├── Proyek_Analisis_Data.ipynb
├── README.md
└── requirements.txt
```


- `data/`: dataset mentah (`day.csv` per hari, `hour.csv` per jam).
- `Proyek_Analisis_Data.ipynb`: proses data wrangling, EDA, visualisasi, dan analisis lanjutan.
- `dashboard/main_data.csv`: data bersih hasil notebook, bergranularitas per jam. Kolom berakhiran `_harian` berasal dari data harian.
- `dashboard/dashboard.py`: aplikasi dashboard Streamlit.

## Setup Environment

```
python -m venv myenv
source myenv/bin/activate        # Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

## Menjalankan Notebook

Jalankan notebook dari folder proyek (yang berisi `data/` dan `dashboard/`), lalu pilih **Run All**. Sel terakhir pada bagian Cleaning akan membuat `dashboard/main_data.csv`.

```
jupyter notebook Proyek_Analisis_Data.ipynb
```

## Menjalankan Dashboard

Pastikan `dashboard/main_data.csv` sudah dibuat oleh notebook, lalu jalankan:

```
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di `http://localhost:8501`.

## Sumber Data

Fanaee-T, H. & Gama, J. (2013). Bike Sharing Dataset, Capital Bikeshare, Washington D.C.
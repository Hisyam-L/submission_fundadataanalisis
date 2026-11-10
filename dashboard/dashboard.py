from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ----------------------------------------------------------------------------
# Konfigurasi halaman & gaya visual (konsisten dengan notebook)
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Bike Sharing", page_icon="🚲", layout="wide")

WARNA_UTAMA = "#1B6CA8"
WARNA_SOROT = "#E4572E"
WARNA_NETRAL = "#B9C0C9"
WARNA_TEKS = "#1f2933"

sns.set_theme(style="whitegrid")
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})

URUTAN_MUSIM = ["Musim Dingin", "Musim Semi", "Musim Panas", "Musim Gugur"]
URUTAN_CUACA = ["Cerah", "Berkabut/Mendung", "Hujan/Salju Ringan", "Hujan/Salju Lebat"]
URUTAN_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
TIPE_HARI = ["Hari Kerja", "Akhir Pekan/Libur"]
WARNA_TIPE = {"Hari Kerja": WARNA_UTAMA, "Akhir Pekan/Libur": WARNA_SOROT}
LABEL_SEGMEN = ["Dini Hari (00-05)", "Pagi (06-09)", "Siang (10-15)", "Sore (16-19)", "Malam (20-23)"]


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    folder = Path(__file__).parent
    df = pd.read_csv(folder / "main_data.csv", parse_dates=["dteday", "datetime"])

    # main_data.csv bergranularitas per jam; kolom berakhiran "_harian" berasal dari data harian.
    kolom_harian = ["casual", "registered", "cnt", "weathersit_label", "temp_c", "hum_pct", "windspeed_kmh"]
    day = (
        df.drop_duplicates("dteday")[["dteday", "season_label", "day_type"] + [f"{k}_harian" for k in kolom_harian]]
        .rename(columns={f"{k}_harian": k for k in kolom_harian})
        .reset_index(drop=True)
    )

    hour = df.drop(columns=[f"{k}_harian" for k in kolom_harian + ["anomali"] if f"{k}_harian" in df.columns])
    hour["segmen_waktu"] = pd.cut(hour["hr"], bins=[-1, 5, 9, 15, 19, 23], labels=LABEL_SEGMEN)
    return day, hour


day_df, hour_df = load_data()

# ----------------------------------------------------------------------------
# Sidebar: filter interaktif
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("🚲 Bike Sharing")
    st.caption("Capital Bikeshare, Washington D.C. (2011-2012)")

    tgl_min, tgl_max = day_df["dteday"].min().date(), day_df["dteday"].max().date()
    rentang = st.date_input("Rentang tanggal", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max)
    musim_pilihan = st.multiselect("Musim", URUTAN_MUSIM, default=URUTAN_MUSIM)

    st.markdown("---")
    st.caption(
        "Catatan: label musim pada Readme dataset tidak sesuai kalender, "
        "sehingga telah dikoreksi berdasarkan bulan dan suhu aktual."
    )

# date_input mengembalikan 1 tanggal saat pengguna baru memilih tanggal awal
if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
    awal, akhir = rentang
else:
    awal, akhir = tgl_min, tgl_max

mask_day = (
    (day_df["dteday"].dt.date >= awal)
    & (day_df["dteday"].dt.date <= akhir)
    & (day_df["season_label"].isin(musim_pilihan))
)
mask_hour = (
    (hour_df["dteday"].dt.date >= awal)
    & (hour_df["dteday"].dt.date <= akhir)
    & (hour_df["season_label"].isin(musim_pilihan))
)
day_f = day_df[mask_day]
hour_f = hour_df[mask_hour]

# ----------------------------------------------------------------------------
# Header & ringkasan
# ----------------------------------------------------------------------------
st.title("Dashboard Analisis Penyewaan Sepeda")
st.write("Menjawab dua pertanyaan bisnis: **kapan** penyewaan memuncak, dan **seberapa besar** cuaca serta musim memengaruhinya.")

if day_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah rentang tanggal atau pilihan musim.")
    st.stop()

total = int(day_f["cnt"].sum())
rata_harian = day_f["cnt"].mean()
pct_registered = day_f["registered"].sum() / day_f["cnt"].sum() * 100
jam_puncak_all = hour_f.groupby("hr")["cnt"].mean().idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{total:,}".replace(",", "."))
k2.metric("Rata-rata per hari", f"{rata_harian:,.0f}".replace(",", "."))
k3.metric("Pengguna terdaftar", f"{pct_registered:.1f}%")
k4.metric("Jam puncak", f"{jam_puncak_all:02d}.00")

tab1, tab2, tab3, tab4 = st.tabs(
    ["⏰ Pola Jam (Pertanyaan 1)", "🌦️ Cuaca & Musim (Pertanyaan 2)", "🔎 Analisis Lanjutan", "📋 Data"]
)

# ----------------------------------------------------------------------------
# Tab 1: pola jam
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("Pada jam berapa penyewaan memuncak: hari kerja vs akhir pekan/libur?")
    pola = hour_f.pivot_table(index="hr", columns="day_type", values="cnt", aggfunc="mean")
    tipe_ada = [t for t in TIPE_HARI if t in pola.columns]

    if not tipe_ada:
        st.info("Data jam tidak tersedia untuk filter ini.")
    else:
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.axvspan(7, 9, color=WARNA_NETRAL, alpha=0.25, lw=0)
        ax.axvspan(16, 19, color=WARNA_NETRAL, alpha=0.25, lw=0)
        for tipe in tipe_ada:
            ax.plot(pola.index, pola[tipe], marker="o", ms=4, lw=2.5, color=WARNA_TIPE[tipe], label=tipe)
            jam_p, nilai_p = pola[tipe].idxmax(), pola[tipe].max()
            ax.annotate(
                f"Puncak {jam_p:02d}.00\n{nilai_p:.0f} sepeda/jam",
                xy=(jam_p, nilai_p),
                xytext=(jam_p, nilai_p + 0.1 * pola.max().max()),
                ha="center", color=WARNA_TIPE[tipe], fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=WARNA_TIPE[tipe]),
            )
        ax.set_ylim(0, pola.max().max() * 1.28)
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{j:02d}" for j in range(0, 24, 2)])
        ax.set_xlabel("Jam dalam sehari")
        ax.set_ylabel("Rata-rata penyewaan per jam")
        ax.legend(frameon=False, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        if len(tipe_ada) == 2:
            hk, wk = pola["Hari Kerja"], pola["Akhir Pekan/Libur"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Puncak hari kerja", f"{hk.idxmax():02d}.00", f"{hk.max():.0f} sepeda/jam", delta_color="off")
            c2.metric("Puncak akhir pekan/libur", f"{wk.idxmax():02d}.00", f"{wk.max():.0f} sepeda/jam", delta_color="off")
            selisih = (hk.loc[hk.idxmax()] / wk.loc[hk.idxmax()] - 1) * 100
            c3.metric(f"Selisih pada {hk.idxmax():02d}.00", f"{selisih:+.0f}%", "hari kerja vs akhir pekan", delta_color="off")

        st.info(
            "Hari kerja memiliki dua puncak komuter (pagi dan sore), sedangkan akhir pekan/libur hanya satu puncak landai "
            "di siang hari. Gunakan pola ini untuk menjadwalkan redistribusi sepeda sebelum jam sibuk dan perawatan "
            "pada jam paling sepi (dini hari hari kerja)."
        )

# ----------------------------------------------------------------------------
# Tab 2: cuaca & musim
# ----------------------------------------------------------------------------
def bar_sorot(ax, data, warna_map, judul):
    warna = [warna_map.get(k, WARNA_NETRAL) for k in data.index]
    batang = ax.bar(data.index, data["rata_rata"], color=warna, width=0.62)
    for b, (_, baris) in zip(batang, data.iterrows()):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + data["rata_rata"].max() * 0.01,
                f"{baris['rata_rata']:,.0f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
    ax.set_title(judul, loc="left", fontsize=12, fontweight="bold")
    ax.set_xlabel("")
    ax.grid(False, axis="x")
    ax.tick_params(axis="x", labelsize=9)


with tab2:
    st.subheader("Seberapa besar cuaca menurunkan penyewaan, dan musim apa tertinggi/terendah?")

    cuaca = (
        day_f.groupby("weathersit_label")["cnt"].agg(rata_rata="mean", jumlah_hari="size")
        .reindex([c for c in URUTAN_CUACA if c in day_f["weathersit_label"].unique()])
    )
    musim = (
        day_f.groupby("season_label")["cnt"].agg(rata_rata="mean", jumlah_hari="size")
        .reindex([m for m in URUTAN_MUSIM if m in day_f["season_label"].unique()])
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)

    # Panel cuaca
    if "Cerah" in cuaca.index:
        cuaca["selisih"] = (cuaca["rata_rata"] / cuaca.loc["Cerah", "rata_rata"] - 1) * 100
    warna_cuaca = {cuaca["rata_rata"].idxmin(): WARNA_SOROT} if len(cuaca) > 1 else {}
    bar_sorot(axes[0], cuaca, warna_cuaca, "Rata-rata penyewaan per hari menurut cuaca")
    for i, (nama, baris) in enumerate(cuaca.iterrows()):
        sorot = warna_cuaca.get(nama) is not None
        teks = f"n={int(baris['jumlah_hari'])} hari"
        if "selisih" in cuaca.columns and nama != "Cerah":
            teks = f"{baris['selisih']:.0f}% vs cerah\n" + teks
        axes[0].text(i, baris["rata_rata"] / 2, teks, ha="center", va="center", fontsize=9, fontweight="bold",
                     color="white" if sorot else WARNA_TEKS)

    # Panel musim
    warna_musim = {}
    if len(musim) > 1:
        warna_musim = {musim["rata_rata"].idxmax(): WARNA_UTAMA, musim["rata_rata"].idxmin(): WARNA_SOROT}
    bar_sorot(axes[1], musim, warna_musim, "Rata-rata penyewaan per hari menurut musim")
    for i, (nama, baris) in enumerate(musim.iterrows()):
        axes[1].text(i, baris["rata_rata"] / 2, f"n={int(baris['jumlah_hari'])} hari", ha="center", va="center",
                     fontsize=9, color="white" if nama in warna_musim else WARNA_TEKS)

    axes[0].set_ylabel("Rata-rata penyewaan per hari")
    ymax = max(cuaca["rata_rata"].max(), musim["rata_rata"].max())
    axes[0].set_ylim(0, ymax * 1.15)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    if "selisih" in cuaca.columns and len(cuaca) > 1:
        kol = st.columns(len(cuaca) - 1)
        for k, (nama, baris) in zip(kol, cuaca.drop(index="Cerah").iterrows()):
            k.metric(f"{nama} vs cerah", f"{baris['selisih']:.1f}%", f"{baris['rata_rata']:,.0f} per hari", delta_color="off")
    if len(musim) > 1:
        st.info(
            f"Musim tertinggi: **{musim['rata_rata'].idxmax()}** ({musim['rata_rata'].max():,.0f}/hari). "
            f"Terendah: **{musim['rata_rata'].idxmin()}** ({musim['rata_rata'].min():,.0f}/hari). "
            "Perhatikan nilai n: kategori cuaca dengan hari yang sedikit sebaiknya dibaca sebagai indikasi, bukan angka presisi."
        )

# ----------------------------------------------------------------------------
# Tab 3: analisis lanjutan (manual grouping & binning)
# ----------------------------------------------------------------------------
with tab3:
    st.subheader("Analisis lanjutan: Manual Grouping & Binning")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Porsi penyewaan per segmen waktu**")
        seg = hour_f.pivot_table(index="segmen_waktu", columns="day_type", values="cnt", aggfunc="sum", observed=True)
        seg = seg[[t for t in TIPE_HARI if t in seg.columns]]
        seg_pct = seg / seg.sum() * 100
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        seg_pct.plot(kind="bar", ax=ax, color=[WARNA_TIPE[c] for c in seg_pct.columns], width=0.75)
        ax.set_xlabel("")
        ax.set_ylabel("% dari total penyewaan")
        ax.set_xticklabels(seg_pct.index, rotation=25, ha="right")
        ax.grid(False, axis="x")
        ax.legend(title="", frameon=False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col_b:
        st.markdown("**Rata-rata penyewaan menurut kelompok suhu**")
        d = day_f.copy()
        d["kategori_suhu"] = pd.cut(d["temp_c"], bins=[0, 10, 20, 30, 50], right=False,
                                    labels=["< 10°C", "10-20°C", "20-30°C", ">= 30°C"])
        suhu = d.groupby("kategori_suhu", observed=True)["cnt"].agg(rata_rata="mean", jumlah_hari="size")
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        warna = [WARNA_UTAMA if v == suhu["rata_rata"].max() else WARNA_NETRAL for v in suhu["rata_rata"]]
        batang = ax.bar(suhu.index.astype(str), suhu["rata_rata"], color=warna, width=0.62)
        for b, (_, baris) in zip(batang, suhu.iterrows()):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + suhu["rata_rata"].max() * 0.01,
                    f"{baris['rata_rata']:,.0f}", ha="center", fontweight="bold")
            ax.text(b.get_x() + b.get_width() / 2, suhu["rata_rata"].max() * 0.03, f"n={int(baris['jumlah_hari'])}",
                    ha="center", fontsize=9, color="white" if b.get_facecolor()[:3] == (0.10588235294117647, 0.4235294117647059, 0.6588235294117647) else WARNA_TEKS)
        ax.set_ylim(0, suhu["rata_rata"].max() * 1.15)
        ax.set_xlabel("Suhu rata-rata harian")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.grid(False, axis="x")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("**Peta panas: rata-rata penyewaan per jam menurut hari**")
    heat = hour_f.pivot_table(index="weekday_name", columns="hr", values="cnt", aggfunc="mean")
    heat = heat.reindex([h for h in URUTAN_HARI if h in heat.index])
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(heat, cmap="Blues", ax=ax, cbar_kws={"label": "Rata-rata penyewaan per jam"}, linewidths=0.3, linecolor="white")
    ax.set_xlabel("Jam dalam sehari")
    ax.set_ylabel("")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ----------------------------------------------------------------------------
# Tab 4: data
# ----------------------------------------------------------------------------
with tab4:
    st.subheader("Data harian (setelah filter)")
    kolom = ["dteday", "season_label", "weathersit_label", "day_type", "temp_c", "hum_pct", "windspeed_kmh",
             "casual", "registered", "cnt"]
    st.dataframe(day_f[kolom].rename(columns={"dteday": "tanggal"}), hide_index=True)
    st.download_button(
        "Unduh data harian (CSV)",
        day_f[kolom].to_csv(index=False).encode("utf-8"),
        file_name="data_harian_terfilter.csv",
        mime="text/csv",
    )
    st.caption("Sumber: Fanaee-T & Gama (2013), Capital Bikeshare, Washington D.C.")
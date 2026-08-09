import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

DATA_FILE = "pengeluaran.csv"

st.set_page_config(page_title="Dashboard Pengeluaran Bulanan", layout="wide")

# ---------- Fungsi bantu ----------

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["Tanggal"])
    else:
        df = pd.DataFrame(columns=["Tanggal", "Kategori", "Jumlah", "Catatan"])
    return df


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


# ---------- State awal ----------

if "df" not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# ---------- Sidebar: input pengeluaran baru ----------

st.sidebar.header("➕ Tambah Pengeluaran")

with st.sidebar.form("form_tambah", clear_on_submit=True):
    tanggal = st.date_input("Tanggal", value=date.today())
    kategori = st.selectbox(
        "Kategori",
        ["Makanan", "Transportasi", "Belanja", "Hiburan", "Kesehatan",
         "Pendidikan", "Tagihan", "Lainnya"]
    )
    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    catatan = st.text_input("Catatan (opsional)")
    submit = st.form_submit_button("Simpan")

    if submit:
        new_row = pd.DataFrame([{
            "Tanggal": pd.to_datetime(tanggal),
            "Kategori": kategori,
            "Jumlah": jumlah,
            "Catatan": catatan
        }])
        st.session_state.df = pd.concat([df, new_row], ignore_index=True)
        save_data(st.session_state.df)
        st.sidebar.success("Pengeluaran tersimpan!")
        st.rerun()

st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader("Atau impor CSV (Tanggal, Kategori, Jumlah, Catatan)", type="csv")
if uploaded is not None:
    imported = pd.read_csv(uploaded, parse_dates=["Tanggal"])
    st.session_state.df = pd.concat([df, imported], ignore_index=True)
    save_data(st.session_state.df)
    st.sidebar.success("Data berhasil diimpor!")
    st.rerun()

# ---------- Muat ulang data terbaru ----------
df = st.session_state.df

st.title("📊 Dashboard Pengeluaran Bulanan")

if df.empty:
    st.info("Belum ada data pengeluaran. Tambahkan lewat sidebar di sebelah kiri.")
    st.stop()

df["Tanggal"] = pd.to_datetime(df["Tanggal"])
df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)

# ---------- Filter bulan ----------
bulan_list = sorted(df["Bulan"].unique(), reverse=True)
bulan_pilihan = st.selectbox("Pilih Bulan", ["Semua"] + bulan_list)

if bulan_pilihan != "Semua":
    df_filtered = df[df["Bulan"] == bulan_pilihan]
else:
    df_filtered = df

# ---------- Ringkasan (metrics) ----------
total = df_filtered["Jumlah"].sum()
rata_harian = df_filtered.groupby(df_filtered["Tanggal"].dt.date)["Jumlah"].sum().mean()
kategori_terbesar = (
    df_filtered.groupby("Kategori")["Jumlah"].sum().idxmax()
    if not df_filtered.empty else "-"
)
jumlah_transaksi = len(df_filtered)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pengeluaran", f"Rp {total:,.0f}")
col2.metric("Rata-rata per Hari", f"Rp {rata_harian:,.0f}")
col3.metric("Kategori Terbesar", kategori_terbesar)
col4.metric("Jumlah Transaksi", jumlah_transaksi)

st.markdown("---")

# ---------- Grafik ----------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Pengeluaran per Kategori")
    kategori_sum = df_filtered.groupby("Kategori")["Jumlah"].sum().reset_index()
    fig_pie = px.pie(kategori_sum, values="Jumlah", names="Kategori", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("Tren Pengeluaran Harian")
    tren = df_filtered.groupby(df_filtered["Tanggal"].dt.date)["Jumlah"].sum().reset_index()
    fig_line = px.line(tren, x="Tanggal", y="Jumlah", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Perbandingan Pengeluaran per Bulan")
bulanan = df.groupby("Bulan")["Jumlah"].sum().reset_index()
fig_bar = px.bar(bulanan, x="Bulan", y="Jumlah", text_auto=".2s")
st.plotly_chart(fig_bar, use_container_width=True)

# ---------- Tabel data ----------
st.subheader("Rincian Transaksi")
st.dataframe(
    df_filtered.sort_values("Tanggal", ascending=False)[["Tanggal", "Kategori", "Jumlah", "Catatan"]],
    use_container_width=True
)

# ---------- Hapus data ----------
with st.expander("🗑️ Hapus semua data"):
    if st.button("Hapus Semua Pengeluaran"):
        st.session_state.df = pd.DataFrame(columns=["Tanggal", "Kategori", "Jumlah", "Catatan"])
        save_data(st.session_state.df)
        st.rerun()
import streamlit as st
import os

st.set_page_config(
    page_title="Aplikasi Hiburan",
    page_icon="🎭",
    layout="wide"
)

# Fungsi untuk upload file Excel
def upload_excel():
    st.sidebar.header("Update Database")
    uploaded_file = st.sidebar.file_uploader("Upload file Excel terbaru", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            # Simpan file ke direktori
            with open("data_hiburan.xlsx", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.sidebar.success("Database berhasil diupdate!")
            st.experimental_rerun()  # Refresh aplikasi
        except Exception as e:
            st.sidebar.error(f"Gagal mengupdate database: {e}")

# Panggil fungsi upload
upload_excel()

# Konten utama
st.title("Selamat Datang di Aplikasi Hiburan")
st.write("""
Pilih halaman yang ingin Anda kunjungi dari menu sidebar di sebelah kiri.
- 🎧 Audiobook: Koleksi buku audio
- 🎬 Film: Koleksi film klasik
""")

# Informasi file database
if os.path.exists("data_hiburan.xlsx"):
    file_size = os.path.getsize("data_hiburan.xlsx") / 1024  # dalam KB
    st.sidebar.info(f"Database saat ini: data_hiburan.xlsx ({file_size:.2f} KB)")
else:
    st.sidebar.error("File database tidak ditemukan!")
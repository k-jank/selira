import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Selira",
    page_icon="",
    layout="wide"
)

# Konten utama
st.title("Selamat Datang")
st.write("""
Pilih halaman yang ingin Anda kunjungi dari menu sidebar di sebelah kiri.
- 🎧 Audiobook
- 🎬 Film
""")

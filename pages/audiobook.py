import streamlit as st
from database import get_audiobooks
import pandas as pd

st.set_page_config(
    page_title="Koleksi Audiobook",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Koleksi Audiobook")

# Load data
with st.spinner('Memuat data audiobook...'):
    audiobooks_df = get_audiobooks()

if audiobooks_df.empty:
    st.warning("Tidak ada data audiobook yang ditemukan dalam database.")
    st.info("Pastikan file Excel Anda memiliki sheet 'audiobooks' dengan data yang sesuai.")
else:
    # Tampilkan statistik
    col1, col2, col3 = st.columns(3)
    if 'penulis' in audiobooks_df.columns:
        unique_authors = audiobooks_df['penulis'].nunique()
        col1.metric("Total Penulis", unique_authors)
    
    if 'durasi' in audiobooks_df.columns and pd.api.types.is_numeric_dtype(audiobooks_df['durasi']):
        total_duration = audiobooks_df['durasi'].sum()
        col2.metric("Total Durasi", f"{total_duration} menit")
    
    col3.metric("Total Audiobook", len(audiobooks_df))

    # Filter
    st.sidebar.header("Filter Audiobook")
    
    if 'penulis' in audiobooks_df.columns:
        authors = audiobooks_df['penulis'].unique()
        selected_authors = st.sidebar.multiselect(
            "Filter berdasarkan Penulis",
            options=authors
        )
        
        if selected_authors:
            audiobooks_df = audiobooks_df[audiobooks_df['penulis'].isin(selected_authors)]
    
    # Tampilkan data
    st.dataframe(
        audiobooks_df,
        column_config={
            "judul": "Judul",
            "penulis": "Penulis",
            "narator": "Narator",
            "durasi": st.column_config.NumberColumn(
                "Durasi",
                help="Durasi dalam menit",
                format="%d menit"
            ),
            "rating": st.column_config.NumberColumn(
                "Rating",
                help="Rating 1-5",
                format="%.1f ⭐",
                min_value=0,
                max_value=5
            ),
            "link": st.column_config.LinkColumn("Link")
        },
        hide_index=True,
        use_container_width=True
    )
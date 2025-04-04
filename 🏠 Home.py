import streamlit as st
import pandas as pd
from database import get_films, get_audiobooks

st.set_page_config(
    page_title="Media Collection",
    page_icon="🏠",
    layout="wide"
)

st.title("Selamat Datang di Selira")

# Apply custom styling
st.markdown("""
<style>
    .media-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-decoration: none !important;
    }
    .media-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .media-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
        text-decoration: none !important;
    }
    .media-count {
        font-size: 18px;
        color: #0066cc;
        margin-bottom: 15px;
        text-decoration: none !important;
    }
    a {
        text-decoration: none !important;
        color: inherit;
    }
    .media-card * {
        text-decoration: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Get data for the home page
try:
    films_df = get_films()
    audiobooks_df = get_audiobooks()
    
    # Handle empty dataframes
    if films_df.empty:
        films_count = 0
        film_previews = []
    else:
        films_count = len(films_df)
        film_previews = films_df.sort_values(by='imdb_rating', ascending=False).head(5) if 'imdb_rating' in films_df.columns else films_df.head(5)
    
    if audiobooks_df.empty:
        audiobooks_count = 0
        audiobook_previews = []
    else:
        audiobooks_count = len(audiobooks_df)
        audiobook_previews = audiobooks_df.sort_values(by='rating', ascending=False).head(5) if 'rating' in audiobooks_df.columns else audiobooks_df.head(5)
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    films_count = 0
    audiobooks_count = 0
    film_previews = []
    audiobook_previews = []

# Create two columns for the media types
col1, col2 = st.columns(2)

# Film Section
with col1:
    st.markdown(f"""
    <a href="/Film" target="_self">
        <div class="media-card">
            <div class="media-title">🎬 Film</div>
            <div class="media-count">{films_count} Film tersedia</div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
# Audiobook Section
with col2:
    st.markdown(f"""
    <a href="/Audiobook" target="_self">
        <div class="media-card">
            <div class="media-title">🎧 Audiobook</div>
            <div class="media-count">{audiobooks_count} Audiobook tersedia</div>
        </div>
    </a>
    """, unsafe_allow_html=True)
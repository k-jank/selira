import streamlit as st
from database import get_films
import pandas as pd
import math

st.set_page_config(
    page_title="Koleksi Film",
    page_icon="🎬",
    layout="wide"
)

# Initialize session state for pagination and video playback
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
    
if 'selected_film' not in st.session_state:
    st.session_state.selected_film = None

# Function to play a video
def play_video(film_id, embed_url, title):
    st.session_state.selected_film = {
        'id': film_id,
        'embed_url': embed_url,
        'title': title
    }

# Search function
def search_films(df, query):
    if not query:
        return df
    query = query.lower()
    return df[df.apply(lambda row: any(query in str(row[col]).lower() 
                                     for col in ['title', 'director', 'actors', 'genres', 'country', 'writer']), axis=1)]

# Layout with search at top left
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎬 Koleksi Film")
with col2:
    search_query = st.text_input("🔍 Cari Film", placeholder="Judul, sutradara, pemain...")

# Display video player if a film is selected
if st.session_state.selected_film:
    film = st.session_state.selected_film
    st.markdown(f"<h3 style='text-align: center;'>{film['title']}</h3>", unsafe_allow_html=True)
    
    # Create a container for the embedded video
    video_container = st.container()
    with video_container:
        # If we have an embed URL, display it
        if film['embed_url'] and pd.notna(film['embed_url']):
            # Create an iframe to embed the video
            st.markdown(f"""
            <div style="position:relative; padding-bottom:56.25%; height:0; overflow:hidden; max-width:100%; border-radius:10px;">
                <iframe src="{film['embed_url']}" 
                        style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;" 
                        allowfullscreen>
                </iframe>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Tidak ada tautan video untuk film ini.")
    
    # Close button to stop watching
    if st.button("❌ Tutup Video"):
        st.session_state.selected_film = None
        st.rerun()
    
    # Horizontal line to separate video from film list
    st.markdown("---")

with st.spinner('Memuat data film...'):
    films_df = get_films()

if films_df.empty:
    st.error("""
    Data film tidak ditemukan. Pastikan:
    1. File Excel memiliki sheet bernama 'films'
    2. Struktur kolom sesuai contoh
    3. Data tidak kosong
    """)
    st.stop()

# Process data
try:
    # Apply search filter first
    if search_query:
        films_df = search_films(films_df, search_query)
    
    # Convert year to integer with proper NaN handling
    if 'year' in films_df.columns:
        # First convert to numeric, coerce errors to NaN
        films_df['year'] = pd.to_numeric(films_df['year'], errors='coerce')
        # Fill NaN values with 0
        films_df['year'] = films_df['year'].fillna(0)
        # Convert to integer
        films_df['year'] = films_df['year'].astype(int)
    
    # Add index as film_id if not present
    if 'id' not in films_df.columns:
        films_df['id'] = films_df.index
    
    # Sidebar filters
    st.sidebar.header("Filter Film")

    # Negara Filter
    if 'country' in films_df.columns:
        all_countries = set()
        for countries in films_df['country'].str.split(','):
            if isinstance(countries, list):
                all_countries.update([c.strip() for c in countries if c.strip()])
        selected_countries = st.sidebar.multiselect(
            "Negara",
            options=sorted(all_countries),
            default=[]
        )
        if selected_countries:
            films_df = films_df[films_df['country'].apply(
                lambda x: any(country in str(x) for country in selected_countries) if pd.notna(x) else False
            )]

    # Genre filter
    if 'genres' in films_df.columns:
        all_genres = set()
        for genres in films_df['genres'].str.split(','):
            if isinstance(genres, list):
                all_genres.update([g.strip() for g in genres])
        selected_genres = st.sidebar.multiselect(
            "Genre",
            options=sorted(all_genres),
            default=[]
        )
        if selected_genres:
            films_df = films_df[films_df['genres'].apply(
                lambda x: any(genre in str(x) for genre in selected_genres) if pd.notna(x) else False
            )]

    # Actors filter
    if 'actors' in films_df.columns:
        all_actors = set()
        for actors in films_df['actors'].str.split(','):
            if isinstance(actors, list):
                all_actors.update([a.strip() for a in actors])
        selected_actors = st.sidebar.multiselect(
            "Pemeran",
            options=sorted(all_actors),
            default=[]
        )
        if selected_actors:
            films_df = films_df[films_df['actors'].apply(
                lambda x: any(actor in str(x) for actor in selected_actors) if pd.notna(x) else False
            )]

    # Directors filter
    if 'director' in films_df.columns:
        all_directors = set()
        for directors in films_df['director'].str.split(','):
            if isinstance(directors, list):
                all_directors.update([d.strip() for d in directors])
        selected_directors = st.sidebar.multiselect(
            "Sutradara",
            options=sorted(all_directors),
            default=[]
        )
        if selected_directors:
            films_df = films_df[films_df['director'].apply(
                lambda x: any(director in str(x) for director in selected_directors) if pd.notna(x) else False
            )]

    # Writers filter
    if 'writer' in films_df.columns:
        all_writers = set()
        for writers in films_df['writer'].str.split(','):
            if isinstance(writers, list):
                all_writers.update([w.strip() for w in writers])
        selected_writers = st.sidebar.multiselect(
            "Penulis Naskah",
            options=sorted(all_writers),
            default=[]
        )
        if selected_writers:
            films_df = films_df[films_df['writer'].apply(
                lambda x: any(writer in str(x) for writer in selected_writers) if pd.notna(x) else False
            )]
    
    # Year filter with NaN handling
    if 'year' in films_df.columns:
        valid_years = films_df[films_df['year'] != 0]['year']
        
        if not valid_years.empty:
            min_year = int(valid_years.min())
            max_year = int(valid_years.max())
            
            if min_year == max_year:
                min_year = max(1900, min_year - 1)
                max_year = min(2100, max_year + 1)
            
            year_range = st.sidebar.slider(
                "Rentang Tahun",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year)
            )

            films_df = films_df[
                (films_df['year'] == 0) | 
                ((films_df['year'] >= year_range[0]) & 
                (films_df['year'] <= year_range[1]))
            ]
        else:
            st.sidebar.warning("Tidak ada data tahun yang valid untuk difilter")
    
    # Rating filter
    if 'imdb_rating' in films_df.columns:
        min_rating = float(films_df['imdb_rating'].min())
        max_rating = float(films_df['imdb_rating'].max())
        
        if min_rating == max_rating:
            if min_rating > 0:
                min_rating = max(0.0, min_rating - 0.5)
                max_rating = min(10.0, max_rating + 0.5)
            else:
                min_rating = 0.0
                max_rating = 1.0
        
        rating_range = st.sidebar.slider(
            "Rentang Rating IMDb",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            step=0.1
        )
        films_df = films_df[
            (films_df['imdb_rating'] >= rating_range[0]) & 
            (films_df['imdb_rating'] <= rating_range[1])
        ]

    # Check if no films match filters
    if len(films_df) == 0:
        st.warning("Tidak ada film yang sesuai dengan kriteria filter")
        st.stop()
    
    # Pagination
    items_per_page = st.session_state.get('items_per_page', 10)
    total_pages = max(1, math.ceil(len(films_df) / items_per_page))
    
    # Ensure page_number doesn't exceed total_pages after filtering
    if st.session_state.page_number > total_pages:
        st.session_state.page_number = total_pages
    
    # Function to change page with boundary checks
    def change_page(change):
        new_page = st.session_state.page_number + change
        if 1 <= new_page <= total_pages:
            st.session_state.page_number = new_page
    
    # Create containers
    pagination_top = st.container()
    film_grid = st.container()
    pagination_bottom = st.container()
    
    # Improved CSS for consistent card layout and clickable titles
    st.markdown("""
    <style>
        /* Card Container */
        .film-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            height: 500px;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        /* Poster Container */
        .poster-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 250px;
            margin-bottom: 10px;
            overflow: hidden;
            cursor: pointer;
        }
        
        /* Film Poster */
        .film-poster {
            max-height: 250px;
            max-width: 100%;
            object-fit: contain;
        }
        
        /* Improved Film Title with clickable styling */
        .film-title {
            font-weight: bold;
            font-size: 16px;
            margin: 5px 0;
            min-height: 60px;
            max-height: 80px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
            word-wrap: break-word;
            line-height: 1.3;
        }
        
        .film-title-link {
            color: #1E88E5;
            text-decoration: none;
            cursor: pointer;
        }
        
        .film-title-link:hover {
            text-decoration: underline;
            color: #0D47A1;
        }
        
        /* Play button overlay on poster */
        .play-overlay {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 24px;
        }
        
        .poster-container:hover .play-overlay {
            opacity: 1;
        }
        
        /* Film Details */
        .film-details {
            margin-top: 5px;
            font-size: 14px;
            flex-grow: 1;
        }
        
        /* Rating and Flag */
        .film-rating {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #ff9d00;
            font-weight: bold;
        }
        
        .country-flag {
            margin-left: 10px;
            color: black;
        }
        
        /* Detail text with scroll */
        .detail-text {
            max-height: 150px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        /* Video player container */
        .video-player {
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Top pagination with items per page selector
    with pagination_top:
        col1, col2, col3 = st.columns([0.4, 0.3, 0.3])
        with col1:
            st.write(f"Menampilkan {len(films_df)} film")
        with col2:
            items_options = [10, 15, 20, 25]
            selected_items = st.selectbox(
                "Film per halaman",
                options=items_options,
                index=items_options.index(items_per_page) if items_per_page in items_options else 0,
                key="items_per_page_select"
            )
            
            if selected_items != items_per_page:
                st.session_state.items_per_page = selected_items
                st.session_state.page_number = 1
                st.rerun()
            
        with col3:
            page_input = st.number_input(
                "Halaman",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.page_number,
                key="page_input_top"
            )
            if page_input != st.session_state.page_number:
                st.session_state.page_number = page_input
                st.rerun()
    
    # Calculate indices for the films to display
    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(films_df))
    paged_films = films_df.iloc[start_idx:end_idx]
    
    # Display film grid with improved layout and clickable titles
    with film_grid:
        # Create rows with 5 columns each
        cols_per_row = 5
        rows = math.ceil(len(paged_films) / cols_per_row)
        
        # Dictionary mapping country names to flag emojis
        country_to_flag = {
            'USA': '🇺🇸', 'United States': '🇺🇸', 'US': '🇺🇸',
            'UK': '🇬🇧', 'United Kingdom': '🇬🇧', 'Great Britain': '🇬🇧',
            'France': '🇫🇷', 'FR': '🇫🇷',
            'Japan': '🇯🇵', 'JP': '🇯🇵',
            'Italy': '🇮🇹', 'IT': '🇮🇹',
            'Germany': '🇩🇪', 'DE': '🇩🇪',
            'Canada': '🇨🇦', 'CA': '🇨🇦',
            'China': '🇨🇳', 'CN': '🇨🇳',
            'Australia': '🇦🇺', 'AU': '🇦🇺',
            'Spain': '🇪🇸', 'ES': '🇪🇸',
            'India': '🇮🇳', 'IN': '🇮🇳',
            'Korea': '🇰🇷', 'South Korea': '🇰🇷', 'KR': '🇰🇷',
            'Indonesia': '🇮🇩', 'ID': '🇮🇩',
            'Brazil': '🇧🇷', 'BR': '🇧🇷',
            'Russia': '🇷🇺', 'RU': '🇷🇺',
            'Mexico': '🇲🇽', 'MX': '🇲🇽',
            # Add more countries as needed
        }
        
        for row in range(rows):
            cols = st.columns(cols_per_row)
            
            for col in range(cols_per_row):
                idx = row * cols_per_row + col
                if idx < len(paged_films):
                    film = paged_films.iloc[idx]
                    with cols[col]:
                        # Get film data with fallbacks
                        film_id = film.get('id', idx)
                        title = film.get('title', 'Judul tidak tersedia')
                        year = film.get('year', 0)
                        year_display = year if year != 0 else 'Tidak tersedia'
                        poster_url = film.get('poster', '')
                        imdb_rating = film.get('imdb_rating', 'N/A')
                        plot = film.get('plot_id', 'Deskripsi tidak tersedia')
                        director = film.get('director', 'Tidak tersedia')
                        actors = film.get('actors', 'Tidak tersedia')
                        genres = film.get('genres', 'Tidak tersedia')
                        writer = film.get('writer', 'Tidak tersedia')
                        country = film.get('country', 'Tidak tersedia')
                        embed_url = film.get('embed_url', '')
                        
                        # Check if embed URL is available
                        has_video = pd.notna(embed_url) and embed_url != ''
                        
                        # Process country flag
                        country_flag = ''
                        if country != 'Tidak tersedia':
                            countries = [c.strip() for c in str(country).split(',')]
                            for c in countries:
                                if c in country_to_flag:
                                    country_flag += country_to_flag[c] + ' '
                        
                        # Create play button code if embed URL is available
                        play_button = ''
                        onclick_attr = ''
                        title_class = 'film-title'
                        
                        if has_video:
                            play_button = '<div class="play-overlay">▶️</div>'
                            onclick_attr = f'onclick="document.getElementById(\'play_btn_{film_id}\').click()"'
                            title_class = 'film-title film-title-link'
                        
                        # Create film card with HTML
                        html = f"""
                        <div class="film-card">
                            <div class="poster-container">
                                {'<img src="' + str(poster_url) + '" class="film-poster" alt="' + title + '" title="' + title + '">' if pd.notna(poster_url) and str(poster_url).startswith('http') else '<div style="text-align: center; color: #888;">Poster tidak tersedia</div>'}
                            </div>
                            <div class="film-title" title="{title} ({year_display})">{title} ({year_display})</div>
                            <div class="film-details">
                                <div class="film-rating">
                                    <span>⭐ {imdb_rating}/10</span>
                                    <span class="country-flag">{country_flag}</span>
                                </div>
                                <div><strong>Genre:</strong> {genres}</div>
                                <div><strong>Sutradara:</strong> {director}</div>
                                <div><strong>Pemeran:</strong> {actors}</div>
                                <div><strong>Penulis:</strong> {writer}</div>
                            </div>
                        </div>
                        """
                        st.markdown(html, unsafe_allow_html=True)
                        
                        # Hidden button to handle the click event
                        if has_video:
                            if st.button("▶️ Tonton", key=f"play_btn_{film_id}", use_container_width=True):
                                play_video(film_id, embed_url, title)
                                st.rerun()
                        
                        # Detail expander with scrollable content
                        with st.expander("Sinopsis"):
                            st.markdown(f'<div class="detail-text">{plot}</div>', unsafe_allow_html=True)
    
    # Bottom pagination
    with pagination_bottom:
        total_items = len(films_df)
        showing_start = start_idx + 1
        showing_end = end_idx
        
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if st.button("⬅️ Sebelumnya", 
                        disabled=(st.session_state.page_number <= 1),
                        key='prev_btn_bottom'):
                change_page(-1)
                st.rerun()
        
        with col2:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    Halaman {st.session_state.page_number} dari {total_pages} 
                    (Menampilkan {showing_start}-{showing_end} dari {total_items} film)
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col3:
            if st.button("Selanjutnya ➡️", 
                        disabled=(st.session_state.page_number >= total_pages),
                        key='next_btn_bottom'):
                change_page(1)
                st.rerun()

except Exception as e:
    st.error(f"Error memproses data: {str(e)}")
import streamlit as st
from database import get_audiobooks
import pandas as pd
import math
import re

st.set_page_config(
    page_title="Audiobook",
    page_icon="🎧",
    layout="wide"
)

# Initialize session state for pagination and audio playback
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
    
if 'selected_audiobook' not in st.session_state:
    st.session_state.selected_audiobook = None

# Function to parse timestamps from string
def parse_timestamps(timestamp_str):
    if not timestamp_str or pd.isna(timestamp_str):
        return []
    
    # Regular expression to match timestamp patterns like "00:00:00 TITLE"
    pattern = r'(\d{2}:\d{2}:\d{2})\s+(.+?)(?=\s+\d{2}:\d{2}:\d{2}|\Z)'
    matches = re.findall(pattern, timestamp_str)
    
    # If no matches found but there's content, check if it starts with "DAFTAR ISI"
    if not matches and "DAFTAR ISI" in timestamp_str:
        # Split by "DAFTAR ISI" and use the pattern on the remainder
        parts = timestamp_str.split("DAFTAR ISI", 1)
        if len(parts) > 1:
            matches = re.findall(pattern, parts[1])
    
    return matches

# Function to convert HH:MM:SS to seconds
def time_to_seconds(time_str):
    if not time_str:
        return 0
    
    parts = time_str.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    return 0

# Function to play audio
def play_audio(audiobook_id, embed_url, title, timestamp=None):
    st.session_state.selected_audiobook = {
        'id': audiobook_id,
        'embed_url': embed_url,
        'title': title,
        'timestamp': timestamp  # Store the selected timestamp
    }

# Search function
def search_audiobooks(df, query):
    if not query:
        return df
    query = query.lower()
    return df[df.apply(lambda row: any(query in str(row[col]).lower() 
                                     for col in ['title', 'author', 'narrator', 'genres', 'language']), axis=1)]

# Layout with search at top left
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎧 Audiobook")
with col2:
    search_query = st.text_input("🔍 Cari Audiobook", placeholder="Judul, penulis, narator...")

# Display audio player if an audiobook is selected
if st.session_state.selected_audiobook:
    audiobook = st.session_state.selected_audiobook
    st.markdown(f"<h3 style='text-align: center;'>{audiobook['title']}</h3>", unsafe_allow_html=True)
    
    # Get the audiobook's timestamp data
    audiobooks_df = get_audiobooks()
    current_audiobook = audiobooks_df[audiobooks_df['id'] == audiobook['id']].iloc[0] if not audiobooks_df.empty else None
    
    # Parse timestamps if available
    timestamps = []
    if current_audiobook is not None and 'timestamp' in current_audiobook and pd.notna(current_audiobook['timestamp']):
        timestamps = parse_timestamps(current_audiobook['timestamp'])
    
    # Generate a unique key for the player
    player_key = f"player_{audiobook['id']}"
    timestamp_dropdown_key = f"timestamp_dropdown_{audiobook['id']}"
    
    audio_container = st.container()
    with audio_container:
        if audiobook['embed_url'] and pd.notna(audiobook['embed_url']):
            # Handle timestamp parameter
            embed_url = audiobook['embed_url']
            timestamp = audiobook.get('timestamp', None)
            total_seconds = 0
            
            # Convert timestamp to seconds if available
            if timestamp:
                total_seconds = time_to_seconds(timestamp)
            
            # For Spotify
            if "spotify.com" in embed_url:
                # Create a list of timestamps for the dropdown
                timestamp_options = []
                for time_str, title in timestamps:
                    seconds = time_to_seconds(time_str)
                    timestamp_options.append((seconds, f"{title} ({time_str})"))
                
                # If timestamps are available, create a dropdown
                if timestamp_options:
                    # Find the index of the currently selected timestamp
                    current_index = 0
                    if timestamp:
                        for i, (sec, _) in enumerate(timestamp_options):
                            if sec == total_seconds:
                                current_index = i
                                break
                    
                    # Create the dropdown
                    selected_option = st.selectbox(
                        "Daftar Isi / Navigasi Bab:",
                        options=timestamp_options,
                        format_func=lambda x: x[1],
                        index=current_index,
                        key=timestamp_dropdown_key
                    )
                    
                    # Update the total_seconds if selection changed
                    if selected_option[0] != total_seconds:
                        total_seconds = selected_option[0]
                        timestamp = selected_option[1].split(' (')[-1].rstrip(')')
                
                # If the embed URL doesn't have a t parameter, add it
                if "?t=" not in embed_url and "&t=" not in embed_url:
                    if "?" in embed_url:
                        embed_url += f"&t={total_seconds}"
                    else:
                        embed_url += f"?t={total_seconds}"
                else:
                    # Replace existing t parameter
                    embed_url = re.sub(r'([?&])t=\d+', f'\\1t={total_seconds}', embed_url)
                
                # Create a unique iframe ID for JavaScript targeting
                iframe_id = f"spotify_iframe_{audiobook['id']}"
                
                # Render the Spotify iframe
                st.markdown(f"""
                <iframe id="{iframe_id}" 
                        src="{embed_url}" 
                        width="100%" 
                        height="152" 
                        frameborder="0" 
                        allowtransparency="true" 
                        allow="encrypted-media"
                        style="border-radius: 10px; margin: 10px 0;">
                </iframe>
                
                <script>
                // Function to navigate to a specific timestamp in Spotify player
                function navigateToSpotifyTimestamp(iframe_id, seconds) {{
                    // Get the iframe element
                    const iframe = document.getElementById(iframe_id);
                    if (!iframe) return;
                    
                    // Get the current src
                    let src = iframe.src;
                    
                    // Update or add the timestamp parameter
                    if (src.includes('t=')) {{
                        src = src.replace(/([?&])t=\\d+/, '$1t=' + seconds);
                    }} else if (src.includes('?')) {{
                        src += '&t=' + seconds;
                    }} else {{
                        src += '?t=' + seconds;
                    }}
                    
                    // Update the iframe src
                    iframe.src = src;
                }}
                
                // Initial navigation to timestamp
                window.addEventListener('load', function() {{
                    setTimeout(function() {{
                        navigateToSpotifyTimestamp('{iframe_id}', {total_seconds});
                    }}, 1000);
                }});
                </script>
                """, unsafe_allow_html=True)
                
                # # Create a button to manually navigate to the timestamp
                # if timestamp:
                #     if st.button(f"Navigasi ke {timestamp}", key=f"nav_btn_{audiobook['id']}"):
                #         # This will trigger a rerun with the updated timestamp
                #         st.session_state.selected_audiobook['timestamp'] = timestamp
                #         st.rerun()
            
            # For SoundCloud
            elif "soundcloud.com" in embed_url:
                # SoundCloud supports timestamp with #t parameter
                timestamp_param = f"&auto_play=true#t={total_seconds}s" if timestamp else ""
                
                # Make sure the URL has the correct format for embedding
                if "api.soundcloud.com/tracks" not in embed_url:
                    # If it's a direct SoundCloud URL, convert it to embed format
                    track_id = embed_url.split('/')[-1]
                    embed_url = f"https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/{track_id}"
                
                # Display the timestamp dropdown if available
                if timestamps:
                    timestamp_options = [(time_to_seconds(time_str), f"{title} ({time_str})") for time_str, title in timestamps]
                    selected_option = st.selectbox(
                        "Daftar Isi / Navigasi Bab:",
                        options=timestamp_options,
                        format_func=lambda x: x[1],
                        key=timestamp_dropdown_key
                    )
                    
                    # Update timestamp if selection changed
                    if selected_option and selected_option[0] != total_seconds:
                        total_seconds = selected_option[0]
                        timestamp_param = f"&auto_play=true#t={total_seconds}s"
                        st.session_state.selected_audiobook['timestamp'] = selected_option[1].split(' (')[-1].rstrip(')')
                        st.rerun()
                
                st.markdown(f"""
                <iframe width="100%" 
                        height="166" 
                        scrolling="no" 
                        frameborder="no" 
                        allow="autoplay"
                        src="{embed_url}{timestamp_param}"
                        style="border-radius: 10px; margin: 10px 0;">
                </iframe>
                """, unsafe_allow_html=True)
            
            # For HTML5 audio (direct MP3 links)
            else:
                # Display the timestamp dropdown if available
                if timestamps:
                    timestamp_options = [(time_to_seconds(time_str), f"{title} ({time_str})") for time_str, title in timestamps]
                    selected_option = st.selectbox(
                        "Daftar Isi / Navigasi Bab:",
                        options=timestamp_options,
                        format_func=lambda x: x[1],
                        key=timestamp_dropdown_key
                    )
                    
                    # Update timestamp if selection changed
                    if selected_option and selected_option[0] != total_seconds:
                        total_seconds = selected_option[0]
                        st.session_state.selected_audiobook['timestamp'] = selected_option[1].split(' (')[-1].rstrip(')')
                        st.rerun()
                
                # Create a unique ID for the audio element
                audio_id = f"audio_{audiobook['id']}"
                
                # Render the audio element with custom HTML and JS for timestamp control
                st.markdown(f"""
                <audio id="{audio_id}" controls style="width: 100%;">
                    <source src="{embed_url}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                
                <script>
                    document.addEventListener("DOMContentLoaded", function() {{
                        var audio = document.getElementById("{audio_id}");
                        if (audio) {{
                            audio.currentTime = {total_seconds};
                            audio.play();
                        }}
                    }});
                </script>
                """, unsafe_allow_html=True)
        else:
            st.warning("Tidak ada tautan audio untuk audiobook ini.")
    
    if st.button("❌ Tutup Audio"):
        st.session_state.selected_audiobook = None
        st.rerun()
    
    st.markdown("---")

# Rest of the code remains the same (filters, pagination, display grid)
with st.spinner('Memuat data audiobook...'):
    audiobooks_df = get_audiobooks()

if audiobooks_df.empty:
    st.error("""
    Data audiobook tidak ditemukan. Pastikan:
    1. File Excel memiliki sheet bernama 'audiobooks'
    2. Struktur kolom sesuai contoh
    3. Data tidak kosong
    """)
    st.stop()

# Process data
try:
    # Apply search filter first
    if search_query:
        audiobooks_df = search_audiobooks(audiobooks_df, search_query)
    
    # Convert year to integer with proper NaN handling
    if 'year' in audiobooks_df.columns:
        # First convert to numeric, coerce errors to NaN
        audiobooks_df['year'] = pd.to_numeric(audiobooks_df['year'], errors='coerce')
        # Fill NaN values with 0
        audiobooks_df['year'] = audiobooks_df['year'].fillna(0)
        # Convert to integer
        audiobooks_df['year'] = audiobooks_df['year'].astype(int)
    
    # Add index as audiobook_id if not present
    if 'id' not in audiobooks_df.columns:
        audiobooks_df['id'] = audiobooks_df.index
    
    # Sidebar filters
    st.sidebar.header("Filter Audiobook")

    # Language Filter
    if 'language' in audiobooks_df.columns:
        all_languages = set()
        for languages in audiobooks_df['language'].str.split(','):
            if isinstance(languages, list):
                all_languages.update([c.strip() for c in languages if c.strip()])
        selected_languages = st.sidebar.multiselect(
            "Bahasa",
            options=sorted(all_languages),
            default=[]
        )
        if selected_languages:
            audiobooks_df = audiobooks_df[audiobooks_df['language'].apply(
                lambda x: any(language in str(x) for language in selected_languages) if pd.notna(x) else False
            )]

    # Genre filter
    if 'genres' in audiobooks_df.columns:
        all_genres = set()
        for genres in audiobooks_df['genres'].str.split(','):
            if isinstance(genres, list):
                all_genres.update([g.strip() for g in genres])
        selected_genres = st.sidebar.multiselect(
            "Genre",
            options=sorted(all_genres),
            default=[]
        )
        if selected_genres:
            audiobooks_df = audiobooks_df[audiobooks_df['genres'].apply(
                lambda x: any(genre in str(x) for genre in selected_genres) if pd.notna(x) else False
            )]

    # Authors filter
    if 'author' in audiobooks_df.columns:
        all_authors = set()
        for authors in audiobooks_df['author'].str.split(','):
            if isinstance(authors, list):
                all_authors.update([d.strip() for d in authors])
        selected_authors = st.sidebar.multiselect(
            "Penulis",
            options=sorted(all_authors),
            default=[]
        )
        if selected_authors:
            audiobooks_df = audiobooks_df[audiobooks_df['author'].apply(
                lambda x: any(author in str(x) for author in selected_authors) if pd.notna(x) else False
            )]

    # Narrator filter
    if 'narrator' in audiobooks_df.columns:
        all_narrators = set()
        for narrators in audiobooks_df['narrator'].str.split(','):
            if isinstance(narrators, list):
                all_narrators.update([a.strip() for a in narrators])
        selected_narrators = st.sidebar.multiselect(
            "Narator",
            options=sorted(all_narrators),
            default=[]
        )
        if selected_narrators:
            audiobooks_df = audiobooks_df[audiobooks_df['narrator'].apply(
                lambda x: any(narrator in str(x) for narrator in selected_narrators) if pd.notna(x) else False
            )]
    
    # Year filter with NaN handling
    if 'year' in audiobooks_df.columns:
        valid_years = audiobooks_df[audiobooks_df['year'] != 0]['year']
        
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

            audiobooks_df = audiobooks_df[
                (audiobooks_df['year'] == 0) | 
                ((audiobooks_df['year'] >= year_range[0]) & 
                (audiobooks_df['year'] <= year_range[1]))
            ]
        else:
            st.sidebar.warning("Tidak ada data tahun yang valid untuk difilter")
    
    # Rating filter
    if 'goodreads_rating' in audiobooks_df.columns:
        min_rating = float(audiobooks_df['goodreads_rating'].min())
        max_rating = float(audiobooks_df['goodreads_rating'].max())
        
        if min_rating == max_rating:
            if min_rating > 0:
                min_rating = max(0.0, min_rating - 0.5)
                max_rating = min(5.0, max_rating + 0.5)
            else:
                min_rating = 0.0
                max_rating = 1.0
        
        rating_range = st.sidebar.slider(
            "Rentang Rating",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            step=0.1
        )
        audiobooks_df = audiobooks_df[
            (audiobooks_df['goodreads_rating'] >= rating_range[0]) & 
            (audiobooks_df['goodreads_rating'] <= rating_range[1])
        ]

    # Check if no audiobooks match filters
    if len(audiobooks_df) == 0:
        st.warning("Tidak ada audiobook yang sesuai dengan kriteria filter")
        st.stop()
    
    # Pagination
    items_per_page = st.session_state.get('items_per_page', 10)
    total_pages = max(1, math.ceil(len(audiobooks_df) / items_per_page))
    
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
    audiobook_grid = st.container()
    pagination_bottom = st.container()
    
    # Improved CSS for consistent card layout and clickable titles
    st.markdown("""
    <style>
        /* Card Container */
        .audiobook-card {
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
        
        /* Cover Container */
        .cover-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 250px;
            margin-bottom: 10px;
            overflow: hidden;
            cursor: pointer;
        }
        
        /* Audiobook Cover */
        .audiobook-cover {
            max-height: 250px;
            max-width: 100%;
            object-fit: contain;
        }
        
        /* Improved Audiobook Title with clickable styling */
        .audiobook-title {
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
        
        .audiobook-title-link {
            color: #1E88E5;
            text-decoration: none;
            cursor: pointer;
        }
        
        .audiobook-title-link:hover {
            text-decoration: underline;
            color: #0D47A1;
        }
        
        /* Play button overlay on cover */
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
        
        .cover-container:hover .play-overlay {
            opacity: 1;
        }
        
        /* Audiobook Details */
        .audiobook-details {
            margin-top: 5px;
            font-size: 14px;
            flex-grow: 1;
        }
        
        /* Rating and Language */
        .audiobook-rating {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #ff9d00;
            font-weight: bold;
        }
        
        .language-flag {
            margin-left: 10px;
            color: black;
        }
        
        /* Detail text with scroll */
        .detail-text {
            max-height: 150px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        /* Audio player container */
        .audio-player {
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Timestamp navigation dropdown styling */
        .timestamp-dropdown {
            margin-bottom: 15px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Top pagination with items per page selector
    with pagination_top:
        col1, col2, col3 = st.columns([0.4, 0.3, 0.3])
        with col1:
            st.write(f"Menampilkan {len(audiobooks_df)} audiobook")
        with col2:
            items_options = [10, 15, 20, 25]
            selected_items = st.selectbox(
                "Audiobook per halaman",
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
    
    # Calculate indices for the audiobooks to display
    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(audiobooks_df))
    paged_audiobooks = audiobooks_df.iloc[start_idx:end_idx]
    
    # Display audiobook grid with improved layout and clickable titles
    with audiobook_grid:
        # Create rows with 5 columns each
        cols_per_row = 5
        rows = math.ceil(len(paged_audiobooks) / cols_per_row)
        
        # Dictionary mapping language names to flag emojis
        language_to_flag = {
            'English': '🇬🇧', 'Inggris': '🇬🇧',
            'Indonesian': '🇮🇩', 'Indonesia': '🇮🇩',
            'French': '🇫🇷', 'Prancis': '🇫🇷',
            'Japanese': '🇯🇵', 'Jepang': '🇯🇵',
            'German': '🇩🇪', 'Jerman': '🇩🇪',
            'Spanish': '🇪🇸', 'Spanyol': '🇪🇸',
            'Chinese': '🇨🇳', 'Mandarin': '🇨🇳',
            'Korean': '🇰🇷', 'Korea': '🇰🇷',
            'Russian': '🇷🇺', 'Rusia': '🇷🇺',
            'Arabic': '🇸🇦', 'Arab': '🇸🇦',
            # Add more languages as needed
        }
        
        for row in range(rows):
            cols = st.columns(cols_per_row)
            
            for col in range(cols_per_row):
                idx = row * cols_per_row + col
                if idx < len(paged_audiobooks):
                    audiobook = paged_audiobooks.iloc[idx]
                    with cols[col]:
                        # Get audiobook data with fallbacks
                        audiobook_id = audiobook.get('id', idx)
                        title = audiobook.get('title', 'Judul tidak tersedia')
                        year = audiobook.get('year', 0)
                        year_display = year if year != 0 else 'Tidak tersedia'
                        cover_url = audiobook.get('cover', '')
                        rating = audiobook.get('goodreads_rating', 'N/A')
                        description = audiobook.get('description', 'Deskripsi tidak tersedia')
                        author = audiobook.get('author', 'Tidak tersedia')
                        narrator = audiobook.get('narrator', 'Tidak tersedia')
                        genres = audiobook.get('genres', 'Tidak tersedia')
                        language = audiobook.get('language', 'Tidak tersedia')
                        embed_url = audiobook.get('embed_url', '')
                        duration = audiobook.get('duration', 'Tidak tersedia')
                        
                        # Check if embed URL is available
                        has_audio = pd.notna(embed_url) and embed_url != ''
                        
                        # Process language flag
                        language_flag = ''
                        if language != 'Tidak tersedia':
                            languages = [c.strip() for c in str(language).split(',')]
                            for c in languages:
                                if c in language_to_flag:
                                    language_flag += language_to_flag[c] + ' '
                        
                        html = f"""
                        <div class="audiobook-card">
                            <div class="cover-container">
                                {'<img src="' + str(cover_url) + '" class="audiobook-cover" alt="' + title + '" title="' + title + '">' if pd.notna(cover_url) and str(cover_url).startswith('http') else '<div style="text-align: center; color: #888;">Cover tidak tersedia</div>'}
                            </div>
                            <div class="audiobook-title" title="{title} ({year_display})">{title} ({year_display})</div>
                            <div class="audiobook-details">
                                <div class="audiobook-rating">
                                    <span>⭐ {rating}/5</span>
                                    <span class="language-flag">{language_flag}</span>
                                </div>
                                <div><strong>Durasi:</strong> {duration}</div>
                                <div><strong>Genre:</strong> {genres}</div>
                                <div><strong>Penulis:</strong> {author}</div>
                                <div><strong>Narator:</strong> {narrator}</div>
                            </div>
                        </div>
                        """
                        st.markdown(html, unsafe_allow_html=True)
                        
                        # Hidden button to handle the click event
                        if has_audio:
                            if st.button("▶️ Dengarkan", key=f"play_btn_{audiobook_id}", use_container_width=True):
                                play_audio(audiobook_id, embed_url, title)
                                st.rerun()
                        
                        # Detail expander with scrollable content
                        with st.expander("Deskripsi"):
                            st.markdown(f'<div class="detail-text">{description}</div>', unsafe_allow_html=True)
    
    # Bottom pagination
    with pagination_bottom:
        total_items = len(audiobooks_df)
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
                    (Menampilkan {showing_start}-{showing_end} dari {total_items} audiobook)
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

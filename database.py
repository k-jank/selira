import pandas as pd
import streamlit as st
import os
from pathlib import Path

def load_excel_data():
    try:
        # Cari file Excel di beberapa lokasi
        excel_path = Path(__file__).parent / "data_hiburan.xlsx"
        if not excel_path.exists():
            excel_path = Path.cwd() / "data_hiburan.xlsx"
        
        if not excel_path.exists():
            st.error(f"File tidak ditemukan di: {excel_path}")
            return pd.DataFrame(), pd.DataFrame()

        # Baca file Excel
        excel_data = pd.ExcelFile(excel_path)
        
        # Baca data film - coba beberapa kemungkinan nama sheet
        sheet_names = ['films', 'Films', 'film', 'Film', 'Sheet1']
        films_df = pd.DataFrame()
        
        for sheet in sheet_names:
            if sheet in excel_data.sheet_names:
                films_df = pd.read_excel(excel_data, sheet)
                # Hapus kolom 'error' jika ada
                if 'error' in films_df.columns:
                    films_df = films_df.drop(columns=['error'])
                break
                
        # Baca data audiobook (jika ada)
        audiobooks_df = pd.DataFrame()
        if 'audiobooks' in excel_data.sheet_names:
            audiobooks_df = pd.read_excel(excel_data, 'audiobooks')
        
        return films_df, audiobooks_df
        
    except Exception as e:
        st.error(f"Error membaca Excel: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def get_films():
    films_df, _ = load_excel_data()    
    return films_df

def get_audiobooks():
    _, audiobooks_df = load_excel_data()
    return audiobooks_df


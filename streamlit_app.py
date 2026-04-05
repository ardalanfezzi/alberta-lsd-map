
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import io

# Set Page Config for Mobile
st.set_page_config(page_title="Alberta LSD Mobile", layout="centered")

st.title("📍 Alberta LSD Map")
st.caption("Developed by Ardalan Fezzi")


@st.cache_resource
def load_data_from_drive():
    # Your Google Drive File ID
    file_id = '1YdMDllcconMl6Bzk835gfiAIRTefJD1T'

    # This specific URL format bypasses the "Large File Virus Scan" warning
    session = requests.Session()
    download_url = "https://docs.google.com/uc?export=download"
    response = session.get(download_url, params={'id': file_id}, stream=True)

    # Look for a confirmation token in the cookies if Google asks "Are you sure?"
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(download_url, params=params, stream=True)

    if response.status_code == 200:
        # Load the Parquet data directly from the download stream
        gdf = gpd.read_parquet(io.BytesIO(response.content))
        if gdf.crs is None:
            gdf.set_crs(epsg=4269, inplace=True)
        return gdf
    else:
        st.error(f"Could not connect to Google Drive. Status: {response.status_code}")
        return None

if 'gdf' not in st.session_state:
    with st.spinner("Streaming Alberta Survey Grid..."):
        st.session_state.gdf = load_data_from_drive()

# --- MOBILE UI ---
col1, col2 = st.columns(2)
with col1:
    ls = st.number_input("LSD", 1, 16, 8)
    sec = st.number_input("SEC", 1, 36, 21)
    twp = st.number_input("TWP", 1, 126, 80)
with col2:
    rge = st.number_input("RGE", 1, 30, 19)
    mer = st.selectbox("MER", [4, 5, 6], index=1)

if st.button("Locate LSD", use_container_width=True):
    gdf = st.session_state.gdf
    if gdf is not None:
        # Filter for the specific LSD
        match = gdf[(gdf['M']==mer) & (gdf['RGE']==rge) & (gdf['TWP']==twp) & (gdf['SEC']==sec) & (gdf['LS']==ls)]
        
        if not match.empty:
            # Get center point and convert to Web GPS coordinates
            center = match.to_crs(epsg=3400).geometry.centroid.to_crs(epsg=4326).iloc[0]
            
            # Create the Map
            m = folium.Map(location=[center.y, center.x], zoom_start=14)
            folium.Marker([center.y, center.x], popup=f"{ls}-{sec}-{twp}-{rge}-W{mer}").add_to(m)
            
            st_folium(m, width=700, height=450)
            st.success(f"Coordinates: {center.y:.6f}, {center.x:.6f}")
        else:
            st.error("LSD not found in database.")
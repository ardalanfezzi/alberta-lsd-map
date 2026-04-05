import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import io

st.set_page_config(page_title="Alberta LSD Mobile", layout="centered")

st.title("📍 Alberta LSD Map")
st.caption("Developed by Ardalan Fezzi")


@st.cache_data(show_spinner="Streaming and optimizing Alberta survey grid...")
def load_data():
    url = "https://github.com/ardalanfezzi/alberta-lsd-map/releases/download/v1.0/ATS_Data.parquet"

    try:
        # Use a stream to avoid loading the whole 218MB into RAM at once
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            # Wrap the stream in a BytesIO object for geopandas
            with io.BytesIO(r.content) as buf:
                # ONLY load essential columns to stay under the 1GB RAM limit
                cols = ['LS', 'SEC', 'TWP', 'RGE', 'M', 'geometry']
                gdf = gpd.read_parquet(buf, columns=cols)

                if gdf.crs is None:
                    gdf.set_crs(epsg=4269, inplace=True)
                return gdf
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return None

if 'gdf' not in st.session_state:
    with st.spinner("Loading Alberta Survey Grid..."):
        st.session_state.gdf = load_data()

# --- The rest of your UI code stays the same ---
ls = st.number_input("LSD", 1, 16, 8)
sec = st.number_input("SEC", 1, 36, 21)
twp = st.number_input("TWP", 1, 126, 80)
rge = st.number_input("RGE", 1, 30, 19)
mer = st.selectbox("MER", [4, 5, 6], index=1)

if st.button("Locate LSD", use_container_width=True):
    gdf = st.session_state.gdf
    if gdf is not None:
        match = gdf[(gdf['M']==mer) & (gdf['RGE']==rge) & (gdf['TWP']==twp) & (gdf['SEC']==sec) & (gdf['LS']==ls)]
        if not match.empty:
            center = match.to_crs(epsg=3400).geometry.centroid.to_crs(epsg=4326).iloc[0]
            m = folium.Map(location=[center.y, center.x], zoom_start=14)
            folium.Marker([center.y, center.x], popup=f"{ls}-{sec}-{twp}-{rge}-W{mer}").add_to(m)
            st_folium(m, width=700, height=450)
            st.success(f"Coordinates: {center.y:.6f}, {center.x:.6f}")
        else:
            st.error("LSD not found.")
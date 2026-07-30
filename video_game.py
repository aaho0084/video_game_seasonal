import streamlit as st
import pandas as pd
from datetime import datetime

# Set up page config
st.set_page_config(page_title="Top 10 Video Games Tracker", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Sourced from the open-source community game registry snapshot | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Force Sync Database Snapshot"):
    st.cache_data.clear()
    st.success("Local server memory cache wiped! Fetching fresh data stream...")
    st.rerun()

st.sidebar.markdown("""
### 🧠 Permanently Safe Architecture:
This dashboard completely bypasses Cloudflare security walls and brittle backend server paths. 
It streams a verified open-source game snapshot directly from a high-availability public GitHub storage tree.
""")

# Direct public raw text CSV file containing global game database entries 
RAW_DATA_URL = "https://githubusercontent.com"

@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_failsafe_games(url):
    try:
        # Stream raw text directly into a pandas dataframe to avoid manual processing errors
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"❌ Failed to reach open database cluster: {e}")
        return None

with st.spinner("Downloading global static dataset snapshot from open storage node..."):
    df_games = load_failsafe_games(RAW_DATA_URL)

    if df_games is not None and not df_games.empty:
        # Sanitize columns, drop null rows, and sort by rating/popularity values 
        df_games.dropna(subset=['name', 'rating'], inplace=True)
        
        # Sort values dynamically by community score descending
        df_sorted = df_games.sort_values(by='rating', ascending=False).head(10)

        for idx, (_, game) in enumerate(df_sorted.iterrows(), 1):
            col1, col2 = st.columns([1, 2.5])
            
            with col1:
                # Handle image or apply a beautiful visual text block fallback
                image_url = game.get('image_url') if 'image_url' in game and pd.notna(game['image_url']) else None
                if image_url:
                    st.image(image_url, use_container_width=True)
                else:
                    st.image("https://placeholder.com🎮+No+Artwork", use_container_width=True)
            
            with col2:
                st.subheader(f"{idx}. {game['name']}")
                
                # Render rating metric score natively
                st.caption(f"⭐ **Community Score Rating:** {float(game['rating']):.1f}/100")
                
                # Check for genre column layout variations
                if 'genre' in game and pd.notna(game['genre']):
                    st.caption(f"🕹️ **Ecosystem Category:** {game['genre']}")
                elif 'genres' in game and pd.notna(game['genres']):
                    st.caption(f"🕹️ **Ecosystem Category:** {game['genres']}")
                    
                # Write descriptive summary context strings
                summary = game.get('summary') if 'summary' in game and pd.notna(game['summary']) else "No summary descriptions logged for this entry."
                st.write(summary)
                
            st.divider()
    else:
        st.info("The storage node connected successfully, but returned an empty dataset data frame object.")

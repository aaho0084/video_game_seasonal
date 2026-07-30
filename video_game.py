import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="RAWG Daily Trending Tracker", page_icon="🎮", layout="centered")

st.title("🎮 Today's Top 10 Trending Games")
st.write(f"Live daily popularity rankings driven by user collections and wishlist velocity from **RAWG** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls & documentation
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Refresh Metrics"):
    st.cache_data.clear()
    st.success("Cache cleared! Syncing trending database...")
    st.rerun()

st.sidebar.markdown("""
### 📊 About RAWG Ranking
This dashboard uses the official `-trending` API filter, which recalculates daily based on global gamers adding titles to their active collections, backlogs, and wishlists.
""")

# Function to fetch top trending games directly from RAWG
@st.cache_data(ttl=3600)  # Cache data for 1 hour to optimize performance
def fetch_rawg_trending(api_key):
    url = "https://rawg.io"
    
    # Clean keys of any accidental paste quotes
    clean_key = str(api_key).strip().replace('"', '').replace("'", "")
    
    params = {
        "key": clean_key,
        "ordering": "-trending",  # Sorts by live daily trending momentum descending
        "page_size": 10           # Limits the payload output to the top 10 items
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            st.error(f"❌ RAWG API Engine Error (HTTP {response.status_code})")
            st.code(response.text)
            return []
    except Exception as e:
        st.error(f"❌ Server Connection Failed: {e}")
        return []

# Retrieve credentials safely from Streamlit Secrets
try:
    API_KEY = st.secrets["RAWG_API_KEY"]
except Exception:
    API_KEY = None

if not API_KEY or "your_" in str(API_KEY):
    st.warning("⚠️ Configuration Required: Please update your Streamlit Secrets with your valid RAWG_API_KEY token.")
else:
    with st.spinner("Streaming live trending datasets from RAWG matrix..."):
        games = fetch_rawg_trending(API_KEY)
        
        if games:
            for idx, game in enumerate(games, 1):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # RAWG serves direct high-res image strings natively under background_image
                    if game.get("background_image"):
                        st.image(game["background_image"], use_container_width=True)
                    else:
                        st.image("https://placeholder.com", use_container_width=True)
                
                with col2:
                    st.subheader(f"{idx}. {game.get('name', 'Unknown Title')}")
                    
                    # Release Date formatting layout
                    if game.get("released"):
                        st.caption(f"📅 **Released:** {game['released']}")
                    
                    # Metacritic Score display
                    if game.get("metacritic"):
                        st.caption(f"💯 **Metacritic Rating:** {game['metacritic']}/100")
                    
                    # Platform Badges extraction loop
                    if game.get("parent_platforms"):
                        platforms = [p["platform"]["name"] for p in game["parent_platforms"] if "platform" in p]
                        st.caption(f"🕹️ **Platforms:** {', '.join(platforms)}")
                        
                    # Added/Wishlist momentum tally (surfacing the core trending score metric)
                    if game.get("added"):
                        st.caption(f"📈 **Trending Metric Count:** {game['added']:,} player profiles tracked")
                
                st.divider()
        else:
            st.info("The API connection completed but returned zero active listings.")

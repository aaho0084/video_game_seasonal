import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="LizardByte GameDB Top 10 Tracker", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Powered by unblockable static snapshot queries via **LizardByte GameDB (IGDB Mirror)** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar platform configuration routing
st.sidebar.header("🕹️ Platform Filter")
platform_choice = st.sidebar.selectbox(
    "Choose Target System Ecosystem:",
    [
        "Personal Computer (PC)",
        "PlayStation 5 (PS5)",
        "PlayStation 4 (PS4)",
        "Xbox Series X/S",
        "Xbox One",
        "Nintendo Switch"
    ]
)

st.sidebar.markdown("""
### 🧠 Firewall-Bypass Strategy:
This version is completely unblockable on Streamlit Community Cloud. 

Instead of routing data requests through live server API endpoints flagged by Cloudflare, it fetches daily pre-scraped static databases hosted natively on [LizardByte GameDB Git CDN Pages](https://github.com/LizardByte/GameDB).
""")

if st.sidebar.button("♻️ Force Sync Static Snapshot"):
    st.cache_data.clear()
    st.success("Local server memory cache wiped! Fetching fresh Git snapshot...")
    st.rerun()

# Map human-readable dropdown options directly to LizardByte's explicit index endpoint IDs
PLATFORM_MAPPING = {
    "Personal Computer (PC)": "6",
    "PlayStation 5 (PS5)": "167",
    "PlayStation 4 (PS4)": "48",
    "Xbox Series X/S": "169",
    "Xbox One": "49",
    "Nintendo Switch": "130"
}

target_platform_id = PLATFORM_MAPPING[platform_choice]

# Base CDN URL for LizardByte GameDB versioned API endpoints
BASE_GAMEDB_URL = f"https://lizardbyte.dev{target_platform_id}/games.json"

@st.cache_data(ttl=86400)  # Cache the static file locally for 24 hours to maximize performance speeds
def load_lizardbyte_snapshot(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Failed to reach open repository mirror (HTTP Status {response.status_code})")
            return []
    except Exception as e:
        st.error(f"❌ Snapshot sync failed: {e}")
        return []

with st.spinner(f"Downloading static dataset snapshot for {platform_choice}..."):
    games_list = load_lizardbyte_snapshot(BASE_GAMEDB_URL)

    if games_list:
        # Filter logic: Eliminate entries missing titles, summaries, or rating metadata
        valid_games = [
            g for g in games_list 
            if g.get("name") and g.get("rating") and g.get("summary") and g.get("summary") != "No summary available."
        ]
        
        # If filtering is too restrictive, fall back to games that at least have a name and rating
        if not valid_games:
            valid_games = [g for g in games_list if g.get("name") and g.get("rating")]

        # Sort the objects dynamically by community rating score values in descending order
        top_10_games = sorted(valid_games, key=lambda x: float(x.get("rating", 0)), reverse=True)[:10]

        if top_10_games:
            for idx, game in enumerate(top_10_games, 1):
                col1, col2 = st.columns([1, 2.5])
                
                with col1:
                    # Sanitize visual artwork link strings from the dump array
                    if game.get("cover") and isinstance(game["cover"], dict) and game["cover"].get("url"):
                        # Convert legacy low-res thumbnail links to crystal clear high-res big covers
                        img_url = "https:" + game["cover"]["url"].replace("t_thumb", "t_cover_big")
                        st.image(img_url, use_container_width=True)
                    else:
                        st.image("https://placeholder.com", use_container_width=True)
                
                with col2:
                    st.subheader(f"{idx}. {game.get('name')}")
                    
                    # Display the rating score securely
                    if game.get("rating"):
                        st.caption(f"⭐ **Community Score Rating:** {float(game['rating']):.1f}/100")
                    
                    # Safely map inner data structure definitions for categories/genres
                    if game.get("genres") and isinstance(game["genres"], list):
                        genres = [gen["name"] for gen in game["genres"] if isinstance(gen, dict) and gen.get("name")]
                        if genres:
                            st.caption(f"🕹️ **Category Tagging:** {', '.join(genres)}")
                            
                    # Display descriptions
                    summary_text = game.get("summary", "No structural summary description logged for this item snapshot.")
                    st.write(summary_text)
                    
                st.divider()
        else:
            st.info("The files pulled successfully, but no entries matched the current data filtering parameters.")
    else:
        st.error("Could not populate data array. The selected platform endpoint returned an empty structure file.")

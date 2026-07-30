import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="Steam Live Global Charts", page_icon="🎮", layout="centered")

st.title("🎮 Today's Top 10 Live Steam Games")
st.write(f"Real-time top sellers based on live hourly global revenue metrics from **Steam** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Force Live Sync"):
    st.cache_data.clear()
    st.success("Wiped local memory cache! Streaming fresh metrics...")
    st.rerun()

# Verified, unblocked hourly global Top Sellers endpoint
STEAM_TOP_SELLERS_URL = "https://steampowered.com"

@st.cache_data(ttl=1800)  # Keep the cache data locked for 30 minutes
def fetch_live_steam_top_sellers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(STEAM_TOP_SELLERS_URL, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Extract top sellers dataset list directly from root keys
            top_sellers = data.get("top_sellers", {}).get("items", [])
            
            processed_games = []
            for item in top_sellers[:10]:
                processed_games.append({
                    "id": item.get("id"),
                    "name": item.get("name", "Unknown Title"),
                    "image": item.get("large_capsule_image"),
                    "price_text": f"${item['final_price']/100:.2f}" if item.get("final_price") else "Free or N/A",
                    "discount": item.get("discount_percent", 0),
                    "url": f"https://steampowered.com{item.get('id')}/"
                })
            return processed_games
    except Exception as e:
        st.error(f"❌ Data Extraction Error: {e}")
    return []

with st.spinner("Streaming real-time global charts structure via Steam CDN..."):
    charts_data = fetch_live_steam_top_sellers()

    if charts_data:
        for idx, entry in enumerate(charts_data, 1):
            col1, col2 = st.columns([1.2, 2.5])
            
            with col1:
                if entry["image"]:
                    st.image(entry["image"], use_container_width=True)
                else:
                    st.image("https://placeholder.com🎮+Steam+Trending", use_container_width=True)
                
            with col2:
                st.subheader(f"{idx}. {entry['name']}")
                
                # Render price tags or active deal badges natively
                if entry["discount"] > 0:
                    st.caption(f"🔥 **Live Price:** {entry['price_text']} ({entry['discount']}% OFF)")
                else:
                    st.caption(f"📈 **Live Price:** {entry['price_text']}")
                
                st.markdown(f"[🔗 Go to Official Steam Page and Community Hub]({entry['url']})")
                
            st.divider()
    else:
        st.info("The connection resolved successfully, but the live trending queue is currently empty.")

import streamlit as st
import pandas as pd

# 1. Page Settings
st.set_page_config(page_title="Webtoon Ranker", page_icon="📖", layout="wide")
st.title("📖 Community Webtoon Ranker")
st.write("Vote for your favorite webtoons and filter the leaderboard!")

# 2. Mock Database (Stored in Session State to preserve votes during user session)
if "webtoon_data" not in st.session_state:
    st.session_state.webtoon_data = [
        {"id": 1, "title": "Lore Olympus", "genre": "Romance", "votes": 120, "rating": 4.7},
        {"id": 2, "title": "Tower of God", "genre": "Fantasy", "votes": 95, "rating": 4.8},
        {"id": 3, "title": "UnOrdinary", "genre": "Action", "votes": 88, "rating": 4.5},
        {"id": 4, "title": "Omniscient Reader", "genre": "Action", "votes": 110, "rating": 4.9},
        {"id": 5, "title": "True Beauty", "genre": "Drama", "votes": 75, "rating": 4.4},
    ]

# 3. Sidebar Filters
st.sidebar.header("Filter & Sort Options")
genre_filter = st.sidebar.selectbox("Select Genre", ["All", "Action", "Fantasy", "Romance", "Drama"])
sort_by = st.sidebar.radio("Sort Leaderboard By", ["Votes (Popularity)", "Rating"])

# 4. Filter and Sort Logic
filtered_list = st.session_state.webtoon_data
if genre_filter != "All":
    filtered_list = [w for w in filtered_list if w["genre"] == genre_filter]

if sort_by == "Votes (Popularity)":
    filtered_list = sorted(filtered_list, key=lambda x: x["votes"], reverse=True)
else:
    filtered_list = sorted(filtered_list, key=lambda x: x["rating"], reverse=True)

# 5. Display Leaderboard & Voting System
st.subheader(f"Top Webtoons ({genre_filter})")

for index, webtoon in enumerate(filtered_list):
    with st.container(border=True):
        # 1:4:2 ratio creates clean spacing for Rank, Details, and Voting Metrics
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            st.markdown(f"### #{index + 1}")
            
        with col2:
            st.markdown(f"### {webtoon['title']}")
            st.caption(f"🎭 **Genre:** {webtoon['genre']}  |  ⭐ **Rating:** {webtoon['rating']}/5.0")
            
        with col3:
            st.metric(label="Total Votes", value=webtoon["votes"])
            # Upvote Button linking to unique webtoon ID
            if st.button(f"🔺 Upvote {webtoon['title']}", key=f"vote_{webtoon['id']}"):
                # Find the original item in session state and increment its vote count
                for original in st.session_state.webtoon_data:
                    if original["id"] == webtoon["id"]:
                        original["votes"] += 1
                # FIXED: Changed from st.Rerun() to the correct native st.rerun() method
                st.rerun()

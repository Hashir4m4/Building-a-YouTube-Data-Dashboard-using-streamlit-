# app.py
import os
import time
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import requests
from googleapiclient.discovery import build
from PIL import Image
from io import BytesIO
import plotly.express as px

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # set in .env

st.set_page_config(page_title="YouTube Data Dashboard", layout="wide")

# -----------------------
# Helper: YouTube API client (Data API v3)
# -----------------------
def get_youtube_client(api_key: str):
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

# -----------------------
# Fetch channel summary (by username or channelId)
# -----------------------
@st.cache_data(ttl=600)
def fetch_channel(youtube, for_username=None, channel_id=None):
    if channel_id:
        req = youtube.channels().list(part="snippet,statistics,brandingSettings", id=channel_id)
    else:
        req = youtube.channels().list(part="snippet,statistics,brandingSettings", forUsername=for_username)
    res = req.execute()
    items = res.get("items", [])
    if not items:
        return None
    c = items[0]
    snippet = c.get("snippet", {})
    stats = c.get("statistics", {})
    branding = c.get("brandingSettings", {}).get("channel", {})
    return {
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "logo": snippet.get("thumbnails", {}).get("default", {}).get("url"),
        "subs": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
        "country": snippet.get("country"),
        "keywords": branding.get("keywords")
    }

# -----------------------
# Fetch videos for channel (most recent, paginated)
# -----------------------
@st.cache_data(ttl=600)
def fetch_videos_for_channel(youtube, channel_id, max_results=50):
    videos = []
    req = youtube.search().list(part="snippet", channelId=channel_id, maxResults=50, order="date", type="video")
    res = req.execute()
    for item in res.get("items", []):
        vid = {
            "videoId": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "publishedAt": item["snippet"]["publishedAt"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        }
        videos.append(vid)
    # optionally page through nextPageToken if you want more than 50 (left as exercise)
    return videos

# -----------------------
# Fetch stats for a list of video ids (batch)
# -----------------------
@st.cache_data(ttl=600)
def fetch_videos_stats(youtube, video_ids):
    df_rows = []
    if not video_ids:
        return pd.DataFrame()
    # chunk into groups of 50
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        req = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(chunk))
        res = req.execute()
        for it in res.get("items", []):
            stats = it.get("statistics", {})
            snippet = it.get("snippet", {})
            df_rows.append({
                "videoId": it["id"],
                "title": snippet.get("title"),
                "publishedAt": snippet.get("publishedAt"),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0,
                "comments": int(stats.get("commentCount", 0)) if stats.get("commentCount") else 0,
                "duration": it.get("contentDetails", {}).get("duration")
            })
    return pd.DataFrame(df_rows)

# -----------------------
# UI: Sidebar controls
# -----------------------
st.sidebar.title("YouTube Dashboard")
mode = st.sidebar.radio("Mode", ["By Channel ID", "By Username"])
input_val = st.sidebar.text_input("Channel ID or Username", value="")
max_videos = st.sidebar.slider("Max videos to fetch (approx)", 10, 50, 25)
refresh = st.sidebar.button("Refresh data")

# -----------------------
# Main
# -----------------------
st.title("YouTube Data Dashboard — Streamlit")
if not YOUTUBE_API_KEY:
    st.error("No YOUTUBE_API_KEY found. Add it to `.env` as YOUTUBE_API_KEY and restart.")
    st.stop()

youtube = get_youtube_client(YOUTUBE_API_KEY)

if input_val:
    with st.spinner("Fetching channel..."):
        if mode == "By Channel ID":
            channel_info = fetch_channel(youtube, channel_id=input_val)
        else:
            channel_info = fetch_channel(youtube, for_username=input_val)
    if not channel_info:
        st.warning("Channel not found. Check ID/username or try OAuth for private channel metrics.")
        st.stop()

    # header
    cols = st.columns([1, 3, 2])
    with cols[0]:
        if channel_info.get("logo"):
            r = requests.get(channel_info["logo"])
            img = Image.open(BytesIO(r.content))
            st.image(img, width=120)
    with cols[1]:
        st.header(channel_info["title"])
        st.write(channel_info.get("description", "")[:300])
        st.write(f"**Subscribers:** {channel_info['subs']:,}  •  **Total views:** {channel_info['views']:,}  •  **Videos:** {channel_info['videos']:,}")
    with cols[2]:
        st.write("Country: ", channel_info.get("country", "—"))
        st.write("Keywords: ", channel_info.get("keywords", "—"))

    # videos
    with st.spinner("Fetching videos..."):
        videos = fetch_videos_for_channel(youtube, channel_id=input_val, max_results=max_videos)
        vid_ids = [v["videoId"] for v in videos][:max_videos]
        stats_df = fetch_videos_stats(youtube, vid_ids)

    if stats_df.empty:
        st.info("No videos found or the videos are private.")
    else:
        # Merge thumbnails/titles with stats (map)
        thumb_map = {v['videoId']: v['thumbnail'] for v in videos}
        stats_df['thumbnail'] = stats_df['videoId'].map(thumb_map)
        stats_df['publishedAt'] = pd.to_datetime(stats_df['publishedAt'])
        stats_df = stats_df.sort_values('views', ascending=False)

        # Top KPIs
        k1, k2, k3 = st.columns(3)
        k1.metric("Top video (views)", stats_df.iloc[0]['title'][:40]+"...", f"{stats_df.iloc[0]['views']:,}")
        k2.metric("Average views", f"{int(stats_df['views'].mean()):,}")
        k3.metric("Total views (sample)", f"{stats_df['views'].sum():,}")

        # Top videos table + thumbnails
        st.subheader("Top videos (sample)")
        def render_row(row):
            thumb = row['thumbnail']
            title = row['title']
            views = row['views']
            return f"**{title}** — {views:,} views  \n"
        for idx, r in stats_df.head(10).iterrows():
            col1, col2 = st.columns([1, 8])
            with col1:
                try:
                    r_img = requests.get(r['thumbnail'], timeout=5)
                    st.image(Image.open(BytesIO(r_img.content)), width=140)
                except:
                    st.write("")
            with col2:
                st.markdown(f"**{r['title']}**")
                st.write(f"Published: {r['publishedAt'].date()}  •  Views: {r['views']:,}  •  Likes: {r['likes']:,}  •  Comments: {r['comments']:,}")
                st.markdown(f"[Watch on YouTube](https://www.youtube.com/watch?v={r['videoId']})")

        # Views timeseries (simple aggregated by published date)
        st.subheader("Views by publish date (sample)")
        agg = stats_df.copy()
        agg['date'] = agg['publishedAt'].dt.date
        daily = agg.groupby('date')['views'].sum().reset_index()
        fig = px.line(daily, x='date', y='views', title='Aggregate views by publish date')
        st.plotly_chart(fig, use_container_width=True)

        # Download CSV
        csv = stats_df.to_csv(index=False)
        st.download_button("Download CSV (videos stats)", csv, file_name="youtube_videos_stats.csv", mime="text/csv")

else:
    st.info("Enter a Channel ID or Username on the left sidebar to get started.")

# Footer quick note
st.markdown("---")
st.caption("Built with Streamlit • Use OAuth for authenticated analytics (watch time, impressions). Watch your API quota.")

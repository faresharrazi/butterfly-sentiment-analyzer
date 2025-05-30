import os
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
import plotly.graph_objects as go
from datetime import datetime
from butterfly_analyzer import analyze_chat

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
if not API_KEY or not SESSION_ID:
    st.error("Please set both API_KEY and SESSION_ID in the .env file.")
    st.stop()

# Auto-refresh the app every 6 seconds
st_autorefresh(interval=6000, key="chat_refresh")

# CSS layout
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
      height: 100vh; margin: 0; overflow: hidden;
    }
    .header {
      width: 100%;
      background-color: #0E1117;
      padding-top: 10px;
      padding-bottom: 10px;
      text-align: center;
      position: relative;
      z-index: 1;
    }
    .chat-container {
      position: absolute;
      top: 10px;
      left: 0; right: 0;
      height: 250px;
      background: white;
      color: black;
      overflow-y: auto;
      padding: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Fetch messages from Livestorm
@st.cache_data(ttl=5)
def fetch_messages():
    url = f"https://api.livestorm.co/v1/sessions/{SESSION_ID}/chat_messages"
    headers = {"accept": "application/vnd.api+json", "Authorization": API_KEY}
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# Gauge rendering
def render_gauge(score):
    val = score * 10
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={'text': "Sentiment Meter", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100], 'tickmode': 'array', 'tickvals': [0, 50, 100], 'ticktext': ['Boring', 'Neutral', 'Exciting']},
            'bar': {'color': 'darkblue', 'thickness': 0.2},
            'steps': [
                {'range': [0, 50], 'color': 'red'},
                {'range': [50, 80], 'color': 'yellow'},
                {'range': [80, 100], 'color': 'green'}
            ],
            'threshold': {'line': {'color': 'black', 'width': 4}, 'thickness': 0.6, 'value': val}
        }
    ))
    fig.update_layout(margin={'t': 60, 'b': 20, 'l': 20, 'r': 20}, height=300, autosize=True)
    st.plotly_chart(fig, use_container_width=True)

# Header UI
st.markdown('<div class="header">', unsafe_allow_html=True)
st.title("🦋 Butterfly Sentiment Analyzer")

# Track sentiment state
if 'processed_scores' not in st.session_state:
    st.session_state.processed_scores = {}

# Fetch chat and always analyze
chat_data = fetch_messages()
overall_score = analyze_chat(chat_data, client=None, processed=st.session_state.processed_scores)
render_gauge(overall_score)

st.markdown('</div>', unsafe_allow_html=True)

# Chat rendering
msgs = list(reversed(chat_data))
msgs_html = ""
for msg in msgs:
    text = msg['attributes'].get('text_content', '')
    ts = msg['attributes'].get('created_at', 0)
    time_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    msgs_html += (
        f"<div style='margin-bottom:10px; position: relative;'>"
        f"<span style='font-size:12px; color:grey; position:absolute; top:0; right:0;'>{time_str}</span>"
        f"<div style='padding-right:70px;'>{text}</div>"
        f"</div>"
    )
chat_html = f'<div class="chat-container">{msgs_html}</div>'
st.markdown(chat_html, unsafe_allow_html=True)

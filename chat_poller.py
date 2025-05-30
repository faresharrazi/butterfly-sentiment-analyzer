import os
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
import plotly.graph_objects as go
from datetime import datetime

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
if not API_KEY or not SESSION_ID:
    st.error("Please set both API_KEY and SESSION_ID in the .env file.")
    st.stop()

# Auto-refresh every 6 seconds
st_autorefresh(interval=6000, key="chat_refresh")

# CSS: fix layout so only chat scrolls
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
      height: 100vh; margin: 0; overflow: hidden;
    }
    /* Header (title + gauge) */
    .header {
      width: 100%;
      background-color: #0E1117;
      padding-top: 10px;
      padding-bottom: 10px;
      text-align: center;
      position: relative;
      z-index: 1;
    }
    /* Chat area below header, scrollable */
    .chat-container {
      position: absolute;
      top: 10px; /* adjust to match header+gauge height */
      left: 0; right: 0;
      height: 250px; /* fixed height */
      background: white;
      color: black;
      overflow-y: auto;
      padding: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Fetch messages
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

# Placeholder sentiment computation
def compute_sentiment(msgs):
    return 0.5

# Render gauge
def render_gauge(score):
    val = score * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        title={'text': "Sentiment Meter", 'font': {'size': 20}},
        gauge={
            'axis': {
                'range': [0,100],
                'tickmode': 'array',
                'tickvals': [0,50,100],
                'ticktext': ['Boring','Neutral','Exciting'],
                'tickfont': {'size':12}
            },
            'bar': {'color': 'darkblue', 'thickness': 0.2},
            'steps': [
                {'range': [0,50], 'color': 'red'},
                {'range': [50,80], 'color': 'yellow'},
                {'range': [80,100], 'color': 'green'}
            ],
            'threshold': {'line': {'color': 'black','width': 4}, 'thickness': 0.6, 'value': val}
        },
        domain={'x': [0.1,0.9], 'y': [0.15,0.85]}
    ))
    fig.update_layout(margin={'t':60,'b':20,'l':20,'r':20}, height=300, autosize=True)
    st.plotly_chart(fig, use_container_width=True)

# Header: title + gauge
st.markdown('<div class="header">', unsafe_allow_html=True)
st.title("🦋 Butterfly Sentiment Analyzer")
messages = fetch_messages()
gauge_score = compute_sentiment(messages)
render_gauge(gauge_score)
st.markdown('</div>', unsafe_allow_html=True)

# Build chat HTML inside the scrollable container with timestamp
msgs = list(reversed(messages))  # newest first
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

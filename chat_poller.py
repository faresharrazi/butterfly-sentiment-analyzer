import os
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
import plotly.graph_objects as go

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
SESSION_ID = os.getenv("SESSION_ID")

if not API_KEY or not SESSION_ID:
    st.error("Please set both API_KEY and SESSION_ID in the .env file.")
    st.stop()

# Streamlit UI title with butterfly icon
st.title("🦋 Butterfly Sentiment Analyzer")

# Auto-refresh the app every 6 seconds
st_autorefresh(interval=6000, key="chat_refresh")

# Function to fetch chat messages
def fetch_messages():
    url = f"https://api.livestorm.co/v1/sessions/{SESSION_ID}/chat_messages"
    headers = {
        "accept": "application/vnd.api+json",
        "Authorization": API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching messages: {e}")
        return []

# Placeholder: compute sentiment score from messages (0.0 to 1.0)
def compute_sentiment(messages):
    # TODO: implement actual sentiment logic
    return 0.5

# Display sentiment meter
def display_sentiment_meter(score):
    value = score * 100
    # Adjust domain and margins to fully show top labels
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': "Sentiment Meter", 'font': {'size': 20}},
        
        gauge={
            'axis': {
                'range': [0, 100],
                'tickmode': 'array',
                'tickvals': [0, 50, 100],
                'ticktext': ['Boring', 'Neutral', 'Exciting'],
                'tickfont': {'size': 12}
            },
            'bar': {'color': 'darkblue', 'thickness': 0.2},
            'steps': [
                {'range': [0, 50], 'color': 'red'},
                {'range': [50, 80], 'color': 'yellow'},
                {'range': [80, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 4},
                'thickness': 0.6,
                'value': value
            }
        },
        # keep gauge centered horizontally and vertically
        domain={'x': [0.1, 0.9], 'y': [0.15, 0.85]}
    ))
    # Increase top margin for title and ticks
    fig.update_layout(
        autosize=True,
        margin={'t': 60, 'b': 20, 'l': 20, 'r': 20},
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

# Main display logic
messages = fetch_messages()
sentiment_score = compute_sentiment(messages)

# Show meter first
display_sentiment_meter(sentiment_score)

# Show plain text chat messages
st.markdown("---")
for msg in messages:
    text = msg.get("attributes", {}).get("text_content", "")
    st.write(text)

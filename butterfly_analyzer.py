import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from mistralai import Mistral

# Load environment variables
def load_config():
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise EnvironmentError("Please set MISTRAL_API_KEY in your .env file.")
    return api_key

# Track processed messages to avoid duplicates
processed_scores = {}  # key = message_id
pending_messages = []  # list of new message dicts
# Timestamp of last API call
t_last_call = 0
CALL_INTERVAL = 5  # Minimum interval between API calls (seconds)

# Fallback scoring based on keywords
def fallback_score(text):
    lower = text.lower()
    if any(word in lower for word in ["boring", "sleep", "tired", "bored"]):
        return 2
    if any(word in lower for word in ["exciting", "fantastic", "great", "yes", "yeah", "cool", "nice", "happy", "wow"]):
        return 9
    return 5

# Batch score multiple messages
def batch_score_messages(messages: list, client) -> dict:
    entries = []
    id_map = {}
    for msg in messages:
        mid = msg['id']
        if mid in processed_scores:
            continue
        author = msg['author_id']
        text = msg['text'].replace('"', '\\"')
        entries.append(f"- {mid}: \"{text}\"")
        id_map[mid] = text

    if not entries:
        return {}

    messages_block = "\n".join(entries)
    prompt_text = f"""
You are a sentiment analyzer assistant.
Analyze each message below and assign a sentiment score from 1 to 10, where:
1 = very boring
5 = neutral
10 = very exciting

Return only a valid JSON object where keys are message IDs and values are the integer scores.

Messages:
{messages_block}
"""
    try:
        resp = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "system", "content": prompt_text}]
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```")
        print("Mistral raw response:\n", content)
        raw_scores = json.loads(content)

        flat_scores = {}
        for mid, value in raw_scores.items():
            if isinstance(value, list) and isinstance(value[0], dict) and 'score' in value[0]:
                flat_scores[mid] = value[0]['score']
            else:
                flat_scores[mid] = value

        result = {}
        for mid, val in flat_scores.items():
            try:
                iv = int(round(float(val)))
            except:
                iv = fallback_score(id_map.get(mid, ""))
            result[mid] = max(1, min(10, iv))
        return result
    except Exception as e:
        print(f"Warning: batch scoring failed: {e}")
        return {msg['id']: fallback_score(msg['text']) for msg in messages if msg['id'] not in processed_scores}

# Main analysis entry point
def analyze_chat(chat_data: list, client=None, processed=None) -> float:
    global processed_scores, pending_messages, t_last_call
    if processed is not None:
        processed_scores = processed

    simplified = []
    for item in chat_data:
        msg_id = item.get('id')
        attrs = item.get('attributes', {})
        author = attrs.get('author_id')
        text = attrs.get('text_content', '')
        if msg_id and author and text:
            simplified.append({'id': msg_id, 'author_id': author, 'text': text})

    new_messages = [msg for msg in simplified if msg['id'] not in processed_scores]
    if not new_messages:
        return sum(processed_scores.values()) / len(processed_scores) if processed_scores else 0.0

    pending_messages.extend(new_messages)

    if client is None:
        try:
            api_key = load_config()
            client = Mistral(api_key=api_key)
        except:
            client = None

    now = time.time()
    if client and pending_messages and (now - t_last_call) >= CALL_INTERVAL:
        new_scores = batch_score_messages(pending_messages, client)
        processed_scores.update(new_scores)
        for msg in pending_messages:
            mid = msg['id']
            score = new_scores.get(mid, '?')
            print(f"{msg['text']} => Score: {score}")
        if new_scores:
            overall = sum(processed_scores.values()) / len(processed_scores)
            print(f"Updated overall sentiment: {overall:.2f}")
        pending_messages.clear()
        t_last_call = now

    return sum(processed_scores.values()) / len(processed_scores) if processed_scores else 0.0

# Standalone test
if __name__ == "__main__":
    print("Butterfly Analyzer updated with accurate message ID mapping and flexible response handling.")

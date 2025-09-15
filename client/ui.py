# ui.py
"""
Streamlit UI for Voice Assistant
"""

import streamlit as st
import requests
import websocket
import threading
import time

st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎤 Voice Assistant")

conversation_id = st.session_state.get("conversation_id", None)
chat_history = st.session_state.get("chat_history", [])

# Audio recording widget (requires streamlit-webrtc or similar for real recording)
st.info("Press the button and speak to record your voice.")
if st.button("Talk"):
    st.warning("Audio recording not implemented in this stub. Upload a .wav file instead.")
    uploaded_file = st.file_uploader("Upload your voice (.wav)", type=["wav"])
    if uploaded_file:
        files = {"file": uploaded_file}
        response = requests.post("http://localhost:8000/api/audio", files=files)
        if response.ok:
            conversation_id = response.json()["conversation_id"]
            st.session_state["conversation_id"] = conversation_id
            st.success(f"Conversation started: {conversation_id}")
        else:
            st.error("Failed to start conversation.")

if conversation_id:
    st.subheader("Chat History")
    history_resp = requests.get(f"http://localhost:8000/api/history/{conversation_id}")
    if history_resp.ok:
        chat_history = history_resp.json()["history"]
        st.session_state["chat_history"] = chat_history
        for item in chat_history:
            st.markdown(f"**You:** {item['user_input']}")
            st.markdown(f"**Assistant:** {item['agent_response']}")
    else:
        st.error("Could not fetch chat history.")

    st.subheader("Live Response (WebSocket)")
    if st.button("Connect to Stream"):
        st.info("WebSocket streaming not implemented in this stub. See README for details.")

# Audio playback (stub)
st.audio(b"", format="audio/wav")

st.caption("Demo UI. For full features, implement audio recording and WebSocket streaming.")

# ui.py
"""
Streamlit UI for Voice Assistant
"""
import asyncio
import json
import queue
from functools import partial

import numpy as np
import sounddevice as sd
import streamlit as st
import websockets

# --- Page Config ---
st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎤 Voice Assistant")

# --- Constants ---
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
WEBSOCKET_URI = "ws://localhost:8000/ws"

# --- Session State Initialization ---
if "app_state" not in st.session_state:
    st.session_state.app_state = "idle"  # idle, recording, processing, error
if "audio_stream" not in st.session_state:
    st.session_state.audio_stream = None
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = None
if "audio_to_process" not in st.session_state:
    st.session_state.audio_to_process = None
if "server_messages" not in st.session_state:
    st.session_state.server_messages = []
if "playback_audio" not in st.session_state:
    st.session_state.playback_audio = None


# --- Audio Handling Functions ---
def audio_callback(indata, frames, time, status, q):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(f"Input stream status: {status}")
    q.put(indata.copy())


async def process_audio_and_interact(audio_data: np.ndarray):
    """Connects to the WebSocket, sends audio, and handles server responses."""
    try:
        async with websockets.connect(WEBSOCKET_URI) as ws:
            await ws.send(audio_data.astype(np.float32).tobytes())
            await ws.send(b"__END__")

            received_audio_chunks = []
            current_messages = []

            async for msg in ws:
                if isinstance(msg, bytes):
                    chunk = np.frombuffer(msg, dtype=np.int16)
                    received_audio_chunks.append(chunk)
                else:
                    try:
                        event = json.loads(msg)
                        msg_type = event.get("type")
                        if msg_type == "text":
                            current_messages.append(f"🤖 Assistant: {event['data']}")
                        elif msg_type == "error":
                            current_messages.append(f" A.I. Error: {event['msg']}")
                        elif msg_type == "end":
                            current_messages.append("✅ Response complete.")
                            break
                    except json.JSONDecodeError:
                        current_messages.append(f"🤖 Raw: {msg}")

            st.session_state.server_messages = current_messages
            if received_audio_chunks:
                st.session_state.playback_audio = np.concatenate(
                    received_audio_chunks
                )
            st.session_state.app_state = "idle"

    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
        st.session_state.app_state = "error"
        st.session_state.server_messages = [
            f"🔌 **Connection Error:** Could not connect to the server at `{WEBSOCKET_URI}`. Please ensure it's running."
        ]
    except Exception as e:
        st.session_state.app_state = "error"
        st.session_state.server_messages = [f"An unexpected error occurred: {e}"]
    finally:
        if "audio_to_process" in st.session_state:
            del st.session_state["audio_to_process"]
        st.rerun()


# --- UI Components and Logic ---

if st.session_state.app_state == "idle":
    st.info("Press 'Start Recording' and speak. Press 'Stop' when you're done.")
    if st.button("Start Recording", type="primary"):
        # Create a queue and store it in session state for the main thread.
        q = queue.Queue()
        st.session_state.audio_queue = q

        # Use functools.partial to pass the queue to the callback function.
        # This avoids accessing st.session_state from the callback thread.
        callback_with_queue = partial(audio_callback, q=q)

        try:
            st.session_state.audio_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=CHUNK_SIZE,
                callback=callback_with_queue,
            )
            st.session_state.audio_stream.start()
            st.session_state.app_state = "recording"
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start recording: {e}")
            st.session_state.app_state = "error"

elif st.session_state.app_state == "recording":
    st.warning("🔴 Recording... Press 'Stop' to process.")
    if st.button("Stop"):
        # Stop the stream and retrieve data
        st.session_state.audio_stream.stop()
        st.session_state.audio_stream.close()
        audio_chunks = []
        while not st.session_state.audio_queue.empty():
            audio_chunks.append(st.session_state.audio_queue.get())

        # Clean up stream resources
        st.session_state.audio_stream = None
        st.session_state.audio_queue = None

        if audio_chunks:
            # Store data and change state to 'processing' for the next run
            st.session_state.audio_to_process = np.concatenate(audio_chunks)
            st.session_state.app_state = "processing"
        else:
            st.warning("No audio was recorded.")
            st.session_state.app_state = "idle"
        st.rerun()

elif st.session_state.app_state == "processing":
    st.info("⏳ Sending audio and waiting for response...")
    audio_data = st.session_state.get("audio_to_process")
    if audio_data is not None:
        # This is a blocking call that handles the entire interaction
        asyncio.run(process_audio_and_interact(audio_data))
    else:
        st.warning("Processing state but no audio data found. Resetting.")
        st.session_state.app_state = "idle"
        st.rerun()

elif st.session_state.app_state == "error":
    if st.button("Try Again"):
        st.session_state.app_state = "idle"
        st.session_state.server_messages = []
        st.session_state.playback_audio = None
        st.rerun()

# --- Display Area for Server Responses ---

# Display server text messages
if st.session_state.server_messages:
    st.markdown("---")
    for msg in st.session_state.server_messages:
        if "Error" in msg:
            st.error(msg)
        else:
            st.markdown(msg)

# Display and play back server audio response
if st.session_state.playback_audio is not None:
    st.audio(st.session_state.playback_audio, sample_rate=SAMPLE_RATE)
    st.session_state.playback_audio = None

st.caption("v4 - Streamlit Voice Client (Thread-Safe)")

# ui.py
"""
Streamlit UI for Voice Assistant
"""
from math import e
import os
import io
import json
import base64
import asyncio
import requests
import websockets
import streamlit as st
import sounddevice as sd
import soundfile as sf
import numpy as np
# from audiorecorder import audiorecorder

st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎤 Voice Assistant")

if "stop_event" not in st.session_state:
    st.session_state.stop_event = None

conversation_id = st.session_state.get("conversation_id", None)
chat_history = st.session_state.get("chat_history", [])

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

async def stream_audio(ws, stop_event):
    queue = asyncio.Queue()
    # loop = asyncio.get_event_loop()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        if not stop_event.is_set():
            # put chunk into async queue (non-blocking)
            queue.put_nowait(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE,
                        channels=1,
                        dtype="float32",
                        blocksize=CHUNK_SIZE,
                        callback=callback):
        async def sender():
            while not stop_event.is_set() or not queue.empty():
                chunk = await queue.get()
                await ws.send(chunk.astype(np.float32).tobytes())

            await ws.send(b"__END__")
        
        # while not stop_event.is_set():
        #     await asyncio.sleep(0.1)
        # run sender until stop_event is set
        await sender()
    # await ws.send("_END_")  # signal end of stream



async def voice_client(file=None):
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        if file:
            st.write("Uploading...!")
            data, samplerate = sf.read(file, dtype="float32")  # numpy array
            chunk_size = int(0.1 * samplerate)  # 100ms chunks
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                await ws.send(chunk.tobytes())  # send raw PCM
                # await asyncio.sleep(0.1)       # pacing, simulating live stream
        else:
            st.write("🔴 Recording... Speak now!")

            # --- 1. Capture mic for 5 sec (example) ---
            # duration = 5
            # samplerate = 16000
            # recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32")
            # sd.wait()

            # Send audio in chunks (simulate streaming)
            # chunk_size = 1024
            # for i in range(0, len(recording), chunk_size):
            #     chunk = recording[i:i+chunk_size].tobytes()
            #     await ws.send(chunk)
            st.write("Recording stopped.")


        # Listen for server messages
        full_audio_chunks = []

        async for msg in ws:
            if isinstance(msg, bytes):
                # handle audio chunk
                chunk = np.frombuffer(msg, dtype=np.int16)
                full_audio_chunks.append(chunk)

                os.write(1, b"Received audio chunk\n")
            else:
                event = json.loads(msg)
                if event["type"] == "text":
                    st.markdown(f"🤖 Assistant: {event['data']}")
                elif event["type"] == "error":
                    st.error(f"Error: {event['msg']}")
                elif event["type"] == "end":
                    st.write("✅ Response complete.")
                    break

        if full_audio_chunks:
            full_pcm = np.concatenate(full_audio_chunks)
            st.audio(full_pcm, sample_rate=24000)
        # audio_buffer = io.BytesIO()
        # async for msg in ws:
        #     st.write("Server:", msg)

        # --- 2. Receive response events ---
        # text_buffer = ""

        # stream_player = sd.OutputStream(samplerate=16000, channels=1)
        # stream_player.start()

        # while True:
        #     try:
        #         message = await asyncio.wait_for(ws.recv(), timeout=5000)

        #         if isinstance(message, bytes):
        #             # handle audio chunk
        #             os.write(1, b"Received audio chunk\n")
        #             audio_buffer.write(message)
        #         else:
        #             event = json.loads(message)
        #             if event["type"] == "text":
        #                 st.markdown(f"🤖 Assistant: {event['data']}")
        #     except asyncio.TimeoutError:
        #         break  # no more messages

        #     event = json.loads(msg)

        #     if event["type"] == "transcript":
        #         st.write(f"📝 User: {event['text']}")

        #     elif event["type"] == "llm":
        #         text_buffer += event["delta"]
        #         st.markdown(f"🤖 Assistant: {text_buffer}")

        #     elif event["type"] == "audio":
        #         chunk = base64.b64decode(event["chunk"])
        #         audio_buffer.write(chunk)
        #         try:
        #             data, samplerate = sf.read(io.BytesIO(chunk), dtype="float32")
        #             if data.ndim > 1:
        #                 data = np.mean(data, axis=1)
        #             stream_player.write(data)
        #         except RuntimeError:
        #             pass

        # stream_player.stop()
        # audio_buffer.seek(0)



st.info("Upload a recored file to get the answer.")
uploaded_file = st.file_uploader("Upload your voice (.wav)", type=["wav"])

if uploaded_file:
    files = {"file": uploaded_file}
    asyncio.run(voice_client(file=uploaded_file))
    # response = requests.post("http://localhost:8000/api/audio", files=files, timeout=20)
    # if response.ok:
    #     conversation_id = response.json()["conversation_id"]
    #     st.session_state["conversation_id"] = conversation_id
    #     st.success(f"Conversation started: {conversation_id}")
    # else:
    #     st.error("Failed to start conversation.")

if conversation_id:
    st.subheader("Chat History")
    history_resp = requests.get(f"http://localhost:8000/api/history/{conversation_id}", timeout=20)
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


st.info("Press the button and speak to record your voice.")
if st.button("Start Recording"):
    asyncio.run(voice_client())


if st.button("Stop Recording"):
    if st.session_state.stop_event and not st.session_state.stop_event.is_set():
        st.session_state.stop_event.set()
# Audio playback (stub)
# st.audio(b"", format="audio/wav")

st.caption("Demo UI. For full features, implement audio recording and WebSocket streaming.")

"""
Handling agent logic and workflow
"""
import io
import random
import asyncio
import numpy as np
from scipy import signal
import soundfile as sf


from agents import Agent, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
    VoicePipelineConfig,
    TTSModelSettings
)


@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    print(f"[debug] get_weather called with city: {city}")
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


vietnamese_agent = Agent(
    name="Vietnamese",
    handoff_description="A vietnamese speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Vietnamese.",
    ),
    model="gpt-4o-mini",
    tools=[get_weather]
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. If the user speaks in Vietnamese, handoff to the vietnamese agent.",
    ),
    model="gpt-4o-mini",
    handoffs=[vietnamese_agent],
    tools=[get_weather],
)


async def run_agent(audio_data:bytes):
    """
    Run agent pipeline in async mode
    """
    tts_config = TTSModelSettings(voice="sage")
    config = VoicePipelineConfig(tracing_disabled=True, tts_settings=tts_config)

    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent), config=config)

    if audio_data is None or audio_data.size == 0:
        buffer = np.zeros(24000 * 3, dtype=np.int16)
        audio_input = AudioInput(buffer=buffer)
    else:
        # Decode wav to numpy array
        # buffer, sample_rate = sf.read(io.BytesIO(audio_data), dtype="float32")
        audio_input = AudioInput(buffer=audio_data, frame_rate=16000)

    result = await pipeline.run(audio_input)

    # Create an audio player using `sounddevice`
    # player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
    # player.start()

    # Play the audio stream as it comes in
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            # print(event.data.dtype)
            audio_24k = event.data
            num_samples_16k = int(len(audio_24k) * 16000 / 24000)
            audio_16k = signal.resample(audio_24k, num_samples_16k)
            pcm_bytes = (audio_16k).astype(np.int16).tobytes()
            
            # Stream in smaller chunks to avoid overwhelming the ESP32 client
            chunk_size = 1024  # Bytes
            for i in range(0, len(pcm_bytes), chunk_size):
                yield pcm_bytes[i:i + chunk_size]
                # Add a small delay to throttle the stream, similar to arduino-audio-tools examples
                await asyncio.sleep(0.01)  # 10ms delay
            # player.write(event.data)


async def dummy_agent(file_path: str, chunk_size: int = 1024):
    """
    A dummy function for testing audio streaming.
    Reads a recorded .wav file and streams 16-bit audio to the websocket client.
    """
    try:
        # Read the WAV file
        data, samplerate = sf.read(file_path, dtype='float32')

        # Ensure mono audio
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Resample to 16kHz if necessary
        target_samplerate = 16000
        if samplerate != target_samplerate:
            num_samples_16k = int(len(data) * target_samplerate / samplerate)
            data = signal.resample(data, num_samples_16k)
            samplerate = target_samplerate

        # Convert to 16-bit PCM
        pcm_data = (data * 32767).astype(np.int16)

        # Stream in chunks
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i + chunk_size]
            yield chunk.tobytes()

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        # Optionally, yield an error message or specific error bytes
        yield b'' 
    except Exception as e:
        print(f"An error occurred in dummy_agent: {e}")
        yield b''

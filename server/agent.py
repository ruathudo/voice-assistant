"""
Handling agent logic and workflow
"""
import io
import random
import numpy as np
import sounddevice as sd
import soundfile as sf

from agents import Agent, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import (
    SingleAgentVoiceWorkflow, 
    VoicePipeline, AudioInput, 
    VoicePipelineConfig, 
    STTModelSettings,
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
    tts_config = TTSModelSettings(voice="sage")
    config = VoicePipelineConfig(tracing_disabled=True, tts_settings=tts_config)

    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent), config=config)
    # buffer = np.zeros(24000 * 3, dtype=np.int16)
    # if not audio_input:
    #     
    #     audio_input = AudioInput(buffer=buffer)
    # Decode wav → numpy array
    buffer, sample_rate = sf.read(io.BytesIO(audio_data), dtype="float32")
    audio_input = AudioInput(buffer=buffer, frame_rate=sample_rate)
    result = await pipeline.run(audio_input)

    # Create an audio player using `sounddevice`
    player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
    player.start()

    # Play the audio stream as it comes in
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            player.write(event.data)

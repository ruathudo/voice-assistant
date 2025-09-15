import os
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "no")
OPENAI_API_URL = "https://api.openai.com/v1"

def speech_to_text(audio_bytes: bytes) -> str:
    """
    Calls OpenAI Whisper API to convert audio to text.
    """
    url = f"{OPENAI_API_URL}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"model": "whisper-1"}
    response = requests.post(url, headers=headers, files=files, data=data, timeout=10)
    if response.status_code == 200:
        return response.json().get("text", "")
    return ""


def generate_text(prompt: str) -> str:
    """
    Calls OpenAI GPT-5 mini API to generate text response.
    """
    url = f"{OPENAI_API_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-5-mini",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        choices = response.json().get("choices", [])
        if choices:
            return choices[0]["message"]["content"]
    return ""


def text_to_speech(text: str) -> bytes:
    """
    Calls OpenAI TTS API to convert text to audio bytes.
    """
    url = f"{OPENAI_API_URL}/audio/speech"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "tts-1",
        "input": text,
        "voice": "alloy"
    }
    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code == 200:
        return response.content
    return b""

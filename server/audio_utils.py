# audio_utils.py
"""
Handles audio file saving and conversion utilities.
"""

import tempfile

def save_audio_file(file) -> str:
    # TODO: Save uploaded audio to disk
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        tmp.write(file.file.read())
        return tmp.name

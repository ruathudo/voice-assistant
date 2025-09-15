# agent.py
"""
Handles conversation logic using PydanticAI and OpenAI GPT-5 mini.
"""


# Example PydanticAI agent using OpenAI for text generation
from .openai_services import generate_text

class VoiceAssistantAgent:
    def __init__(self):
        # You can add PydanticAI config here if needed
        pass

    def process(self, text: str) -> str:
        """
        Uses OpenAI GPT-5 mini to generate agent response.
        """
        # Here you could add PydanticAI agent logic, memory, tools, etc.
        response = generate_text(text)
        return response

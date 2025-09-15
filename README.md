# Voice assistant

### Features

* Send voice command from client and get voice answer back
* Task management
* Clock and weather
* Animation control by emotion detection

### Stack
* FastAPI
* Postgres
* PydanticAI
* VLLM
* WhisperX
* Piper

### Run

Run server:
`uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload`
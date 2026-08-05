"""# CLAUDE.md - Voice Subsystem

## 1. Overview
ORION's Voice Subsystem provides natural language interaction capabilities, allowing users to communicate with the agent using spoken commands and enabling ORION to respond verbally. It integrates Speech-to-Text (STT) for understanding spoken input and Text-to-Speech (TTS) for generating spoken responses.

## 2. Components
- **VoiceEngine (`voice_engine.py`):** Orchestrates the overall voice interaction, managing STT and TTS processes, and handling wake word detection.
- **STTEngine (`stt_engine.py`):** Converts spoken audio into text. Supports local (e.g., faster-whisper) and cloud-based (e.g., Google Speech-to-Text) solutions.
- **TTSEngine (`tts_engine.py`):** Converts text into spoken audio. Supports local (e.g., Kokoro, Piper) and cloud-based (e.g., Google Text-to-Speech) solutions.
- **WakeWordDetector (`wake_word_detector.py`):** Continuously listens for a predefined wake word to activate ORION's listening mode.

## 3. Interfaces (Contracts)
Voice-related data structures are defined in `orion/contracts/voice_contracts.py`.

### 3.1 VoiceEngine Interface
- `async start_listening()`: Activates the microphone and starts listening for input.
- `async stop_listening()`: Deactivates the microphone.
- `async speak(text: str)`: Converts text to speech and plays it.

### 3.2 STTEngine Interface
- `async transcribe_audio(audio_data: bytes) -> STTResult`: Transcribes audio data into text.

### 3.3 TTSEngine Interface
- `async synthesize_speech(text: str) -> bytes`: Synthesizes speech from text and returns audio data.

## 4. Dependencies
- **Internal:** `orion.contracts.voice_contracts`, `orion.core.communication.event_bus`, `orion.intelligence.router.model_router`
- **External:** `pyaudio`, `sounddevice`, `faster_whisper`, `kokoro-tts`, `piper-tts`, `asyncio`.

## 5. Build Order & Verification (Phase 6 - M6.1)
1. Define voice-related Pydantic models in `orion/contracts/voice_contracts.py`.
2. Implement `WakeWordDetector` (initially with a simple keyword spotting, later with more advanced models).
3. Implement `STTEngine` with a local `faster-whisper` integration.
4. Implement `TTSEngine` with a local `piper-tts` integration.
5. Implement `VoiceEngine` to orchestrate STT, TTS, and wake word detection.
6. Create a demo script (`examples/voice_system_demo.py`) to demonstrate wake word detection, speech input, and spoken response.
7. Ensure unit tests for all Voice modules pass.
"""

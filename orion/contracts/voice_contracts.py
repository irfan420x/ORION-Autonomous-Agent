from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class STTResult(BaseModel):
    text: str = Field(..., description="Transcribed text from speech")
    language: Optional[str] = Field(None, description="Detected language of the speech")
    confidence: float = Field(..., description="Confidence score of the transcription")
    duration: float = Field(..., description="Duration of the audio segment transcribed")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to be converted to speech")
    voice_id: Optional[str] = Field(None, description="ID of the voice to use for synthesis")
    speed: float = Field(1.0, description="Speech speed multiplier (1.0 is normal)")
    emotion: Optional[Literal["neutral", "happy", "sad", "angry"]] = Field(None, description="Emotional tone of the speech")

class TTSResult(BaseModel):
    audio_data_base64: str = Field(..., description="Base64 encoded audio data")
    audio_format: str = Field("wav", description="Format of the audio data (e.g., wav, mp3)")
    duration: float = Field(..., description="Duration of the synthesized speech")

class WakeWordDetection(BaseModel):
    wake_word: str = Field(..., description="The detected wake word")
    timestamp: float = Field(..., description="Unix timestamp of detection")
    confidence: float = Field(..., description="Confidence score of the wake word detection")

class VoiceCommand(BaseModel):
    command_text: str = Field(..., description="Transcribed command text")
    intent: Optional[str] = Field(None, description="Detected intent of the command")
    entities: Dict[str, Any] = Field({}, description="Extracted entities from the command")

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="TTS Service")

class TTSRequest(BaseModel):
    text: str
    voice: str = "alena"

class TTSResponse(BaseModel):
    audioUri: str

@app.post("/internal/v1/tts/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    # Мок: возвращаем ссылку на "сгенерированное" аудио
    return TTSResponse(audioUri=f"https://mock-storage/audio/{hash(request.text)}.wav")

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import datetime

app = FastAPI(title="ASR Service")

# --- 1. In-memory брокер сообщений ---
# В реальности здесь был бы Kafka или ZeroMQ, но для лабораторной простая очередь
event_queue = asyncio.Queue()

# --- 2. Единая модель ошибок (RFC 7807) ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": exc.detail,
            "status": exc.status_code,
            "detail": f"Ошибка при распознавании речи"
        },
        media_type="application/problem+json"
    )

class ASRRequest(BaseModel):
    audioUri: str
    useCloud: bool = True

class ASRResponse(BaseModel):
    text: str
    confidence: float

@app.post("/internal/v1/asr/recognize", response_model=ASRResponse)
async def recognize_speech(request: ASRRequest):
    if "user42.wav" in request.audioUri:
        recognized_text = "Открой браузер"
        
        # асинхронное событие 
        event = {
            "eventId": "evt-123",
            "eventType": "speech.recognized",
            "occurredAt": datetime.datetime.now().isoformat(),
            "payload": {"text": recognized_text, "audioUri": request.audioUri}
        }
        await event_queue.put(event)
        print(f"--- [ASYNC] Событие speech.recognized отправлено в очередь ---")
        
        return ASRResponse(text=recognized_text, confidence=0.95)
    else:
        raise HTTPException(status_code=422, detail="Речь не распознана")

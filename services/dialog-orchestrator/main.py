from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from typing import Optional

app = FastAPI(title="Dialog Orchestrator")

# --- 1. Единая модель ошибок (RFC 7807) ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": str(exc.detail),
            "status": exc.status_code,
            "detail": f"Ошибка в оркестраторе при обработке {request.url.path}"
        },
        media_type="application/problem+json"
    )

# Адреса сервисов
ASR_URL = "http://localhost:8001"
NLU_URL = "http://localhost:8002"
SKILL_URL = "http://localhost:8003"
TTS_URL = "http://localhost:8004"

class CommandRequest(BaseModel):
    sessionId: str
    audioUri: Optional[str] = None
    text: Optional[str] = None
    isOnline: bool = True

class CommandResponse(BaseModel):
    transcript: str
    intent: str
    status: str
    responseAudioUri: str

@app.post("/api/v1/assistant/command", response_model=CommandResponse)
async def process_command(request: CommandRequest, idempotency_key: str = Header(...)):
    async with httpx.AsyncClient() as client:
        print(f"\n--- НОВЫЙ ЗАПРОС (ID: {idempotency_key}) ---")
        
        transcript = request.text
        if not transcript and request.audioUri:
            print(f"-> Вызов ASR для файла: {request.audioUri}")
            try:
                asr_res = await client.post(
                    f"{ASR_URL}/internal/v1/asr/recognize", 
                    json={"audioUri": request.audioUri, "useCloud": request.isOnline}
                )
                asr_res.raise_for_status()
                transcript = asr_res.json()["text"]
                print(f"<- ASR ответил: {transcript}")
            except Exception as e:
                print(f"!!! ОШИБКА ASR: {e}")
                raise HTTPException(status_code=422, detail="Речь не распознана")
        elif not transcript:
            raise HTTPException(status_code=400, detail="Нет ни текста, ни аудио")

        print(f"-> Вызов NLU для текста: {transcript}")
        try:
            nlu_res = await client.post(f"{NLU_URL}/internal/v1/nlu/parse", json={"text": transcript})
            nlu_res.raise_for_status()
            nlu_data = nlu_res.json()
            print(f"<- NLU ответил: intent={nlu_data['intent']}")
        except Exception as e:
            print(f"!!! ОШИБКА NLU: {e}")
            raise HTTPException(status_code=500, detail="Ошибка понимания речи")

        print(f"-> Вызов Skill: {nlu_data['intent']}")
        try:
            skill_res = await client.post(
                f"{SKILL_URL}/internal/v1/skills/{nlu_data['intent']}/execute", 
                json={"slots": nlu_data["slots"]}
            )
            skill_res.raise_for_status()
            status = skill_res.json()["status"]
            print(f"<- Skill ответил: {status}")
        except Exception as e:
            print(f"!!! ОШИБКА SKILL: {e}")
            status = "REJECTED"

        print(f"-> Вызов TTS для текста: 'Команда {status}'")
        try:
            tts_res = await client.post(f"{TTS_URL}/internal/v1/tts/synthesize", json={"text": f"Команда {status}"})
            tts_res.raise_for_status()
            tts_data = tts_res.json()
            print(f"<- TTS ответил: {tts_data['audioUri']}")
        except Exception as e:
            print(f"!!! ОШИБКА TTS: {e}")
            raise HTTPException(status_code=500, detail="Ошибка синтеза речи")

        print("--- ЗАПРОС УСПЕШНО ОБРАБОТАН ---\n")
        
        return CommandResponse(
            transcript=transcript,
            intent=nlu_data["intent"],
            status=status,
            responseAudioUri=tts_data["audioUri"]
        )

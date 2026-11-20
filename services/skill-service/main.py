from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import datetime

app = FastAPI(title="Skill Service")

# --- 1. Собственное хранилище (in-memory) ---
db_skills: List[dict] = []

# --- 2. Единая модель ошибок (RFC 7807) ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": exc.detail,
            "status": exc.status_code,
            "detail": f"Ошибка при выполнении запроса к {request.url.path}"
        },
        media_type="application/problem+json"
    )

class SkillRequest(BaseModel):
    slots: Dict[str, Any] = {}

class SkillResponse(BaseModel):
    status: str
    message: str

@app.post("/internal/v1/skills/{skillId}/execute", response_model=SkillResponse)
async def execute_skill(skillId: str, request: SkillRequest):
    # Сохраняем в "базу данных" (in-memory)
    execution_record = {
        "skill": skillId,
        "slots": request.slots,
        "timestamp": datetime.datetime.now().isoformat()
    }
    db_skills.append(execution_record)

    if skillId == "open_browser":
        print(f">>> ОС: Открываю браузер... (Слоты: {request.slots})")
        return SkillResponse(status="EXECUTED", message="Браузер открыт")
    elif skillId == "open_folder":
        folder = request.slots.get('folder_name', 'Неизвестно')
        print(f">>> ОС: Открываю папку {folder}...")
        return SkillResponse(status="EXECUTED", message=f"Папка {folder} открыта")
    else:
        raise HTTPException(status_code=403, detail="Навык не найден или нет прав")

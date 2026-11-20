from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="NLU Service")

class NLURequest(BaseModel):
    text: str

class NLUResponse(BaseModel):
    intent: str
    slots: dict

@app.post("/internal/v1/nlu/parse", response_model=NLUResponse)
async def parse_text(request: NLURequest):
    # Мок: очень простой парсер
    text = request.text.lower()
    if "браузер" in text:
        return NLUResponse(intent="open_browser", slots={})
    elif "папку" in text:
        return NLUResponse(intent="open_folder", slots={"folder_name": "Документы"})
    else:
        return NLUResponse(intent="unknown", slots={})

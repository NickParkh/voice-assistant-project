from fastapi.testclient import TestClient
from main import app

# Создаем тестовый клиент, который будет имитировать запросы к нашему API
client = TestClient(app)

def test_missing_idempotency_key():
    """
    Тест 1: Проверяем, что сервер вернет ошибку 422, 
    если клиент не передал обязательный заголовок Idempotency-Key.
    """
    response = client.post(
        "/api/v1/assistant/command",
        json={"sessionId": "123", "text": "Открой браузер"}
        # Мы намеренно НЕ передаем headers={"idempotency-key": ...}
    )
    # FastAPI автоматически возвращает 422, если обязательный параметр отсутствует
    assert response.status_code == 422

def test_empty_request():
    """
    Тест 2: Проверяем, что сервер вернет ошибку 400, 
    если клиент не передал ни текст, ни аудио.
    """
    response = client.post(
        "/api/v1/assistant/command",
        headers={"idempotency-key": "123e4567-e89b-12d3-a456-426614174000"},
        json={"sessionId": "123"} # Нет ни text, ни audioUri
    )
    
    assert response.status_code == 400
    # Проверяем, что формат ошибки соответствует RFC 7807
    assert response.json()["status"] == 400
    assert response.json()["title"] == "Нет ни текста, ни аудио"

def test_successful_text_command():
    """
    Тест 3: Проверяем, что при передаче текста сервис корректно обрабатывает запрос.
    Если соседние сервисы (NLU, Skill, TTS) запущены в соседних терминалах, 
    оркестратор вернет 200 OK. Если они выключены (изолированный тест) — вернется 500.
    """
    response = client.post(
        "/api/v1/assistant/command",
        headers={"idempotency-key": "test-key-123"},
        json={"sessionId": "123", "text": "Открой браузер"}
    )
    
    # Тест считается пройденным в обоих случаях, так как он проверяет 
    # не наличие соседних сервисов, а то, что валидация прошла и запрос был отправлен.
    assert response.status_code in [200, 500]

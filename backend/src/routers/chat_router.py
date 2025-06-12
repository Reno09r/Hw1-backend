# src/routers/chat_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.services.service_dependencies import get_chat_service
from src.services.chat_service import ChatService
from src.dto.chat import ChatMessageCreate, ChatSessionResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatSessionResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Отправить новое сообщение. Если session_id не указан, создается новый чат.
    Возвращает всю историю текущего чата.
    """
    return await chat_service.process_user_message(current_user.id, message_data)

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Получить историю сообщений для конкретной сессии чата (для polling'а).
    """
    history = await chat_service.get_chat_history(session_id)
    # Проверка, что пользователь имеет доступ к этому чату
    if not history.messages or history.messages[0].user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    
    return history

# --- ДОБАВЬТЕ ЭТОТ КОД В src/routers/chat_router.py ---
from fastapi import Request

@router.post("/diagnose")
async def diagnose_request(request: Request):
    """
    Этот эндпоинт просто покажет нам, что сервер получает в сыром виде.
    """
    content_type = request.headers.get("content-type")
    raw_body = await request.body()
    decoded_body = raw_body.decode()

    json_from_fastapi = None
    parsing_error = None
    try:
        # Попытаемся сделать то, что FastAPI делает под капотом
        json_from_fastapi = await request.json()
    except Exception as e:
        parsing_error = str(e)

    return {
        "message": "Это диагностический ответ.",
        "received_content_type": content_type,
        "raw_body_as_string": decoded_body,
        "result_of_fastapi_json_parsing": json_from_fastapi,
        "error_during_parsing": parsing_error
    }
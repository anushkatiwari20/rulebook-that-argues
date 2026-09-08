from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse
from app.services.pipeline import answer_question

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return answer_question(request.question)

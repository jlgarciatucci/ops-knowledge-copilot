from fastapi import APIRouter, Depends
import asyncpg
from app.api.dependencies import db_dep, user_email_dep
from app.core.errors import AppError
from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix='/feedback', tags=['feedback'])


@router.post('', response_model=FeedbackResponse)
async def create_feedback(
    payload: FeedbackRequest,
    conn: asyncpg.Connection = Depends(db_dep),
    user_email: str = Depends(user_email_dep),
) -> FeedbackResponse:
    exists = await conn.fetchval(
        'SELECT id FROM query_logs WHERE id = $1::uuid AND user_email = $2',
        payload.query_id, user_email,
    )
    if not exists:
        raise AppError('query_id not found for current user', status_code=404)
    row = await conn.fetchrow(
        '''INSERT INTO feedback (query_id, rating, comment)
           VALUES ($1::uuid, $2, $3) RETURNING id''',
        payload.query_id, payload.rating, payload.comment,
    )
    return FeedbackResponse(feedback_id=str(row['id']), status='stored')

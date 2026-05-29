from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str

from pydantic import BaseModel


class UserRequest(BaseModel):
    session_id: str
    description: str


class HumanFeedback(BaseModel):
    session_id: str
    feedback: str
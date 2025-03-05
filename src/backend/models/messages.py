from pydantic import BaseModel
from autogen_core.models import LLMMessage


class UserRequest(BaseModel):
    # all user's session chat history
    context: list[LLMMessage]


class AgentResponse(BaseModel):
    reply_to_topic: str
    context: list[LLMMessage]


class Session(BaseModel):
    pass

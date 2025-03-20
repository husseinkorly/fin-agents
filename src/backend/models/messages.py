from typing import Dict, List, Optional, Any
import uuid
from pydantic import BaseModel, Field
from autogen_core.models import (
    LLMMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    FunctionExecutionResultMessage,
)


class SerializableMessage(BaseModel):
    type: str
    content: Any
    source: Optional[str] = "System"
    role: Optional[str] = "assistant"

    @classmethod
    def from_llm_message(cls, msg: LLMMessage) -> "SerializableMessage":
        msg_type = type(msg).__name__
        content = msg.content if hasattr(msg, "content") else ""
        source = getattr(msg, "source", "System")
        role = "user" if source == "User" else "assistant"
        return cls(type=msg_type, content=content, source=source, role=role)

    def to_llm_message(self) -> LLMMessage:
        if self.type == "UserMessage":
            return UserMessage(content=self.content, source=self.source)
        elif self.type == "AssistantMessage":
            return AssistantMessage(content=self.content, source=self.source)
        elif self.type == "SystemMessage":
            return SystemMessage(content=self.content)
        elif self.type == "FunctionExecutionResultMessage":
            return FunctionExecutionResultMessage(content=self.content)
        else:
            return LLMMessage(content=self.content, source=self.source)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_agent: str
    context: List[SerializableMessage] = []
    max_messages: int
    status: str = "idle"  # Values: "idle", "processing", "complete"

    def add_message(self, message: LLMMessage) -> None:
        serializable_msg = SerializableMessage.from_llm_message(message)
        self.context.append(serializable_msg)
        if len(self.context) > self.max_messages:
            self.context = self.context[-self.max_messages :]

    def get_context_as_llm_messages(self) -> List[LLMMessage]:
        return [msg.to_llm_message() for msg in self.context]


# API models
class UserRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SessionDetailResponse(BaseModel):
    session_id: str
    current_agent: str
    status: str
    messages: List[Dict] = []

from autogen_core import RoutedAgent, message_handler, MessageContext
from context.session_manager import SessionManager
from models.messages import Session
from autogen_core.models import AssistantMessage


class HumanAgent(RoutedAgent):
    def __init__(
        self,
        description,
        agent_topic_type: str,
        user_topic_type: str,
        sessionManager: SessionManager,
    ) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type
        self._session_manager = sessionManager

    @message_handler
    async def handle_message(self, message: Session, ctx: MessageContext) -> None:
        # TODO: Implement a proper user interface for human agent
        message.status = "processing"
        self._session_manager._update_session(message)
        agent_input = input("Human agent: ")
        message.add_message(AssistantMessage(content=agent_input, source=self.id.type))
        message.current_agent = self.id.type
        message.status = "completed"
        self._session_manager._update_session(message)

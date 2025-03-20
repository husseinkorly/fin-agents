from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    message_handler,
)
from models.messages import Session


class UserAgent(RoutedAgent):
    def __init__(self, description: str, agent_topic_type: str) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type

    @message_handler
    async def handle_session_message(
        self, message: Session, ctx: MessageContext
    ) -> None:
        await self.publish_message(
            message,
            topic_id=TopicId(message.current_agent, source=self.id.key),
        )

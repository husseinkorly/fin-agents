from autogen_core import (
    RoutedAgent,
    message_handler,
    MessageContext,
    TopicId,
)

from models.messages import UserRequest, AgentResponse
from autogen_core.models import AssistantMessage


class HumanAgent(RoutedAgent):
    def __init__(
        self, description, agent_topic_type: str, user_topic_type: str
    ) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type

    @message_handler
    async def handle_message(self, message: UserRequest, ctx: MessageContext) -> None:
        # TODO: instead of taking input from the console, take the input from the API endpoint
        agent_input = input("Human agent: ")
        message.context.append(
            AssistantMessage(content=agent_input, source=self.id.type)
        )
        await self.publish_message(
            AgentResponse(
                context=message.context, reply_to_topic=self._agent_topic_type
            ),
            topic_id=TopicId(self._user_topic_type, source=self.id.key),
        )

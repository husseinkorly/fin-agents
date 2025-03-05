from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    message_handler,
)
from models.messages import UserRequest, Session, AgentResponse
from autogen_core.models import UserMessage
from rich.console import Console
from rich.theme import Theme

# Create a console with a theme that defines "user" as green
console = Console(theme=Theme({"user": "green"}))


class UserAgent(RoutedAgent):
    def __init__(self, description: str, agent_topic_type: str) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type

    @message_handler
    async def handle_new_session_message(
        self, message: Session, ctx: MessageContext
    ) -> None:
        # Print the prompt in green and get user input
        console.print("[user]User:[/user]", end=" ")
        user_input = input()
        
        user_message = UserRequest(
            context=[UserMessage(content=user_input, source="User")]
        )
        # since this is the first message, we send it to the orchestrator agent
        await self.publish_message(
            user_message,
            topic_id=TopicId(self._agent_topic_type, source=self.id.key),
        )

    @message_handler
    async def handle_message(self, message: AgentResponse, ctx: MessageContext) -> None:
        # Print the prompt in green and get user input
        console.print("[user]User:[/user]", end=" ")
        user_input = input()
        
        message.context.append(UserMessage(content=user_input, source="User"))
        await self.publish_message(
            UserRequest(context=message.context),
            # response to the agent who sent the message
            topic_id=TopicId(message.reply_to_topic, source=self.id.key),
        )

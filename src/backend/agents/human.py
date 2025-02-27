from autogen_core import (
    RoutedAgent,
    default_subscription,
    message_handler,
    MessageContext,
)

from models.messages import HumanFeedback


@default_subscription
class HumanAgent(RoutedAgent):
    def __init__(self, session_id: str) -> None:
        super().__init__("HumanAgent")
        self.session_id = session_id

    @message_handler
    def handle_message(self, message: HumanFeedback, ctx: MessageContext) -> None:
        """
        handles human feedback
        """
        pass
        # send feedback to the orchestrator agent

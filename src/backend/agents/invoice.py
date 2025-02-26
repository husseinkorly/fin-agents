from autogen_core import (
    RoutedAgent,
    default_subscription,
    message_handler,
    MessageContext,
)


@default_subscription
class InvoiceAgent(RoutedAgent):
    def __init__(self, session_id: str) -> None:
        super().__init__("InvoiceAgent")
        self.session_id = session_id

    @message_handler
    def handle_message(self, message: str, ctx: MessageContext) -> None:
        """
        handles invoice related requests
        """
        pass

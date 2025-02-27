from autogen_core import (
    RoutedAgent,
    default_subscription,
    message_handler,
    MessageContext,
)


@default_subscription
class PurchaseOrderAgent(RoutedAgent):
    def __init__(self, session_id: str) -> None:
        super().__init__("PurchaseOrderAgent")
        self.session_id = session_id

    @message_handler
    def handle_message(self, message: str, ctx: MessageContext) -> None:
        """
        handles purchase order related requests
        """
        # probably don't need to implement this yet - we can just let it use tools
        pass

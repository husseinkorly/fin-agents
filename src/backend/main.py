import asyncio
import uuid
from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
)
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from models.messages import Session
from agents.invoice import InvoiceAgent
from agents.purchase_order import PurchaseOrderAgent
from agents.orchestrator import OrchestratorAgent
from agents.human import HumanAgent
from agents.user import UserAgent
from rich.console import Console
from rich.theme import Theme

# Define topic types for all agents
orchestrator_agent_topic_type = "OrchestratorAgent"
invoice_agent_topic_type = "InvoiceAgent"
po_agent_topic_type = "PurchaseOrderAgent"
human_agent_topic_type = "HumanAgent"
user_topic_type = "User"

console = Console(theme=Theme({"system": "yellow"}))

async def main():
    runtime = SingleThreadedAgentRuntime()

    model_client = AzureOpenAIChatCompletionClient(
        model="gpt-4",
        azure_deployment="gpt-4",
        api_version="2025-01-01-preview",
        api_key="",
        azure_endpoint="",
    )

    # Register the orchestrator agent - using factory functions
    orchestrator_agent_type = await OrchestratorAgent.register(
        runtime,
        type=orchestrator_agent_topic_type,
        factory=lambda: OrchestratorAgent(
            model_client=model_client,
            agent_topic_type=orchestrator_agent_topic_type,
            user_topic_type=user_topic_type,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=orchestrator_agent_topic_type,
            agent_type=orchestrator_agent_type.type,
        )
    )

    # Register the invoice agent
    invoice_agent_type = await InvoiceAgent.register(
        runtime,
        type=invoice_agent_topic_type,
        factory=lambda: InvoiceAgent(
            model_client=model_client,
            user_topic_type=user_topic_type,
            agent_topic_type=invoice_agent_topic_type,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=invoice_agent_topic_type, agent_type=invoice_agent_type.type
        )
    )

    # Register the purchase order agent
    po_agent_type = await PurchaseOrderAgent.register(
        runtime,
        type=po_agent_topic_type,
        factory=lambda: PurchaseOrderAgent(
            model_client=model_client,
            agent_topic_type=po_agent_topic_type,
            user_topic_type=user_topic_type
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(topic_type=po_agent_topic_type, agent_type=po_agent_type.type)
    )

    # Register the human agent
    human_agent_type = await HumanAgent.register(
        runtime,
        type=human_agent_topic_type,
        factory=lambda: HumanAgent(
            description="A human agent that handles complex user inquiries",
            agent_topic_type=human_agent_topic_type,
            user_topic_type=user_topic_type,
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(
            topic_type=human_agent_topic_type, agent_type=human_agent_type.type
        )
    )

    # Register the user agent
    user_agent_type = await UserAgent.register(
        runtime,
        type=user_topic_type,
        factory=lambda: UserAgent(
            description="A user agent that handles user interactions",
            # start with orchestrator agent
            agent_topic_type=orchestrator_agent_topic_type
        ),
    )
    await runtime.add_subscription(
        TypeSubscription(topic_type=user_topic_type, agent_type=user_agent_type.type)
    )

    # Start the runtime
    runtime.start()

    # Create a new session for the user
    session_id = str(uuid.uuid4())
    console.print(f"[system]Starting session with ID: {session_id}[/system]")
    await runtime.publish_message(
        Session(), topic_id=TopicId(user_topic_type, source=session_id)
    )

    # Run until completion
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())

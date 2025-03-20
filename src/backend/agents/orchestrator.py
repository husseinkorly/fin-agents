from typing import Annotated
from autogen_core.models import SystemMessage, ChatCompletionClient
from autogen_core.tools import FunctionTool

from context.session_manager import SessionManager
from .ai import AIAgent


class OrchestratorAgent(AIAgent):
    """Agent that orchestrates workflows and routes users to specialized agents."""

    def __init__(
        self,
        model_client: ChatCompletionClient,
        user_topic_type: str,
        agent_topic_type: str,
        sessionManager: SessionManager,
    ) -> None:
        description = (
            "An orchestrator agent that directs users to the appropriate department"
        )
        # Define the agent's system message
        system_message = SystemMessage(
            content="""You are an Orchestrator agent.
                    Your job is to understand what the user needs and direct them to the appropriate agent:

                    - For invoice-related queries (viewing, creating, managing invoices, billing questions),
                    transfer the user to invoice agent. If purchase order not given, ask the purchase order agent for PO details.
                    
                    - For purchase order queries (creating POs, checking PO status, modifying POs), 
                    transfer the user to purchase order agent.
                    
                    - For complex issues that require human expertise or when the user explicitly 
                    asks to speak to a human, transfer the user to human agent.

                    Ask natural, conversational questions to determine where to route the user. 
                    Be brief but helpful in your responses. Don't make the user feel like they're 
                    talking to a robot.

                    Example questions to determine user needs:
                    - "Are you inquiring about an invoice or a purchase order today?"
                    - "Would you like help with creating a new purchase order or checking an existing one?"

                    Once you understand their needs, transfer them to the appropriate agent.
                    """
        )

        # Define delegation tools
        delegate_tools = [
            transfer_to_invoice_agent_tool,
            transfer_to_po_agent_tool,
            escalate_to_human_tool,
        ]

        # Initialize the base AIAgent with these specifications
        super().__init__(
            description=description,
            system_message=system_message,
            model_client=model_client,
            tools=[],
            delegate_tools=delegate_tools,
            agent_topic_type=agent_topic_type,
            user_topic_type=user_topic_type,
            sessionManager=sessionManager,
        )


# Tools for the Orchestrator Agent to delegate to specialized agents
async def transfer_to_invoice_agent(
    reason: Annotated[str, "Reason for transferring to invoice agent"],
) -> str:
    """Transfer the user to the invoice agent for invoice-related inquiries"""
    return "InvoiceAgent"


async def transfer_to_po_agent(
    reason: Annotated[str, "Reason for transferring to purchase order agent"],
) -> str:
    """Transfer the user to the purchase order agent for PO-related inquiries"""
    return "PurchaseOrderAgent"


async def escalate_to_human(
    reason: Annotated[str, "Reason for escalating to a human"],
) -> str:
    """Escalate the user to a human agent for complex issues"""
    return "HumanAgent"


transfer_to_invoice_agent_tool = FunctionTool(
    transfer_to_invoice_agent,
    description="Transfer the user to the invoice agent for invoice-related inquiries",
)

transfer_to_po_agent_tool = FunctionTool(
    transfer_to_po_agent,
    description="Transfer the user to the purchase order agent for PO-related inquiries",
)

escalate_to_human_tool = FunctionTool(
    escalate_to_human,
    description="Escalate the user to a human agent for complex issues",
)

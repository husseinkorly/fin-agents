from typing import Dict, Any, List, Annotated
from datetime import datetime
from autogen_core.models import SystemMessage, ChatCompletionClient
from autogen_core.tools import FunctionTool
from .ai import AIAgent


class PurchaseOrderAgent(AIAgent):
    """Specialized agent for handling purchase order operations."""

    def __init__(
        self,
        model_client: ChatCompletionClient,
        user_topic_type: str,
        agent_topic_type: str,
    ) -> None:
        description = "An agent that handles purchase order related tasks"
        system_message = SystemMessage(
            content="""You are a Purchase Order agent. You can help users with:
                       - Finding information about their existing purchase orders
                       - Creating new purchase orders
                       - Checking the status of purchase orders (open or closed)
                       - Generating invoices for open purchase orders (by delegating to the invoice agent)

                    Respond concisely but professionally. Always assist users with PO-related queries
                    efficiently. Ask for specific details like PO ID when needed to provide accurate information.

                    When a users wants to create an invoice for an open purchase order, transfer them to the invoice agent
                    and provide the PO ID and its details to the invoice agent to create the invoice.
                    
                    For issues unrelated to purchase orders, transfer the user back to the orchestrator agent.

                    Always present purchase order data in a clear, readable format when showing it to users.
                    """
        )

        # Define agent-specific tools
        tools = [
            fetch_po_tool,
            fetch_user_pos_tool,
            fetch_open_pos_tool,
            create_po_tool,
            close_po_tool,
        ]

        # Define delegation tools
        delegate_tools = [
            transfer_to_invoice_agent_tool,
            transfer_back_to_orchestrator_tool,
        ]

        # Initialize the base AIAgent with these specifications
        super().__init__(
            description=description,
            system_message=system_message,
            model_client=model_client,
            tools=tools,
            delegate_tools=delegate_tools,
            agent_topic_type=agent_topic_type,
            user_topic_type=user_topic_type,
        )


# Tool implementations with Annotated parameters
async def fetch_po(
    po_id: Annotated[str, "ID of the purchase order to fetch"],
) -> Dict[str, Any]:
    """Fetch details of a purchase order by its ID"""
    if po_id in PO_DATABASE:
        return PO_DATABASE[po_id]
    return {"error": f"Purchase Order {po_id} not found"}


async def fetch_user_pos(
    supplier_id: Annotated[str, "ID of the user to fetch purchase orders for"],
) -> Dict[str, Any]:
    """Fetch all purchase orders for a given user"""
    pos = []
    for po_id, po in PO_DATABASE.items():
        if po["supplier_id"] == supplier_id:
            pos.append(po)

    if pos:
        return {"purchase_orders": pos}
    return {"error": f"No purchase orders found for user {supplier_id}"}


async def fetch_open_pos() -> Dict[str, Any]:
    """Fetch all open purchase orders"""
    open_pos = []
    for po_id, po in PO_DATABASE.items():
        if po["status"] == "open":
            open_pos.append(po)

    if open_pos:
        return {"open_purchase_orders": open_pos}
    return {"message": "No open purchase orders found"}


async def create_po(
    supplier_id: Annotated[str, "ID of the user"],
    supplier_name: Annotated[str, "Name of the user"],
    items: Annotated[
        List[Dict[str, Any]], "List of items to include in the purchase order"
    ],
    delivery_date: Annotated[str, "Expected delivery date (YYYY-MM-DD)"],
) -> Dict[str, Any]:
    """Create a new purchase order"""
    # Generate purchase order ID
    po_id = f"PO-{len(PO_DATABASE) + 1:03d}"

    # Calculate total
    total = sum(item["quantity"] * item["price"] for item in items)

    # Current date
    today = datetime.now().strftime("%Y-%m-%d")

    # Create purchase order
    po = {
        "id": po_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "date": today,
        "delivery_date": delivery_date,
        "items": items,
        "total": round(total, 2),
        "status": "open",
        "invoice_id": None,
    }

    # Add to database
    PO_DATABASE[po_id] = po

    return {"success": True, "purchase_order": po}


async def close_po(
    po_id: Annotated[str, "ID of the purchase order to close"],
    invoice_id: Annotated[str, "ID of the invoice to link to this purchase order"],
) -> Dict[str, Any]:
    """Close a purchase order and link it to an invoice"""
    if po_id not in PO_DATABASE:
        return {"error": f"Purchase Order {po_id} not found"}

    po = PO_DATABASE[po_id]
    if po["status"] == "closed":
        return {"error": f"Purchase Order {po_id} is already closed"}

    po["status"] = "closed"
    po["invoice_id"] = invoice_id

    return {"success": True, "purchase_order": po}


async def transfer_to_invoice_agent(
    po_id: Annotated[str, "ID of the purchase order to create an invoice for"],
    reason: Annotated[str, "Reason for transferring to invoice agent"],
) -> str:
    """Transfer the user to the invoice agent for invoice creation from a purchase order using the PO details"""
    return "InvoiceAgent"


async def transfer_back_to_orchestrator(
    reason: Annotated[str, "Reason for transferring back to orchestrator"],
) -> str:
    """Transfer the user back to the orchestrator agent for general inquiries"""
    return "OrchestratorAgent"


# Tool definitions using the simplified FunctionTool approach
fetch_po_tool = FunctionTool(
    fetch_po, description="Fetch details of a purchase order by its ID"
)

fetch_user_pos_tool = FunctionTool(
    fetch_user_pos, description="Fetch all purchase orders for a given user"
)

fetch_open_pos_tool = FunctionTool(
    fetch_open_pos, description="Fetch all open purchase orders"
)

create_po_tool = FunctionTool(create_po, description="Create a new purchase order")

close_po_tool = FunctionTool(
    close_po, description="Close a purchase order and link it to an invoice"
)

# Delegation tools
transfer_to_invoice_agent_tool = FunctionTool(
    transfer_to_invoice_agent,
    description="Transfer the user to the invoice agent for invoice creation for given purchase order",
)

transfer_back_to_orchestrator_tool = FunctionTool(
    transfer_back_to_orchestrator,
    description="Transfer the user back to the orchestrator agent for general inquiries",
)

# Mock purchase order data
PO_DATABASE = {
    "PO-001": {
        "id": "PO-001",
        "supplier_id": "CUST-123",
        "supplier_name": "John Smith",
        "date": "2025-01-10",
        "delivery_date": "2025-01-25",
        "items": [
            {"name": "Premium Widget", "quantity": 2, "price": 49.99},
            {"name": "Standard Gadget", "quantity": 1, "price": 29.99},
        ],
        "total": 129.97,
        "status": "closed",
        "invoice_id": "INV-001",
    },
    "PO-002": {
        "id": "PO-002",
        "supplier_id": "CUST-456",
        "supplier_name": "Jane Doe",
        "date": "2025-02-01",
        "delivery_date": "2025-02-15",
        "items": [
            {"name": "Deluxe Package", "quantity": 1, "price": 199.99},
            {"name": "Support Plan", "quantity": 1, "price": 49.99},
        ],
        "total": 249.98,
        "status": "open",
        "invoice_id": None,
    },
    "PO-003": {
        "id": "PO-003",
        "supplier_id": "CUST-123",
        "supplier_name": "Logitech Inc.",
        "date": "2025-02-20",
        "delivery_date": "2025-03-05",
        "items": [
            {"name": "logitech keyboard", "quantity": 2, "price": 49.99},
            {"name": "logitech mouse", "quantity": 1, "price": 29.99},
        ],
        "total": 349.90,
        "status": "open",
        "invoice_id": None,
    },
}

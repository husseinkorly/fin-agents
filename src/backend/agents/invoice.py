from typing import Dict, Any, List, Annotated
from datetime import datetime
from autogen_core.models import SystemMessage, ChatCompletionClient
from autogen_core.tools import FunctionTool

from context.session_manager import SessionManager
from .ai import AIAgent


class InvoiceAgent(AIAgent):
    def __init__(
        self,
        model_client: ChatCompletionClient,
        user_topic_type: str,
        agent_topic_type: str,
        sessionManager: SessionManager,
    ) -> None:
        description = "An agent handles invoice related tasks"
        system_message = SystemMessage(
            content="""You are an Invoice agent and can help users with the following tasks:
                       - Finding information about their existing invoices
                       - Creating new invoices
                       - Creating invoices from purchase order details
                       - Return current date and time
                    
                    When creating an invoice from a purchase order, you should:
                    1. Try to get all the necessary details from the context if possible and ask the user for any missing details
                    2. Ask the user for the purchase order ID if not provided
                    3. Ask for supplier details if they aren't clear from the context
                    4. ALWAYS include line items in the invoice with their name, quantity, and price
                    5. Create the invoice and confirm with the user
                    
                    When calling the create_invoice_from_po_details function, ALWAYS include the items parameter
                    with an array of items that includes name, quantity, and price for each item.
                    
                    Example items format:
                    "items": [
                        {"name": "Deluxe Package", "quantity": 1, "price": 199.99},
                        {"name": "Support Plan", "quantity": 1, "price": 49.99}
                    ]
                    
                    Always confirm the invoice creation with the user before finalizing it.

                    IMPORTANT: For any queries unrelated to invoices, ALWAYS use the 'transfer_to_orchestrator' function with a brief reason. 
                    Examples when to transfer:
                    - General financial questions
                    - Questions about purchases
                    - User asks about other financial documents
                    - User wants to exit invoice context
                    
                    Be sure to notice when the user's request is not related to invoices and use transfer_to_orchestrator in these cases.
                    """
        )
        # agent's tools
        tools = [
            fetch_invoice_tool,
            fetch_invoices_tool,
            create_invoice_tool,
            create_invoice_from_po_details_tool,
        ]

        # Define delegation tools
        delegate_tools = [
            transfer_to_orchestrator_tool,
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
            sessionManager=sessionManager,
        )


async def fetch_invoice(
    invoice_id: Annotated[str, "ID of the invoice to fetch"],
) -> Dict[str, Any]:
    """Fetch details of an invoice by its ID"""
    if invoice_id in INVOICE_DATABASE:
        return INVOICE_DATABASE[invoice_id]
    return {"error": f"Invoice {invoice_id} not found"}


async def fetch_invoices() -> Dict[str, Any]:
    """Fetch all invoices for a given user"""
    return INVOICE_DATABASE


async def create_invoice(
    supplier_id: Annotated[str, "ID of the user"],
    supplier_name: Annotated[str, "Name of the user"],
    items: Annotated[List[Dict[str, Any]], "List of items to include in the invoice"],
) -> Dict[str, Any]:
    """Create a new invoice for a customer"""
    # Generate invoice ID
    invoice_id = f"INV-{len(INVOICE_DATABASE) + 1:03d}"

    # Calculate total
    total = sum(item["quantity"] * item["price"] for item in items)

    # Current date and due date (30 days later)
    today = datetime.now().strftime("%Y-%m-%d")
    due_date = (
        datetime.now().replace(month=datetime.now().month + 1).strftime("%Y-%m-%d")
    )

    # Create invoice
    invoice = {
        "id": invoice_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "date": today,
        "due_date": due_date,
        "items": items,
        "total": round(total, 2),
        "status": "unpaid",
    }

    # Add to database
    INVOICE_DATABASE[invoice_id] = invoice

    return {"success": True, "invoice": invoice}


async def create_invoice_from_po_details(
    po_id: Annotated[str, "ID of the purchase order to reference"],
    supplier_id: Annotated[str, "ID of the supplier"],
    supplier_name: Annotated[str, "Name of the supplier"],
    items: Annotated[List[Dict[str, Any]], "List of items from the purchase order to include in the invoice"],
) -> Dict[str, Any]:
    """Create a new invoice based on purchase order details provided in the context or by the user"""
    # Generate invoice ID
    invoice_id = f"INV-{len(INVOICE_DATABASE) + 1:03d}"

    # Calculate total from items
    total = sum(item["quantity"] * item["price"] for item in items)

    # Current date and due date (30 days later)
    today = datetime.now().strftime("%Y-%m-%d")
    due_date = (
        datetime.now().replace(month=datetime.now().month + 1).strftime("%Y-%m-%d")
    )

    # Create invoice
    invoice = {
        "id": invoice_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "purchase_order": po_id,  # Reference to the PO ID
        "date": today,
        "due_date": due_date,
        "items": items,
        "total": round(total, 2),
        "status": "unpaid",
    }

    # Add to database
    INVOICE_DATABASE[invoice_id] = invoice

    return {
        "success": True,
        "message": f"Invoice {invoice_id} created based on Purchase Order {po_id}",
        "invoice": invoice,
    }


async def transfer_to_orchestrator(
    reason: Annotated[str, "Reason for transferring back to orchestrator"],
) -> str:
    """Transfer the conversation to the orchestrator agent for general inquiries or tasks outside invoice handling"""
    # Just return the target agent type
    return "OrchestratorAgent"


# Tool definitions - simplified to match the example
fetch_invoice_tool = FunctionTool(
    fetch_invoice, description="Fetch details of an invoice by its ID"
)
fetch_invoices_tool = FunctionTool(
    fetch_invoices, description="Fetch all invoices for a given user"
)
create_invoice_tool = FunctionTool(
    create_invoice, description="Create a new invoice for a user"
)
create_invoice_from_po_details_tool = FunctionTool(
    create_invoice_from_po_details,
    description="Create a new invoice based on purchase order details provided by the user or in context",
)
transfer_to_orchestrator_tool = FunctionTool(
    transfer_to_orchestrator,
    description="Transfer the conversation to the orchestrator agent when user needs help with tasks unrelated to invoices",
)

# Mock invoice data
INVOICE_DATABASE = {
    "INV-001": {
        "id": "INV-001",
        "supplier_id": "CUST-123",
        "purchase_order": "PO-456",
        "supplier_name": "John Smith",
        "date": "2025-01-15",
        "due_date": "2025-02-15",
        "items": [
            {"name": "Premium Widget", "quantity": 2, "price": 49.99},
            {"name": "Standard Gadget", "quantity": 1, "price": 29.99},
        ],
        "total": 129.97,
        "status": "paid",
    },
    "INV-002": {
        "id": "INV-002",
        "supplier_id": "CUST-456",
        "purchase_order": "PO-789",
        "supplier_name": "Jane Doe",
        "date": "2025-02-03",
        "due_date": "2025-03-03",
        "items": [
            {"name": "Deluxe Package", "quantity": 1, "price": 199.99},
            {"name": "Support Plan", "quantity": 1, "price": 49.99},
        ],
        "total": 249.98,
        "status": "unpaid",
    },
}

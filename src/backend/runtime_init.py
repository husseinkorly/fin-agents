from autogen_core import (
    SingleThreadedAgentRuntime,
    TypeSubscription,
)
from agents.invoice import InvoiceAgent
from agents.purchase_order import PurchaseOrderAgent
from agents.orchestrator import OrchestratorAgent
from agents.human import HumanAgent
from agents.user import UserAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import AzureCliCredential, get_bearer_token_provider
from context.session_manager import SessionManager


class RuntimeInit:
    # Define topic types as class attributes
    ORCHESTRATOR_TOPIC = "OrchestratorAgent"
    INVOICE_TOPIC = "InvoiceAgent"
    PO_TOPIC = "PurchaseOrderAgent"
    HUMAN_TOPIC = "HumanAgent"
    USER_TOPIC = "User"

    def __init__(self):
        """Standard constructor (non-async)"""
        self.runtime = None
        self.model_client = None
        self.token_provider = None
        self.initialized = False

    @classmethod
    async def create(cls):
        """Async factory method to create and initialize the runtime"""
        instance = cls()
        await instance._initialize()
        return instance

    async def _initialize(self):
        """Internal method to initialize the runtime and agents"""
        # Create runtime
        self.runtime = SingleThreadedAgentRuntime()

        self.session_manager = SessionManager.get_instance()

        # Set up the model client
        try:
            self.token_provider = get_bearer_token_provider(
                AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
            )
            self.model_client = AzureOpenAIChatCompletionClient(
                model="o3-mini",
                azure_deployment="o3-mini",
                api_version="2024-12-01-preview",
                azure_ad_token_provider=self.token_provider,
                azure_endpoint="",
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize the model client: {str(e)}")

        # Register the orchestrator agent
        orchestrator_agent_type = await OrchestratorAgent.register(
            self.runtime,
            type=self.ORCHESTRATOR_TOPIC,
            factory=lambda: OrchestratorAgent(
                model_client=self.model_client,
                agent_topic_type=self.ORCHESTRATOR_TOPIC,
                user_topic_type=self.USER_TOPIC,
                sessionManager=self.session_manager,
            ),
        )
        await self.runtime.add_subscription(
            TypeSubscription(
                topic_type=self.ORCHESTRATOR_TOPIC,
                agent_type=orchestrator_agent_type.type,
            )
        )

        # Register the invoice agent
        invoice_agent_type = await InvoiceAgent.register(
            self.runtime,
            type=self.INVOICE_TOPIC,
            factory=lambda: InvoiceAgent(
                model_client=self.model_client,
                user_topic_type=self.USER_TOPIC,
                agent_topic_type=self.INVOICE_TOPIC,
                sessionManager=self.session_manager,
            ),
        )
        await self.runtime.add_subscription(
            TypeSubscription(
                topic_type=self.INVOICE_TOPIC, agent_type=invoice_agent_type.type
            )
        )

        # Register the purchase order agent
        po_agent_type = await PurchaseOrderAgent.register(
            self.runtime,
            type=self.PO_TOPIC,
            factory=lambda: PurchaseOrderAgent(
                model_client=self.model_client,
                agent_topic_type=self.PO_TOPIC,
                user_topic_type=self.USER_TOPIC,
                sessionManager=self.session_manager,
            ),
        )
        await self.runtime.add_subscription(
            TypeSubscription(topic_type=self.PO_TOPIC, agent_type=po_agent_type.type)
        )

        # Register the human agent
        human_agent_type = await HumanAgent.register(
            self.runtime,
            type=self.HUMAN_TOPIC,
            factory=lambda: HumanAgent(
                description="A human agent that handles complex user inquiries",
                agent_topic_type=self.HUMAN_TOPIC,
                user_topic_type=self.USER_TOPIC,
                sessionManager=self.session_manager,
            ),
        )
        await self.runtime.add_subscription(
            TypeSubscription(
                topic_type=self.HUMAN_TOPIC, agent_type=human_agent_type.type
            )
        )

        # Register the user agent
        user_agent_type = await UserAgent.register(
            self.runtime,
            type=self.USER_TOPIC,
            factory=lambda: UserAgent(
                description="A user agent that handles user interactions",
                # start with orchestrator agent
                agent_topic_type=self.ORCHESTRATOR_TOPIC,
            ),
        )
        await self.runtime.add_subscription(
            TypeSubscription(
                topic_type=self.USER_TOPIC, agent_type=user_agent_type.type
            )
        )

        self.initialized = True

    def start(self):
        """Start the runtime"""
        if not self.initialized:
            raise RuntimeError("Runtime not initialized. Call create() first.")

        self.runtime.start()
        return self.runtime

    def get_runtime(self):
        """Get the initialized runtime"""
        if not self.initialized:
            raise RuntimeError("Runtime not initialized. Call create() first.")

        return self.runtime

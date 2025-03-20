from typing import List, Optional, ClassVar
from models.messages import Session
from autogen_core.models import LLMMessage
from datetime import datetime
from azure.cosmos import CosmosClient
from config import COSMOS_DB


class SessionManager:
    _instance: ClassVar[Optional["SessionManager"]] = None

    @classmethod
    def get_instance(cls, default_max_messages: int = 20) -> "SessionManager":
        """Get or create the singleton instance of SessionManager"""
        if cls._instance is None:
            cls._instance = cls(default_max_messages)
        return cls._instance

    def __init__(self, default_max_messages: int = 20) -> None:
        # Only initialize if this is not a duplicate instance
        if self.__class__._instance is not None:
            print("SessionManager instance already exists. Use get_instance() instead.")
            return

        self.default_max_messages = default_max_messages
        cosmos_endpoint = COSMOS_DB["endpoint"]
        cosmos_key = COSMOS_DB["key"]
        database_name = COSMOS_DB["database"]
        container_name = COSMOS_DB["container"]

        if not cosmos_endpoint or not cosmos_key:
            print("COSMOS_ENDPOINT or COSMOS_KEY not set.")
            return
        try:
            self.client = CosmosClient(cosmos_endpoint, cosmos_key)
            self.database = self.client.get_database_client(database_name)
            self.container = self.database.get_container_client(container_name)
            print(f"Connected printB container: {container_name}")
        except Exception as e:
            print(f"Failed to connect to Cosmos DB: {str(e)}")

    def create_session(self, current_agent: str = "OrchestratorAgent") -> Session:
        """Create a new session and save to Cosmos DB."""
        session = Session(
            current_agent=current_agent, max_messages=self.default_max_messages
        )
        try:
            session_data = session.model_dump()
            self.container.create_item(body=session_data)
            print(f"Session created in Cosmos DB: {session.id}")
        except Exception as e:
            print(f"Failed to create session: {str(e)}")

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID from Cosmos DB"""
        print(f"Getting session {session_id} from Cosmos DB")
        if not session_id:
            return None
        try:
            item = self.container.read_item(item=session_id, partition_key=session_id)
            print(f"Session {session_id} found in Cosmos DB")
            print(item)
            return Session(**item)
        except Exception as e:
            print(f"Session {session_id} not found: {str(e)}")
            return None

    def update_current_agent(self, session_id: str, agent_type: str) -> bool:
        """Update the current agent for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            session.current_agent = agent_type

            # Update in Cosmos DB
            return self._update_session(session)
        except Exception as e:
            print(f"Error updating agent for session {session_id}: {str(e)}")
            return False

    def get_messages(self, session_id: str) -> List[LLMMessage]:
        """Get messages for a session"""
        session = self.get_session(session_id)
        if not session:
            return []

        return session.get_context_as_llm_messages()

    def update_status(self, session_id: str, status: str) -> bool:
        """Update the status of a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                print(f"Cannot update status - session not found: {session_id}")
                return False

            session.status = status
            # Update in Cosmos DB
            return self._update_session(session)
        except Exception as e:
            print(f"Error updating status for session {session_id}: {str(e)}")
            return False

    def get_status(self, session_id: str) -> Optional[str]:
        """Get the status of a session"""
        session = self.get_session(session_id)
        if not session:
            return None

        return session.status

    def _update_session(self, session: Session) -> bool:
        """Update an existing session in Cosmos DB"""
        try:
            session_data = session.model_dump()
            self.container.replace_item(item=session.id, body=session_data)
            print(f"Updated session in Cosmos DB: {session.id}")
            return True
        except Exception as e:
            print(f"Error updating session in Cosmos DB {session.id}: {str(e)}")
            return False

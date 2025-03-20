from contextlib import asynccontextmanager
from autogen_core import TopicId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from autogen_core.models import UserMessage
from runtime_init import RuntimeInit
from context.session_manager import SessionManager
from models.messages import UserRequest, SessionDetailResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runtime, session_manager

    print("Initializing agent runtime...")
    runtime_manager = await RuntimeInit.create()
    runtime_manager.start()
    runtime = runtime_manager.get_runtime()
    print("Agent runtime initialized successfully!")
    
    # Use the singleton pattern
    session_manager = SessionManager.get_instance()
    
    yield
    # Shutdown: Clean up resources
    await runtime.stop_when_idle()
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=str)
async def chat(request: UserRequest):
    """Handle user chat requests"""
    if not request.session_id:
        session = session_manager.create_session()
    else:
        session = session_manager.get_session(request.session_id)

    # Add user message to the session context
    session.add_message(UserMessage(content=request.message, source="User"))
    session_manager.update_status(session.id, "processing")

    # send a message to the user agent to process the request
    print(f"Publishing message to User agent for session {session.id}")
    await runtime.publish_message(
        session,
        topic_id=TopicId("User", source=session.id),
    )

    return session.id


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    """Get details for a specific session including messages"""
    session = session_manager.get_session(session_id)
    
    if not session:
        print(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # Format messages for the response
    formatted_messages = []
    for msg in session.context:
        content = msg.content if hasattr(msg, "content") else "No content"
        source = msg.source if hasattr(msg, "source") else "System"

        formatted_messages.append(
            {
                "content": content,
                "source": source,
                "role": "user" if source == "User" else "assistant",
            }
        )

    print(f"Returning session {session_id} with {len(formatted_messages)} messages")
    return SessionDetailResponse(
        session_id=session.id,
        current_agent=session.current_agent,
        status=session.status,
        messages=formatted_messages,
    )


@app.get("/health")
async def health_check():
    """Check if the service is running"""
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting 🤖 application")
    uvicorn.run(app, host="0.0.0.0", port=8000)

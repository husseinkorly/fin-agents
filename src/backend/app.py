from fastapi import FastAPI
import uvicorn
import uuid

from models.messages import UserRequest, HumanFeedback

app = FastAPI()

app.add_middleware(
    allow_origins=["*"], # for development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/request")
async def handle_request(user_request: UserRequest):
    """
        handles initial user request
    """
    if not user_request.session_id:
        user_request.session_id = str(uuid.uuid4())

    # initializing runtime and agents to serve user request

    # messgae the orchestrator agent to get the next action


@app.post("/human_feedback")
async def handle_human_feedback(human_feedback: HumanFeedback):
    """
        handles human feedback
    """
    pass
    # human (user) is considered as another agent in the system
    # send the feedback to the human agent


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

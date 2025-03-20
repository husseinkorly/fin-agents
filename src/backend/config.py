import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Cosmos DB settings
COSMOS_DB = {
    "endpoint": os.environ.get(
        "COSMOS_ENDPOINT", ""
    ),
    "key": os.environ.get(
        "COSMOS_KEY",
        "",
    ),
    "database": os.environ.get("COSMOS_DATABASE", "agents_data"),
    "container": os.environ.get("COSMOS_CONTAINER", "sessions"),
}

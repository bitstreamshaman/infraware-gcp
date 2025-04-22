import uvicorn
import os


# Set up environment for local development
os.environ["GOOGLE_CLOUD_PROJECT"] = "local-development"

# Mock Google Cloud credentials for local development
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["STORAGE_EMULATOR_HOST"] = "localhost:9023"

if __name__ == "__main__":
    # Run the API with hot reload for development
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
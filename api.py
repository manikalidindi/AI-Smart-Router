
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from Agent_pipeline import workflow

app = FastAPI(title="Nexus AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    answer: str
    route: str


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Nexus AI backend is running",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    query = request.user_input.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Please provide a message.",
        )

    try:
        result = workflow.invoke({
            "user_input": query,
        })

        return ChatResponse(
            answer=result["answer"],
            route=result["route"],
        )

    except Exception:
        # Log the real exception in the backend terminal,
        # but do not expose API keys or internal errors.
        import logging
        logging.exception("LangGraph workflow failed")

        raise HTTPException(
            status_code=500,
            detail="AI workflow failed. Check the backend terminal.",
        )

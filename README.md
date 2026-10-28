Nexus AI Smart Router
Nexus AI Smart Router is an AI application that classifies a user's request and routes it to an appropriate processing workflow. It uses LangGraph to coordinate the routing logic, a FastAPI backend to expose the workflow through an HTTP API, and an HTML frontend for user interaction.
Features
- Routes simple conversational requests to a local Ollama model.
- Routes coding tasks to Google Gemini.
- Routes factual research queries through Tavily search and uses Gemini to generate a response.
- Exposes the workflow through a FastAPI API.
- Provides a browser-based frontend.
- Returns the selected route along with the generated answer.
Architecture
The application contains three main parts:
1. Frontend: frontend/index.html provides the chat interface and sends requests to the backend.
2. API: api.py validates incoming requests and invokes the LangGraph workflow.
3. Agent workflow: Agent_pipeline.py classifies requests and runs the selected node.
Routing paths
- simple_response: Handles general conversational requests with Ollama.
- coding_task: Handles programming requests with Gemini.
- factual_query: Searches for relevant information using Tavily and uses Gemini to formulate the answer.
The router determines which path to use based on the user's input.
Project Structure
AI-Smart-Router/
├── Agent_pipeline.py
├── api.py
├── frontend/
│   └── index.html
├── .env
└── README.md
Your repository may contain additional files, such as a virtual environment, dependency lockfile, or configuration files.
Requirements
- Python 3.10 or a compatible version supported by your installed dependencies
- uv or another Python environment and package manager
- Ollama installed and running locally
- An Ollama model available locally, such as llama3.2
- A Google Gemini API key
- A Tavily API key
Setup
1. Clone or open the project
Open a terminal in the project root directory, where api.py and Agent_pipeline.py are located.
2. Create and activate an environment
If you use uv, create an environment with:
uv venv
Activate it on macOS or Linux:
source .venv/bin/activate
Install the dependencies used by the application:
uv add fastapi uvicorn pydantic langgraph langchain-google-genai langchain-ollama tavily-python python-dotenv
If your project already has a pyproject.toml and lockfile, install its declared dependencies instead:
uv sync
3. Configure environment variables
Create a .env file in the project root:
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
Replace the example values with your actual API keys. Do not commit .env or expose API keys in frontend code.

Make sure Agent_pipeline.py loads the environment variables before creating the Gemini and Tavily clients.
4. Start Ollama
Ensure Ollama is installed and running, and that the model configured in Agent_pipeline.py is available. For example:
ollama pull llama3.2
If Ollama is not already running, start its service using the method appropriate for your operating system.
Run the Application
Run the frontend and backend in separate terminals. The examples below use port 8001 for the frontend and port 8000 for the API.
Terminal 1: Start the backend
From the project root:
uv run uvicorn api:app --reload --port 8000
The API should be available at:
- API health check: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs
Terminal 2: Start the frontend
From the project root:
cd frontend
python -m http.server 8001
Open this URL in your browser:

http://localhost:8001

If your frontend uses a different port, update the CORS configuration in api.py to allow the exact frontend origin. The frontend's API URL should point to:
const API_URL = "http://127.0.0.1:8000";
The backend and frontend must use different ports when running on the same machine.
API Reference
GET /
Checks whether the backend is running.

Example response:
{
  "status": "ok",
  "message": "Nexus AI backend is running"
}
POST /chat
Runs a user message through the LangGraph workflow.

Request body:
{
  "user_input": "Write a Python function to reverse a string"
}
Example response shape:
{
  "answer": "The generated response appears here.",
  "route": "coding_task"
}
The answer content and selected route depend on the request and model output.

You can test this endpoint in the interactive documentation at http://127.0.0.1:8000/docs.
CORS Configuration
The backend must allow the origin from which the frontend is served. For a frontend running at http://localhost:8001, configure CORS in api.py to include both:
allow_origins=[
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]
Add other origins only when needed for your development setup. For production, configure the exact trusted frontend domain rather than allowing every origin.
Troubleshooting
The browser cannot connect to the API
- Confirm the backend is running on port 8000.
- Open http://127.0.0.1:8000/ to check the health endpoint.
- Confirm API_URL in frontend/index.html is http://127.0.0.1:8000.
- Check the browser console and backend terminal for errors.
CORS errors appear in the browser
- Confirm the frontend URL and port match an entry in allow_origins.
- Restart Uvicorn after changing api.py.
- Remember that localhost and 127.0.0.1 are distinct origins and may both need to be listed.
Gemini or Tavily authentication fails
- Check that .env exists in the project root.
- Confirm GEMINI_API_KEY and TAVILY_API_KEY are correct.
- Ensure load_dotenv() runs before the clients are initialized.
- Restart the backend after changing environment variables.
Ollama requests fail
- Confirm Ollama is installed and running.
- Confirm the model name in Agent_pipeline.py matches an installed model.
- Pull the required model if it is missing.
The API returns a 500 error
The API is configured to return a general error message to the client while logging the underlying exception in the backend terminal. Read that terminal traceback to identify the cause. Do not share API keys or other secrets when sharing logs.
The frontend shows a favicon 404
A missing /favicon.ico file usually does not affect the application. Add a favicon to the frontend if you want to remove this message.
Security Notes
- Keep API keys in environment variables and never expose them in frontend JavaScript.
- Do not commit .env to version control. Add it to .gitignore.
- Restrict CORS to trusted frontend origins.
- Validate incoming request data and avoid returning internal exceptions or secrets to clients.
- Before deploying publicly, add appropriate authentication, rate limiting, request logging, and operational monitoring.
- Review model and search-provider usage limits and costs before allowing unrestricted access.
Development Notes
- api.py is the HTTP entry point.
- Agent_pipeline.py defines and compiles the LangGraph workflow.
- frontend/index.html contains the browser interface.
- The research workflow depends on the router selecting factual_query; a frontend research prompt alone does not guarantee that route unless the backend routing logic explicitly enforces it.
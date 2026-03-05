# Bollette Agent

Bollette Agent is a Flask-based AI service that manages a betting slip from natural language prompts.

Given user text (for example, "add Inter over" or "checkout 20"), the app:

- recognizes the user intent (`add`, `remove`, `replace`, `checkout`)
- searches and resolves the target match from external tournament data
- updates an in-memory payslip for the user session
- returns the updated state and a user-facing message

## Tech stack and dependencies

Core dependencies (from `Pipfile`):

- `flask`, `flask-cors`, `gevent`
- `flask-openapi3` (Swagger/OpenAPI generation)
- `langchain`, `langchain-community`, `langchain-openai`
- `openai`
- `numpy`
- `python-dotenv`
- `requests`, `aiohttp`
- `colorama`

Runtime:

- Python `3.11`
- Pipenv for dependency and virtualenv management

## Project structure (main entry points)

- `app.py`: app bootstrap and server startup (`0.0.0.0:8082`)
- `api_routes.py`: HTTP route definitions
- `api_models.py`: typed request/response models for OpenAPI
- `bollette_agent.py`: core orchestration logic for user actions
- `tools/match_list.py`: tournament data retrieval + vector search preparation

## Environment variables

Required for normal runtime:

- `OPENAI_API_KEY`
- `BOLLETTE_SERVER_BASE_URL`

Used by LangSmith/LangChain observability (optional but supported):

- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2`
- `LANGCHAIN_ENDPOINT`
- `LANGCHAIN_PROJECT`

Present in legacy docs / environment templates:

- `PROXYCURL_API_KEY`
- `PYTHONPATH`

You can place variables in a `.env` file in the project root.

## Setup and startup

1. Install dependencies:

	 ```bash
	 pipenv install
	 ```

2. Start the app:

	 ```bash
	 pipenv run python app.py
	 ```

3. Service runs on:

	 - `http://localhost:8082`

## API documentation (Swagger/OpenAPI)

Once the app is running:

- Swagger UI: `http://localhost:8082/api/swagger`
- OpenAPI JSON: `http://localhost:8082/openapi.json`

## API endpoints

### `GET /health`

Health check endpoint.

Response `200`:

```json
{
	"status": "ok"
}
```

### `POST /`

Main endpoint for user actions.

Request body:

```json
{
	"input": "add Inter over",
	"session": "optional-session-id"
}
```

- `input` (string, required): natural language action
- `session` (string, optional): existing session id

Behavior:

- If `session` is missing or unknown, the app creates a new session and starts a new payslip.
- If `session` exists, the app applies the action to that session payslip.

Possible responses:

- `200`: action processed (startup/update/checkout response)
- `400`: invalid input (e.g., empty `input`)
- `500`: processing error

Example `400` / `500` response:

```json
{
	"message": "An error occurred, try again"
}
```

## Notes

- Payslips are stored in memory (`PAYSLIPS` dict), so data is reset when the process restarts.
- Tournament/match availability depends on the upstream service configured in `BOLLETTE_SERVER_BASE_URL`.

## Troubleshooting

- If Swagger UI says to install `flask-openapi3[swagger,...]`, install extras with quotes in zsh:

	```bash
	pipenv run pip install -U 'flask-openapi3[swagger]'
	```
# AI Orchestrator

Production-ready AI Orchestrator microservice — a conversational layer that orchestrates existing microservice APIs via LangChain tool calling. It never accesses PostgreSQL or generates SQL.

## Architecture

```
User Chat → AI Orchestrator → IAM Permission Check → Allowed Tools → Existing APIs → Microservices
```

### Clean Architecture Layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| **API** | `app/api/` | HTTP endpoints, middleware, dependency injection |
| **Application** | `app/application/` | Use cases (chat, permissions) |
| **Domain** | `app/domain/` | Models, prompts — no infrastructure deps |
| **Infrastructure** | `app/infrastructure/` | HTTP clients, LLM providers, tools |
| **Agents** | `app/agents/` | LangChain agent orchestration |
| **Core** | `app/core/` | Config, logging, exceptions |

## Tech Stack

- **FastAPI** — async HTTP API
- **LangChain + LangGraph** — tool-calling agent
- **Ollama** — local LLM (Qwen2.5:7b)
- **Pydantic Settings** — environment-based config
- **Structlog** — structured logging
- **Docker** — containerized deployment

## Quick Start

### Local Development

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama and pull model
ollama pull qwen2.5:7b

# 5. Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
cp .env.example .env
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:7b
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness probe |
| `GET` | `/api/v1/health/ready` | Readiness probe (checks IAM, Ollama) |
| `POST` | `/api/v1/chat` | Send a chat message |
| `POST` | `/api/v1/chat/stream` | Streaming chat (placeholder) |
| `GET` | `/api/v1/chat/tools` | List tools available to the caller |

### Chat Example

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me my profile"}'
```

## Adding New Tools

1. Create a tool module in `app/infrastructure/tools/definitions/`
2. Use the `@register_tool` decorator with required IAM permissions
3. Call existing microservice HTTP APIs — never SQL
4. Register the module in `app/infrastructure/tools/loader.py`

```python
@register_tool(
    name="my_tool",
    description="What this tool does",
    required_permissions=["module:action"],
    service="my-service",
    args_schema=MyToolInput,
)
async def my_tool(*, token: str, user_id: str, param: str) -> str:
    data = await client.get("/api/v1/resource", token=token)
    return json.dumps(data)
```

## Configuration

All settings are loaded from environment variables. See `.env.example` for the full list.

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama model name |
| `IAM_SERVICE_URL` | `http://localhost:3001` | IAM service base URL |
| `LOG_JSON` | `false` | Enable JSON structured logging |

## Design Principles

- **Never access PostgreSQL** — all data via existing HTTP APIs
- **Never generate SQL** — tools call REST endpoints only
- **Never decide permissions** — IAM is the sole authority
- **No business logic** — orchestration and formatting only
- **Permission-aware tools** — dynamically loaded per user session

## Future Roadmap

- [ ] Native streaming via `agent.astream()`
- [ ] OpenAI provider (`LLM_PROVIDER=openai`)
- [ ] WhatsApp Business API integration
- [ ] Redis session / chat history
- [ ] Multi-tenant support
- [ ] Audit logging

## Tests

```bash
pytest tests/ -v
```

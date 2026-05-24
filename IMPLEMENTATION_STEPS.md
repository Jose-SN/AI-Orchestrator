# AI Orchestrator — Implementation Roadmap

> **Purpose:** Step-by-step guide to take the AI Orchestrator from starter code to production.
> **Audience:** Developers new to the project; structured for enterprise delivery.
> **Last updated:** May 2026

---

## Executive Summary

The AI Orchestrator is a **conversational API layer** — it understands user intent, calls existing microservice HTTP APIs via LangChain tools, and returns formatted responses. It **never** accesses PostgreSQL directly and **never** decides permissions (IAM does).

```
User → AI Orchestrator → IAM → Allowed Tools → Existing APIs → Microservices → DB
```

### Current Status (Starter Complete)

| Area | Status | Notes |
|------|--------|-------|
| Clean architecture & folder structure | ✅ Done | `bootstrap/`, `domain/`, `application/`, `infrastructure/`, `presentation/` |
| FastAPI + Docker | ✅ Done | Health, chat, tools endpoints |
| IAM client + middleware | ✅ Done | JWT validation, permissions cache, module/actions |
| Dynamic tool registry | ✅ Done | Permission-aware, CRUD sample tools |
| LangChain tool-calling agent | ✅ Done | Ollama + Qwen2.5, deterministic config |
| Audit logging hooks | ✅ Done | Structured audit events |
| Unit tests | ✅ Done | 21 tests passing |
| Streaming responses | 🔶 Stub | SSE endpoint exists, not native LLM streaming |
| Redis | 🔶 Planned | In-memory memory stub only |
| WhatsApp | 🔶 Stub | Adapter placeholder |
| OpenAI production | 🔶 Stub | Provider exists, not production-tested |
| Full observability | 🔶 Partial | Metrics/tracing stubs, OTel not wired |
| Integration / E2E tests | ❌ Not started | Folders ready |

---

## Architecture Phases

### Phase 0 — Foundation (Complete)

**Goal:** Runnable service with correct boundaries.

- [x] Enterprise folder structure (clean architecture)
- [x] Pydantic settings + `.env` configuration
- [x] Structured logging (structlog) + audit logger
- [x] Global error handling + request/trace IDs
- [x] Docker + docker-compose (Ollama sidecar)
- [x] Health + readiness probes

**Exit criteria:** `uvicorn app.main:app` runs; `/api/v1/health` returns 200; tests pass.

---

### Phase 1 — Core Orchestration (Complete)

**Goal:** End-to-end chat with IAM-gated tools.

- [x] IAM integration client (validate, permissions, modules, actions, cache)
- [x] IAM auth middleware
- [x] Permission service → dynamic tool loading
- [x] Tool registry + `@orchestrator_tool` decorator
- [x] Sample tools (users, modules, customers)
- [x] LangChain ReAct agent (tool-calling only)
- [x] Agent factory, prompts, structured output parser

**Exit criteria:** Authenticated chat request invokes allowed tools and returns formatted response.

---

### Phase 2 — Platform Integration (Current Focus)

**Goal:** Connect to your real microservices and IAM.

**Priority: P0 — Do this first**

- [ ] Align IAM API contract with your Node.js IAM service
  - [ ] Confirm `/api/v1/auth/validate` response shape
  - [ ] Confirm `/api/v1/auth/permissions` response shape
  - [ ] Confirm module/actions endpoint paths
- [ ] Map IAM permission strings to tool `required_permissions`
- [ ] Point service URLs in `.env` to real microservices
- [ ] Build tools for each existing CRUD API domain (one module per microservice)
- [ ] Manual smoke test: frontend → orchestrator → API → response

**Checklist — Tool per microservice**

```
For each microservice:
  [ ] Create HTTP client in infrastructure/http/clients/
  [ ] Add service URL to settings
  [ ] Create tools in infrastructure/tools/definitions/
  [ ] Register in infrastructure/tools/loader.py
  [ ] Document required IAM permissions
  [ ] Add unit test for permission filtering
```

**Exit criteria:** At least 3 real business domains work end-to-end in dev/staging.

---

### Phase 3 — Quality & Reliability

**Goal:** Confidence to deploy beyond localhost.

**Priority: P0**

- [ ] Integration tests (mock IAM + mock downstream APIs)
- [ ] Contract tests against IAM OpenAPI spec
- [ ] Agent behavior tests (tool selection, no hallucination patterns)
- [ ] Load test baseline (concurrent chat requests)
- [ ] Error scenario tests (IAM down, microservice timeout, Ollama down)

**Priority: P1**

- [ ] CI pipeline (lint → test → build Docker image)
- [ ] Pre-commit hooks (ruff, mypy optional)
- [ ] Test coverage report (target: 70%+ on application/domain layers)

**Exit criteria:** CI green on every PR; integration suite runs in < 5 minutes.

---

### Phase 4 — Production Hardening

**Goal:** Safe, observable, operable production deployment.

**Priority: P0**

- [ ] Secrets via env/vault (never commit `.env`)
- [ ] Non-root Docker user (already in Dockerfile — verify)
- [ ] Resource limits (CPU/memory) in K8s/compose
- [ ] Timeouts on all HTTP clients (IAM, microservices, Ollama)
- [ ] Rate limiting on chat endpoints
- [ ] Disable `/docs` in production (`APP_ENV=production`)
- [ ] JSON structured logging in production (`LOG_JSON=true`)

**Priority: P1**

- [ ] Circuit breaker for downstream services
- [ ] Graceful degradation when Ollama unavailable
- [ ] IAM cache invalidation strategy on permission changes
- [ ] Security review: token never logged, tools never expose token to LLM

**Exit criteria:** Production checklist signed off; on-call runbook exists.

---

### Phase 5 — Enhanced Capabilities

**Goal:** Streaming, memory, channels, optional cloud LLM.

**Priority: P1–P2 (after Phase 2–4 stable)**

See dedicated plans below: Redis, OpenAI, WhatsApp, Observability.

---

## Recommended Implementation Order

```
Week 1–2   Phase 2  → Real IAM + real API tools
Week 3     Phase 3  → Integration tests + CI
Week 4     Phase 4  → Production hardening
Week 5–6   Phase 5a → Streaming + Redis memory
Week 7–8   Phase 5b → Observability full stack
Week 9+    Phase 5c → WhatsApp / OpenAI (as needed)
```

### Priority Matrix

| Priority | Meaning | Examples |
|----------|---------|----------|
| **P0** | Blocker for production | IAM alignment, real tools, integration tests, secrets |
| **P1** | Important, soon after launch | Streaming, Redis, OTel, rate limits |
| **P2** | Valuable enhancement | WhatsApp, OpenAI, RAG/vector DB |
| **P3** | Future / optional | Multi-agent, multi-tenant, voice |

---

## Milestones

| Milestone | Description | Target |
|-----------|-------------|--------|
| **M1 — Local Demo** | Chat works with Ollama + sample tools | ✅ Complete |
| **M2 — IAM Connected** | Real JWT + permissions from IAM service | Phase 2 |
| **M3 — First Production Domain** | One business workflow end-to-end in staging | Phase 2 |
| **M4 — CI Green** | Automated test pipeline | Phase 3 |
| **M5 — Staging Deploy** | Docker deploy to staging environment | Phase 4 |
| **M6 — Production MVP** | Limited user pilot, audit + monitoring | Phase 4 |
| **M7 — Streaming + Memory** | SSE streaming + Redis conversation history | Phase 5 |
| **M8 — Channel Expansion** | WhatsApp or OpenAI (business decision) | Phase 5 |

---

## Testing Strategy

### Test Pyramid

```
        ┌─────────┐
        │   E2E   │  Few — full flow with test environment
       ┌┴─────────┴┐
       │ Integration│  IAM mocks, HTTP client mocks, agent + tools
      ┌┴───────────┴┐
      │    Unit     │  Many — parsers, registry, permissions, config
      └─────────────┘
```

### Layer-by-Layer

| Layer | Location | What to test | Tools |
|-------|----------|--------------|-------|
| **Unit** | `tests/unit/` | Tool registry filtering, IAM parsing, agent parser, cache TTL | pytest, pytest-asyncio |
| **Integration** | `tests/integration/` | ChatService + mocked IAM + mocked APIs | httpx, respx or pytest-httpx |
| **E2E** | `tests/e2e/` | Full HTTP request → response against staging | pytest + real/staging services |
| **Contract** | `tests/contract/` | IAM + microservice response shapes | schemathesis or manual fixtures |

### Critical Test Scenarios (Must Have)

- [ ] User with `customers:read` cannot invoke `create_customer`
- [ ] Invalid JWT returns 401
- [ ] IAM timeout returns 502 (not 500 unhandled)
- [ ] Agent does not receive tools when permissions empty
- [ ] Tool downstream error returns structured `ToolResponse` failure
- [ ] Audit events emitted for chat request, tool invoke, auth failure

### Running Tests

```bash
# All unit tests
pytest tests/unit -v

# With coverage (after adding pytest-cov)
pytest tests/ --cov=app --cov-report=term-missing

# Integration (when added)
pytest tests/integration -v
```

---

## Deployment Strategy

### Environments

| Environment | Purpose | LLM | IAM | Notes |
|-------------|---------|-----|-----|-------|
| **Local** | Developer machine | Ollama local | Mock or dev IAM | Hot reload |
| **Dev** | Shared integration | Ollama in cluster | Dev IAM | Auto-deploy from main |
| **Staging** | Pre-production | Ollama or OpenAI | Staging IAM | Mirror prod config |
| **Production** | Live users | Ollama or OpenAI | Prod IAM | No docs, JSON logs |

### Docker Deployment (Current)

```bash
cp .env.example .env
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:7b
```

### Production Deployment Checklist

```
Pre-deploy
  [ ] .env secrets injected via vault/K8s secrets
  [ ] IAM_SERVICE_URL points to production IAM
  [ ] All microservice URLs verified
  [ ] OLLAMA_BASE_URL or OPENAI_API_KEY configured
  [ ] LOG_JSON=true, APP_ENV=production
  [ ] CORS_ORIGINS restricted to frontend domain

Deploy
  [ ] Build and push Docker image (tagged by git SHA)
  [ ] Rolling update with health check grace period
  [ ] Readiness probe passes (/api/v1/health/ready)

Post-deploy
  [ ] Smoke test: authenticated chat request
  [ ] Verify audit logs appearing
  [ ] Verify metrics/traces (when OTel enabled)
  [ ] Rollback plan documented
```

### Kubernetes (Recommended for Production)

```
Deployment: ai-orchestrator (2+ replicas)
Service: ClusterIP :8000
Ingress: TLS termination
Probes:
  liveness:  GET /api/v1/health
  readiness: GET /api/v1/health/ready
Resources:
  requests: 512Mi RAM, 250m CPU
  limits:   2Gi RAM, 1000m CPU
Sidecar (optional): Ollama on GPU node OR external Ollama service
```

---

## Future Improvements

### Near-Term (3–6 months)

- [ ] Native LLM streaming (`agent.astream()`)
- [ ] Redis conversation memory
- [ ] Full OpenTelemetry (traces + metrics export)
- [ ] Tool catalog admin API (list all registered tools)
- [ ] Conversation history API (read-only, for UI)
- [ ] Prompt versioning (A/B test prompts without redeploy)

### Mid-Term (6–12 months)

- [ ] WhatsApp Business API channel
- [ ] OpenAI / Azure OpenAI production path
- [ ] RAG via vector DB (Qdrant) for document-aware answers
- [ ] Multi-tenant isolation (tenant ID in context)
- [ ] Specialist agents per domain (billing, CRM, HR)

### Long-Term (12+ months)

- [ ] Voice integration
- [ ] Multi-agent supervisor pattern
- [ ] Fine-tuned domain models
- [ ] Cost tracking per tenant / per model

---

## WhatsApp Integration Plan

### Overview

WhatsApp becomes another **presentation channel** — same agent pipeline, different input/output adapter.

```
WhatsApp Webhook → WhatsAppAdapter → ChatService → Agent → Tools → APIs
                                      ↓
                              WhatsApp reply API
```

### Implementation Steps

| Step | Task | Priority |
|------|------|----------|
| 1 | Register Meta WhatsApp Business API app | P2 |
| 2 | Implement webhook verification (GET challenge) | P2 |
| 3 | Parse inbound message payload → `ChatRequest` | P2 |
| 4 | Map WhatsApp user ID → platform user (via IAM or mapping table in user service) | P2 |
| 5 | Use `whatsapp` prompt template (shorter responses) | P2 |
| 6 | Send outbound message via Graph API | P2 |
| 7 | Handle media messages (defer or reject gracefully) | P3 |
| 8 | Rate limit + idempotency (duplicate webhook protection) | P1 |

### Files to Extend

- `app/infrastructure/channels/whatsapp/adapter.py`
- `app/presentation/http/v1/endpoints/webhooks.py` (new)
- `app/domain/prompts/system.py` — `WHATSAPP_GREETING_PROMPT` (exists)

### Checklist

```
[ ] WHATSAPP_ENABLED=true in production env
[ ] Webhook URL registered in Meta dashboard
[ ] Verify token stored in secrets
[ ] User identity mapping documented
[ ] Audit log includes channel=whatsapp
[ ] E2E test with Meta sandbox number
```

### Risks

| Risk | Mitigation |
|------|------------|
| User identity mismatch | Map via phone number lookup in user service API |
| 24-hour messaging window | Design flows for session vs template messages |
| Long AI responses | Enforce shorter prompts; split long replies |

---

## OpenAI Migration Plan

### When to Migrate

- Need higher tool-calling reliability at scale
- Ollama GPU ops become costly to maintain
- Latency requirements exceed local model capacity

### Current State

- `LLM_PROVIDER=openai` supported in settings
- `OpenAIProvider` in `app/infrastructure/llm/providers/openai.py`
- Agent factory falls back to generic provider when not Ollama

### Migration Steps

| Step | Task | Effort |
|------|------|--------|
| 1 | Set `OPENAI_API_KEY` in secrets manager | Low |
| 2 | Set `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-4o-mini` (start cheap) | Low |
| 3 | Run tool-calling eval suite — compare vs Qwen2.5 | Medium |
| 4 | Tune prompts for OpenAI (may need minor adjustments) | Medium |
| 5 | Add cost tracking (tokens in/out per request) | Medium |
| 6 | Feature flag: per-tenant or per-route provider selection | High |
| 7 | Azure OpenAI variant (enterprise compliance) | Medium |

### Dual-Provider Strategy (Recommended)

```
Default:  Ollama (dev, cost-sensitive, on-prem)
Fallback: OpenAI (production peak, complex queries)
Config:   LLM_PROVIDER=ollama | openai (env-level first, user-level later)
```

### Checklist

```
[ ] OPENAI_API_KEY in vault, never in git
[ ] Rate limits configured on OpenAI account
[ ] Tool-calling accuracy benchmark documented
[ ] Cost per conversation estimated
[ ] Rollback to Ollama tested (change LLM_PROVIDER only)
[ ] Audit log includes model + provider used
```

### Risks

| Risk | Mitigation |
|------|------------|
| Data leaving premises | Use Azure OpenAI with private endpoint; review data policy |
| Cost spikes | Token limits, max iterations, rate limiting |
| Tool format differences | Keep StructuredTool + same tool definitions |

---

## Redis Integration Plan

### Use Cases

1. **Conversation memory** — multi-turn chat history
2. **IAM permission cache** — distributed cache (replace in-memory)
3. **Rate limiting** — per-user request counts
4. **Session state** — conversation metadata, last active

### Architecture

```
ChatService → ConversationMemoryStore (port)
                    ↓
            RedisMemoryStore (adapter)
                    ↓
                 Redis
```

### Implementation Steps

| Step | Task | Priority |
|------|------|----------|
| 1 | Add `redis` + `redis.asyncio` to requirements | P1 |
| 2 | Add settings: `REDIS_URL`, `REDIS_TTL_SECONDS` | P1 |
| 3 | Implement `RedisConversationStore` in `infrastructure/persistence/redis/` | P1 |
| 4 | Wire into agent when `AGENT_MEMORY_ENABLED=true` | P1 |
| 5 | Replace `IAMPermissionCache` in-memory with Redis (optional) | P2 |
| 6 | Add Redis health check to readiness probe | P1 |
| 7 | Docker compose: add Redis service | P1 |

### Key Design Rules

- **Never store JWT tokens in Redis** — store conversation messages only
- **TTL everything** — default 24h conversation expiry
- **Key pattern:** `orchestrator:conv:{conversation_id}` / `orchestrator:iam:{token_hash}`

### Checklist

```
[ ] REDIS_URL configured
[ ] Memory enabled via AGENT_MEMORY_ENABLED=true
[ ] Conversation survives pod restart
[ ] TTL verified (keys expire)
[ ] Redis failure → graceful fallback (stateless mode)
[ ] Load test with Redis under concurrent writes
```

---

## Observability Plan

### Current State

- Structlog JSON logging
- Audit logger (separate stream)
- Request ID + Trace ID headers
- In-process metrics stub (`increment_counter`)
- OTel stub (`OTEL_ENABLED=false`)

### Target State

```
Request → FastAPI → Agent → Tools
    ↓         ↓        ↓       ↓
  Logs    Traces   Metrics  Audit
    ↓         ↓        ↓       ↓
  ELK/Loki  Tempo/Jaeger  Prometheus  SIEM
```

### Implementation Phases

| Phase | Task | Priority |
|-------|------|----------|
| **O1** | Enable `LOG_JSON=true` in staging/prod | P0 |
| **O2** | Ship logs to centralized store (Loki/ELK) | P0 |
| **O3** | Wire OpenTelemetry SDK + exporter | P1 |
| **O4** | Prometheus metrics endpoint `/metrics` | P1 |
| **O5** | Dashboards: latency, error rate, tool usage | P1 |
| **O6** | Alerts: IAM down, Ollama down, error spike | P0 |
| **O7** | Audit log export for compliance | P1 |

### Key Metrics to Track

| Metric | Type | Purpose |
|--------|------|---------|
| `chat_requests_total` | Counter | Volume |
| `chat_request_duration_seconds` | Histogram | Latency |
| `tool_invocations_total` | Counter | Tool usage by name |
| `iam_cache_hit_ratio` | Gauge | Cache efficiency |
| `agent_iterations` | Histogram | Detect runaway loops |
| `downstream_errors_total` | Counter | Microservice health |

### Checklist

```
[ ] LOG_JSON=true in production
[ ] Request ID in every log line
[ ] Trace ID propagated to tool calls
[ ] OTEL_ENABLED=true with exporter endpoint
[ ] Grafana dashboard created
[ ] PagerDuty/alert on readiness probe failures
[ ] Audit logs retained per compliance policy
```

---

## Production Hardening Plan

### Security

| Item | Status | Action |
|------|--------|--------|
| JWT validation via IAM | ✅ | Keep IAM as sole authority |
| Token not in logs | ⚠️ Verify | Audit all log statements |
| Token not passed to LLM | ✅ | Injected server-side only |
| No SQL generation | ✅ | Prompt + code review per tool |
| CORS restricted | ⚠️ | Set explicit origins in prod |
| Rate limiting | ❌ | Add middleware (Redis-backed) |
| Input sanitization | ⚠️ | Max message length enforced (8000 chars) |

### Reliability

| Item | Action |
|------|--------|
| Timeouts | All HTTP clients have explicit timeouts |
| Retries | IAM + microservices retry with backoff (IAM done) |
| Circuit breaker | Add for each downstream service |
| Graceful shutdown | Lifespan closes HTTP clients (done) |
| Health probes | Liveness + readiness (done) |
| Idempotency | Add for chat if needed (conversation_id) |

### Operations

| Item | Action |
|------|--------|
| Runbook | Document: IAM down, Ollama down, high latency |
| Rollback | Previous Docker image tag ready |
| Config management | Env-only, no config in image |
| Backup | Redis persistence if used for memory |
| DR | Stateless orchestrator — redeploy anywhere |

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM hallucinates data | High | Medium | Tool-only responses; never trust LLM for facts |
| Wrong tool selected | Medium | Medium | Clear tool descriptions; deterministic temp; eval tests |
| IAM outage blocks all chat | High | Low | Cache TTL; graceful error message; monitor IAM |
| Ollama slow under load | Medium | Medium | Horizontal scaling; consider OpenAI fallback |
| Permission string mismatch | High | Medium | Document mapping; integration tests with real IAM |
| Token leakage in logs | Critical | Low | Code review; never log Authorization header |
| Scope creep (business logic in AI) | High | Medium | Architecture reviews; tools call APIs only |
| WhatsApp identity mapping errors | Medium | Medium | Explicit user linking flow |

---

## Master Checklist — Path to Production

### Phase 2 — Integration (Do Now)

- [ ] Connect to real IAM service
- [ ] Verify permission strings match tool definitions
- [ ] Implement tools for priority business domains
- [ ] Smoke test from React frontend
- [ ] Document API permission matrix (IAM ↔ tools)

### Phase 3 — Quality

- [ ] Add integration test suite
- [ ] Set up CI (GitHub Actions / Azure DevOps)
- [ ] Agent eval: 20+ golden questions with expected tools

### Phase 4 — Hardening

- [ ] Production env config
- [ ] Rate limiting
- [ ] JSON logs + log aggregation
- [ ] Alerts on health/readiness failures
- [ ] Security review

### Phase 5 — Enhance

- [ ] Redis memory
- [ ] Native streaming
- [ ] Full OTel
- [ ] WhatsApp OR OpenAI (business priority)

---

## Quick Reference — Key Files

| Concern | Path |
|---------|------|
| App entry | `app/main.py` |
| Settings | `app/core/config/settings.py` |
| IAM client | `app/infrastructure/iam/client.py` |
| IAM middleware | `app/presentation/http/middleware/iam_auth.py` |
| Permissions | `app/application/permissions/service.py` |
| Tool registry | `app/infrastructure/tools/registry.py` |
| Add tools | `app/infrastructure/tools/definitions/` |
| Agent | `app/infrastructure/agents/tool_calling_agent.py` |
| Agent factory | `app/infrastructure/agents/factory.py` |
| Examples | `examples/` |

---

## Getting Help

1. Read `AI_ARCHITECTURE_CONTEXT.md` for project rules
2. Read `README.md` for setup
3. Run `pytest tests/unit -v` to verify local state
4. Check `examples/` for IAM, tools, and agent patterns

**Golden rule:** If you're about to add SQL, business logic, or permission checks in the orchestrator — stop. Put it in an existing microservice and expose it as a tool.

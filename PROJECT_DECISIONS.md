# Project Decisions — AI Orchestrator

> **Purpose:** Record architecture decisions and the reasoning behind them.
> **Audience:** Current and future developers joining the PetaxAI platform.
> **Format:** Each decision includes context, decision, rationale, consequences, and status.
> **Last updated:** May 2026

---

## How to Use This Document

- **Before changing architecture**, check if a decision already exists here.
- **When making a new significant choice**, add an entry using the template at the bottom.
- **When reversing a decision**, mark the old entry as *Superseded* and link to the new one.
- Decisions marked **Accepted** are active project policy unless noted otherwise.

---

## Decision Index

| ID | Decision | Status |
|----|----------|--------|
| [ADR-001](#adr-001-ai-orchestrator-as-a-separate-service) | AI Orchestrator as a separate service | Accepted |
| [ADR-002](#adr-002-ai-never-accesses-the-database-directly) | AI never accesses DB directly | Accepted |
| [ADR-003](#adr-003-tools-call-existing-http-apis-only) | Tools call HTTP APIs only | Accepted |
| [ADR-004](#adr-004-iam-owns-all-permissions) | IAM owns all permissions | Accepted |
| [ADR-005](#adr-005-langchain-for-tool-calling) | LangChain for tool calling | Accepted |
| [ADR-006](#adr-006-ollama--qwen25-for-initial-llm) | Ollama + Qwen2.5 for initial LLM | Accepted |
| [ADR-007](#adr-007-clean-architecture--async-first) | Clean architecture + async-first | Accepted |
| [ADR-008](#adr-008-future-llm-migration-strategy) | Future LLM migration strategy | Accepted |
| [ADR-009](#adr-009-scaling-approach) | Scaling approach | Accepted |
| [ADR-010](#adr-010-security-principles) | Security principles | Accepted |
| [ADR-011](#adr-011-multi-channel-strategy) | Multi-channel strategy | Accepted |

---

## ADR-001: AI Orchestrator as a Separate Service

**Status:** Accepted  
**Date:** 2026

### Context

PetaxAI already has a React frontend, IAM service, multiple FastAPI microservices, and PostgreSQL databases with full CRUD APIs. Users need a conversational way to interact with the platform without building AI logic into every service.

### Decision

Add a dedicated **AI Orchestrator** microservice that sits between users and existing APIs. It is a thin, stateless (initially) conversational layer — not a replacement for business services.

### Rationale

- **Separation of concerns:** Business rules stay in domain microservices; AI handles intent, tool selection, and response formatting only.
- **Independent evolution:** LLM stack, prompts, and agent behavior can change without touching CRM, billing, or user services.
- **Single entry point for AI:** One place to enforce AI safety rules (no SQL, no permission bypass, audit logging).
- **Reusability:** Web app, WhatsApp, and future voice channels all share the same orchestrator.

### Consequences

- ✅ Clear boundary: orchestrator orchestrates, microservices own data and logic.
- ✅ Easier to test AI behavior in isolation.
- ⚠️ Extra network hop per tool call (acceptable for conversational UX).
- ⚠️ Requires disciplined tool development — every capability needs an API tool.

### Architecture Flow

```
User Chat → AI Orchestrator → IAM → Allowed Tools → Existing APIs → Microservices → PostgreSQL
```

---

## ADR-002: AI Never Accesses the Database Directly

**Status:** Accepted  
**Date:** 2026

### Context

LLMs can generate SQL. Direct database access would bypass validation, authorization, audit trails, and business rules already implemented in microservices.

### Decision

The AI Orchestrator **must never** connect to PostgreSQL (or any database) for business data. It may use Redis later for session/memory only — not as a source of business truth.

### Rationale

- **Security:** SQL injection and data exfiltration risks are eliminated at the AI layer.
- **Authorization:** Databases cannot enforce IAM module permissions; APIs can.
- **Data integrity:** Business validation lives in microservices — duplicating it in AI would drift over time.
- **Auditability:** API calls are logged and traceable; ad-hoc SQL is not.
- **Compliance:** Easier to explain and audit "AI only calls approved APIs."

### Consequences

- ✅ Strong safety boundary; LLM cannot "query around" permissions.
- ✅ Existing APIs remain the single source of truth.
- ⚠️ Every new AI capability requires a corresponding API (and tool) — by design.
- ❌ AI cannot perform ad-hoc analytics unless an API exists for it.

### Enforcement

- No database drivers in orchestrator dependencies for business data.
- System prompts explicitly forbid SQL generation.
- Code review checklist: tools must use `BaseAPITool` / HTTP clients only.
- Architecture reviews reject any PR adding direct DB access.

---

## ADR-003: Tools Call Existing HTTP APIs Only

**Status:** Accepted  
**Date:** 2026

### Context

The orchestrator needs to perform actions (list users, create customers, etc.) on behalf of users. There are multiple ways to implement this: direct DB, embedded business logic, or HTTP API calls.

### Decision

Every AI **tool** is a thin adapter that calls an **existing microservice HTTP API**. Tools declare required IAM permissions and return structured JSON responses. No business logic in tools.

### Rationale

- **Reuse:** CRUD APIs, Excel upload, and validation already exist — don't rebuild them.
- **Consistency:** Web UI and AI use the same endpoints → same behavior.
- **Permission alignment:** Tool `required_permissions` map to IAM; API enforces authorization server-side.
- **Testability:** Tools are mockable HTTP calls; no DB fixtures in AI tests.
- **LangChain fit:** Tool calling maps naturally to "function → HTTP request → result."

### Tool Pattern

```python
@orchestrator_tool(
    name="create_customer",
    required_permissions=["customers:create"],
    service="customer-service",
    operation=ToolOperation.CREATE,
)
async def create_customer(ctx, name: str, email: str):
    return await _customer_api.create(ctx, {"name": name, "email": email}, ...)
```

### Consequences

- ✅ Modular: one file per domain; register in `loader.py`.
- ✅ Dynamic: only IAM-allowed tools reach the agent per request.
- ⚠️ Latency: each tool call is an HTTP round-trip.
- ⚠️ API must exist before AI can do something — intentional gate.

---

## ADR-004: IAM Owns All Permissions

**Status:** Accepted  
**Date:** 2026

### Context

RBAC, module permissions, and user management already live in the Node.js IAM service. The AI layer could theoretically infer or cache permissions locally and make access decisions.

### Decision

The orchestrator **never decides permissions**. It delegates entirely to IAM:

1. Validate JWT via IAM
2. Fetch permissions, module access, and allowed actions
3. Filter registered tools to those the user may use
4. Pass user token through to downstream API calls (APIs re-validate)

### Rationale

- **Single authority:** Permission changes in IAM apply immediately (with cache TTL).
- **No drift:** AI won't have a parallel permission model that diverges from the platform.
- **Existing investment:** IAM already handles roles, modules, and JWT — reuse it.
- **Defense in depth:** Tool filtering + API authorization = two layers.

### Implementation

- `IAMClient` — validate, permissions, modules, actions, TTL cache
- `IAMAuthMiddleware` — attaches `UserContext` to every request
- `PermissionService` — resolves context, loads allowed tools
- `UserContext.effective_permissions` — merged set for tool filtering only (derived from IAM, not invented)

### Consequences

- ✅ Security model stays centralized and familiar to the platform team.
- ✅ New tools only need IAM permission strings documented — no AI-side RBAC code.
- ⚠️ IAM availability affects all chat (mitigated by cache + graceful errors).
- ❌ Orchestrator cannot grant extra permissions "for convenience."

---

## ADR-005: LangChain for Tool Calling

**Status:** Accepted  
**Date:** 2026

### Context

We need an LLM integration that supports structured tool/function calling, works with Ollama and future OpenAI, and has an active ecosystem.

### Decision

Use **LangChain** + **LangGraph** (`create_react_agent`) for tool-calling orchestration. The agent is **tool-calling only** — bounded ReAct loop, not an autonomous planner.

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Raw Ollama API** | Minimal deps | Manual tool loop, no standard abstractions | Rejected |
| **LangChain + LangGraph** | Tool calling, providers, community | Dependency weight | **Chosen** |
| **Custom agent loop** | Full control | Maintenance burden, reinventing patterns | Rejected |
| **OpenAI Assistants API** | Managed | Vendor lock-in, cloud-only for now | Deferred |

### Rationale

- **Tool calling:** First-class `StructuredTool` support with Pydantic schemas.
- **Provider abstraction:** Swap Ollama ↔ OpenAI via factory without rewriting agent logic.
- **Bounded behavior:** LangGraph ReAct with `recursion_limit` — not open-ended autonomy.
- **Ecosystem:** Integrations for memory, streaming, and observability when needed.

### Constraints (By Design)

- No SQL generation (prompt + architecture rules).
- No autonomous multi-step planning beyond tool loop.
- Deterministic defaults: `temperature=0`, fixed `seed`.
- Structured output via `AgentOutputParser` — not free-form only.

### Consequences

- ✅ Faster delivery of tool-calling features.
- ✅ Clear upgrade path to streaming (`agent.astream()`).
- ⚠️ LangChain API changes require occasional updates.
- ⚠️ Team should understand LangGraph message flow for debugging.

---

## ADR-006: Ollama + Qwen2.5 for Initial LLM

**Status:** Accepted  
**Date:** 2026

### Context

The platform needs local, open-source LLM support now, with optional cloud migration later. Requirements include tool calling, reasonable quality, and controllable cost.

### Decision

Use **Ollama** as the default LLM runtime with **Qwen2.5:7b** as the default model.

### Rationale

- **On-prem / dev-friendly:** Run locally and in Docker without API keys or cloud dependency.
- **Cost:** No per-token billing during development and early production.
- **Tool calling:** Qwen2.5 supports function calling via Ollama.
- **Data residency:** Conversations and inference stay within your infrastructure.
- **Determinism:** Ollama supports temperature and seed for reproducible behavior.

### Configuration Defaults

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
AGENT_TEMPERATURE=0.0
AGENT_SEED=42
```

### Consequences

- ✅ No cloud LLM dependency for MVP.
- ✅ docker-compose includes Ollama sidecar.
- ⚠️ GPU recommended for production throughput.
- ⚠️ Model quality may lag GPT-4 class models for complex reasoning.
- 🔶 OpenAI provider stub exists for future migration (see ADR-008).

---

## ADR-007: Clean Architecture + Async-First

**Status:** Accepted  
**Date:** 2026

### Context

The service must scale, be testable, and remain maintainable as tools and channels grow.

### Decision

Organize code in **clean architecture layers** with **async-first** I/O throughout.

### Layer Structure

| Layer | Path | Rule |
|-------|------|------|
| **Presentation** | `app/presentation/` | HTTP, WebSocket, webhooks — no business logic |
| **Application** | `app/application/` | Use cases: chat, permissions, tool registry |
| **Domain** | `app/domain/` | Models, prompts — zero infrastructure imports |
| **Infrastructure** | `app/infrastructure/` | IAM, HTTP clients, LLM, tools, channels |
| **Bootstrap** | `app/bootstrap/` | DI container, app factory, lifespan |
| **Core** | `app/core/` | Config, logging, observability, exceptions |

### Rationale

- **Testability:** Mock ports at application boundaries; unit test domain without HTTP.
- **Replaceability:** Swap Ollama for OpenAI, in-memory for Redis, without touching use cases.
- **Team clarity:** New developers know where code belongs.
- **Async:** FastAPI + httpx async clients handle concurrent chat without blocking.

### Consequences

- ✅ DI via `AppContainer` — explicit wiring, test overrides.
- ⚠️ More folders than a minimal FastAPI app — intentional tradeoff for enterprise scale.

---

## ADR-008: Future LLM Migration Strategy

**Status:** Accepted  
**Date:** 2026

### Context

Ollama suits dev and cost-sensitive deployments. Production may need higher accuracy, lower ops burden, or cloud-managed inference.

### Decision

Support **multiple LLM providers** behind a factory interface. Migrate incrementally — never big-bang.

### Strategy

```
Phase 1 (now):     Ollama + Qwen2.5 — default everywhere
Phase 2:           Dual-provider — env-level switch (LLM_PROVIDER=openai)
Phase 3:           Eval-driven — benchmark tool-calling accuracy per provider
Phase 4 (optional): Per-tenant or per-route provider selection
```

### Provider Interface

- `app/infrastructure/llm/providers/ollama.py`
- `app/infrastructure/llm/providers/openai.py`
- `app/infrastructure/agents/factory.py` — creates LLM from config

### Migration Checklist (When Moving to OpenAI)

1. Set `OPENAI_API_KEY` in secrets manager
2. Run golden eval suite (same tools, same prompts)
3. Compare: tool selection accuracy, latency, cost per conversation
4. Enable in staging first; keep Ollama as rollback (`LLM_PROVIDER=ollama`)
5. Add token/cost tracking to audit metadata

### Rationale

- **No lock-in:** Agent and tools unchanged; only provider swaps.
- **Risk reduction:** Rollback is an env var change.
- **Business flexibility:** Choose cost vs quality per environment.

### Consequences

- ✅ Azure OpenAI path possible for enterprise compliance.
- ⚠️ Prompt tuning may differ slightly between models — budget eval time.

---

## ADR-009: Scaling Approach

**Status:** Accepted  
**Date:** 2026

### Context

Chat workloads are I/O-bound (LLM inference, HTTP tool calls, IAM lookups). The orchestrator must scale horizontally without shared mutable state in the application layer.

### Decision

Design the orchestrator as **stateless** (Phase 1). Push shared state to **Redis** when conversation memory is needed. Scale **Ollama separately** from the API tier.

### Scaling Dimensions

| Component | Scale Strategy |
|-----------|----------------|
| **AI Orchestrator API** | Horizontal — multiple FastAPI replicas behind load balancer |
| **Ollama** | Separate GPU nodes or dedicated inference service; not 1:1 with API pods |
| **IAM** | Cached permissions (TTL 300s default); IAM service scales independently |
| **Microservices** | Existing platform scaling — orchestrator is just another client |
| **Redis (future)** | Conversation memory, distributed IAM cache, rate limits |

### Stateless Principles

- No in-process session state required for single-turn chat.
- JWT + IAM cache per request; conversation_id for multi-turn when memory enabled.
- Tool registry loaded at startup — same across all replicas.

### Bottlenecks to Monitor

1. **Ollama inference latency** — primary user-perceived delay
2. **Tool call fan-out** — agent may call multiple APIs sequentially
3. **IAM latency** — mitigated by cache
4. **Agent iteration count** — cap via `AGENT_MAX_ITERATIONS`

### Consequences

- ✅ Kubernetes-friendly: scale API pods on CPU/request rate.
- ⚠️ Ollama requires separate capacity planning (GPU/memory).
- 🔶 Redis needed before multi-turn memory works across replicas.

---

## ADR-010: Security Principles

**Status:** Accepted  
**Date:** 2026

### Context

The orchestrator handles user messages, JWT tokens, and acts on behalf of users via APIs. It is a high-trust component that must fail safely.

### Decision

Adopt the following **non-negotiable security principles**:

### Principles

| # | Principle | Implementation |
|---|-----------|----------------|
| 1 | **IAM is authoritative** | All authz via IAM; no local permission invention |
| 2 | **Token never reaches LLM** | Injected server-side in tool wrapper only |
| 3 | **Token never logged** | Audit logs use user_id, not raw JWT |
| 4 | **No direct DB access** | ADR-002 |
| 5 | **No SQL generation** | Prompt rules + code review |
| 6 | **APIs re-validate** | User token forwarded; downstream services enforce authz |
| 7 | **Least privilege tools** | Agent receives minimum tool set per IAM permissions |
| 8 | **Structured audit trail** | Chat, tool invoke, auth failure events |
| 9 | **Fail closed** | Invalid token → 401; IAM down → 502, not anonymous access |
| 10 | **Production hardening** | No `/docs` in prod; JSON logs; CORS restricted; secrets in vault |

### Threat Model (Simplified)

| Threat | Mitigation |
|--------|------------|
| User prompts SQL injection | No DB access; tools are HTTP only |
| Permission bypass via prompt | Tool registry filtered before agent sees tools |
| Token exfiltration via LLM | Token excluded from tool schemas and prompts |
| Hallucinated data | Agent instructed to use tool results only |
| IAM spoofing | All permission fetches server-side to IAM URL |

### Consequences

- ✅ Defense in depth aligned with enterprise expectations.
- ⚠️ Security reviews required for every new tool and channel adapter.

---

## ADR-011: Multi-Channel Strategy

**Status:** Accepted  
**Date:** 2026

### Context

Users will interact via web chat now, WhatsApp later, and potentially voice. Each channel has different UX constraints but the same underlying capabilities.

### Decision

Use a **channel adapter pattern** in infrastructure — one **shared agent pipeline**, multiple **presentation adapters**.

### Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  REST API   │  │  WhatsApp   │  │  WebSocket  │  ← Presentation
│  (exists)   │  │  (planned)  │  │  (planned)  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌───────────────────┐
              │    ChatService    │  ← Application (channel-agnostic)
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  ToolCallingAgent │  ← Same agent, same tools, same IAM
              └───────────────────┘
```

### Channel-Specific Concerns

| Channel | Adapter Location | Special Handling |
|---------|----------------|------------------|
| **REST** | `presentation/http/v1/` | Standard JSON chat API |
| **WhatsApp** | `infrastructure/channels/whatsapp/` | Short prompts, webhook, Meta Graph API |
| **WebSocket** | `presentation/websocket/` | Streaming chunks, connection lifecycle |
| **Voice (future)** | TBD | STT/TTS adapters → same ChatService |

### Prompt Templates

- `orchestrator` — default web/professional tone
- `whatsapp` — shorter, mobile-friendly (exists in prompt templates)

### Rationale

- **DRY:** One agent, one tool registry, one permission model.
- **Consistency:** Same IAM rules regardless of how user asks.
- **Incremental delivery:** Add channels without rewriting core.

### Consequences

- ✅ WhatsApp stub already in place; wire to ChatService when ready.
- ⚠️ WhatsApp needs user identity mapping (phone → platform user).
- ⚠️ Each channel needs its own rate limits and webhook security.

---

## Summary — Guiding Principles for Future Developers

When in doubt, ask:

1. **Does this belong in a microservice?** → If yes, build an API and a tool — not logic in the orchestrator.
2. **Does this access the database?** → Stop. Use an API.
3. **Does this check permissions?** → Only via IAM + tool filtering — never invent rules here.
4. **Does this add business logic?** → Wrong layer. Orchestrator formats and routes only.
5. **Does this need a new channel?** → Add an adapter; reuse ChatService and the agent.

**The orchestrator is a conversational shell around existing APIs — not a new backend.**

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [AI_ARCHITECTURE_CONTEXT.md](./AI_ARCHITECTURE_CONTEXT.md) | Original project context and rules |
| [IMPLEMENTATION_STEPS.md](./IMPLEMENTATION_STEPS.md) | Phased roadmap, checklists, migration plans |
| [README.md](./README.md) | Setup, API reference, quick start |

---

## Template for New Decisions

```markdown
## ADR-XXX: [Title]

**Status:** Proposed | Accepted | Superseded by ADR-YYY
**Date:** YYYY-MM

### Context
[What problem or question led to this decision?]

### Decision
[What was decided?]

### Alternatives Considered
[What else was evaluated?]

### Rationale
[Why this choice?]

### Consequences
[Positive, negative, and neutral outcomes]

### Enforcement
[How do we ensure this decision is followed?]
```

---

*Maintainers: Update this file when architecture changes. Prefer updating an existing ADR over informal decisions in chat or PR comments.*

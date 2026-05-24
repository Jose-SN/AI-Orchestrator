# Project Context

We already have an enterprise microservice architecture.

Current services:

1. React Frontend
2. IAM Service (Node.js)
   - JWT authentication
   - RBAC permissions
   - module permissions
   - user management
3. Multiple Python FastAPI microservices
4. PostgreSQL databases
5. Existing CRUD APIs already implemented
6. Excel upload functionality already exists

We are adding a new AI Orchestrator Service.

The AI service should:
- act as an intelligent conversational layer
- NEVER directly access PostgreSQL
- NEVER directly handle permissions
- NEVER contain business logic
- ONLY orchestrate APIs
- ONLY understand user intent
- ONLY call existing APIs
- ONLY format conversational responses

Architecture flow:

User Chat
→ AI Orchestrator
→ IAM Permission Check
→ Allowed Tools Registration
→ Existing APIs
→ Existing Microservices
→ PostgreSQL

Future Requirements:
- WhatsApp integration
- voice integration
- OpenAI support later
- local open-source LLM support now
- scalable enterprise architecture
- audit logging
- streaming responses
- multi-tenant support later

Initial AI stack:
- Python FastAPI
- LangChain
- Ollama
- Qwen2.5:7b
- Redis (later)
- PostgreSQL optional for chat history

Important Rules:
- AI should NEVER generate raw SQL
- AI should NEVER bypass APIs
- AI should NEVER decide permissions
- Existing APIs remain source of truth
- AI is only a conversational interface

Recommended Pattern:
User Message
→ Intent Extraction
→ Tool Selection
→ Existing API Calls
→ Response Formatting

We want:
- clean architecture
- scalable folder structure
- async-first implementation
- Docker-ready setup
- enterprise coding standards
- modular tool registration
- dynamic permissions-based tools
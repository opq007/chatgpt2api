# ChatGPT2API - Agent Guide

## Project Overview

ChatGPT2API is a reverse-engineered ChatGPT wrapper providing OpenAI-compatible image generation/editing APIs with account pool management. It consists of a Python FastAPI backend and Next.js frontend.

**Tech Stack:**
- Backend: Python 3.13+, FastAPI, uvicorn, SQLAlchemy, curl-cffi
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS
- Package Managers: `uv` (Python), `bun` (Node.js)
- Deployment: Docker with multi-arch support (amd64/arm64)

## Development Commands

### Backend Development
```bash
# Install dependencies
uv sync

# Run backend server
uv run main.py
```

Backend runs on port 8000 by default (configurable via uvicorn args).

### Frontend Development
```bash
cd web
bun install
bun run dev
```

Frontend dev server runs on port 3000 with hot reload.

### Docker Development
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f app
```

### Testing
```bash
# Run all tests
python -m unittest discover test

# Run specific test
python -m unittest test.test_v1_images_generations
```

Tests use `unittest` framework. Test files are in `test/` directory.

## Architecture

### Backend Structure
```
api/              # FastAPI routes and app setup
  ├── app.py      # Main FastAPI app with CORS, static files, lifespan
  ├── ai.py       # OpenAI-compatible endpoints (/v1/*)
  ├── accounts.py # Account pool management API
  ├── image_tasks.py # Image task tracking
  ├── register.py # Account registration
  └── system.py   # System status and config

services/         # Business logic
  ├── account_service.py    # Account pool management (thread-safe)
  ├── config.py             # Configuration management
  ├── openai_backend_api.py # ChatGPT backend API wrapper
  ├── storage/              # Storage backends (JSON/SQLite/Postgres/Git)
  └── protocol/             # OpenAI protocol implementations

utils/            # Utilities (logging, PoW, Turnstile, helpers)
main.py           # Backend entry point
```

### Frontend Structure
```
web/
  ├── src/        # Next.js app source
  ├── package.json
  └── next.config.ts
```

### Key Entry Points
- **Backend**: `main.py` → `api/app.py:create_app()`
- **Frontend**: `web/src/app/page.tsx` (Next.js App Router)

## Configuration

### Required Configuration
- `config.json` must contain `auth-key` field
- Or set environment variable `CHATGPT2API_AUTH_KEY`

### Storage Backends
Set via `STORAGE_BACKEND` environment variable:
- `json` (default): Local JSON file at `data/accounts.json`
- `sqlite`: Local SQLite database at `data/accounts.db`
- `postgres`: PostgreSQL via `DATABASE_URL`
- `git`: Git private repo via `GIT_REPO_URL` and `GIT_TOKEN`

Example:
```bash
STORAGE_BACKEND=postgres
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Important Config Fields
- `auth-key`: API authentication key (required)
- `refresh_account_interval_minute`: Account refresh interval (default: 60)
- `image_retention_days`: Image cleanup threshold (default: 15)
- `image_account_concurrency`: Max concurrent image requests per account (default: 3)
- `auto_remove_invalid_accounts`: Auto-remove failed tokens (default: true)
- `auto_remove_rate_limited_accounts`: Auto-remove rate-limited accounts (default: false)

## API Endpoints

All AI endpoints require `Authorization: Bearer <auth-key>` header.

### OpenAI-Compatible Endpoints
- `GET /v1/models` - List available models
- `POST /v1/images/generations` - Image generation
- `POST /v1/images/edits` - Image editing (multipart/form-data)
- `POST /v1/chat/completions` - Chat completions (image-focused)
- `POST /v1/responses` - Responses API (image generation tools)
- `POST /v1/messages` - Anthropic-compatible messages

### Management Endpoints
- Account pool management: `/api/accounts/*`
- Image tasks: `/api/image-tasks/*`
- System config: `/api/system/*`

## Account Pool Management

The account pool (`services/account_service.py`) is thread-safe with:
- Round-robin token selection
- Automatic quota tracking and rate limit detection
- Concurrent request limiting per account (`image_account_concurrency`)
- Automatic cleanup of invalid/rate-limited accounts (configurable)

**Key Methods:**
- `get_available_access_token()` - Get next available token for image generation
- `mark_image_result(token, success)` - Update account status after request
- `refresh_accounts(tokens)` - Batch refresh account info
- `fetch_remote_info(token)` - Fetch latest account info from ChatGPT

## Storage Backend Pattern

All storage backends implement `services/storage/base.py:StorageBackend` interface:
- `load_accounts()` - Load account list
- `save_accounts(accounts)` - Save account list
- `load_auth_keys()` - Load auth keys
- `save_auth_keys(keys)` - Save auth keys

Factory pattern in `services/storage/factory.py:create_storage_backend()`.

## Important Constraints

### Thread Safety
- `AccountService` uses locks for all account operations
- Image slot acquisition uses condition variables for concurrency control
- Never access `_accounts` dict directly - use service methods

### Image Generation Flow
1. Acquire token via `get_available_access_token()` (blocks if no quota)
2. Make request to ChatGPT backend
3. Call `mark_image_result(token, success)` to update status
4. Always call `release_image_slot(token)` in finally block

### Configuration Loading
- Config loads from `config.json` at startup
- Environment variables override config values
- `auth-key` validation happens early in startup

## Testing Notes

- Tests use `unittest` framework
- Test files mirror API structure (e.g., `test_v1_images_generations.py`)
- Tests require backend running on `http://localhost:8000`
- Default test auth key: `chatgpt2api`

## Docker Deployment

- Multi-stage build: web build → app runtime
- Supports `linux/amd64` and `linux/arm64`
- Exposes port 80
- Volume mounts: `./data:/app/data`, `./config.json:/app/config.json`
- Environment variables in `docker-compose.yml` override config

## Common Gotchas

1. **Missing auth-key**: Backend will fail to start with clear error message
2. **Storage backend mismatch**: Ensure `DATABASE_URL` or `GIT_REPO_URL` matches `STORAGE_BACKEND`
3. **Account pool exhaustion**: If all accounts are rate-limited, requests will block indefinitely
4. **Image cleanup**: Old images are automatically cleaned based on `image_retention_days`
5. **Proxy configuration**: Global proxy applies to all outbound requests via `services/proxy_service.py`

## Feature Status

See `docs/feature-status.en.md` for detailed feature status. Key points:
- ✅ Image generation/editing APIs fully implemented
- ✅ Account pool management with auto-refresh
- ✅ Multiple storage backends
- ⚠️ Advanced token scheduling still in progress
- ❌ Anthropic protocol support pending
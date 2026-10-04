# Zero-Trust API Gateway

This project is a modular FastAPI microservice built around Zero-Trust security principles. Instead of relying on simple perimeter defense, every request is authenticated, authorized by role, and checked against an active revocation list before reaching the underlying resources.

I built this repository to demonstrate a practical DevSecOps workflow, combining application-level security controls with container hardening and a multi-stage CI validation pipeline.

## System Overview & Design Decisions

### Authentication and Stateful Token Revocation
Standard JWT implementations are stateless, meaning once a token is issued, it remains valid until it expires, even if a user logs out. To solve this without sacrificing JWT performance:
- Every token is signed (`HS256`) with a 15-minute lifespan and assigned a unique identifier (`jti`).
- When a user logs out via `/logout`, the token's `jti` is pushed to a **Redis** blacklist with a TTL matching its remaining validity.
- The authentication dependency (`verify_token`) checks Redis on every incoming request, immediately rejecting revoked tokens with `401 Unauthorized`.

### Role-Based Access Control (RBAC)
Authentication and authorization are decoupled inside `app/security.py`. While any authenticated user (`admin` or `viewer`) can read from `/vault-data`, destructive operations like `/admin/purge-logs` are guarded by a role-checking dependency that enforces `admin` privileges and returns `403 Forbidden` for lower-privileged accounts.

### Database & Container Infrastructure
- **PostgreSQL 15:** Stores user records with **Bcrypt** password hashes (`passlib`). All database interactions use parameterized queries (`psycopg2`) to prevent SQL injection.
- **Multi-Stage Docker Build:** The `Dockerfile` separates dependency compilation (`builder` stage) from the runtime environment. The final image runs under a non-root user (`appuser`) to minimize the container's attack surface.
- **Zero Hardcoded Secrets:** All database credentials, Redis hosts, and signing keys are injected via environment variables. `.env` is ignored by Git, and `.env.example` documents the required variables.

### Interactive Testing Dashboard
To make testing easier without relying solely on cURL or Swagger, the root endpoint (`/`) serves a lightweight vanilla JS/CSS control panel (`static/`). It allows switching between `alex` (admin) and `guest` (viewer) accounts to observe RBAC restrictions and Redis token revocation in real time.

## Automated CI Security Pipeline

Every push and pull request to `main` triggers the GitHub Actions workflow (`.github/workflows/devsecops-pipeline.yml`), which acts as a four-step security gate:

1. **Gitleaks:** Scans the commit history to ensure no secrets or `.env` files were accidentally committed.
2. **Bandit (SAST):** Performs static analysis on the `app/` directory to catch common Python security issues.
3. **Pytest Security Suite:** Runs automated tests (`tests/test_security.py`) verifying that unauthenticated requests, tampered tokens, revoked tokens, and unauthorized role escalations are properly blocked.
4. **Trivy:** Builds the production Docker image in the runner and scans both OS packages and Python libraries for high and critical CVEs.

## Local Setup

1. Clone the repository and create your environment file from the template:
```bash
cp .env.example .env
```

2. Build and start the containers (PostgreSQL, Redis, and FastAPI):
```bash
docker compose up --build
```

3. Once the services are healthy, access the endpoints at:
- **Security Control Panel:** `http://localhost:8000/`
- **Swagger UI Documentation:** `http://localhost:8000/docs`
- **Healthcheck Endpoint:** `http://localhost:8000/health`


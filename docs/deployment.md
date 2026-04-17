# Deployment Runbook

## 1) Production env files

Create:

- `backend/.env.production` from `backend/.env.production.example`
- `frontend/.env.production` from `frontend/.env.production.example`

Set strong secrets and production host URLs.

## 2) Managed stack (Supabase + Qdrant + Vercel)

Recommended topology:

- Frontend: Vercel
- Primary database: Supabase Postgres
- Vector database: Qdrant Cloud
- Backend + workers: Docker on your server

Update `backend/.env.production` with:

- `DATABASE_URL` from Supabase (pooler URL preferred)
- `QDRANT_URL` from Qdrant Cloud
- `CORS_ORIGINS` including your Vercel domain
- strong `JWT_SECRET`

Run backend/workers:

```bash
docker compose -f infra/docker-compose.managed.yml up -d
```

Deploy frontend on Vercel:

- Workflow: `.github/workflows/deploy-vercel.yml`
- Required secrets:
  - `VERCEL_TOKEN`

## 3) Self-contained stack run (optional)

From repo root:

```bash
docker compose -f infra/docker-compose.prod.yml up -d
```

## 3b) HTTPS with Caddy (optional if not using Vercel frontend)

Create DNS A records:

- `APP_DOMAIN` -> your server IP (e.g. `app.your-domain.example`)
- `API_DOMAIN` -> your server IP (e.g. `api.your-domain.example`)

Set shell env vars on host:

- `APP_DOMAIN`
- `API_DOMAIN`
- `ACME_EMAIL`
- optional: `GITHUB_REPOSITORY_OWNER`, `IMAGE_TAG`

Then run:

```bash
docker compose -f infra/docker-compose.prod.yml -f infra/docker-compose.tls.yml up -d
```

## 4) GitHub Actions backend image deployment

Workflow: `.github/workflows/deploy.yml`

- Trigger via tag push (`v*`) or manual dispatch
- Builds and pushes these images to GHCR:
  - `dsgvo-copilot-backend`
  - `dsgvo-copilot-worker`
  - `dsgvo-copilot-ml-worker`
  - `dsgvo-copilot-frontend`
- Optional SSH deploy step pulls and restarts stack on host

## 5) Required GitHub secrets

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`

If these are missing, build-and-push still runs; deploy step is skipped.

## 6) Post-deploy checks

- Backend health: `GET /health`
- Frontend reachable on port 3000 or reverse-proxy domain
- Login + risk report API smoke
- ML queue smoke:
  - `POST /ml/rerank`
  - `GET /ml/tasks/{task_id}`

For TLS setup, validate:

- `https://$APP_DOMAIN` returns frontend
- `https://$API_DOMAIN/health` returns backend health

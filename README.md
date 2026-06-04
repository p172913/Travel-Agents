# TravelSouls

An AI-powered multi-agent travel planning platform.

## Project Structure

- **frontend/**: Next.js frontend application.
- **api-gateway/**: FastAPI application exposing endpoints to the frontend.
- **orchestrator/**: LangGraph orchestrator to coordinate multi-agent queries.
- **research-agent/**: Destination, weather, and attractions research agent.
- **booking-agent/**: Flight and hotel search agent.
- **budget-agent/**: Budget allocation and expense prediction agent.
- **recommendation-agent/**: Personalization and attraction recommendation agent.
- **shared/**: Shared schemas, helper functions, and database models.
- **infra/**: Docker Compose, configuration files, and database initialization scripts.

## Getting Started

This repository contains a travel planning prototype with a complete API gateway, multi-agent backend services, and a Next.js frontend.

### Local development

- Backend: `api_gateway/main.py`
- Frontend: `frontend/src/app`
- Local stack: `infra/docker-compose.yml`

### Production readiness

The project now includes production-ready hosting infrastructure without requiring authentication.

- `infra/docker-compose.prod.yml`: production-style Docker Compose stack
- `frontend/Dockerfile`: production build for the frontend
- `frontend/vercel.json`: Vercel frontend deployment config
- `frontend/.env.local.example`: frontend environment template
- `.github/workflows/deploy.yml`: AWS ECS deployment workflow
- `infra/aws/ecs-task-definition.json`: ECS task definition template
- `render.yaml`: Render deployment blueprint for the backend
- `.env.example`: environment variable template
- `HOSTING.md`: hosting instructions

## Hosting

You can deploy the frontend to Vercel from the `frontend/` directory, and host the backend on Render using `Dockerfile` or `render.yaml`.

See `HOSTING.md` for step-by-step deployment information.
